import pytest

from supplychain_simulation import pipeline


def test_pipeline_invalid():
    """Test if an error is raised if the pipeline is not of the correct type"""
    with pytest.raises(TypeError):
        pipeline.Pipeline([1, 2, 3])  # type: ignore
