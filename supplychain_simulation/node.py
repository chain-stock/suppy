from __future__ import annotations

import logging
from collections import UserDict
from dataclasses import dataclass, field
from typing import Any

from .edge import Edge
from .leadtime import LeadTime
from .pipeline import Pipeline, Receipt
from .types import IdDict, LeadTimeStrategy, SalesStrategy

logger = logging.getLogger(__name__)


class Sales(UserDict[int, list[int]]):
    """dict of sales per period"""

    def pop_sales(self, period: int) -> list[int]:
        """Remove and return the sales for a specific period

        If there were no sales for the period, returns 0
        """
        return self.data.pop(period, [])


@dataclass
class Node:
    """A single node in a supply-chain

    A node is identified by it's `id` and can be used as a key in IdDict instances

    The behaviour of a node during simulation can be influenced by providing custom
    `sales` and `lead_time` objects.

    Any additional data for a Node can be provided using the `data` field.

    Arguments:
        id: Unique identifier of this Node
        lead_time: An object capable of returning the lead-time for a specific period
            should adhere to the LeadTimeStrategy Protocol
        sales: An object capable of returning the sales order-lines for a specific period
            should adhere to the SalesStrategy Protocol
        predecessors: A list Edges that together could produce/assemble this Node
        backorders: The number of outstanding backorders for this Node
            defaults to 0, provide this to initialize the simulation with existing backorders
        pipeline: A Pipeline instance for this Node
            defaults to an empty pipeline, provide this to initialize the simulation with
            existing receipts in the pipeline
        stock: Current stock levels at this Node
            defaults to an empty stock, provide this to initialize the simulation with existing
            items in stock
        orders: Outstanding orders at this Node
            default to no outstanding orders, provide this to initialize the simulation with
            existing orders at this Node
        data: dict of any additional data this Node might need
            This should be used to provide per-Node data for user-configurable parts of the sim
            For example when using the RSQ control-strategy this should contain the
            `review_time`, `reorder_level` and `order_quantity` fields.
            See `:RsqData:` for more info.
        llc: The low-level-code of this Node
            Will be automatically set/overwritten when initializing a SupplyChain with this Node
    """

    id: str
    # TODO: make lead_time mandatory
    #   The default right now will still result in an error when run
    lead_time: LeadTimeStrategy = field(default_factory=LeadTime)
    sales: SalesStrategy = field(default_factory=Sales)
    predecessors: list[Edge] = field(default_factory=list)
    backorders: int = 0
    pipeline: Pipeline = field(default_factory=Pipeline)
    stock: Stock = field(default_factory=lambda: Stock())
    orders: Orders = field(default_factory=lambda: Orders())
    data: dict[Any, Any] = field(default_factory=dict)
    llc: int = -1

    def __str__(self) -> str:
        """Only include the Node ID in it's string representation

        Each node is supposed to be unique within a supply-chain so this
        is enough to identify a Node
        """
        return f"Node({self.id})"

    def __hash__(self) -> int:
        """Hash by the Node ID

        Allow using a Node as a key in a dict
        Be aware that this hash does not uniquely identifies this instance
        and should not be relied upon to ensure uniqueness
        """
        return hash(f"{self.id}")

    @property
    def intercompany(self) -> bool:
        """Indicates if this Node is an inter-company Node

        A Node is considered inter-company if it has predecessors
        """
        return len(self.predecessors) > 0

    @property
    def supplier(self) -> bool:
        """Indicates if this Node is a supplier Node

        A Node is considered supplier if it has no predecessors
        """
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
        sales = sum(self.sales.pop_sales(period))
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
        """Return the lead-time of this Node at the provided period"""
        return self.lead_time.get_lead_time(period)


class Orders(IdDict[Node, int]):
    """Orders placed at a node

    The key represents the target node, the value the quantity to send
    To get the orders for a specific Node, use the ID of a node or the Node instance itself:
    ```
    orders["A"] == orders[Node("A")]
    ```
    """

    def __missing__(self, key: str | Node) -> int:
        """When a key is missing, create the key and default to 0"""
        self.__setitem__(key, 0)
        return 0

    def sum(self) -> int:
        """Return the sum of all orders"""
        return sum(self.values())


class Stock(IdDict[Node, int]):
    """Stock levels at a specific node

    Each node can have stock for itself any any other node

    To get the stock level, use the ID of a node or the Node instance itself:
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