from __future__ import annotations

from abc import abstractmethod
from collections import UserDict
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Any,
    Generic,
    Iterator,
    Protocol,
    TypeVar,
    Union,
    ValuesView,
    runtime_checkable,
)

if TYPE_CHECKING:
    from supplychain_simulation.node import Node, Orders


class LeadTimeStrategy(Protocol):
    @abstractmethod
    def get_lead_time(self, period: int) -> int:
        ...


class SalesStrategy(Protocol):
    @abstractmethod
    def pop_sales(self, period: int) -> list[int]:
        ...


@runtime_checkable
class ControlStrategy(Protocol):
    @abstractmethod
    def get_order_quantity(self, node: Node, period: int) -> int:
        ...


@runtime_checkable
class ReleaseStrategy(Protocol):
    @abstractmethod
    def get_releases(self, node: Node) -> Orders:
        ...


class _K(Protocol):
    """Interface for the key in the Generic IdDict"""

    @property
    @abstractmethod
    def id(self) -> str:
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

    def values(self) -> ValuesView[_V]:
        return super().values()

    def items(self) -> AbstractSet[tuple[str | _TId, _V]]:
        return super().items()
