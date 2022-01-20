import json
import logging
from unittest.mock import patch

from supplychain_simulation.utils import handlers


def test_json_rotating_file_handler(tmp_path):
    """Test if the output written is valid JSON (if the messages are also valid JSON)"""
    logger = logging.getLogger("unittest")
    handler = handlers.JsonRotatingFileHandler(tmp_path / "unittest")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    # logs need to be valid JSON so add some quotes around the message
    logger.info('"foo"')
    logger.info('"bar"')

    handler.close()

    files = list(handler.files)
    assert len(files) == 1
    data = files[0].read_text()
    assert data == '[\n"foo"\n,"bar"\n]'
    result = json.loads(data)
    assert result == ["foo", "bar"]


@patch("supplychain_simulation.utils.handlers.JsonRotatingFileHandler.shouldRollover")
def test_json_rotating_file_handler_rollover(should_rollover_mock, tmp_path):
    """Test if we can correctly rollover a logfile"""
    logger = logging.getLogger("unittest")
    handler = handlers.JsonRotatingFileHandler(tmp_path / "unittest")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    # logs need to be valid JSON so add some quotes around the message
    should_rollover_mock.return_value = False
    logger.info('"foo"')
    should_rollover_mock.return_value = True
    logger.info('"bar"')

    handler.close()

    files = list(handler.files)
    assert len(files) == 2
    result = json.loads(files[0].read_text())
    assert result == ["foo"]
    result = json.loads(files[1].read_text())
    assert result == ["bar"]
