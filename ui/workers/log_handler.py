import logging
from typing import TYPE_CHECKING
from hinstall import STATUS_LEVEL

if TYPE_CHECKING:
    from .pkg_install_worker import PkgInstallWorker



class WorkerLogHandler(logging.Handler):
    def __init__(self, worker):
        super().__init__()
        self.worker: PkgInstallWorker = worker
        self.addFilter(lambda r: r.levelno == STATUS_LEVEL)

    def format(self, record: logging.LogRecord) -> str:
        return record.getMessage()

    def emit(self, record):
        msg = self.format(record)
        self.worker.handle_log_message(msg)

