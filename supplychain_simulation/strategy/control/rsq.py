from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import TypedDict

from supplychain_simulation.node import Node
from supplychain_simulation.simulator import SupplyChain


class RsqData(TypedDict):
    review_time: int
    reorder_level: int
    order_quantity: int


@dataclass
class RSQ:
    supply_chain: SupplyChain

    def get_order_quantity(self, node: Node, period: int) -> int:
        """Return the quantity of `node` to order"""
        # Cast node.data to RsqData, this is only done to allow mypy to infer the types of `data` properly.
        data = RsqData(
            review_time=node.data["review_time"],
            reorder_level=node.data["reorder_level"],
            order_quantity=node.data["order_quantity"],
        )
        inventory = self.supply_chain.inventory_assemblies_feasible(node)

        order_quantity = 0
        if (period % data["review_time"] == 0) and (inventory < data["reorder_level"]):
            order_quantity = (
                ceil((data["reorder_level"] - inventory) / data["order_quantity"])
                * data["order_quantity"]
            )

        return order_quantity
