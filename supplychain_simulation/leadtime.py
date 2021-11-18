from collections import UserDict


class LeadTime(UserDict):
    """dict of lead-times per period

    Returns default for missing keys if provided
    Raises KeyError for missing keys if default is not provided
    """

    def __init__(self, _dict=None, /, default=None, **kwargs):
        super().__init__(_dict, **kwargs)
        self.default = default

    def __missing__(self, key):
        if self.default:
            return self.default
        raise KeyError(key)

    def get_lead_time(self, period: int) -> int:
        return self[period]
