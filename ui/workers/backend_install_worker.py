from __future__ import annotations
import asyncio
import json
import logging
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
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
from hinstall import (
    get_python_version,
    ilog,
)
from hytils import yellow
from .ws_install_client import (
    RequestMessage, ResponseMessage, WsInstallClient, deserialize, serialize, WssIdentity,
    CommandState
)
from .log_handler import WorkerLogHandler
from websockets import (
    connect,
    ClientConnection,
    ConnectionClosedError,
    ConnectionClosedOK,
)

class BackendInstallWorker(QThread):
    progress = Signal(float)
    task_name = Signal(str)
    finished = Signal(bool, list)


    def __init__(
        self,
        settings: dict[str, Any],
        app_cfg: dict[str, Any],
    ):
        super().__init__()
        self.user_settings = settings
        self.app_cfg = app_cfg
        self._backend_process: subprocess.Popen = None


    def run(self):
        # Create handler to forward log to log viewer
        handler = WorkerLogHandler(self)
        handler.setFormatter(logging.Formatter('[S] %(message)s'))
        ilog.addHandler(handler)

        backend_python_version: str = get_python_version()
        ilog.info(f"Backend python version: {backend_python_version}")

        backend_env = generate_backend_env()
        if backend_env is None:
            ilog.removeHandler(handler)
            return

        sep: str = ";" if sys.platform == "win32" else ":"
        devmode: bool = self.user_settings.get('devmode', False)
        if not devmode:
            # Put all in scripts for fun and already in path
            backend_script_fp: Path = (
                g_backend_dirs.python_exe.parent / "Scripts" / f"wss.py"
            )
        else:
            # The repo might be in different dir
            if sys.platform == "win32":
                repo_dirs: list[str] = ["A:\\", "D:\\", "E:\\"]
            else:
                repo_dirs: list[str] = [
                    os.environ.get('XDG_DATA_HOME', Path.home() / "github"),
                    os.environ.get('XDG_DATA_HOME', Path.home()),
                ]
            for dir in repo_dirs:
                backend_script_fp: Path = (
                    Path(dir).resolve() / "hwss" / f"wss.py"
                )
                if backend_script_fp.exists():
                    break

        # Cannot continue if not exists
        ilog.debug(backend_script_fp)
        if not backend_script_fp.exists():
            if not self.user_settings['devmode']:
                ilog.critical("Backend server is not found, can't continue.")
            else:
                ilog.critical(f"Backend used for dev is not found in {repo_dirs}, can't continue.")
            ilog.removeHandler(handler)
            return

        # Add the path when in devmode
        if devmode:
            ilog.info(f"Start the server from {backend_script_fp}")
            backend_env['PATH'] = (
                backend_env['PATH'] + f"{sep}{backend_script_fp.parent}"
            )

        if False:
            ilog.debug(f"Backend environment:")
            for k, v in backend_env.items():
                v: str
                if k == 'PATH':
                    v = v.replace(sep, "\n      ")
                ilog.debug(
                    f"  {k}: {v}"
                )

        # Server IP
        server_ip = self.user_settings.get('server_ip', "127.0.0.1")

        # Run all async operations in a single event loop
        # starts a new event loop and runs the coroutine self._async_run
        asyncio.run(
            self._async_run(server_ip, backend_script_fp, handler)
        )


    async def start_backend_subprocess(
        self,
        backend_script_fp: Path,
        port: int,
    ) -> bool:
        started: bool = False
        self.threads: list[threading.Thread] = []
        self._backend_process = None

        self.process = None
        cmd = [
            str(g_backend_dirs.python_exe),
            "-u",
            backend_script_fp,
            "--port",
            str(port)
        ]
        ilog.info(f"Starting backend: {cmd}")

        try:
            self._backend_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=1,
                universal_newlines=True,
                start_new_session=False,
            )

            # Wait until backend prints "READY"
            for line in iter(self._backend_process.stdout.readline, ""):
                sys.stdout.write(line)
                sys.stdout.flush()
                if "READY" in line:
                    ilog.info("The backend server is ready to work")
                    self._last_pong = time.time()
                    self._is_server_ready = True
                    break

            # Forward stdout
            def forward(stream, target):
                for line in iter(stream.readline, ""):
                    target.write(f"[std] {line}")
                    target.flush()
                    line = line.rstrip()
                stream.close()

            self.threads = [
                threading.Thread(
                    target=forward, args=(self._backend_process.stdout, sys.stdout)
                ),
                threading.Thread(
                    target=forward, args=(self._backend_process.stderr, sys.stderr)
                ),
            ]
            ilog.info(f"Backend server is running")
            for t in self.threads:
                t.start()

        except Exception as e:
            started = False

        return started



    async def _async_run(
        self,
        server_ip: str,
        backend_script_fp: Path,
        logging_handler: logging.Handler,
        stages: int | list[int] = 1
    ):
        """Run all async operations in a single event loop
        stages must be 1, 2 or [1, 2]
        - installer gui:
            * shutdown after stage 1 even if already installed because we need to change page
                don't try to restart the server, it will be done on next page
            * shutdown after stage 2 because we will need to start the application server
            * but retry if failed
        - splash: automatically run both stages if asking to be up-to-date or 1st time
        """
        # When
        remaining_stages = stages

        # Port detection
        port = await self._get_free_port_async(server_ip)
        if port is None:
            ilog.critical(f"Another installation is on going or port is used by another process.")
            self.task_name.emit("Cannot start backend.")
            self.finished.emit(False, [])
            ilog.removeHandler(logging_handler)
            return

        # Use a loop
        retry_max_count: bool = 2
        while True:
            self.client = None
            devmode: bool = self.user_settings.get('devmode', False)

            try:
                started: bool = self.start_backend_subprocess(
                    backend_script_fp=backend_script_fp, port=port,
                )

                if not started:
                    break

                # backend has to install its own external packages if not local
                is_local_backend = (
                    self.user_settings.get('server_ip', '127.0.0.1') in ('localhost', '127.0.0.1')
                )

                # Send this config and selection to backend.
                install_config = {
                    'cfg': json.dumps(self.app_cfg),
                    'local_backend': is_local_backend,
                    'reinstall': False,
                    'use_local_rehost': devmode and is_local_backend,
                    'local_rehost': ""
                }

                # Start the client in the same event loop
                uri = f"ws://{server_ip}:{port}"
                self.client = WsInstallClient(
                    uri,
                    install_config=install_config,
                    stages=remaining_stages,
                )
                await self.client.start()

                # wait for the end of the std thread
                for t in self.threads:
                    t.join()

                return_code = self._backend_process.wait()
                ilog.info(f"Backend exited with code {return_code}")

                # Check if restart was requested:
                #   restart asked
                #   and failed
                if self.client:
                    if self.client.restart_requested():
                        self._backend_process = None
                        if self.client.retry() and retry_max_count:
                            ilog.info("Restart requested. Reason: retry")
                        else:
                            ilog.info("Restart requested. Restarting backend loop...")
                        self._backend_process = None

                    else:
                        ilog.info("Shutdown")
                        break

            except Exception as e:
                ilog.exception(f"{str(e)}")
                break

        if self._backend_process:
            if self._backend_process.poll() is None:
                self._backend_process.terminate()
                self._backend_process.wait()
        self._backend_process = None

        ilog.info("Finished the installation of the backend server")
        ilog.removeHandler(logging_handler)


    async def _get_free_port_async(self, server_ip: str) -> int | None:
        """Async version of get_free_port - runs in the same event loop"""
        found_port = None

        # Check ports
        for port in range(49990, 49991):
            status = await self.probe_port(server_ip, port)

            if status == "WS_SERVER":
                ilog.info(f"Found existing Installation on going on port {port}.")
                break

            elif status == 'terminated':
                # Verify that it is really free
                verified = False
                for i in range(3):
                    v_status = await self.probe_port(server_ip, port)
                    if v_status == 'free':
                        verified = True
                        break
                    ilog.info(f"Port {port} verified status={v_status} (attempt {i+1}/3)")

                if verified:
                    found_port = port
                    break

                else:
                    ilog.error(f"Port {port} failed verification after 3 attempts.")
                    self.task_name.emit("Failed to verify port availability.")
                    self.finished.emit(False, [])
                    break

            elif status == 'free':
                found_port = port
                break

            else: # BUSY
                ilog.info(f"Port {port} is busy, trying next...")

        return found_port



    async def probe_port(self, server_ip: str, port: int) -> str:
        ilog.debug(f"probe port {port} for backend server")
        uri = f"ws://{server_ip}:{port}"
        try:
            async with connect(uri) as wscc:

                # Request server identity
                await wscc.send(serialize(RequestMessage('identify')))

                # Wait for response with timeout
                try:
                    msg = await asyncio.wait_for(wscc.recv(), timeout=1.0)
                    data = deserialize(msg)

                except (asyncio.TimeoutError, json.JSONDecodeError):
                    # Not our server or unresponsive
                    return 'busy'

                # Check identity to stop it if a zombie
                if data.get("type") == 'identity':
                    response = ResponseMessage(**data)
                    identity = WssIdentity(**response.payload)
                    if (
                        identity.organization == 'herlegon'
                        and identity.app == 'hinstall'
                    ):
                        # Already a websocket serve running
                        ilog.info(f"Found herlegon installation with {identity.clients} clients.")

                        if identity.clients <= 1:
                            # Only us connected (or 0?), treat as zombie
                            ilog.info(f"Only 1 client connected (probe). Treating as zombie. Trying to stop it...")
                            await self.shutdown(wscc=wscc)
                            return 'terminated'

                        else:
                            # Actual running instance
                            return "WS_SERVER"

                return 'busy'

        except (ConnectionRefusedError, OSError):
            return 'free'

        except Exception as e:
            ilog.debug(f"Probe port {port}. exception: {str(e)}")
            return 'busy'


    async def send(self, wscc, data: dict):
        if wscc is None:
            ilog.warning(f"Try to send a command while not connected to the backend")
            return
        try:
            await wscc.send(json.dumps(data))
        except Exception as e:
            ilog.error(f"Send failed: {e}")


    async def shutdown(self, wscc: ClientConnection):
        """Handle graceful shutdown when the window is closed
        """
        self._is_shutting_down = True
        ilog.info("Shutting down the backend...")

        # Send a shutdown command to the backend (if needed)
        if wscc:
            print(yellow(f"{__class__.__name__} shutdown"))
            try:
                await wscc.send(serialize(request='shutdown'))
                ilog.info("Shutdown command sent to server")

            except Exception as e:
                ilog.warning(f"Failed to send shutdown command: {e}")

        if self._backend_process and self._backend_process.poll() is None:
            ilog.info("Terminating backend process...")
            self._backend_process.terminate()

        if self._backend_process is not None:
            try:
                self._backend_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                ilog.warning("Backend didn't stop, killing...")
                self._backend_process.kill()

            # Stop the asyncio loop
            ilog.info("Controller stopped")



    def stop(self):
        """Gracefully stop the worker and all subprocesses"""
        ilog.info("Stopping BackendInstallWorker...")
        if self.client:
            self.client.stop()

        # If client loop is running, stop() might not be enough if it's stuck on I/O
        # We rely on client.stop() triggering shutdown logic.

        if self.process and self.process.poll() is None:
             self.process.terminate()

        self.quit()
        self.wait()



    def handle_log_message(self, msg: str):
        pass
