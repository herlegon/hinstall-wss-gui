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
from hytils import lightcyan, lightgreen, red
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
    FETCH_SYS_INFO = 'fetch_backend_details'
    FETCHING_SYS_INFO = 'fetching_backend_details'
    INSTALL = 'install'
    INSTALLING = 'installing'
    RESTART = 'restart'
    SHUTDOWN = 'shutdown'
    FETCHING_BACKEND_DETAILS = 'fetching_backend_details'
    ENDED = 'ended'
    CRITICAL = 'error'


sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent / "hwss"))
from api import (
    RequestMessage,
    deserialize,
    serialize,
    ResponseMessage,
    EventMessage,
    EventType,
    ResponseType,
    WssIdentity,
    ParseTask,
    InstallTaskResult,
    InstallProgress,
    InstallTask,
)


LEVEL_MAPPING: dict[str, str] = {
    'critical': "[C]",
    'error': "[E]",
    'warning': "[W]",
    'info': "[I]",
    'debug': "[D]",
}



class WsInstallClient:
    def __init__(
        self,
        uri: str,
        install_config: dict,
        stages: int | list[int],
        on_message: Optional[Callable] = None,
        devmode: bool = False,
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
        self.wss_running = False
        self._last_pong = None
        self.state = CommandState.IDLE
        self._retry: bool = False
        self._do_restart: bool = False
        self._on_message = on_message or self._default_message_handler
        self._loop = None
        self.task_result: InstallTaskResult = None
        self.devmode = devmode


    def retry(self) -> bool:
        return self._retry


    def restart_requested(self) -> bool:
        return self._do_restart


    async def _main(self):
        retries = 0
        delay = 0.5
        exception: str = ""

        ilog.info(f"[INFO] Connecting to {self._uri}")
        while self.wss_running:
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
                    self.state = CommandState.IDLE

                    # Run state machine as the main driver, with background tasks
                    tasks = [
                        asyncio.create_task(self._reception_task()),
                        asyncio.create_task(self._heartbeat_loop()),
                    ]
                    try:
                        await self.state_machine()
                    finally:
                        for t in tasks:
                            t.cancel()
                        await asyncio.gather(*tasks, return_exceptions=True)

                if self.state == CommandState.RESTART:
                    self.wss_running = False
                    break

            except (ConnectionClosedError, ConnectionClosedOK) as e:
                ilog.warning(f"[WARNING] WebSocket closed: {e}")
                if self.state == CommandState.RESTART:
                    self.wss_running = False
                    break
                self.state = CommandState.CRITICAL

            except Exception as e:
                retries += 1
                exception = str(e)
                ilog.error(f"[ERROR] Connection error ({retries}): {e}")
                if retries >= 3:
                    self.wss_running = False
                    self.state = CommandState.CRITICAL
                self.ws_cc = None
                await asyncio.sleep(delay)

            finally:
                self.ws_cc = None
                if self.wss_running:
                    await asyncio.sleep(delay)

        self.wss_running = False
        self.ws_cc = None
        msg = f" with error: {exception}" if exception else ""
        ilog.info(f"[INFO] Connection loop terminated, {msg}")


    async def start(self):
        """Start the WebSocket client"""
        self.wss_running = True
        self._loop = asyncio.get_event_loop()
        await self._main()


    def stop(self):
        """Stop the WebSocket client"""
        self.wss_running = False
        if self._loop and self._loop.is_running():
            # Try to close websocket to unblock recv loop
            async def close_ws():
                if self.ws_cc:
                    await self.ws_cc.close()

            asyncio.run_coroutine_threadsafe(close_ws(), self._loop)


    def _default_message_handler(self, msg: dict):
        print(lightcyan("rcv"), msg)
        # ilog.debug(f"Message received: {msg}")
        pass


    async def _reception_task(self):
        """Receive messages from server"""
        try:
            while self.wss_running and self.ws_cc:
                msg = await self.ws_cc.recv()
                data: dict = deserialize(msg)
                self.handle_received_message(data)

        except Exception as e:
            if self.wss_running:
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
            level = event.payload['type']
            text = event.payload['text']
            prefix = (
                LEVEL_MAPPING.get(level, "[?]")
            )
            print(f"{prefix} {text}")

        elif event.type == "telemetry":
            # Handle telemetry event
            pass

        elif event.type == "status":
            # Handle status event
            pass

        elif event.type == "progress":
            p: InstallProgress = InstallProgress(**event.payload)
            if p.type == 'indet' and p.progress != 100:
                print(f"[PROGRESS][INDENT] {p.task_id} {p.package_name}")
            else:
                print(f"[PROGRESS] {p.task_id} {p.package_name} {p.progress}")


    def handle_response(self, response: ResponseMessage) -> None:
        """Handle ResponseMessage
        """
        if response.type == 'pong':
            self._last_pong = time.time()
            return

        if response.type == 'install':
            self.task_result = InstallTaskResult(**response.payload)
            return

        if response.type == 'shutdown':
            self.wss_running = False
            return

        print(f"handle_response: {response}")


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


    async def send_identify_request(self):
        await self._send_message(RequestMessage(type='identify'))


    async def send_shutdown_request(self):
        await self._send_message(RequestMessage(type='shutdown'))



    async def _heartbeat_loop(self):
        """Send periodic heartbeat, to see if everything is ok
        while running a long task
        """
        heartbeat_msg = serialize(RequestMessage(type='heartbeat'))
        while self.wss_running and self.ws_cc:
            try:
                await self._send_message(heartbeat_msg)

                if self._last_pong is None:
                    self._last_pong = time.time()

                elif time.time() - self._last_pong > 10:
                    ilog.error("[ERROR] Backend unresponsive")
                    self.state = CommandState.CRITICAL
                    break

                await asyncio.sleep(2)

            except Exception as e:
                ilog.error(f"[ERROR] Heartbeat error: {e}")
                break


    # STATE MACHINE
    #-------------------------------------------------------------------------------------
    async def _state_idle(self) -> None:
        cfg = self.install_config
        toml_cfg = cfg.get('toml', "")
        task = ParseTask(
            app_name=cfg.get('app_name', ""),
            cfg=json.dumps(toml_cfg),
            cache=cfg.get('cache', True),
            local_backend=cfg.get('local_backend', False),
            reinstall=cfg.get('reinstall', False),
            use_local_rehost=cfg.get('use_local_rehost', False),
            local_rehost=cfg.get('local_rehost', ""),
        )
        await self.send_task(task)
        self.task_result = None
        self.state = CommandState.PARSING


    async def _state_parsing(self) -> None:
        # Wait for end of parsing
        if self.task_result is None:
            await asyncio.sleep(0.5)

        # Task is finished
        elif self.task_result.task_id != 'parse':
            print(red("Error! wrong task_id"))

        elif self.task_result.status == 'parsed':
            self.task_result = None
            if self.stages[0] == 2:
                self.state = CommandState.FETCH_SYS_INFO
            self.state = CommandState.INSTALL

        elif self.task_result.status == 'failed':
            # Cannot continue
            self.state = CommandState.END
            print(red("Failed parsing"))


    async def _state_fetch_sysinfo(self) -> None:
        ilog.critical("TODO")
        self.state = CommandState.FETCHING_SYS_INFO
        await asyncio.sleep(0)


    async def _state_fetching_sysinfo(self) -> None:
        self.state = CommandState.INSTALL
        await asyncio.sleep(0)


    async def _state_install(self) -> None:
        if not self.stages:
            self.state = CommandState.ENDED

        await self.send_task(InstallTask(stage=self.stages[0]))
        self.task_result = None
        self.state = CommandState.INSTALLING


    async def _state_installing(self) -> None:
        if self.task_result is None:
            await asyncio.sleep(0.5)

        elif self.task_result.task_id != 'install':
            print(red("Error! wrong task_id"))

        elif self.task_result.status == 'installed':
            print(f"installed stage {self.stages[0]}")
            self.stages.pop(0)
            if self.task_result.restart:
                self.state = CommandState.RESTART
            elif self.stages:
                print("next stage")
                self.state = CommandState.INSTALL
            else:
                self.state = CommandState.SHUTDOWN
            self.task_result = None

        elif self.task_result.status == 'failed':
            self._retry = True
            self.state = CommandState.RESTART
            print(red("Failed installing"))


    async def _state_shutdown(self) -> None:
        self.wss_running
        if not self.devmode:
            await self.send_shutdown_request()

            # Wait to see if connection is closed by server
            try:
                await self.ws_cc.wait_closed()
                print(lightgreen("Connection closed by server"))

            except Exception as e:
                print(f"Wait closed exception: {e}")

        self.state = CommandState.ENDED


    async def _state_restart(self) -> None:
        await self._state_shutdown()
        self._do_restart = True


    async def _state_critical(self) -> None:
        ilog.info("Critical error occured")
        await self._state_shutdown()
        # The decision to retry will be done by the parent
        self._do_restart = True
        self._retry = True


    async def _state_ended(self) -> None:
        self.wss_running = False
        await asyncio.sleep(0)


    async def _state_unknown(self) -> None:
        self.wss_running = False
        await asyncio.sleep(0)


    async def state_machine(self):
        """State machine that sends commands in sequence"""
        self.task_result: InstallTaskResult = None

        state_map: dict[CommandState, Callable] = {
            CommandState.IDLE: self._state_idle,
            CommandState.PARSING: self._state_parsing,
            CommandState.FETCH_SYS_INFO: self._state_fetch_sysinfo,
            CommandState.FETCHING_SYS_INFO: self._state_fetching_sysinfo,
            CommandState.INSTALL: self._state_install,
            CommandState.INSTALLING: self._state_installing,
            CommandState.RESTART: self._state_restart,
            CommandState.CRITICAL:self._state_critical,
            CommandState.SHUTDOWN:self._state_shutdown,
            CommandState.ENDED: self._state_ended,
        }

        while self.wss_running and self.ws_cc:
            try:
                await state_map.get(self.state, lambda: self._state_unknown())()

            except Exception as e:
                ilog.error(f"[ERROR] State machine error at state {CommandState(self.state)}: {e}")
                await self._state_shutdown()
                break

        self.wss_running = False
        if self.ws_cc:
            await self.ws_cc.close()
        print("end of the state machine")
