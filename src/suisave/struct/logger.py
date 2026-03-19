import logging
import sys
from rich.console import Console
from rich.logging import RichHandler

console = Console()


# -----------------------
# Simple log buffer
# -----------------------
class PanelLogHandler(RichHandler):
    def __init__(self, buffer, max_lines=20):
        super().__init__(
            console=console,
            rich_tracebacks=True,
            show_time=True,
            show_level=True,
            show_path=False,
        )
        self.buffer = buffer
        self.max_lines = max_lines

    def emit(self, record):
        msg = self.format(record)
        self.buffer.append(msg)

        if len(self.buffer) > self.max_lines:
            self.buffer.pop(0)


class ColorFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: "\033[36m",  # cyan
        logging.INFO: "\033[32m",  # green
        logging.WARNING: "\033[33m",  # yellow
        logging.ERROR: "\033[31m",  # red
        logging.CRITICAL: "\033[41m",  # red background
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelno, "")
        levelname = record.levelname
        record.levelname = f"{color}{levelname}{self.RESET}"
        msg = super().format(record)
        record.levelname = levelname  # restore
        return msg


def get_logger(
    name: str = "gremux",
    level: int = logging.INFO,
) -> logging.Logger:
    """
    Get a logger object from the standard logging library that
    formats the text according to ColorFormatter

    Parameters:
    ----------
    * `name`: str
    * `level`: int
    """

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    handler = logging.StreamHandler(sys.stdout)
    formatter = ColorFormatter(fmt="[%(levelname)s] %(message)s")
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.propagate = False
    return logger


def make_logger() -> logging.Logger:
    logger = logging.getLogger("comet")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.propagate = False

    base_format = "%(asctime)s %(message)s"
    date_fmt = "%Y-%m-%d %H:%M:%S"

    handler = RichHandler(
        console=console,
        rich_tracebacks=True,
        show_time=True,
        show_level=True,
        show_path=False,
    )

    formatter = logging.Formatter(fmt=base_format, datefmt=date_fmt)
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger
