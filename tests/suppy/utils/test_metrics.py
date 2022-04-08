import json
import logging
from io import StringIO

from suppy import Node
from suppy.utils import metrics


def test_setup_metrics(tmp_path):
    """Test if we can run setup metrics multiple times"""
    logger = logging.getLogger("metrics")
    metrics.setup_metrics()

    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0], logging.FileHandler)

    metrics.setup_metrics()

    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0], logging.FileHandler)

    metrics.setup_metrics(stream=StringIO())

    assert len(logger.handlers) == 2
    assert isinstance(logger.handlers[0], logging.FileHandler)
    assert isinstance(logger.handlers[1], logging.StreamHandler)


def test_setup_metrics_custom():
    """Test if we can use a custom stream for the metrics"""
    local_stream = StringIO()

    m = metrics.setup_metrics(stream=local_stream)
    metrics.log_event(period=1, loop=0, node=Node("A"), event="test", quantity=42)
    metrics.log_event(period=1, loop=0, node=Node("A"), event="test", quantity=42)
    m.stop_metrics()

    local_stream.seek(0)
    for line in local_stream:
        data = json.loads(line)
        assert data["period"] == "1"
        assert data["node"] == "A"
        assert data["event"] == "test"
        assert data["quantity"] == "42"
