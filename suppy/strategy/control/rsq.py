from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import TypedDict

from suppy.node import Node, Orders
from suppy.simulator import SupplyChain


class RsqData(TypedDict):
    """Typed dict with mandatory data fields when using the RSQ strategy"""

    review_time: int
    reorder_level: int
    order_quantity: int


@dataclass
class RSQ:
    """RSQ implementation of the supply-chain control strategy

    Arguments:
        supply_chain(SupplyChain) SupplyChain instance to fetch the inventory levels from
    """

    supply_chain: SupplyChain

    def get_orders(self, node: Node, period: int) -> Orders:
        """Return the quantity of `node` to order"""
        # Cast node.data to RsqData
        # This is only done to allow mypy to infer the types of `data` properly.
        data = RsqData(
            review_time=node.data["review_time"],
            reorder_level=node.data["reorder_level"],
            order_quantity=node.data["order_quantity"],
        )
        # Get the inventory level for the requested node
        inventory = self.supply_chain.inventory_assemblies_feasible(node)

        order_quantity = 0
        if (period % data["review_time"] == 0) and (inventory < data["reorder_level"]):
            order_quantity = (
                ceil((data["reorder_level"] - inventory) / data["order_quantity"])
                * data["order_quantity"]
            )
        orders = Orders()
        orders[node] = order_quantity
        return orders
