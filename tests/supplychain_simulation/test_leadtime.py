import pytest

from supplychain_simulation import leadtime


def test_leadtime_no_default():
    """Test if an error is raised when no default is provided"""
    lt = leadtime.LeadTime()
    with pytest.raises(KeyError):
        lt[1]


def test_leadtime_default():
    """Test if we can set a default for leadtime"""
    lt = leadtime.LeadTime({3: 3}, default=5)
    assert lt[1] == 5
    assert lt[2] == 5
    assert lt[3] == 3
