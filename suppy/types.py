from __future__ import annotations

from abc import abstractmethod
from collections import UserDict
from typing import (
    TYPE_CHECKING,
    Any,
    Protocol,
    TypedDict,
    TypeVar,
    Union,
    runtime_checkable,
)

if TYPE_CHECKING:
    from suppy.node import Node, Orders


# pylint: disable=too-few-public-methods


class LeadTimeStrategy(Protocol):
    """Interface for a Node's lead-time"""

    @abstractmethod
    def get_lead_time(self, period: int) -> int:  # pragma: no cover
        """Should return the lead-time for the provided period

        Arguments:
            period: The period to return the lead-time for

        Raises:
            ValueError: When there is no lead-time or default set for the requested period
        """
        ...


class SalesStrategy(Protocol):
    """Interface for a Node's sales"""

    @abstractmethod
    def pop_sales(self, period: int) -> list[int]:  # pragma: no cover
        """Should return the order lines for the provided period"""
        ...


@runtime_checkable
class ControlStrategy(Protocol):
    """Interface for the SupplyChain's control_strategy"""

    @abstractmethod
    def get_orders(self, node: Node, period: int) -> Orders:  # pragma: no cover
        """Should return the orders to place for `node` at `period`"""
        ...


@runtime_checkable
class ReleaseStrategy(Protocol):
    """Interface for the SupplyChain's release_strategy"""

    @abstractmethod
    def get_releases(self, node: Node) -> Orders:  # pragma: no cover
        """Should return the orders to release"""
        ...


class _K(Protocol):
    """Interface for the key in the Generic IdDict"""

    @property
    @abstractmethod
    def id(self) -> str:  # pragma: no cover
        """Require the TypeVar to have either an attribute or property `id`"""
        ...


_TId = TypeVar("_TId", bound=_K)
_V = TypeVar("_V")


class IdDict(UserDict[Union[_TId, str], _V]):
    """Generic typed UserDict

    Define the types as IdDict[<key type>, <value type>]
    The type of the key needs to have an attribute or property `id` of type str

    This allows set and lookup by either str or object so
    ```
    d = IdDict[Node, int]()
    node = Node("A")
    d[node] = 5
    d["A"] == d[node] ==  5
    d["A"] = 10
    d["A"] == d[node] ==  10
    ```
    """

    @staticmethod
    def _key(key: str | _TId) -> str:
        """
        If key is a string, use it as the key.
        If not take key.id as the key
        """
        return key.id if not isinstance(key, str) else key

    def __getitem__(self, key: str | _TId) -> _V:
        """Get the item either by _TId.id or string"""
        return super().__getitem__(self._key(key))

    def __setitem__(self, key: str | _TId, value: _V) -> None:
        """Set the item either by _TId.id or string"""
        super().__setitem__(self._key(key), value)

    def __contains__(self, key: Any) -> bool:
        """Ensure "'x' in IdDict()" works"""
        return self._key(key) in self.data


class MetricEntryType(TypedDict):
    """Dict representation of a metrics entry"""

    timestamp: str
    level: str
    period: str
    node: str
    event: str
    quantity: str
    message: str
