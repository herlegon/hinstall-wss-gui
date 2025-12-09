import asyncio
import json
from pathlib import Path
import signal
import sys
import time
from enum import Enum
import tomllib
from typing import Any, Optional, Callable
from websockets import (
    connect, ClientConnection,
    ConnectionClosedError, ConnectionClosedOK,
)

from hytils import lightcyan, orange, yellow
sys.path.append(str(Path(__file__).resolve().parent.parent))
from hinstall import (
    ilog,
)

class CommandState(Enum):
    """State machine states for command sequence"""
    IDLE = 'idle'
    PARSING = 'parsing'
    INSTALL = 'install'
    INSTALLING = 'installing'
    RESTART = 'restart'
    RESTARTING = 'restarting'
    FETCH_BACKEND_DETAILS = 'fetch_backend_details'
    FETCHING_BACKEND_DETAILS = 'fetching_backend_details'
    END = 'end'
    ERROR = 'error'


sys.path.append(str(Path(__file__).resolve().parent.parent.parent / "hwss"))
from api import (
    RequestMessage,
    deserialize,
    serialize,
    ResponseMessage,
    EventMessage,
    EventType,
    ResponseType,
    WssIdentity,
    InstallTask,
)




class WsInstallClient:
    def __init__(
        self,
        uri: str,
        install_config: dict,
        stages: int | list[int],
        on_message: Optional[Callable] = None
    ):
        # Stages from 0 to 2
        #   0: external packages
        #   1: backend packages
        #   2: AI packages
        self._uri = uri
        self.install_config = install_config
        self.stages: list[int] = (
            stages if isinstance(stages, list | tuple) else [stages,]
        )
        self.ws_cc: Optional[ClientConnection] = None
        self._running = False
        self._last_pong = None
        self._state = CommandState.IDLE
        self._on_message = on_message or self._default_message_handler
        self._loop = None
        self.event = ''


    async def _main(self):
        retries = 0
        delay = 0.5
        exception: str = ""

        ilog.info(f"[INFO] Connecting to {self._uri}")

        while self._running:
            try:
                async with connect(
                    uri=self._uri,
                    proxy=None,
                    ping_interval=3,
                    ping_timeout=1.5,
                ) as ws:
                    retries = 0
                    self.ws_cc = ws
                    ilog.info("[INFO] Connected to backend")
                    self._state = CommandState.IDLE

                    await asyncio.gather(
                        self._reception_task(),
                        self._heartbeat_loop(),
                        self.state_machine(),
                    )

            except (ConnectionClosedError, ConnectionClosedOK) as e:
                ilog.warning(f"[WARNING] WebSocket closed: {e}")
                self._state = CommandState.ERROR

            except Exception as e:
                retries += 1
                exception = str(e)
                ilog.error(f"[ERROR] Connection error ({retries}): {e}")
                if retries >= 3:
                    self._running = False
                    self._state = CommandState.ERROR
                self.ws_cc = None
                await asyncio.sleep(delay)

            finally:
                self.ws_cc = None
                if self._running:
                    await asyncio.sleep(delay)

        self._running = False
        self.ws_cc = None
        msg = f" with error: {exception}" if exception else ""
        ilog.info(f"[INFO] Connection loop terminated{msg}")


    async def start(self):
        """Start the WebSocket client"""
        self._running = True
        self._loop = asyncio.get_event_loop()
        await self._main()


    def stop(self):
        """Stop the WebSocket client"""
        self._running = False
        if self._loop and self._loop.is_running():
            # Try to close websocket to unblock recv loop
            async def close_ws():
                if self.ws_cc:
                    await self.ws_cc.close()

            asyncio.run_coroutine_threadsafe(close_ws(), self._loop)


    def _default_message_handler(self, msg: dict):
        # print(yellow(msg))
        # ilog.debug(f"Message received: {msg}")
        pass


    async def _reception_task(self):
        """Receive messages from server"""
        try:
            while self._running and self.ws_cc:
                msg = await self.ws_cc.recv()
                data: dict = deserialize(msg)

                # For debug
                # self._on_message(data)
                self.handle_received_message(data)

        except Exception as e:
            ilog.error(f"[ERROR] Receive loop error: {e}")



    def handle_received_message(self, data: dict):
        """Process and dispatch the received message based on its type"""
        try:
            # Check the 'type' field to determine if it's a Response or Event
            msg_type = data.get('type')

            if msg_type in ResponseType.__args__:
                response = ResponseMessage(**data)
                self.handle_response(response)

            elif msg_type in EventType.__args__:
                event = EventMessage(**data)
                self.handle_event(event)

            else:
                ilog.error(f"Unknown message type: {msg_type}")

        except Exception as e:
            ilog.error(f"[ERROR] Failed to handle received message: {e}")



    def handle_event(self, event: EventMessage) -> None:
        """Handle EventMessage"""
        if event.type == "msg":
            # Handle message event
            # print(orange(event))
            print(f"handle_event: {event}")
            pass

        elif event.type == "telemetry":
            # Handle telemetry event
            pass

        elif event.type == "status":
            # Handle status event
            pass


    def handle_response(self, response: ResponseMessage) -> None:
        """Handle ResponseMessage
        """
        if response.type == 'pong':
            self._last_pong = time.time()
            return

        if response.type != 'install':
            return

        task_result: dict = response.payload
        if 'status' in task_result.keys():
            self.event = task_result['status']

        print(response.payload)





    async def state_machine(self):
        """State machine that sends commands in sequence"""
        self.event = ''
        while self._running and self.ws_cc:

            try:
                if self._state == CommandState.IDLE:
                    task = {
                        'task_id': 'parse',
                        **self.install_config
                    }
                    await self.send_task(task)
                    self.event = ''
                    self._state = CommandState.PARSING


                elif self._state == CommandState.PARSING:
                    if self.event == 'parsed':
                        self._state = CommandState.INSTALL
                        self.event = ''
                    await asyncio.sleep(0.5)


                elif self._state == CommandState.INSTALL:
                    if not self.stages:
                        self._state = CommandState.END

                    await self.send_task(
                        InstallTask(stage=self.stages.pop())
                    )
                    self.event = ''
                    self._state = CommandState.INSTALLING


                elif self._state == CommandState.INSTALLING:
                    print("wait")
                    await asyncio.sleep(2)


                elif self._state == CommandState.RESTARTING:
                    # Wait for restart to complete
                    await asyncio.sleep(1)


                elif self._state == CommandState.ERROR:
                    ilog.info("[STATE] Error state reached, breaking state machine")
                    break

                elif self._state == CommandState.FETCH_BACKEND_DETAILS:
                    break


                else:
                    await asyncio.sleep(2)

            except Exception as e:
                ilog.error(f"[ERROR] State machine error: {e}")
                self._state = CommandState.ERROR
                break


    def process_reception(self, packet: dict):
        """Update state machine based on server response
        """
        packet_type: ResponseType = packet.get("type")
        payload = packet.get('payload', None)

        pprint(packet)
        # if response_type == 'pong':
        # elif response_type == 'status':
        # elif response_type == 'warning':
        # elif response_type == 'error':
        # elif response_type == 'exception':





        # if type == 'install' and status == "success":
        #     ilog.info("[RESPONSE] Install successful")
        #     self._state = CommandState.STARTING


        # elif type == "start" and status == "success":
        #     ilog.info("[RESPONSE] Start successful")
        #     self._state = CommandState.RUNNING


        # elif type == "restart" and status == "success":
        #     ilog.info("[RESPONSE] Restart successful")
        #     self._state = CommandState.RUNNING


        # elif type == "discard" and status == "success":
        #     ilog.info("[RESPONSE] Discard successful")
        #     self._state = CommandState.IDLE


        # elif status == 'error"'
        #     ilog.info(f"[RESPONSE] Command failed: {response.get('error', 'Unknown error')}")
        #     self._state = CommandState.ERROR



    async def _send_message(self, message: RequestMessage | str):
        """Send command to server"""
        if not self.ws_cc:
            ilog.warning("[WARNING] Attempted to send while not connected")
            return

        try:
            msg = (
                serialize(message)
                if not isinstance(message, str)
                else message
            )
            await self.ws_cc.send(msg)
            # ilog.info(f"[SEND] {msg}")

        except Exception as e:
            ilog.error(f"[ERROR] Send failed: {e}")


    async def send_task(self, task: dict[str, Any]):
        await self._send_message(
            RequestMessage(type='setup', payload=task)
        )


    async def send_restart_request(self):
        await self._send_message(RequestMessage(type='restart'))


    async def send_identify_request(self):
        await self._send_message(RequestMessage(type='identify'))


    async def send_shutdown_request(self):
        await self._send_message(RequestMessage(type='shutdowns'))



    async def _heartbeat_loop(self):
        """Send periodic heartbeat, to see if everything is ok
        while running a long task
        """
        heartbeat_msg = serialize(RequestMessage(type='heartbeat'))
        while self._running and self.ws_cc:
            try:
                await self._send_message(heartbeat_msg)

                if self._last_pong is None:
                    self._last_pong = time.time()

                elif time.time() - self._last_pong > 10:
                    ilog.error("[ERROR] Backend unresponsive")
                    self._state = CommandState.ERROR
                    break

                await asyncio.sleep(2)

            except Exception as e:
                ilog.error(f"[ERROR] Heartbeat error: {e}")
                break



# Example usage
async def main():
    server_ip: str = "127.0.0.1"
    port: int = 49990
    local_backend = True
    use_local_host = True

    tool = "hconvert"
    config_fp = (Path(__file__).parent.parent / "tests" / "configs" / f"{tool}.toml").resolve()

    # Load config
    print(f"loading config: {config_fp}")
    with open(config_fp, "rb") as f:
        toml_cfg: dict[str, Any] = tomllib.load(f)

    install_config = {
        'app_name': "hconvert",
        'cfg': json.dumps(toml_cfg),
        'local_backend': local_backend,
        'reinstall': False,
        'use_local_host': use_local_host,
        'local_host': ""
    }

    uri = f"ws://{server_ip}:{port}"
    client = WsInstallClient(
        uri,
        install_config=install_config,
        stages=1,
    )

    try:
        await client.start()
    except KeyboardInterrupt:
        print("[INFO] Shutting down...")
        client.stop()


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    asyncio.run(main())
