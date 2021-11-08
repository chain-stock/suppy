import chainstock_simulation.order_release as orl


def test_fractional_feasible():
    orders = {
        "A": 20,
        "B": 40,
    }

    stock = 70

    order_release = orl.fractional(orders, stock)

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

    order_release = orl.fractional(orders, stock)

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

    order_release = orl.fractional(orders, stock)

    assert order_release == {
        "A": 0,
        "B": 0,
    }
