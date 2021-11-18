import pytest

from supplychain_simulation.leadtime import LeadTime
from supplychain_simulation.node import Orders, Stock
from supplychain_simulation.pipeline import Pipeline
from supplychain_simulation.receipt import Receipt
from supplychain_simulation.sales import Sales
from supplychain_simulation.simulator import Edge, Node, Simulator, SupplyChain
from supplychain_simulation.strategy.control.rsq import RSQ
from supplychain_simulation.strategy.release.fractional import Fractional


def test_simulate_period():
    sc = SupplyChain(
        nodes=[
            Node(
                "A",
                data=dict(
                    order_quantity=30,
                    reorder_level=25,
                    review_time=1,
                    safety_stock=1,
                ),
                llc=0,
                sales=Sales({1: 10, 2: 10, 3: 10}),
                lead_time=LeadTime(default=1),
                stock=Stock({"A": 15, "C": 5}),
            ),
            Node(
                "B",
                data=dict(
                    order_quantity=25,
                    reorder_level=40,
                    review_time=1,
                ),
                llc=0,
                sales=Sales({1: 15, 2: 15, 3: 15}),
                lead_time=LeadTime(default=2),
                pipeline=Pipeline([Receipt(sku_code="D", eta=1, quantity=75)]),
                backorders=5,
            ),
            Node(
                "C",
                data=dict(
                    order_quantity=150,
                    reorder_level=20,
                    review_time=1,
                ),
                llc=1,
                lead_time=LeadTime({1: 3, 2: 7}, default=3),
                stock=Stock({"C": 200}),
            ),
            Node(
                "D",
                data=dict(
                    order_quantity=200,
                    reorder_level=20,
                    review_time=2,
                ),
                llc=1,
                lead_time=LeadTime(default=4),
                orders=Orders({"B": 15}),
                stock=Stock({"D": 40}),
                pipeline=Pipeline([Receipt(sku_code="D", eta=2, quantity=200)]),
            ),
        ],
        edges=[
            Edge(source="C", destination="A", number=2),
            Edge(source="D", destination="A", number=1),
            Edge(source="D", destination="B", number=3),
        ],
    )

    sim = Simulator(
        control_strategy=RSQ(sc), release_strategy=Fractional(), supply_chain=sc
    )
    sim.simulate_period(1)

    assert sc.nodes["A"].pipeline.receipts == [
        Receipt(sku_code="C", eta=1, quantity=60),
        Receipt(sku_code="D", eta=1, quantity=7),
    ]
    assert sc.nodes["A"].stock == {"A": 5, "C": 5, "D": 0}


def test_supply_chain_node_exists():
    sc = SupplyChain(nodes=[Node("A"), Node("B")])

    assert len(list(sc.nodes)) == 2
    assert len(list(sc.nodes)) == 2

    assert sc.node_exists("A")
    assert sc.node_exists(Node("A"))
    assert not sc.node_exists("C")


def test_supply_chain_release_orders():
    """Test if the orders of a node are properly released"""
    sc = SupplyChain(
        nodes=[
            Node(
                id="A", lead_time=LeadTime(default=10), predecessors=[Edge("B", "A", 1)]
            ),
            Node(
                id="B",
                stock=Stock({"B": 20}),
                orders=Orders({"A": 20}),
            ),
        ]
    )

    releases = Orders({"A": 20})
    sc.release_orders(sc.nodes["B"], releases=releases, period=1)

    assert sc.nodes["A"].pipeline.receipts == [
        Receipt(sku_code="B", eta=10, quantity=20)
    ]
    assert sc.nodes["B"].stock == {"B": 0}
    assert sc.nodes["B"].orders == {"A": 0}


def test_supply_chain_release_orders_infeasbile():
    """Test if only orders are released if we have stock to release from"""
    sc = SupplyChain(
        nodes=[
            Node(
                id="A", lead_time=LeadTime(default=10), predecessors=[Edge("B", "A", 1)]
            ),
            Node(
                id="B",
                stock=Stock({"B": 20}),
                orders=Orders({"A": 21}),
            ),
        ]
    )

    releases = Orders({"A": 21})
    sc.release_orders(sc.nodes["B"], releases=releases, period=1)

    assert sc.nodes["A"].pipeline.receipts == [
        Receipt(sku_code="B", eta=10, quantity=20)
    ]
    assert sc.nodes["B"].stock == {"B": 0}
    assert sc.nodes["B"].orders == {"A": 1}


@pytest.mark.parametrize("releases", (Orders({"A": 0}), Orders()))
def test_supply_chain_release_orders_zero(releases):
    """Test if nothing is released when not asking for it"""
    sc = SupplyChain(
        nodes=[
            Node(
                id="A", lead_time=LeadTime(default=10), predecessors=[Edge("B", "A", 1)]
            ),
            Node(
                id="B",
                stock=Stock({"B": 20}),
                orders=Orders({"A": 20}),
            ),
        ]
    )

    sc.release_orders(sc.nodes["B"], releases=releases, period=1)

    assert sc.nodes["A"].pipeline.receipts == []
    assert sc.nodes["B"].stock == {"B": 20}
    assert sc.nodes["B"].orders == {"A": 20}


def test_supply_chain_inventory():
    """Test if we can get the inventory of a node"""
    sc = SupplyChain(
        nodes=[
            Node(
                id="A",
                predecessors=[Edge("B", "A", 2)],
                backorders=3,
                orders=Orders({"C": 7, "D": 7}),
                pipeline=Pipeline(
                    [
                        Receipt(sku_code="A", eta=1, quantity=10),
                        Receipt(sku_code="A", eta=8, quantity=10),
                        Receipt(sku_code="B", eta=9, quantity=10),
                    ]
                ),
                stock=Stock({"A": 100, "B": 10}),
            ),
            Node(
                id="B",
                stock=Stock({"B": 10}),
                orders=Orders({"A": 20}),
            ),
        ]
    )
    assert sc.inventory(sc.nodes["A"]) == {"A": 103, "B": 40}
    assert sc.inventory(sc.nodes["B"]) == {"B": -10}


def test_supply_chain_inventory_assemblies_feasible():
    """Test if we can get the feasible assemblies from inventory"""
    sc = SupplyChain(
        nodes=[
            Node(
                id="A",
                predecessors=[Edge("B", "A", 2)],
                stock=Stock({"A": 100, "B": 10}),
                backorders=3,
                orders=Orders({"C": 7, "D": 7}),
                pipeline=Pipeline(
                    [
                        Receipt(sku_code="A", eta=1, quantity=10),
                        Receipt(sku_code="A", eta=8, quantity=10),
                        Receipt(sku_code="B", eta=9, quantity=10),
                    ]
                ),
            ),
            Node(
                id="B",
                stock=Stock({"B": 10}),
                orders=Orders({"A": 20}),
            ),
        ]
    )
    assert sc.inventory(sc.nodes["A"]) == {"A": 103, "B": 40}
    assert sc.inventory_assemblies_feasible(sc.nodes["A"]) == 123


def test_supply_chain_create_orders():
    """Test if the orders are correctly placed at the intercompany nodes"""
    sc = SupplyChain(
        nodes=[
            Node(
                id="A",
                predecessors=[
                    Edge("B", "A", 1),
                    Edge("C", "A", 2),
                ],
            ),
            Node(id="B", orders=Orders({"A": 1})),
            Node(id="C", orders=Orders({"A": 0})),
        ]
    )

    sc.create_orders(sc.nodes["A"], quantity=10, period=1)

    assert sc.nodes["B"].orders == {"A": 11}
    assert sc.nodes["C"].orders == {"A": 20}


def test_supply_chain_create_orders_supplier():
    """Test if any orders for supplier items are added to the pipeline"""
    sc = SupplyChain(
        nodes=[
            Node(
                id="A",
                pipeline=Pipeline(
                    [
                        Receipt(sku_code="A", eta=1, quantity=5),
                    ]
                ),
                lead_time=LeadTime(default=7),
            )
        ]
    )
    sc.create_orders(sc.nodes["A"], quantity=10, period=1)

    assert sc.nodes["A"].pipeline.receipts == [
        Receipt(sku_code="A", eta=1, quantity=5),
        Receipt(sku_code="A", eta=7, quantity=10),
    ]


def test_supply_chain_create_orders_none():
    """Test if any orders for supplier items are added to the pipeline"""
    sc = SupplyChain(nodes=[Node("A")])
    sc.create_orders(sc.nodes["A"], quantity=0, period=1)

    assert sc.nodes["A"].pipeline.receipts == []


def test_supply_chain_set_llc():
    sc = SupplyChain(
        nodes=[
            Node("A"),
            Node("B"),
            Node("C"),
            Node("D"),
            Node("E"),
            Node("F"),
        ],
        edges=[
            Edge(source="B", destination="A", number=1),
            Edge(source="C", destination="B", number=1),
            Edge(source="D", destination="B", number=1),
            Edge(source="E", destination="C", number=1),
            Edge(source="F", destination="A", number=1),
            Edge(source="F", destination="E", number=1),
        ],
    )

    assert sc.nodes["A"].llc == 0
    assert sc.nodes["B"].llc == 1
    assert sc.nodes["C"].llc == 2
    assert sc.nodes["D"].llc == 2
    assert sc.nodes["E"].llc == 3
    assert sc.nodes["F"].llc == 4
