import json
import logging
from io import StringIO

from supplychain_simulation import Node
from supplychain_simulation.utils import metrics


def test_setup_metrics(tmp_path):
    """Test if we can run setup metrics mulitple times"""
    logger = logging.getLogger("metrics")
    metrics.setup_metrics()

    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0], logging.StreamHandler)
    assert not isinstance(logger.handlers[0], logging.FileHandler)

    metrics.setup_metrics()

    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0], logging.StreamHandler)
    assert not isinstance(logger.handlers[0], logging.FileHandler)

    metrics.setup_metrics(tmp_path / "metrics.json")

    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0], logging.FileHandler)


def test_setup_metrics_custom():
    """Test if we can use a custom stream for the metrics"""
    local_stream = StringIO()

    metrics.setup_metrics(stream=local_stream)
    metrics.log_event(period=1, node=Node("A"), event="test", quantity=42)
    metrics.log_event(period=1, node=Node("A"), event="test", quantity=42)
    metrics.stop_metrics()

    local_stream.seek(0)
    for line in local_stream:
        data = json.loads(line)
        assert data["period"] == "1"
        assert data["node"] == "A"
        assert data["event"] == "test"
        assert data["quantity"] == "42"
