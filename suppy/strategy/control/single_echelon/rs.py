from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import TypedDict

from suppy.node import Node, Orders
from suppy.simulator import SupplyChain


class RSData(TypedDict):
    """Typed dict with mandatory data fields when using the RSQ strategy"""

    review_time: int
    order_up_to_level: int


@dataclass
class se_RS:
    """RsQ implementation of the supply-chain control strategy

    Arguments:
        supply_chain(SupplyChain) SupplyChain instance to fetch the inventory levels from
    """

    supply_chain: SupplyChain

    def get_orders(self, node: Node, period: int) -> Orders:
        """Return the quantity of `node` to order"""
        # Cast node.data to RsqData
        # This is only done to allow mypy to infer the types of `data` properly.
        data = RSData(
            review_time=node.data["review_time"],
            order_up_to_level=node.data["order_up_to_level"],
        )
        # Get the inventory level for the requested node
        inventory = self.supply_chain.inventory_assemblies_feasible(node)

        order_quantity = 0
        if period % data["review_time"] == 0:
            order_quantity = max(data["order_up_to_level"] - inventory, 0)
        orders = Orders()
        orders[node] = order_quantity
        return orders
    