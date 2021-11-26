from __future__ import annotations

from collections import UserDict
from typing import Optional

from typeguard import typechecked


class LeadTime(UserDict[int, int]):
    """dict of lead-times per period

    Returns default for missing keys if provided
    Raises KeyError for missing keys if default is not provided
    """

    @typechecked
    def __init__(
        self,
        _dict: Optional[dict[int, int]] = None,
        /,
        default: Optional[int] = None,
        **kwargs: int,
    ):
        super().__init__(_dict, **kwargs)
        self.default = default

    def __missing__(self, key: int) -> int:
        """Return the default value if provided

        Raises:
            KeyError
        """
        if self.default:
            return self.default
        raise KeyError(key)

    def __bool__(self) -> bool:
        """Consider self True if default is set"""
        return (len(self) != 0) | (self.default is not None)

    def get_lead_time(self, period: int) -> int:
        """Return the lead-time for a specific period

        Arguments:
            period: the period to return the lead-time for

        Raises:
            KeyError
        """
        try:
            return self[period]
        except KeyError:
            raise ValueError(f"No lead-time set for period {period}") from None
