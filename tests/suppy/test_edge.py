import pytest

from suppy import edge


def test_edge_negative():
    """Test if an error is raised when an edge defines an invalid number"""
    with pytest.raises(ValueError):
        edge.Edge("A", "B", -1)
    with pytest.raises(ValueError):
        edge.Edge("A", "B", 0)
