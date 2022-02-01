from unittest.mock import MagicMock

from suppy import Node
from suppy.strategy import RSQ


def test_r_s_q_order():
    supplychain = MagicMock()
    supplychain.inventory_assemblies_feasible.return_value = 5
    d = {
        "reorder_level": 7,
        "review_time": 8,
        "order_quantity": 9,
    }
    t = 16

    rsq = RSQ(supplychain)
    node = Node("A", data=d)

    assert rsq.get_orders(node=node, period=t)[node] == 9


def test_r_s_q_no_order():
    supplychain = MagicMock()
    supplychain.inventory_assemblies_feasible.return_value = 5
    d = {
        "reorder_level": 7,
        "review_time": 8,
        "order_quantity": 9,
    }

    rsq = RSQ(supplychain)
    node = Node("A", data=d)

    t = 17
    assert rsq.get_orders(node=node, period=t)[node] == 0

    supplychain.inventory_assemblies_feasible.return_value = 7
    t = 16
    assert rsq.get_orders(node=node, period=t)[node] == 0
