from __future__ import annotations

from math import ceil

from suppy.node import Node, Orders


class Fractional:  # pylint: disable=too-few-public-methods
    """Fractional implementation of the supply-chain release strategy"""

    def get_releases(self, node: Node) -> Orders:  # pylint: disable=no-self-use
        """Build a set of Orders that should be released"""
        releases = Orders()
        orders = node.orders
        stock = node.stock[node]

        # determine the total amount ordered
        order_total = orders.sum()
        # if there are no orders
        if order_total == 0:
            # release nothing
            return releases

        # shortage can not be negative
        shortage = max(order_total - stock, 0)

        # create an order release where the shortage is divided relative to the
        # share ordered by each sku.
        for q_str, order in orders.items():
            releases[q_str] = ceil(order - shortage * (order / order_total))

        # In case the rounding caused more to be released than possible, reduce the largest
        # release by 1 until the total released equals the available stock.
        while releases.sum() > stock:
            max_order_release = max(releases, key=lambda x: releases[x])
            releases[max_order_release] -= 1

        return releases
