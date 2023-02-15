import logging

from rich.logging import RichHandler

FORMAT = "%(message)s"
logging.basicConfig(
    level="INFO",
    format=FORMAT,
    handlers=[RichHandler(rich_tracebacks=True, show_time=False)],
)

logger = logging.getLogger("rich")
