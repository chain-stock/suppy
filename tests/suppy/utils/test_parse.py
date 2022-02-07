import json

import pytest

from suppy import Edge, LeadTime, SupplyChain
from suppy.node import Node, Orders, Sales, Stock
from suppy.pipeline import Pipeline, Receipt


def test_supplychain_from_json(tmp_path):
    """Test if we can parse a JSON file and get a valid SupplyChain object"""
    json_data = """
    {
        "nodes": [
            {
                "id": "A",
                "sales": [
                    [1, 2, 3],
                    [4]
                ],
                "lead_time": {
                    "queue": [
                        1, 2, 3, 4
                    ]
                },
                "backorders": 5,
                "pipeline": [
                    {
                        "sku_code": "B",
                        "eta": 2,
                        "quantity": 5
                    }
                ],
                "stock": {
                    "A": 42,
                    "B": 24
                },
                "orders": {
                    "A": 43,
                    "B": 25
                }
            },
            {
                "id": "B",
                "sales": {
                    "1": [5,6,7],
                    "2": [8]
                },
                "lead_time": {
                    "queue": {
                        "1": 5,
                        "2": 6
                    },
                    "default": 42
                }
            }
        ],
        "edges": [
            {
                "source": "B",
                "destination": "A",
                "number": 42
            }
        ]
    }
    """

    result = SupplyChain.from_json(json_data)

    assert isinstance(result, SupplyChain)
    assert result.node_exists("A")
    assert result.node_exists("B")
    assert result.edge_exists("B->A")

    node_a = result.nodes["A"]
    node_b = result.nodes["B"]

    assert node_a.predecessors == [Edge("B", "A", 42)]
    assert node_b.predecessors == []

    assert isinstance(node_a.sales, Sales)
    assert isinstance(node_b.sales, Sales)
    assert node_a.sales == {1: [1, 2, 3], 2: [4]}
    assert node_b.sales == {1: [5, 6, 7], 2: [8]}

    assert isinstance(node_a.lead_time, LeadTime)
    assert isinstance(node_b.lead_time, LeadTime)
    assert node_a.lead_time == LeadTime([1, 2, 3, 4])
    assert node_b.lead_time == LeadTime({1: 5, 2: 6}, default=42)

    assert node_a.backorders == 5
    assert node_b.backorders == 0

    assert isinstance(node_a.pipeline, Pipeline)
    assert isinstance(node_b.pipeline, Pipeline)
    assert node_a.pipeline == [Receipt(sku_code="B", eta=2, quantity=5)]
    assert node_b.pipeline == []

    assert isinstance(node_a.stock, Stock)
    assert isinstance(node_a.stock, Stock)
    assert node_a.stock == {"A": 42, "B": 24}
    assert node_b.stock == {}

    assert isinstance(node_a.orders, Orders)
    assert isinstance(node_a.orders, Orders)
    assert node_a.orders == {"A": 43, "B": 25}
    assert node_b.orders == {}

    file = tmp_path / "tmp.json"
    file.write_text(json_data)
    result = SupplyChain.from_json(file)

    assert isinstance(result, SupplyChain)
    assert result.node_exists("A")
    assert result.node_exists("B")
    assert result.edge_exists("B->A")

    node_a = result.nodes["A"]
    node_b = result.nodes["B"]

    assert node_a.predecessors == [Edge("B", "A", 42)]
    assert node_b.predecessors == []

    assert isinstance(node_a.sales, Sales)
    assert isinstance(node_b.sales, Sales)
    assert node_a.sales == {1: [1, 2, 3], 2: [4]}
    assert node_b.sales == {1: [5, 6, 7], 2: [8]}

    assert isinstance(node_a.lead_time, LeadTime)
    assert isinstance(node_b.lead_time, LeadTime)
    assert node_a.lead_time == LeadTime([1, 2, 3, 4])
    assert node_b.lead_time == LeadTime({1: 5, 2: 6}, default=42)
    assert node_a.lead_time.get_lead_time(5) == 1
    assert node_b.lead_time.get_lead_time(5) == 42

    assert node_a.backorders == 5
    assert node_b.backorders == 0

    assert isinstance(node_a.pipeline, Pipeline)
    assert isinstance(node_b.pipeline, Pipeline)
    assert node_a.pipeline == [Receipt(sku_code="B", eta=2, quantity=5)]
    assert node_b.pipeline == []

    assert isinstance(node_a.stock, Stock)
    assert isinstance(node_b.stock, Stock)
    assert node_a.stock == {"A": 42, "B": 24}
    assert node_b.stock == {}

    assert isinstance(node_a.orders, Orders)
    assert isinstance(node_b.orders, Orders)
    assert node_a.orders == {"A": 43, "B": 25}
    assert node_b.orders == {}


def test_supplychain_from_json_minimal(tmp_path):
    """Test if we can parse the minimum set of values for a Node"""
    json_data = """
    {
        "nodes": [
            {
                "id": "A"
            }
        ]
    }
    """

    result = SupplyChain.from_json(json_data)

    assert result.node_exists("A")

    node_a = result.nodes["A"]

    assert node_a.predecessors == []
    assert isinstance(node_a.sales, Sales)
    assert node_a.sales == {}
    assert isinstance(node_a.lead_time, LeadTime)
    assert node_a.lead_time == LeadTime()
    assert node_a.backorders == 0
    assert isinstance(node_a.pipeline, Pipeline)
    assert node_a.pipeline == []
    assert isinstance(node_a.stock, Stock)
    assert node_a.stock == {}
    assert isinstance(node_a.orders, Orders)
    assert node_a.orders == {}


def test_supplychain_from_json_lead_time_default(tmp_path):
    """Test if we can only supply a default for lead_time"""
    json_data = """
    {
        "nodes": [
            {
                "id": "A",
                "lead_time": 6
            }
        ]
    }
    """

    result = SupplyChain.from_json(json_data)

    assert result.node_exists("A")

    node_a = result.nodes["A"]

    assert node_a.lead_time == LeadTime(default=6)
    assert node_a.lead_time.get_lead_time(66) == 6


@pytest.mark.parametrize(
    "json_data",
    (
        '{"nodes": [{"id": 4}]}',
        '{"nodes": [{"backorders": 4}]}',
        '{"nodes": [{"id": "A", "sales": 5}]}',
        '{"nodes": [{"id": "A", "stock": 5}]}',
        '{"nodes": [{"id": "A", "orders": 5}]}',
        '{"nodes": [{"id": "A", "backorders": "A"}]}',
        '{"nodes": [{"id": "A", "data": "A"}]}',
    ),
    ids=[
        "id-type",
        "id-missing",
        "sales-type",
        "stock-type",
        "orders-type",
        "backorders-type",
        "data-type",
    ],
)
def test_parse_invalid_type(json_data):
    """Test if an error is raised when the data type is invalid"""
    with pytest.raises(TypeError):
        SupplyChain.from_json(json_data)


def test_supplychain_to_json(tmp_path):
    """Test if we can serialise a SuppyChain"""
    sc = SupplyChain(
        nodes=[
            Node(
                "A",
                sales=Sales({1: [2]}),
                lead_time=LeadTime(default=14),
                orders=Orders({"B": 12}),
                stock=Stock({"A": 100, "B": 3}),
            ),
            Node(
                "B",
                lead_time=LeadTime({1: 13}, default=4),
                pipeline=Pipeline([Receipt(eta=3, sku_code="A", quantity=3)]),
            ),
            Node("C", lead_time=LeadTime([1, 2]), orders=Orders({Node("B"): 12})),
        ],
        edges=[Edge("A", "B", 2)],
    )
    _file = tmp_path / "unittest.json"
    sc.to_json(_file)
    data = json.loads(_file.read_text(encoding="utf8"))
    assert data == {
        "nodes": [
            {
                "id": "A",
                "llc": 1,
                "backorders": 0,
                "data": {},
                "sales": {"1": [2]},
                "lead_time": {"default": 14},
                "orders": {"B": 12},
                "pipeline": [],
                "predecessors": [],
                "stock": {"A": 100, "B": 3},
            },
            {
                "id": "B",
                "llc": 0,
                "backorders": 0,
                "data": {},
                "sales": {},
                "lead_time": {"queue": {"1": 13}, "default": 4},
                "orders": {},
                "pipeline": [{"eta": 3, "sku_code": "A", "quantity": 3}],
                "predecessors": [{"destination": "B", "number": 2, "source": "A"}],
                "stock": {},
            },
            {
                "id": "C",
                "llc": 0,
                "backorders": 0,
                "data": {},
                "sales": {},
                "lead_time": {"queue": [1, 2]},
                "orders": {"B": 12},
                "pipeline": [],
                "predecessors": [],
                "stock": {},
            },
        ],
        "edges": [{"source": "A", "destination": "B", "number": 2}],
    }

    assert json.loads(SupplyChain.from_json(sc.to_json()).to_json()) == data
