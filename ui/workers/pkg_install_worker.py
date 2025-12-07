from __future__ import annotations
import logging
from PySide6.QtCore import QThread, Signal
from hinstall import (
    download_install_ext_packages,
    ExtPackages,
    ilog,
)
from .log_handler import WorkerLogHandler


class PkgInstallWorker(QThread):
    progress = Signal(float)
    task_name = Signal(str)
    finished = Signal(bool, list)


    def __init__(self, packages: ExtPackages, reinstall: bool = True, threads: int = 1, use_local_host: bool = True):
        super().__init__()
        self.packages = packages
        self.reinstall = reinstall
        self.threads = threads
        self.use_local_host = use_local_host
        self.total_packages = len(packages) if packages else 0
        self.current_package = 0


    def run(self):
        # Create handler
        handler = WorkerLogHandler(self)
        handler.setFormatter(logging.Formatter('[S] %(message)s'))
        ilog.addHandler(handler)

        try:
            installed = download_install_ext_packages(
                packages=self.packages,
                reinstall=self.reinstall,
                threads=self.threads,
                use_local_host=self.use_local_host
            )

            if installed:
                self.progress.emit(100)
                self.task_name.emit(f"All packages installed.")
                self.finished.emit(True, [])
            else:
                self.finished.emit(False, [])

        except Exception as e:
            self.task_name.emit(f"Error: {str(e)}")
            self.finished.emit(False, [])
        finally:
            ilog.removeHandler(handler)


    def handle_log_message(self, msg: str):
        task_code = msg[1:3]
        payload = msg[4:]

        if task_code == "sd":
            # Start download...
            pkg_name = payload
            self.task_name.emit(f"Downloading {pkg_name}...")
            self.progress.emit(0)

        if task_code == "rd":
            # Retry download...
            pkg_name = payload
            self.task_name.emit(f"Retry to download {pkg_name}...")
            self.progress.emit(0)

        elif task_code == "si":
            # start installing package
            pkg_name = payload
            self.task_name.emit(f"Installing {pkg_name}...")
            self.progress.emit(0)

        elif task_code == "pg":
            # progress
            value = float(payload)
            # print(f"refresh progress to {value}: {type(value)}")
            self.progress.emit(value)

        elif task_code == "ed":
            # ended
            pkg_name = payload
            self.progress.emit(100.)
            self.task_name.emit(f"{pkg_name} downloaded.")

        elif task_code == "ei":
            # ended
            pkg_name = payload
            self.progress.emit(100.)
            self.task_name.emit(f"{pkg_name} installed.")

        elif task_code == "if":
            # Failed
            pkg_name = payload
            self.progress.emit(0.)
            self.task_name.emit(f"Failed to install {pkg_name}...")

        elif task_code == "df":
            # Failed
            pkg_name = payload
            self.progress.emit(0.)
            self.task_name.emit(f"Failed to download {pkg_name}...")

        elif task_code == "cm":
            # custom message
            self.task_name.emit(payload)

        elif task_code == "ce":
            # critcial error
            self.task_name.emit(payload)
            # end of worker, exit
            # cannot install

