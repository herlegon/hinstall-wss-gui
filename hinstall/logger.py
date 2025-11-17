import logging
import os
import sys
from typing import Optional
from hytils import darkgrey, green, yellow, red


class ColorFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: darkgrey,
        logging.INFO: green,
        logging.WARNING: yellow,
        logging.ERROR: red,
        logging.CRITICAL: red,
    }

    def format(self, record: logging.LogRecord) -> str:
        color_fn = self.COLORS.get(record.levelno, lambda x: x)
        msg = super().format(record)

        # Use relative path for readability
        try:
            rel_path = os.path.relpath(record.pathname)
        except ValueError:
            rel_path = os.path.basename(record.pathname)

        filename = darkgrey(os.path.basename(record.pathname))
        link = f"{rel_path}:{record.lineno}"

        # formatted = f"[{record.levelname}]  {filename}: {record.getMessage()}  ({link})"
        formatted = color_fn(f"[{record.levelname}]") + f" {record.getMessage()}  ({link})"
        return formatted



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

    # # GUI handler
    # if to_gui:
    #     to_gui.setFormatter(gui_formatter or SimpleFormatter())
    #     logger.addHandler(to_gui)

    return logger


# Default initialization (basic mode)
ilog: logging.Logger = setup_alog(to_stdout=True)



