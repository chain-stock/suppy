import pytest

from supplychain_simulation import Edge, LeadTime, SupplyChain
from supplychain_simulation.node import Orders, Sales, Stock
from supplychain_simulation.pipeline import Pipeline, Receipt
from supplychain_simulation.utils import parse


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

    result = parse.supplychain_from_jsons(json_data)

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
    assert node_a.lead_time == {1: 1, 2: 2, 3: 3, 4: 4}
    assert node_b.lead_time == {1: 5, 2: 6}

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
    result = parse.supplychain_from_json(file)

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
    assert node_a.lead_time == {1: 1, 2: 2, 3: 3, 4: 4}
    assert node_b.lead_time == {1: 5, 2: 6}
    with pytest.raises(KeyError):
        node_a.lead_time.get_lead_time(5)
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

    result = parse.supplychain_from_jsons(json_data)

    assert result.node_exists("A")

    node_a = result.nodes["A"]

    assert node_a.predecessors == []
    assert isinstance(node_a.sales, Sales)
    assert node_a.sales == {}
    assert isinstance(node_a.lead_time, LeadTime)
    assert node_a.lead_time == {}
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

    result = parse.supplychain_from_jsons(json_data)

    assert result.node_exists("A")

    node_a = result.nodes["A"]

    assert node_a.lead_time == {}
    assert node_a.lead_time.get_lead_time(66) == 6


def test_parse_sales_invalid_type():
    """Test if an error is raised when the sales type is invalid"""
    with pytest.raises(ValueError):
        x = "foo"
        parse.parse_sales(x)  # type: ignore[arg-type]
