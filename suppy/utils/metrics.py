from __future__ import annotations

import json
import logging
from datetime import datetime
from os import PathLike
from pathlib import Path
from typing import IO, TYPE_CHECKING, Any, Iterator, Optional

from suppy.utils.handlers import JsonRotatingFileHandler

if TYPE_CHECKING:
    from suppy import Node

logger = logging.getLogger("metrics")
# Ensure anything logged to this logger won't propagate to the root logger
logger.propagate = False


DEFAULT_FILENAME = "suppy"


def get_default_filename() -> str:
    """Return the default filename"""
    return DEFAULT_FILENAME


class MetricsExporter:
    """MetricsExporter

    Clears any handlers on the "metrics" logger on init
    while also keeping track of explicitly added handlers

    This allows for finding the output files of the handlers added by this class
    without interference of other processes adding handlers to the same logger
    """

    handlers: list[logging.Handler]
    logger: logging.Logger

    def __init__(
        self,
        filename: PathLike[str] | str | None = None,
        stream: IO[str] | None = None,
        level: int = logging.INFO,
        max_bytes: int = 0,
    ):
        self.handlers = []

        # Clear any existing log handlers
        if logger.hasHandlers():
            for hndlr in list(logger.handlers):
                logger.removeHandler(hndlr)

        # Build the default file handler
        file = Path(filename if filename else get_default_filename())
        if file.is_dir():
            file = file / get_default_filename()
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        file = file.with_stem(f"{file.stem}_{timestamp}")
        file.parent.mkdir(parents=True, exist_ok=True)
        handler = JsonRotatingFileHandler(file, encoding="utf-8", max_bytes=max_bytes)

        # Format the log as json for easy parsing
        # The formatter expects the LogRecord to be created with extras:
        # node, event, quantity, period
        formatter = logging.Formatter(
            "{"
            '"timestamp": "%(asctime)s", '
            '"level": "%(levelname)s", '
            '"period": "%(period)s", '
            '"node": "%(node)s", '
            '"event": "%(event)s", '
            '"quantity": "%(quantity)s", '
            '"message": %(message)s'
            "}"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        self.handlers.append(handler)

        if stream is not None:
            streamhandler = logging.StreamHandler(stream)
            streamhandler.setFormatter(formatter)
            logger.addHandler(streamhandler)
            self.handlers.append(streamhandler)

        logger.setLevel(level)

        self.logger = logger

    def stop_metrics(self) -> None:
        """Flush the collected metrics and remove the handler

        Ensures the metrics are flushed to disk and the file is closed
        """
        # by default only a single handler should be available
        # but if someone tapped into the logger, we'll close all handlers
        for handler in self.handlers:
            handler.flush()
            handler.close()

    @property
    def output(self) -> Iterator[PathLike[str]]:
        """Return the Path for every metrics output file"""
        for hndlr in self.filehandlers:
            yield from hndlr.files

    @property
    def filehandlers(self) -> Iterator[JsonRotatingFileHandler]:
        """Return any FileHandler instance for this exporter"""
        for hndlr in self.handlers:
            if isinstance(hndlr, JsonRotatingFileHandler):
                yield hndlr


def setup_metrics(
    filename: PathLike[str] | str | None = None,
    level: int = logging.INFO,
    stream: Optional[IO[str]] = None,
    max_bytes: int = 0,
) -> MetricsExporter:
    """Setup the metrics

    Arguments:
        filename: if provided output the metrics to this file with the current timestamp appended.
            will create a file in the current working directory by default
            if filename points to an existing directory
            the output will be written there with the default filename
        level: log level to set for the metrics logger
            by default all metrics are logged on level INFO, setting this to a higher
            value will disable the metrics logs
        stream: If set adds an additional StreamHandler writing metrics to the provided stream.
        **kwargs: Additional arguments passed to the RotatingFileHandler

    Returns:
        Path to the logfile
    """
    return MetricsExporter(
        filename=filename, stream=stream, level=level, max_bytes=max_bytes
    )


def log_event(  # pylint: disable=too-many-arguments
    period: int,
    node: Node,
    event: str,
    quantity: float,
    message: Any = "",
    level: int | None = logging.INFO,
) -> None:
    """Add an event to the metrics

    Arguments:
        period: current period
        node: Node emitting the event
        event: the event to output
        quantity: quantity of the event
        message: optional message to add to the metric
        level: optional log level to set for the metric, default: logging.INFO
    """
    level = logging.INFO if level is None else level
    extra = {
        "node": node.id,
        "event": event,
        "quantity": quantity,
        "period": period,
    }
    logger.log(level, json.dumps(message), extra=extra)
