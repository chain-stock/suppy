from __future__ import annotations

import json
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from os import PathLike
from pathlib import Path
from typing import IO, TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from supplychain_simulation import Node

logger = logging.getLogger("metrics")
# Ensure anything logged to this logger won't propagate to the root logger
logger.propagate = False


DEFAULT_FILENAME = "suppy"
EXTENTION = ".txt"


def get_default_filename() -> str:
    """Return the default filename"""
    return DEFAULT_FILENAME


def setup_metrics(
    filename: PathLike[str] | str | None = None,
    level: int = logging.INFO,
    stream: Optional[IO[str]] = None,
    **kwargs: Any,
) -> None:
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
    # Remove any existing handlers
    if logger.hasHandlers():
        for hndlr in list(logger.handlers):
            logger.removeHandler(hndlr)

    file = Path(filename if filename else get_default_filename())
    if file.is_dir():
        file = file / get_default_filename()
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    file = file.with_stem(f"{file.stem}_{timestamp}").with_suffix(EXTENTION)
    file.parent.mkdir(parents=True, exist_ok=True)
    handler: logging.Handler = RotatingFileHandler(file, encoding="utf-8", **kwargs)

    # Format the log as json for easy parsing
    # The formatter expects the LogRecord to be create with extras:
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

    if stream is not None:
        streamhandler = logging.StreamHandler(stream)
        streamhandler.setFormatter(formatter)
        logger.addHandler(streamhandler)

    logger.setLevel(level)


def stop_metrics() -> None:
    """Flush the collected metrics and remove the handler

    Ensures the metrics are flushed to disk and the file is closed
    """
    # by default only a single handler should be available
    # but if someone tapped into the logger, we'll close all handlers
    for handler in logger.handlers:
        handler.flush()
        handler.close()


def log_event(
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
