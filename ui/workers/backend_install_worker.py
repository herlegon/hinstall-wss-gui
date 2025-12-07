from __future__ import annotations
import asyncio
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
from tests.test_ws_install import WebSocketClient
from .log_handler import WorkerLogHandler


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

        if True:
            ilog.debug(f"Backend environment:")
            for k, v in backend_env.items():
                if k == 'PATH':
                    v = v.replace(sep, "\n      ")
                ilog.debug(
                    f"  {k}: {v}"
                )

        self.process = None
        self.client = None

        try:
            self.process = subprocess.Popen(
                [str(g_backend_dirs.python_exe), backend_script_fp],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=backend_env,
                text=True
            )

            # Allow some time for the server to start
            # Wait a bit or retry connection in client

            uri = "ws://127.0.0.1:8442"
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
                if self.process.poll() is None:
                    ilog.info("Terminating backend server process...")
                    self.process.terminate()
                    try:
                        self.process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        self.process.kill()

                if self.process.returncode != 0 and self.process.returncode is not None:
                     # Check if we have output to show from pipe?
                     # Since we used PIPE, we might want to read it if we can
                     # But Popen stdout is not read automatically unless we do it.
                     pass

            ilog.removeHandler(handler)

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
