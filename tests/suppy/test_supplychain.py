import pytest
from hypothesis import given
from hypothesis import strategies as st

from suppy import Edge
from suppy.supplychain import SupplyChain
from suppy.leadtime import LeadTime
from suppy.node import Node, Orders, Stock
from suppy.pipeline import Pipeline, Receipt


def test_supply_chain_node_exists():
    sc = SupplyChain(nodes=[Node("A"), Node("B")])

    assert len(list(sc.nodes)) == 2
    assert len(list(sc.nodes)) == 2

    assert sc.node_exists("A")
    assert sc.node_exists(Node("A"))
    assert not sc.node_exists("C")


def test_supply_chain_check_edges_error():
    """Test if an error is raised if an edge is added without it's corresponding nodes"""
    with pytest.raises(
        ValueError,
        match=r"Edge\(source='A', destination='B', number=42\) defines unknown source node A",
    ):
        SupplyChain(edges=[Edge("A", "B", 42)])

    with pytest.raises(
        ValueError,
        match=r"Edge\(source='A', destination='B', number=42\) "
        r"defines unknown destination node B",
    ):
        SupplyChain(edges=[Edge("A", "B", 42)], nodes=[Node("A")])


def test_supply_chain_check_edges_existing_edge():
    """Test if Edges in Node.predecessors have precedence over the edges list"""
    sc = SupplyChain(
        nodes=[
            Node("A", predecessors=[Edge("B", "A", 5)]),
            Node("B"),
        ],
        edges=[Edge("B", "A", 42)],
    )
    assert sc.nodes["A"].predecessors[0].number == 5
    assert sc.edges["B->A"].number == 5


def test_supply_chain_check_nodes_invalid_predecessor():
    """Check if we raise an error if a Node defines a predecessor with the wrong destination"""
    with pytest.raises(ValueError):
        SupplyChain(
            nodes=[
                Node("A", predecessors=[Edge("A", "B", 5)]),
                Node("B"),
            ],
        )


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
    sc._release_orders(sc.nodes["B"], releases=releases, period=1)

    assert sc.nodes["A"].pipeline == [Receipt(sku_code="B", eta=10, quantity=20)]
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
    sc._release_orders(sc.nodes["B"], releases=releases, period=1)

    assert sc.nodes["A"].pipeline == [Receipt(sku_code="B", eta=10, quantity=20)]
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

    sc._release_orders(sc.nodes["B"], releases=releases, period=1)

    assert sc.nodes["A"].pipeline == []
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

    sc._create_orders(sc.nodes["A"], orders=Orders({"A": 10, "B": 2, "C": 1}), period=1)

    assert sc.nodes["B"].orders == {"A": 13}
    assert sc.nodes["C"].orders == {"A": 21}


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
    sc._create_orders(sc.nodes["A"], orders=Orders({"A": 10}), period=1)

    assert sc.nodes["A"].pipeline == [
        Receipt(sku_code="A", eta=1, quantity=5),
        Receipt(sku_code="A", eta=7, quantity=10),
    ]


def test_supply_chain_create_orders_none():
    """Test if any orders for supplier items are added to the pipeline"""
    sc = SupplyChain(nodes=[Node("A")])
    sc._create_orders(sc.nodes["A"], orders=Orders({"A": 0}), period=1)

    assert sc.nodes["A"].pipeline == []


@given(
    nodes=st.permutations(
        [
            Node("A"),
            Node("B"),
            Node("C"),
            Node("D"),
            Node("E"),
            Node("F"),
            Node("G"),
        ]
    ),
    edges=st.permutations(
        [
            Edge(source="F", destination="A", number=1),
            Edge(source="B", destination="A", number=1),
            Edge(source="C", destination="B", number=1),
            Edge(source="D", destination="B", number=1),
            Edge(source="E", destination="C", number=1),
            Edge(source="F", destination="E", number=1),
        ]
    ),
)
def test_supply_chain_set_llc(nodes, edges):
    """Test if the correct llc is set, regardless of node/edge order"""
    sc = SupplyChain(
        nodes=nodes,
        edges=edges,
    )

    assert sc.nodes["A"].llc == 0
    assert sc.nodes["G"].llc == 0
    assert sc.nodes["B"].llc == 1
    assert sc.nodes["C"].llc == 2
    assert sc.nodes["D"].llc == 2
    assert sc.nodes["E"].llc == 3
    assert sc.nodes["F"].llc == 4


def test_supply_chain_set_llc_single_echelon():
    """Ensure the llc is correctly set for single-echelon supply chains"""
    sc = SupplyChain(
        nodes=[
            Node("A"),
            Node("B"),
        ],
        edges=[],
    )

    assert sc.nodes["A"].llc == 0
    assert sc.nodes["B"].llc == 0
