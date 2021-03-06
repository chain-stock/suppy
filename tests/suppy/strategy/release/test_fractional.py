from suppy import Node
from suppy.node import Orders, Stock
from suppy.strategy import Fractional


def test_fractional_feasible():
    orders = {
        "A": 20,
        "B": 40,
    }

    stock = 70

    node = Node("A", orders=Orders(**orders), stock=Stock({"A": stock}))

    order_release = Fractional().get_releases(node=node)

    assert order_release == {
        "A": 20,
        "B": 40,
    }


def test_fractional_infeasible():
    """
    Test whereby the sum of orders requested is larger than the available stock.
    Furthermore, the rounding causes the initial sum of released orders to be larger than the available stock.
    """
    orders = {
        "A": 20,
        "B": 40,
    }
    stock = 7

    node = Node("A", orders=Orders(**orders), stock=Stock({"A": stock}))

    order_release = Fractional().get_releases(node=node)

    assert order_release == {
        "A": 3,
        "B": 4,
    }


def test_fractional_no_order():
    """
    Test whereby the sum of orders requested is larger than the available stock.
    Furthermore, the rounding causes the initial sum of released orders to be larger than the available stock.
    """
    orders = {
        "A": 0,
        "B": 0,
    }
    stock = 7
    node = Node("A", orders=Orders(**orders), stock=Stock({"A": stock}))

    order_release = Fractional().get_releases(node=node)

    assert order_release == {}
