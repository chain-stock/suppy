from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Union

from typeguard import check_type

QueueType = Union[list[int], dict[int, int]]


@dataclass
class LeadTime:
    """Provides lead-times per period

    Arguments:
        queue: can be a list of lead-times to be consumed in-order
            or a dict of {<period>: <leadtime>}
        default: will be returned when the queue does not define a lead-time for a period
    """

    queue: QueueType | None = None
    default: int | None = None
    _queue_idx: int = field(default=0, init=False, repr=False)

    def __post_init__(self) -> None:
        check_type("queue", self.queue, Optional[QueueType])
        check_type("default", self.default, Optional[int])

    def get_lead_time(self, period: int) -> int:
        """Return the lead-time for a specific period

        Arguments:
            period: the period to return the lead-time for

        Raises:
            ValueError: when no lead-time is defined for the requested period
        """
        if isinstance(self.queue, dict) and period in self.queue:
            # queue is a dict of lead-time per period
            return self.queue[period]
        if isinstance(self.queue, list) and self._queue_idx < len(self.queue):
            # queue is a list of lead-times to consume in-order
            # regardless of period
            idx = self._queue_idx
            self._queue_idx += 1
            return self.queue[idx]
        if self.default is not None:
            # No specific lead-time provided, check the default
            return self.default
        raise ValueError(f"No lead-time set for period {period}")
