from __future__ import annotations
from dataclasses import asdict, dataclass
import logging
from pathlib import Path
from pprint import pprint
import subprocess
import sys
from typing import Any, Literal
from PySide6.QtCore import QThread, Signal
from hinstall import (
    download_install_ext_packages,
    ExtPackages,
    ilog,
    generate_backend_env,
    clean_invalid_distributions,
    g_backend_dirs,
)
from hinstall import get_python_version
from .log_handler import WorkerLogHandler
import asyncio
import json
import time
from enum import Enum

from typing import Optional, Callable
from websockets import (
    connect, ClientConnection,
    ConnectionClosedError, ConnectionClosedOK,
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



RequestType = Literal[
    'heartbeat',
    'identify',
    'restart',
    'shutdown',
    'telemetry',

    # applications:
    'setup',
    'convert',
    # ...
]


ResponseType = Literal[
    'pong',
    'identity',
    'setup',
]


EventType = Literal[
    'msg',
    'telemetry',
    'status',
]


SetupTaskId = Literal[
    'parse',
    'install',
]



@dataclass(slots=True)
class RequestMessage:
    type: RequestType
    payload: dict | None = None



@dataclass(slots=True)
class ResponseMessage:
    type: ResponseType
    payload: dict | None = None



@dataclass(slots=True)
class EventMessage:
    type: EventType
    payload: dict | None = None



def serialize(msg: RequestMessage) -> str:
    return json.dumps(asdict(msg))


def deserialize(msg: ResponseMessage | EventMessage) -> dict:
    return json.loads(msg)


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
        self._ws: Optional[ClientConnection] = None
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
                    self._ws = ws
                    ilog.info("[INFO] Connected to backend")
                    self._state = CommandState.IDLE

                    # Update pong timestamp when we receive a pong
                    ws.pong_handler = lambda _: setattr(self, "_last_pong", time.time())

                    await asyncio.gather(
                        self._reception_loop(),
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
                self._ws = None
                await asyncio.sleep(delay)

            finally:
                self._ws = None
                if self._running:
                    await asyncio.sleep(delay)

        self._running = False
        self._ws = None
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
                if self._ws:
                    await self._ws.close()

            asyncio.run_coroutine_threadsafe(close_ws(), self._loop)


    def _default_message_handler(self, msg: dict):
        ilog.debug(f"Message received: {msg}")



    async def _reception_loop(self):
        """Receive messages from server"""
        try:
            while self._running and self._ws:
                msg = await self._ws.recv()
                data: dict = deserialize(msg)

                # For debug
                self._on_message(data)
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


        task_result = response.payload
        print(task_result)






    async def state_machine(self):
        """State machine that sends commands in sequence"""
        self.event = ''
        while self._running and self._ws:

            try:
                if self._state == CommandState.IDLE:
                    task = {
                        'task_id': 'parse',
                        **self.install_config
                    }
                    await self.send_setup_task(task)
                    self.event = ''
                    self._state = CommandState.PARSING


                elif self._state == CommandState.PARSING:
                    if self.event == 'parsed':
                        self._state = CommandState.INSTALL
                    await asyncio.sleep(0.5)


                elif self._state == CommandState.INSTALL:
                    if not self.stages:
                        self._state = CommandState.END

                    stage_no = self.stages.pop()
                    task = {
                        'task_id': 'install',
                        'stage_no': stage_no
                    }
                    await self.send_setup_task(task)
                    self._state = CommandState.INSTALLING


                elif self._state == CommandState.INSTALLING:
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
        if not self._ws:
            ilog.warning("[WARNING] Attempted to send while not connected")
            return

        try:
            msg = (
                serialize(message)
                if not isinstance(message, str)
                else message
            )
            await self._ws.send(msg)
            ilog.info(f"[SEND] {msg}")

        except Exception as e:
            ilog.error(f"[ERROR] Send failed: {e}")


    async def send_setup_task(self, task: dict[str, Any]):
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
        while self._running and self._ws:
            try:
                await self._send_message(heartbeat_msg)

                if self._last_pong is None:
                    self._last_pong = time.time()

                elif time.time() - self._last_pong > 10:
                    ilog.error("[ERROR] Backend unresponsive")
                    self._state = CommandState.ERROR
                    break

                else:
                    print(time.time() - self._last_pong)

                await asyncio.sleep(2)

            except Exception as e:
                ilog.error(f"[ERROR] Heartbeat error: {e}")
                break

