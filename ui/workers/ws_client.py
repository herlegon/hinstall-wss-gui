from __future__ import annotations
import logging
from pathlib import Path
import subprocess
import sys
from typing import Any
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
import tomllib
from typing import Optional, Callable
from websockets import (
    connect, ClientConnection,
    ConnectionClosedError, ConnectionClosedOK,
)


class CommandState(Enum):
    """State machine states for command sequence"""
    IDLE = "idle"
    INSTALLING = "installing"
    STARTING = "starting"
    RUNNING = "running"
    DISCARDING = "discarding"
    RESTARTING = "restarting"
    ERROR = "error"


class WebSocketClient:
    def __init__(self, uri: str, on_message: Optional[Callable] = None):
        self._uri = uri
        self._ws: Optional[ClientConnection] = None
        self._running = False
        self._last_pong = None
        self._state = CommandState.IDLE
        self._on_message = on_message or self._default_message_handler
        self._loop = None


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
                        self._recv_loop(),
                        self._heartbeat_loop(),
                        self._command_state_machine(),
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
        ilog.info(f"Message received: {msg}")


    async def _recv_loop(self):
        """Receive messages from server"""
        try:
            while self._running and self._ws:
                msg = await self._ws.recv()
                data = json.loads(msg)
                self._on_message(data)
                self._update_state_from_response(data)
        except Exception as e:
            ilog.error(f"[ERROR] Receive loop error: {e}")


    async def _heartbeat_loop(self):
        """Send periodic heartbeat"""
        while self._running and self._ws:
            try:
                await self.send({"cmd": "heartbeat"})

                if self._last_pong is None:
                    self._last_pong = time.time()
                elif time.time() - self._last_pong > 10:
                    ilog.error("[ERROR] Backend unresponsive")
                    self._state = CommandState.ERROR
                    break

                await asyncio.sleep(3)
            except Exception as e:
                ilog.error(f"[ERROR] Heartbeat error: {e}")
                break


    async def _command_state_machine(self):
        """State machine that sends commands in sequence"""
        while self._running and self._ws:
            try:
                if self._state == CommandState.IDLE:
                    ilog.info("[STATE] Transitioning to INSTALLING")

                    tool = "hconvert"
                    # Config file is located in tests/configs
                    config_fp = (Path(__file__).parent.parent.parent / "tests" / "configs" / f"{tool}.toml").resolve()
                    ilog.info(f"loading config: {config_fp}")

                    if config_fp.exists():
                        with open(config_fp, "rb") as f:
                            data: dict[str, Any] = tomllib.load(f)

                        await self.send(
                            {
                                "cmd": "install",
                                "payload": {
                                    "cfg": json.dumps(data),
                                    "reinstall": False,
                                    "use_local_host": True,
                                    "local_host": ""
                                }
                            }
                        )
                        self._state = CommandState.INSTALLING
                    else:
                        ilog.error(f"Config file not found: {config_fp}")
                        self._state = CommandState.ERROR

                    await asyncio.sleep(0)

                elif self._state == CommandState.INSTALLING:
                    # Wait for install response (handled in _update_state_from_response)
                    await asyncio.sleep(1)

                elif self._state == CommandState.STARTING:
                    ilog.info("[STATE] Transitioning to STARTING")
                    await self.send({"cmd": "start"})
                    await asyncio.sleep(2)

                elif self._state == CommandState.RUNNING:
                    ilog.info("[STATE] System RUNNING")
                    # Optionally transition to restart after some time
                    await asyncio.sleep(5)
                    # For installing worker, maybe we just stop after success or keep running?
                    # The test script restarts. Let's keep it but logging only.
                    # ilog.info("[STATE] Transitioning to RESTARTING")
                    # await self.send({"cmd": "restart"})
                    # self._state = CommandState.RESTARTING
                    # await asyncio.sleep(2)

                elif self._state == CommandState.RESTARTING:
                    # Wait for restart to complete
                    await asyncio.sleep(1)

                elif self._state == CommandState.DISCARDING:
                    ilog.info("[STATE] Transitioning to DISCARDING")
                    await self.send({"cmd": "discard"})
                    self._state = CommandState.IDLE
                    await asyncio.sleep(2)

                elif self._state == CommandState.ERROR:
                    ilog.info("[STATE] Error state reached, breaking state machine")
                    break

                else:
                    await asyncio.sleep(1)

            except Exception as e:
                ilog.error(f"[ERROR] State machine error: {e}")
                self._state = CommandState.ERROR
                break


    def _update_state_from_response(self, response: dict):
        """Update state machine based on server response"""
        cmd = response.get("cmd")
        status = response.get("status", "")

        if cmd == "install" and status == "success":
            ilog.info("[RESPONSE] Install successful")
            self._state = CommandState.STARTING

        elif cmd == "start" and status == "success":
            ilog.info("[RESPONSE] Start successful")
            self._state = CommandState.RUNNING
        elif cmd == "restart" and status == "success":
            ilog.info("[RESPONSE] Restart successful")
            self._state = CommandState.RUNNING
        elif cmd == "discard" and status == "success":
            ilog.info("[RESPONSE] Discard successful")
            self._state = CommandState.IDLE
        elif status == "error":
            ilog.info(f"[RESPONSE] Command failed: {response.get('error', 'Unknown error')}")
            self._state = CommandState.ERROR


    async def send(self, data: dict):
        """Send command to server"""
        if not self._ws:
            ilog.warning("[WARNING] Attempted to send while not connected")
            return
        try:
            await self._ws.send(json.dumps(data))
            ilog.info(f"[SEND] {data}")
        except Exception as e:
            ilog.error(f"[ERROR] Send failed: {e}")


    def send_command(self, data: dict):
        """Send command from a different thread"""
        if self._loop:
            ilog.info(f"[SEND] Scheduling: {data}")
            asyncio.run_coroutine_threadsafe(self.send(data), self._loop)


    def transition_to(self, state: CommandState):
        """Manually transition to a specific state"""
        ilog.info(f"[MANUAL] Transitioning from {self._state.value} to {state.value}")
        self._state = state


