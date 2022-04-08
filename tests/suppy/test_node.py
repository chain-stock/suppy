from unittest.mock import call, patch

import pytest

from suppy import Edge
from suppy.leadtime import LeadTime
from suppy.node import Node, Sales, Stock
from suppy.pipeline import Pipeline, Receipt


def test_assemblies_feasible():
    """Test the number of assemblies we can create for a node"""
    node = Node(
        id="A",
        predecessors=[
            Edge("B", "A", 1),
            Edge("C", "A", 2),
        ],
        stock=Stock({"A": 100, "B": 20, "C": 2}),
    )

    assert node.assemblies_feasible() == 1


def test_assemble():
    """Test if we can assemble a node"""
    node = Node(
        id="A",
        predecessors=[
            Edge("B", "A", 1),
            Edge("C", "A", 2),
        ],
        stock=Stock({"A": 100, "B": 20, "C": 2}),
    )
    node.assemble()

    assert node.stock == {"A": 101, "B": 19, "C": 0}


def test_satisfy_backorders_feasible():
    """Test if we can satisfy the backorders from stock"""
    node = Node(id="A", backorders=40, stock=Stock({"A": 100, "B": 20}))
    node.satisfy_backorders()
    assert node.backorders == 0
    assert node.stock == {"A": 60, "B": 20}


def test_satisfy_backorders_infeasible():
    """Test if we can partially satisfy the backorders from stock"""
    node = Node(id="A", backorders=140, stock=Stock({"A": 100, "B": 20}))
    node.satisfy_backorders()
    assert node.backorders == 40
    assert node.stock == {"A": 0, "B": 20}


def test_satisfy_backorders_none():
    """Test if nothing happens is we don't have any backorders"""
    node = Node(id="A", stock=Stock({"A": 100, "B": 20}))
    node.satisfy_backorders()
    assert node.backorders == 0
    assert node.stock == {"A": 100, "B": 20}


def test_satisfy_sales_feasible():
    """Test if we can satisfy sales from stock"""
    node = Node(
        id="A",
        stock=Stock({"A": 100, "B": 20}),
        sales=Sales({1: [5, 5]}),
    )
    node.satisfy_sales(1, loop=0)
    assert node.backorders == 0
    assert node.stock == {"A": 90, "B": 20}


def test_satisfy_sales_infeasible():
    """Test if we can satisfy sales from stock and add backorders for outage"""
    node = Node(
        id="A",
        stock=Stock({"A": 100, "B": 20}),
        sales=Sales({1: [140]}),
    )
    node.satisfy_sales(1, loop=0)
    assert node.backorders == 40
    assert node.stock == {"A": 0, "B": 20}


def test_satisfy_sales_none():
    """Test if nothing happens without sales for this period"""
    node = Node(
        id="A",
        stock=Stock({"A": 100, "B": 20}),
        sales=Sales({2: [140]}),
    )
    node.satisfy_sales(1, loop=0)
    assert node.backorders == 0
    assert node.stock == {"A": 100, "B": 20}


def test_satisfy_sales_custom():
    """Test if we can provide a custom sales interface"""

    class CustomSales:
        def __init__(self):
            self.sales = iter(range(3))

        def get_sales(self, period: int) -> list[int]:
            try:
                return [next(self.sales)]
            except StopIteration:
                raise ValueError("Out of Sales") from None

    node = Node(
        id="A",
        stock=Stock({"A": 100, "B": 20}),
        sales=CustomSales(),
    )
    node.satisfy_sales(1, loop=0)
    assert node.stock == {"A": 100, "B": 20}
    node.satisfy_sales(20, loop=0)
    assert node.stock == {"A": 99, "B": 20}
    node.satisfy_sales(7, loop=0)
    assert node.stock == {"A": 97, "B": 20}

    with pytest.raises(ValueError, match="Out of Sales"):
        node.satisfy_sales(7, loop=0)


@patch("suppy.node.log_event")
def test_satisfy_sales_metrics_all_satisfied(log_event_mock):
    """Test if the correct metrics are emitted"""
    node = Node("A", sales=Sales({1: [2, 2]}), stock=Stock({"A": 4}))
    node.satisfy_sales(1, loop=0)

    log_event_mock.assert_has_calls(
        [
            call(node=node, event="sales", quantity=4, period=1, loop=0),
            call(node=node, event="order-lines", quantity=2, period=1, loop=0),
            call(node=node, event="sales-satisfied", quantity=4, period=1, loop=0),
            call(node=node, event="order-lines-satisfied", quantity=2, period=1, loop=0),
        ],
    )


@patch("suppy.node.log_event")
def test_satisfy_sales_metrics_partial_satisfied(log_event_mock):
    """Test if the correct metrics are emitted"""
    node = Node("A", sales=Sales({1: [2, 2]}), stock=Stock({"A": 3}))
    node.satisfy_sales(1, loop=0)

    log_event_mock.assert_has_calls(
        [
            call(node=node, event="sales", quantity=4, period=1, loop=0),
            call(node=node, event="order-lines", quantity=2, period=1, loop=0),
            call(node=node, event="sales-satisfied", quantity=3, period=1, loop=0),
            call(node=node, event="order-lines-satisfied", quantity=1, period=1, loop=0),
            call(node=node, event="sales-backordered", quantity=1, period=1, loop=0),
            call(node=node, event="order-lines-backordered", quantity=1, period=1, loop=0),
        ],
    )


def test_stock_default():
    stock = Stock()
    assert stock["foo"] == 0
    stock["bar"] += 10
    assert stock["bar"] == 10


def test_stock_access():
    """Test if we can use a string or a node as the stock key"""
    stock = Stock()
    node = Node("A")

    stock["A"] = 5

    assert stock["A"] == 5
    assert stock[node] == 5

    stock[node] = 10
    assert stock["A"] == 10
    assert stock[node] == 10


def test_satisfy_received_receipts():
    """Test if we add the received receipts to the nodes stock"""
    node = Node(
        id="A",
        stock=Stock({"A": 10, "B": 0, "C": 3}),
        pipeline=Pipeline(
            [
                Receipt(sku_code="A", eta=0, quantity=8),
                Receipt(sku_code="B", eta=0, quantity=9),
                Receipt(sku_code="A", eta=8, quantity=10),
            ]
        ),
    )
    node.satisfy_received_receipts()

    assert node.stock == {"A": 18, "B": 9, "C": 3}
    assert node.pipeline == [
        Receipt(sku_code="A", eta=8, quantity=10),
    ]


def test_get_lead_time():
    """Test if we can get a nodes lead-time"""
    node = Node("A", lead_time=LeadTime(default=10))
    assert node.get_lead_time(period=1) == 10
    assert node.get_lead_time(period=10) == 10
    assert node.get_lead_time(period=5) == 10


def test_get_lead_time_per_period():
    """Test if we can define a leadtime per period"""
    node = Node("A", lead_time=LeadTime({1: 14, 10: 12}, default=10))
    assert node.get_lead_time(period=1) == 14
    assert node.get_lead_time(period=10) == 12
    assert node.get_lead_time(period=5) == 10


def test_sales_invalid():
    """Test if an error is raised when providing the wrong data"""
    with pytest.raises(TypeError):
        Sales({"1": [1]})  # type: ignore


def test_stock_negative():
    """Test if an error is raised if the stock drops below zero"""
    with pytest.raises(ValueError):
        Stock({"A": -1})

    stock = Stock()
    with pytest.raises(ValueError):
        stock["A"] = -2

    stock["A"] = 0
    with pytest.raises(ValueError):
        stock["A"] -= 1
