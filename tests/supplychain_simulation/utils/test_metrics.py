import logging

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
