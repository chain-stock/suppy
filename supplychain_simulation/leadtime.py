from __future__ import annotations

from collections import UserDict
from typing import Mapping


class LeadTime(UserDict[int, int]):
    """dict of lead-times per period

    Returns default for missing keys if provided
    Raises KeyError for missing keys if default is not provided
    """

    # TODO: verify values
    def __init__(
        self,
        _dict: Mapping[int, int] | None = None,
        /,
        default: int | None = None,
        **kwargs: int,
    ):
        super().__init__(_dict, **kwargs)
        self.default = default

    def __missing__(self, key: int) -> int:
        if self.default:
            return self.default
        raise KeyError(key)

    def get_lead_time(self, period: int) -> int:
        return self[period]
