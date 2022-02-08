import pytest

from suppy import leadtime


def test_leadtime_no_default():
    """Test if an error is raised when no default is provided"""
    lt = leadtime.LeadTime()
    with pytest.raises(ValueError):
        lt.get_lead_time(1)


def test_leadtime_default():
    """Test if we can set a default for leadtime"""
    lt = leadtime.LeadTime({3: 3}, default=5)
    assert lt.get_lead_time(1) == 5
    assert lt.get_lead_time(2) == 5
    assert lt.get_lead_time(3) == 3


def test_leadtime_invalid():
    """Test if an error is raised if we provide invalid leadtime data"""
    with pytest.raises(TypeError):
        leadtime.LeadTime({3: "A"})  # type: ignore


def test_leadtime_list():
    """Test if we can use a list for lead-time"""
    lt = leadtime.LeadTime([4, 2, 3, 1])
    assert lt.get_lead_time(1) == 4
    assert lt.get_lead_time(1) == 2
    assert lt.get_lead_time(1000) == 3
    assert lt.get_lead_time(1) == 1


def test_leadtime_dict():
    """Test if we can use a list for lead-time"""
    lt = leadtime.LeadTime({3: 3, 5: 2, 7: 1})
    assert lt.get_lead_time(3) == 3
    assert lt.get_lead_time(5) == 2
    assert lt.get_lead_time(7) == 1
