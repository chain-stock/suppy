from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict

from suppy.node import Node, Orders
from suppy.simulator import SupplyChain


class RSData(TypedDict):
    """Typed dict with mandatory data fields when using the RSQ strategy"""

    review_time: int
    order_up_to_level: int


@dataclass
class me_RS:
    """Multi-echelon RS implementation of the supply-chain control strategy

    Arguments:
        supply_chain(SupplyChain) SupplyChain instance to fetch the echelon inventory levels from
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
        # Get the echelon inventory level for the requested node
        echelon_inventory = 0
        echelon = [node]
        while echelon:
            echelon_next = []
            for _node in echelon:
                echelon_inventory += self.supply_chain.inventory_assemblies_feasible(_node)
                for edge in _node.successors:
                    if self.supply_chain.nodes[edge.destination] not in echelon_next:
                        echelon_next.append(self.supply_chain.nodes[edge.destination])
            echelon = echelon_next

        order_quantity = 0
        if period % data["review_time"] == 0:
            order_quantity = max(data["order_up_to_level"] - echelon_inventory, 0)
        orders = Orders()
        orders[node] = order_quantity
        return orders
