import logging
import os
import sys
from typing import Optional
from hytils import darkgrey, green, yellow, red


STATUS = 15
logging.addLevelName(STATUS, "STATUS")


class ColorFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: darkgrey,
        logging.INFO: green,
        STATUS: lambda x: x,
        logging.WARNING: yellow,
        logging.ERROR: red,
        logging.CRITICAL: red,
    }

    LEVEL_PREFIX = {
        logging.DEBUG: "[D]",
        5: "[V]",
        logging.INFO: "[I]",
        STATUS: "",
        logging.WARNING: "[W]",
        logging.ERROR: "[E]",
        logging.CRITICAL: "[C]",
    }

    def format(self, record: logging.LogRecord) -> str:
        level_no: int = record.levelno
        if level_no == STATUS:
            return record.getMessage()

        color_fn = self.COLORS.get(level_no, lambda x: x)
        prefix: str = self.LEVEL_PREFIX.get(level_no, f"{level_no}")
        if level_no < logging.INFO:
            # Use relative path for readability
            try:
                rel_path = os.path.relpath(record.pathname)
            except ValueError:
                rel_path = os.path.basename(record.pathname)
            link = f"{rel_path}:{record.lineno}"
            formatted = color_fn(f"{prefix}") + f"{record.getMessage()}  ({link})"

        else:
            formatted = color_fn(f"{prefix}") + f"{record.getMessage()}"

        return formatted



class HInstallLogger(logging.Logger):
    def status(self, msg, *args, **kwargs):
        if self.isEnabledFor(STATUS):
            self._log(STATUS, msg, args, **kwargs)


logging.setLoggerClass(HInstallLogger)


def setup_alog(
    log_file: Optional[str] = None,
    to_stdout: bool = True,
    to_gui: Optional[logging.Handler] = None,
    stdout_formatter: Optional[logging.Formatter] = None,
    gui_formatter: Optional[logging.Formatter] = None,
    file_formatter: Optional[logging.Formatter] = None,
):
    """Reconfigure the global logger."""
    logger = logging.getLogger("hinstall")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    # Console handler
    if to_stdout:
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(stdout_formatter or ColorFormatter())
        logger.addHandler(stream_handler)

    # # File handler
    # if log_file:
    #     file_handler = logging.FileHandler(log_file, mode="w", encoding="utf-8")
    #     file_handler.setFormatter(file_formatter or SimpleFormatter())
    #     logger.addHandler(file_handler)

    # GUI handler
    if to_gui:
        to_gui.setFormatter(gui_formatter or logging.Formatter('%(message)s'))
        logger.addHandler(to_gui)

    return logger


# Default initialization (basic mode)
ilog: HInstallLogger = setup_alog(to_stdout=True)



