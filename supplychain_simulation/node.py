from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from supplychain_simulation.leadtime import LeadTime
from supplychain_simulation.pipeline import Pipeline
from supplychain_simulation.receipt import Receipt
from supplychain_simulation.sales import Sales
from supplychain_simulation.types import IdDict

if TYPE_CHECKING:
    from supplychain_simulation.simulator import Edge
    from supplychain_simulation.types import LeadTimeStrategy, SalesStrategy


logger = logging.getLogger(__name__)


@dataclass
class Node:
    id: str
    data: dict[Any, Any] = field(default_factory=dict)
    sales: SalesStrategy = field(default_factory=Sales)
    lead_time: LeadTimeStrategy = field(default_factory=LeadTime)
    llc: int = -1
    backorders: int = 0
    predecessors: list[Edge] = field(default_factory=list)
    pipeline: Pipeline = field(default_factory=Pipeline)
    stock: Stock = field(default_factory=lambda: Stock())
    orders: Orders = field(default_factory=lambda: Orders())

    def __str__(self) -> str:
        return self.id

    def __hash__(self) -> int:
        """Hash by the Node ID

        Nodes are keyed in Stock and SupplyChain by their hash to allow lookup
        by either string or Node instance
        """
        return hash(f"{self.id}")

    @property
    def intercompany(self) -> bool:
        return len(self.predecessors) > 0

    @property
    def supplier(self) -> bool:
        return len(self.predecessors) == 0

    def assemblies_feasible(self, stock: IdDict[Node, int] | None = None) -> int:
        """Returns the number of self that could be assembled from stock

        If no stock is provided use the stock at this node
        """
        if stock is None:
            stock = self.stock
        # for intercompany skus
        if self.intercompany:
            feasible = min(
                [int(stock[edge.source] / edge.number) for edge in self.predecessors]
            )
        # for supplier skus
        else:
            feasible = 0

        # the number of items that can be assembled is non-negative.
        # this check should be unnecessary.
        if feasible < 0:
            logger.warning(f"Found negative feasible assemblies for node {self}")
        feasible = max(feasible, 0)

        return feasible

    def satisfy_received_receipts(self) -> None:
        """Update the stock with the received receipts from the pipeline"""
        received_receipts = self.pipeline.pop_received()
        logger.debug(f"Node {self}: {len(received_receipts)} receipts received")
        self.stock.add_received(received_receipts)

    def satisfy_backorders(self) -> None:
        """Send out any backorders we can satisfy from stock"""
        if self.backorders:
            feasible = min(self.stock[self], self.backorders)
            logger.debug(
                f"Node {self}: {feasible}/{self.backorders} backorders satisfied"
            )
            self.backorders -= feasible
            self.stock[self] -= feasible

    def satisfy_sales(self, period: int) -> None:
        """Satisfy sales for this period from stock

        adds backorders for any sales that could not be satisfied
        """
        sales = self.sales.pop_sales(period)
        feasible = min(self.stock[self], sales)
        backorders = sales - feasible
        self.stock[self] -= feasible
        self.backorders += backorders
        logger.debug(
            f"Node {self}: {feasible}/{sales} sales satisfied ({backorders} backorders)"
        )

    def assemble(self) -> None:
        """Assemble this node where possible

        In order to assemble the node, all needed quantities of all predecessors should be in stock
        """
        feasible = self.assemblies_feasible()
        for edge in self.predecessors:
            self.stock[edge.source] -= feasible * edge.number
        self.stock[self] += feasible
        logger.debug(f"Node {self}: Assembled {feasible}")

    def get_lead_time(self, period: int) -> int:
        return self.lead_time.get_lead_time(period)


class Orders(IdDict[Node, int]):
    """Orders placed at a node

    The key represents the target node, the value the quantity to send
    """

    def __missing__(self, key: str | Node) -> int:
        """When a key is missing, create the key and default to 0"""
        self.__setitem__(key, 0)
        return 0

    def sum(self) -> int:
        return sum(self.values())


class Stock(IdDict[Node, int]):
    """Stock levels at a specific node

    Each node can have stock for itself any any other node

    To get the stock level, use the ID of a node or the Node instance itself
    ```
    stock["A"] == stock[Node("A")]
    ```
    """

    def __missing__(self, key: str | Node) -> int:
        """When a key is missing, default to 0"""
        self.__setitem__(key, 0)
        return 0

    def add_received(self, received: list[Receipt]) -> None:
        """Add the received receipts to the stock"""
        for receipt in received:
            self[receipt.sku_code] += receipt.quantity
            logger.debug(f"\t{receipt.quantity} {receipt.sku_code} added to stock")
