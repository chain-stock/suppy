from __future__ import annotations

import logging
from io import TextIOWrapper
from logging.handlers import RotatingFileHandler
from os import PathLike
from pathlib import Path
from typing import Iterator


class JsonRotatingFileHandler(RotatingFileHandler):
    """Logging handler that will wrap emitted logs in a JSON list in each file

    To make the output contain valid JSON, ensure the formatter emits valid JSON objects.
    When opening a new file the first line will contain a "[".
    When rolling over or closing the file, a trailing "]" will be written.

    Each log emitted will have a "," prepended.

    The default RotatingFileHandler will only roll over if there is a max number of files set
    This handler will happyly continue creating new files if needed ensuring no output loss
    """

    def __init__(
        self,
        filename: str | PathLike[str],
        max_bytes: int = 0,
        encoding: str | None = None,
        errors: str | None = None,
    ):
        super().__init__(
            self.new_name(filename, 0),
            maxBytes=max_bytes,
            backupCount=0,
            encoding=encoding,
            delay=False,
            errors=errors,
        )
        self.original_filename = str(filename)
        self.file_count = 1
        self._first_emit = True

    def rotation_filename(self, default_name: str) -> str:
        """Return the new rotation filename"""
        return str(self.new_name(default_name, self.file_count))

    @staticmethod
    def new_name(default_name: str | PathLike[str], count: int) -> Path:
        """Generate the filename with count"""
        if count == 0:
            return Path(default_name).with_suffix(".json")
        return Path(default_name).with_suffix(f".{count}.json")

    def doRollover(self) -> None:
        """Do a rollover"""

        self.close()

        dfn = self.rotation_filename(self.original_filename)
        self.baseFilename = str(dfn)
        self.stream = self._open()
        self.file_count += 1

    def _open(self) -> TextIOWrapper:
        """Add the opening bracket on new file open"""
        stream = super()._open()
        stream.write("[\n")
        self._first_emit = True
        return stream

    def close(self) -> None:
        """Add the closing bracket before closing the file"""
        if self.stream:
            self.stream.write("]")
        super().close()

    def emit(self, record: logging.LogRecord) -> None:
        """Prepend a "," before emitting a log

        This ensures the output, if the record is valid JSON, also contains valid JSON
        """
        try:
            if self.shouldRollover(record):
                self.doRollover()
            if self._first_emit:
                # Don't prepend "," on the first record written
                self._first_emit = False
            else:
                self.stream.write(",")
            logging.FileHandler.emit(self, record)
        except Exception:  # pylint: disable=broad-except
            self.handleError(record)

    @property
    def files(self) -> Iterator[Path]:
        """Return the path to all files written by this handler"""
        for count in range(0, self.file_count):
            yield self.new_name(self.original_filename, count)
