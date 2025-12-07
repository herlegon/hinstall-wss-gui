from __future__ import annotations
import asyncio
import json
import logging
from pathlib import Path
import subprocess
import sys
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
from tests.test_ws_install import WebSocketClient
from .log_handler import WorkerLogHandler
from websockets import (
    connect
)


class BackendInstallWorker(QThread):
    progress = Signal(float)
    task_name = Signal(str)
    finished = Signal(bool, list)

    def __init__(
        self,
        user_settings: dict[str, Any],
    ):
        super().__init__()
        self.user_settings = user_settings


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
                    os.environ.get('XDG_DATA_HOME', Path.home(), "github"),
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

        # Port detection
        found_port = None
        start_server = True

        # Check ports
        for port in range(49990, 49999):
            # Probing
            status = asyncio.run(self.probe_port(port))

            if status == "WS_SERVER":
                ilog.info(f"Found existing backend server on port {port}.")
                ilog.removeHandler(handler)
                return

            elif status == "KILLED":
                # Verify that it is really free
                verified = False
                for i in range(3):
                    time.sleep(1)
                    v_status = asyncio.run(self.probe_port(port))
                    if v_status == "FREE":
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
                    ilog.removeHandler(handler)
                    return

            elif status == "FREE":
                found_port = port
                break

            else: # BUSY
                ilog.info(f"Port {port} is busy, trying next...")

        if found_port is None:
            ilog.error("Could not find a free port for backend.")
            self.task_name.emit("Failed to start backend.")
            self.finished.emit(False, [])
            ilog.removeHandler(handler)
            return

        if True:
            ilog.debug(f"Backend environment:")
            for k, v in backend_env.items():
                v: str
                if k == 'PATH':
                    v = v.replace(sep, "\n      ")
                ilog.debug(
                    f"  {k}: {v}"
                )

        self.process = None
        self.client = None

        try:
            cmd = [str(g_backend_dirs.python_exe), backend_script_fp, "--port", str(found_port)]
            ilog.info(f"Starting backend: {cmd}")

            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=backend_env,
                text=True
            )

            uri = f"ws://127.0.0.1:{found_port}"
            self.client = WebSocketClient(uri)

            # Start the client loop (blocking this thread, but handling async)
            asyncio.run(self.client.start())

        except Exception as e:
            ilog.error(f"Backend worker error: {e}")
            self.task_name.emit("Failed to run the backend.")
            self.progress.emit(0)
            self.finished.emit(False, [])

        finally:
            if self.process:
                # Check if process exited
                exit_code = self.process.poll()

                # If it crashed early or was terminated, log output
                if exit_code is not None and exit_code != 0:
                     ilog.error(f"Backend process exited with code {exit_code}")
                     try:
                         # Read remaining output
                         output = self.process.stdout.read()
                         if output:
                             ilog.error(f"Backend Output:\n{output}")
                     except Exception as process_read_err:
                         ilog.error(f"Failed to read backend output: {process_read_err}")

                if exit_code is None:
                    ilog.info("Terminating backend server process...")
                    self.process.terminate()
                    try:
                        self.process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        self.process.kill()

            ilog.removeHandler(handler)

    async def probe_port(self, port: int) -> str:
        uri = f"ws://127.0.0.1:{port}"
        try:
            async with connect(uri, open_timeout=0.5) as ws:
                # Send identify command
                await ws.send(json.dumps({"cmd": "identify"}))

                # Wait for response with timeout
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=1.0)
                    data = json.loads(msg)
                except (asyncio.TimeoutError, json.JSONDecodeError):
                    # Not our server or unresponsive
                    return "BUSY"

                # Check identity
                if data.get("type") == "server_identity" and \
                   data.get("payload", {}).get("name") == "herlegon install":

                    client_count = data["payload"].get("clients", 0)
                    ilog.info(f"Prob port {port}: Found herlegon install with {client_count} clients.")

                    if client_count <= 1:
                        # Only us connected (or 0?), treat as zombie
                        ilog.info(f"Only 1 client connected (probe). Treating as zombie. Sending stop...")
                        await ws.send(json.dumps({"cmd": "stop"}))

                        # Wait a bit for server to shutdown
                        await asyncio.sleep(3.0)
                        return "KILLED"
                    else:
                        # Actual running instance
                        return "WS_SERVER"

                return "BUSY"

        except (ConnectionRefusedError, OSError):
            return "FREE"
        except Exception as e:
            ilog.debug(f"Probe port {port} error: {e}")
            return "BUSY"

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
