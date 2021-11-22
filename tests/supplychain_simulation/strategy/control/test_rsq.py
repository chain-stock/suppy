from unittest.mock import MagicMock

from supplychain_simulation import Node
from supplychain_simulation.strategy import RSQ


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

    assert rsq.get_order_quantity(node=node, period=t) == 9


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
    assert rsq.get_order_quantity(node=node, period=t) == 0

    supplychain.inventory_assemblies_feasible.return_value = 7
    t = 16
    assert rsq.get_order_quantity(node=node, period=t) == 0
