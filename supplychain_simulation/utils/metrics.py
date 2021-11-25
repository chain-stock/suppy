from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from os import PathLike
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from supplychain_simulation import Node

logger = logging.getLogger("metrics")
# Ensure anything logged to this logger won't propagate to the root logger
logger.propagate = False


def setup_metrics(
    filename: PathLike[str] | None = None, level: int = logging.INFO, **kwargs: Any
) -> None:
    """Setup the metrics

    Arguments:
        filename: if provided output the metrics to this file,
            outputs to stdout by default
        **kwargs: Additional arguments for the RotatingFileHandler
            if filename is provided
    """
    kwargs["encoding"] = "utf-8" if "encoding" not in kwargs else kwargs["encoding"]
    # Remove any existing handlers
    if logger.hasHandlers():
        for hndlr in list(logger.handlers):
            logger.removeHandler(hndlr)

    if filename is not None:
        file = Path(filename)
        handler: logging.Handler = RotatingFileHandler(file, **kwargs)
    else:
        handler = logging.StreamHandler(sys.stdout)

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
        '"message": "%(message)s"'
        "}"
    )

    handler.setFormatter(formatter)
    logger.addHandler(handler)
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
    message: str = "",
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
    logger.log(level, message, extra=extra)
