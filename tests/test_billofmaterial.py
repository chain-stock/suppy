import os

import pytest

from chainstock_simulation.billofmaterial import BillOfMaterialGraph

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def test_import_json_empty():
    with pytest.raises(AttributeError):
        bill_of_material = BillOfMaterialGraph(
            data=None,
        )


def test_import_json_no_control():
    with pytest.raises(AttributeError):
        bill_of_material = BillOfMaterialGraph(
            data=[{"id": "A", "data": {}, "adjacencies": {}}],
            auxiliary_data={},
        )


def test_import_json_control1():
    bill_of_material = BillOfMaterialGraph(
        data=[{"id": "A", "data": {}, "adjacencies": {}}],
        auxiliary_data={
            "safety_stock_queue": {"A": {0: 1}},
        },
    )
    assert bill_of_material.nodes["A"]["safety_stock_queue"] == {0: 1}


def test_import_json_control2():
    bill_of_material = BillOfMaterialGraph(
        data=[{"id": "A", "data": {}, "adjacencies": {}}],
        auxiliary_data={"reorder_point_queue": {"A": {0: 1}}},
    )
    assert bill_of_material.nodes["A"]["reorder_point_queue"] == {0: 1}


def test_import_json_data():
    json_data = [
        {
            "id": "A",
            "data": {
                "added_value": 1,
                "review_period": 1,
                "e_lead_time": 1,
                "order_quantity": 1,
            },
            "adjacencies": [
                {
                    "data": {"number": 1},
                    "item_to": "B",
                },
            ],
        },
        {
            "id": "B",
            "data": {
                "added_value": 1,
                "review_period": 1,
                "e_lead_time": 10,
                "order_quantity": 50,
                "customer_data": {
                    "e_demand": 10,
                    "s_demand": 10,
                    "target_service_level": 0.95,
                },
            },
            "adjacencies": [],
        },
    ]

    bill_of_material = BillOfMaterialGraph(
        data=json_data,
        auxiliary_data={
            "safety_stock_queue": {"B": {0: 2}},
        },
    )

    expected_a = {
        "added_value": 1,
        "review_period": 1,
        "e_lead_time": 1,
        "order_quantity": 1,
        "llc": 1,
    }

    expected_b = {
        "added_value": 1,
        "review_period": 1,
        "e_lead_time": 10,
        "order_quantity": 50,
        "e_demand": 10,
        "s_demand": 10,
        "target": 0.95,
        "llc": 0,
        "safety_stock_queue": {0: 2},
    }

    assert bill_of_material.nodes["A"] == expected_a
    assert bill_of_material.nodes["B"] == expected_b
    assert bill_of_material.edges[("A", "B")]["number"] == 1


def test_import_json_file():
    bill_of_material = BillOfMaterialGraph(
        file=os.path.join(TEST_DATA_DIR, "input", "bill_of_material.json"),
        auxiliary_data={"safety_stock_queue": {"B": {0: 2}}},
    )

    expected_a = {
        "added_value": 1,
        "review_period": 1,
        "e_lead_time": 1,
        "order_quantity": 1,
        "llc": 1,
    }

    expected_b = {
        "added_value": 1,
        "review_period": 1,
        "e_lead_time": 10,
        "order_quantity": 50,
        "e_demand": 10,
        "s_demand": 10,
        "target": 0.95,
        "llc": 0,
        "safety_stock_queue": {0: 2},
    }

    assert bill_of_material.nodes["A"] == expected_a
    assert bill_of_material.nodes["B"] == expected_b
    assert bill_of_material.edges[("A", "B")]["number"] == 1


def test_import_excel():
    bill_of_material = BillOfMaterialGraph(
        file=os.path.join(TEST_DATA_DIR, "input", "bill_of_material.xlsx"),
        auxiliary_data={
            "safety_stock_queue": {"B": {0: 2}},
        },
    )

    expected_a = {
        "added_value": 1,
        "review_period": 1,
        "e_lead_time": 1,
        "order_quantity": 1,
        "llc": 1,
    }

    expected_b = {
        "added_value": 1,
        "review_period": 1,
        "e_lead_time": 10,
        "order_quantity": 50,
        "e_demand": 10,
        "s_demand": 10,
        "target": 0.95,
        "llc": 0,
        "safety_stock_queue": {0: 2},
    }

    assert bill_of_material.nodes["A"] == expected_a
    assert bill_of_material.nodes["B"] == expected_b
    assert bill_of_material.edges[("A", "B")]["number"] == 1


def test_import_auxiliary_data():
    bill_of_material = BillOfMaterialGraph(
        data=[
            {
                "id": "A",
                "data": {},
                "adjacencies": {},
            }
        ],
        auxiliary_data={
            "sales_queue": {"A": {1: 10, 2: 20, 3: 5, 4: 10, 5: 20}},
            "stock": {"A": 1000},
            "lead_time_queue": {"A": [2]},
            "safety_stock_queue": {"A": {0: 5}},
            "reorder_point_queue": {"A": {0: 12}},
        },
    )

    assert bill_of_material.nodes["A"]["sales_queue"] == {
        1: 10,
        2: 20,
        3: 5,
        4: 10,
        5: 20,
    }
    assert bill_of_material.nodes["A"]["stock"] == 1000
    assert bill_of_material.nodes["A"]["lead_time_queue"] == [2]
    assert bill_of_material.nodes["A"]["safety_stock_queue"] == {0: 5}
    assert bill_of_material.nodes["A"]["reorder_point_queue"] == {0: 12}
