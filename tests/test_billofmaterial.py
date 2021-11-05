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


def test_initialize_simulation():
    bill_of_material = BillOfMaterialGraph(
        data=[
            {
                "id": "A",
                "data": {},
                "adjacencies": {},
            }
        ],
        auxiliary_data={
            "safety_stock_queue": {"A": {0: 5}},
            "reorder_point_queue": {"A": {0: 12}},
        },
    )

    bill_of_material.initialize_simulation()

    assert bill_of_material.nodes["A"]["pipeline"] == []
    assert bill_of_material.nodes["A"]["safety_stock"] == 5
    assert bill_of_material.nodes["A"]["reorder_point"] == 12


def test_assemble_feasible_stock():
    bill_of_material = BillOfMaterialGraph(
        data=[
            {
                "id": "A",
                "data": {},
                "adjacencies": {},
            },
            {
                "id": "B",
                "data": {},
                "adjacencies": [{"data": {"number": 1}, "item_to": "A"}],
            },
            {
                "id": "C",
                "data": {},
                "adjacencies": [{"data": {"number": 2}, "item_to": "A"}],
            },
        ],
        auxiliary_data={
            "safety_stock_queue": {"A": {0: 1}},
        },
    )
    stock = {"A": 100, "B": 20, "C": 2}

    assert bill_of_material.assemble_feasible_stock("A", stock) == 1


def test_assemble_feasible_stock_self():
    """
    Test for the determination of feasible number of items to be assembled from stock
    where the items to be assembled are the sku itself.
    """
    bill_of_material = BillOfMaterialGraph(
        data=[
            {
                "id": "A",
                "data": {},
                "adjacencies": {},
            },
        ],
        auxiliary_data={
            "safety_stock_queue": {"A": {0: 1}},
        },
    )
    stock = {"A": 10}

    assert bill_of_material.assemble_feasible_stock("A", stock) == 0


def test_assemble():
    bill_of_material = BillOfMaterialGraph(
        data=[
            {
                "id": "A",
                "data": {"stock": {"A": 100, "B": 20, "C": 2}},
                "adjacencies": {},
            },
            {
                "id": "B",
                "data": {},
                "adjacencies": [{"data": {"number": 1}, "item_to": "A"}],
            },
            {
                "id": "C",
                "data": {},
                "adjacencies": [{"data": {"number": 2}, "item_to": "A"}],
            },
        ],
        auxiliary_data={
            "safety_stock_queue": {"A": {0: 1}},
        },
    )

    bill_of_material.assemble("A")
    bill_of_material.nodes["A"]["stock"] = {"A": 101, "B": 19, "C": 0}


def test_satisfy_backorders_feasible():
    bill_of_material = BillOfMaterialGraph(
        data=[
            {
                "id": "A",
                "data": {"backorder_quantity": 40, "stock": {"A": 100, "B": 20}},
                "adjacencies": {},
            },
        ],
        auxiliary_data={
            "safety_stock_queue": {"A": {0: 1}},
        },
    )

    bill_of_material.satisfy_backorders("A")

    assert bill_of_material.nodes["A"]["backorder_quantity"] == 0
    assert bill_of_material.nodes["A"]["stock"] == {"A": 60, "B": 20}


def test_satisfy_backorders_infeasible():
    bill_of_material = BillOfMaterialGraph(
        data=[
            {
                "id": "A",
                "data": {"backorder_quantity": 140, "stock": {"A": 100, "B": 20}},
                "adjacencies": {},
            },
        ],
        auxiliary_data={
            "safety_stock_queue": {"A": {0: 1}},
        },
    )

    bill_of_material.satisfy_backorders("A")

    assert bill_of_material.nodes["A"]["backorder_quantity"] == 40
    assert bill_of_material.nodes["A"]["stock"] == {"A": 0, "B": 20}


def test_satisfy_backorders_none():
    bill_of_material = BillOfMaterialGraph(
        data=[
            {"id": "A", "data": {"stock": {"A": 100, "B": 20}}, "adjacencies": {}},
        ],
        auxiliary_data={
            "safety_stock_queue": {"A": {0: 1}},
        },
    )

    bill_of_material.satisfy_backorders("A")

    assert "backorder_quantity" not in bill_of_material.nodes["A"].keys()
    assert bill_of_material.nodes["A"]["stock"] == {"A": 100, "B": 20}


def test_satisfy_sales_feasible():
    bill_of_material = BillOfMaterialGraph(
        data=[
            {
                "id": "A",
                "data": {
                    "backorder_quantity": 0,
                    "sales": {1: 10},
                    "stock": {"A": 100, "B": 20},
                },
                "adjacencies": {},
            },
        ],
        auxiliary_data={
            "safety_stock_queue": {"A": {0: 1}},
        },
    )

    bill_of_material.satisfy_sales("A", 1)

    assert bill_of_material.nodes["A"]["backorder_quantity"] == 0
    assert bill_of_material.nodes["A"]["stock"] == {"A": 90, "B": 20}


def test_satisfy_sales_infeasible():
    bill_of_material = BillOfMaterialGraph(
        data=[
            {
                "id": "A",
                "data": {
                    "backorder_quantity": 0,
                    "sales": {1: 140},
                    "stock": {"A": 100, "B": 20},
                },
                "adjacencies": {},
            },
        ],
        auxiliary_data={
            "safety_stock_queue": {"A": {0: 1}},
        },
    )

    bill_of_material.satisfy_sales("A", 1)

    assert bill_of_material.nodes["A"]["backorder_quantity"] == 40
    assert bill_of_material.nodes["A"]["stock"] == {"A": 0, "B": 20}
    assert bill_of_material.nodes["A"]["sales"] == {}


def test_satisfy_sales_none():
    bill_of_material = BillOfMaterialGraph(
        data=[
            {
                "id": "A",
                "data": {
                    "backorder_quantity": 0,
                    "sales": {2: 10},
                    "stock": {"A": 100, "B": 20},
                },
                "adjacencies": {},
            },
        ],
        auxiliary_data={
            "safety_stock_queue": {"A": {0: 1}},
        },
    )

    bill_of_material.satisfy_sales("A", 1)

    assert bill_of_material.nodes["A"]["backorder_quantity"] == 0
    assert bill_of_material.nodes["A"]["stock"] == {"A": 100, "B": 20}


def test_initialize_simulation_customer():
    bill_of_material = BillOfMaterialGraph(
        data=[
            {
                "id": "A",
                "data": {
                    "sales": {2: 10},
                },
                "adjacencies": {},
            },
        ],
        auxiliary_data={
            "safety_stock_queue": {"A": {0: 1}},
        },
    )

    bill_of_material.initialize_simulation()

    assert bill_of_material.nodes["A"]["customer"]
    assert bill_of_material.nodes["A"]["backorder_quantity"] == 0


def test_initialize_simulation_customer_backorder():
    bill_of_material = BillOfMaterialGraph(
        data=[
            {
                "id": "A",
                "data": {
                    "backorder_quantity": 7,
                    "sales": {2: 10},
                },
                "adjacencies": {},
            },
        ],
        auxiliary_data={
            "safety_stock_queue": {"A": {0: 1}},
        },
    )

    bill_of_material.initialize_simulation()

    assert bill_of_material.nodes["A"]["customer"]
    assert bill_of_material.nodes["A"]["backorder_quantity"] == 7


def test_initialize_simulation_pipeline():
    bill_of_material = BillOfMaterialGraph(
        data=[
            {
                "id": "A",
                "data": {
                    "pipeline": [{"sku_code": "A", "eta": 9, "quantity": 1}],
                },
                "adjacencies": {},
            },
        ],
        auxiliary_data={
            "safety_stock_queue": {"A": {0: 1}},
        },
    )

    bill_of_material.initialize_simulation()

    assert bill_of_material.nodes["A"]["pipeline"] == [
        {"sku_code": "A", "eta": 9, "quantity": 1}
    ]


def test_initialize_simulation_not_customer():
    bill_of_material = BillOfMaterialGraph(
        data=[
            {"id": "A", "data": {}, "adjacencies": {}},
        ],
        auxiliary_data={
            "safety_stock_queue": {"A": {0: 1}},
        },
    )

    bill_of_material.initialize_simulation()

    assert not bill_of_material.nodes["A"]["customer"]


def test_release_orders():
    bill_of_material = BillOfMaterialGraph(
        data=[
            {
                "id": "A",
                "data": {"e_lead_time": 10, "pipeline": []},
                "adjacencies": {},
            },
            {
                "id": "B",
                "data": {
                    "stock": {"B": 20},
                    "orders": {"A": 20},
                },
                "adjacencies": [{"data": {"number": 1}, "item_to": "A"}],
            },
        ],
        auxiliary_data={
            "safety_stock_queue": {"A": {0: 1}},
        },
    )

    order_release = {"A": 20}
    bill_of_material.release_orders(p_str="B", order_release=order_release)

    assert bill_of_material.nodes["A"]["pipeline"] == [
        {"sku_code": "B", "eta": 10, "quantity": 20}
    ]
    assert bill_of_material.nodes["B"]["stock"] == {"B": 0}
    assert bill_of_material.nodes["B"]["orders"] == {"A": 0}


def test_release_orders_infeasible():
    bill_of_material = BillOfMaterialGraph(
        data=[
            {
                "id": "A",
                "data": {"e_lead_time": 10, "pipeline": []},
                "adjacencies": {},
            },
            {
                "id": "B",
                "data": {
                    "stock": {"B": 20},
                    "orders": {"A": 21},
                },
                "adjacencies": [{"data": {"number": 1}, "item_to": "A"}],
            },
        ],
        auxiliary_data={
            "safety_stock_queue": {"A": {0: 1}},
        },
    )

    order_release = {"A": 21}
    bill_of_material.release_orders(p_str="B", order_release=order_release)

    assert bill_of_material.nodes["A"]["pipeline"] == [
        {"sku_code": "B", "eta": 10, "quantity": 20}
    ]
    assert bill_of_material.nodes["B"]["stock"] == {"B": 0}
    assert bill_of_material.nodes["B"]["orders"] == {"A": 1}


def test_inventory():
    bill_of_material = BillOfMaterialGraph(
        data=[
            {
                "id": "A",
                "data": {
                    "stock": {"A": 100, "B": 10},
                    "backorder_quantity": 3,
                    "orders": {"C": 7, "D": 7},
                    "pipeline": [
                        {"sku_code": "A", "eta": 1, "quantity": 10},
                        {"sku_code": "A", "eta": 8, "quantity": 10},
                        {"sku_code": "B", "eta": 9, "quantity": 10},
                    ],
                },
                "adjacencies": {},
            },
            {
                "id": "B",
                "data": {
                    "stock": {"B": 10},
                    "orders": {"A": 20},
                    "pipeline": [],
                },
                "adjacencies": [{"data": {"number": 2}, "item_to": "A"}],
            },
        ],
        auxiliary_data={
            "safety_stock_queue": {"A": {0: 1}},
        },
    )

    inventory = bill_of_material.inventory("A")
    assert inventory == {"A": 103, "B": 40}

    inventory = bill_of_material.inventory("B")
    assert inventory == {"B": -10}


def test_assemble_feasible_inventory():

    bill_of_material = BillOfMaterialGraph(
        data=[
            {
                "id": "A",
                "data": {
                    "stock": {"A": 100, "B": 10},
                    "backorder_quantity": 3,
                    "orders": {"C": 7, "D": 7},
                    "pipeline": [
                        {"sku_code": "A", "eta": 1, "quantity": 10},
                        {"sku_code": "A", "eta": 8, "quantity": 10},
                        {"sku_code": "B", "eta": 9, "quantity": 10},
                    ],
                },
                "adjacencies": {},
            },
            {
                "id": "B",
                "data": {
                    "stock": {"B": 10},
                    "orders": {"A": 20},
                    "pipeline": [],
                },
                "adjacencies": [{"data": {"number": 2}, "item_to": "A"}],
            },
        ],
        auxiliary_data={
            "safety_stock_queue": {"A": {0: 1}},
        },
    )

    assert bill_of_material.assemble_feasible_inventory("A") == 123


def test_create_orders():
    bill_of_material = BillOfMaterialGraph(
        data=[
            {
                "id": "A",
                "data": {},
                "adjacencies": {},
            },
            {
                "id": "B",
                "data": {"orders": {"A": 1}},
                "adjacencies": [{"data": {"number": 1}, "item_to": "A"}],
            },
            {
                "id": "C",
                "data": {"orders": {"A": 0}},
                "adjacencies": [{"data": {"number": 2}, "item_to": "A"}],
            },
        ],
        auxiliary_data={
            "safety_stock_queue": {"A": {0: 1}},
        },
    )

    bill_of_material.create_orders("A", 10)

    assert bill_of_material.nodes["B"]["orders"]["A"] == 11
    assert bill_of_material.nodes["C"]["orders"]["A"] == 20


def test_create_orders_supplier():
    bill_of_material = BillOfMaterialGraph(
        data=[
            {
                "id": "A",
                "data": {
                    "pipeline": [{"sku_code": "A", "eta": 1, "quantity": 5}],
                    "e_lead_time": 7,
                },
                "adjacencies": {},
            },
        ],
        auxiliary_data={
            "safety_stock_queue": {"A": {0: 1}},
        },
    )

    bill_of_material.create_orders("A", 10)

    assert bill_of_material.nodes["A"]["pipeline"] == [
        {"sku_code": "A", "eta": 1, "quantity": 5},
        {"sku_code": "A", "eta": 7, "quantity": 10},
    ]


def test_create_orders_none():
    bill_of_material = BillOfMaterialGraph(
        data=[
            {
                "id": "A",
                "data": {"pipeline": []},
                "adjacencies": {},
            },
        ],
        auxiliary_data={
            "safety_stock_queue": {"A": {0: 1}},
        },
    )

    bill_of_material.create_orders("A", 0)

    assert bill_of_material.nodes["A"]["pipeline"] == []


def test_fetch_receipts():

    bill_of_material = BillOfMaterialGraph(
        data=[
            {
                "id": "A",
                "data": {
                    "stock": {"A": 10, "B": 0, "C": 3},
                    "pipeline": [
                        {"sku_code": "A", "eta": 0, "quantity": 8},
                        {"sku_code": "B", "eta": 0, "quantity": 9},
                        {"sku_code": "A", "eta": 8, "quantity": 10},
                    ],
                },
                "adjacencies": {},
            },
        ],
        auxiliary_data={
            "safety_stock_queue": {"A": {0: 1}},
        },
    )

    bill_of_material.fetch_receipts("A")

    assert bill_of_material.nodes["A"]["stock"] == {"A": 18, "B": 9, "C": 3}
    assert bill_of_material.nodes["A"]["pipeline"] == [
        {"sku_code": "A", "eta": 8, "quantity": 10}
    ]


def test_fetch_lead_time():
    bill_of_material = BillOfMaterialGraph(
        data=[
            {
                "id": "A",
                "data": {
                    "e_lead_time": 10,
                    "pipeline": [],
                },
                "adjacencies": {},
            },
        ],
        auxiliary_data={
            "safety_stock_queue": {"A": {0: 1}},
        },
    )

    assert bill_of_material.fetch_lead_time("A") == 10


def test_fetch_lead_time_queue():
    bill_of_material = BillOfMaterialGraph(
        data=[
            {
                "id": "A",
                "data": {
                    "e_lead_time": 10,
                    "pipeline": [],
                    "lead_time_queue": [7, 8, 9],
                },
                "adjacencies": {},
            },
        ],
        auxiliary_data={
            "safety_stock_queue": {"A": {0: 1}},
        },
    )

    assert bill_of_material.fetch_lead_time("A") == 7


def test_simulate_period():
    bill_of_material = BillOfMaterialGraph(
        data=[
            {
                "id": "A",
                "data": {
                    "llc": 0,
                    "sales": {1: 10, 2: 10, 3: 10},
                    "e_lead_time": 1,
                    "stock": {"A": 15, "C": 5, "D": 0},
                    "pipeline": [],
                    "order_quantity": 30,
                    "reorder_level": 25,
                    "review_time": 1,
                    "backorder_quantity": 0,
                    "orders": {},
                },
                "adjacencies": {},
            },
            {
                "id": "B",
                "data": {
                    "llc": 0,
                    "sales": {1: 15, 2: 15, 3: 15},
                    "e_lead_time": 2,
                    "stock": {"B": 0, "D": 0},
                    "pipeline": [{"sku_code": "D", "eta": 1, "quantity": 75}],
                    "order_quantity": 25,
                    "reorder_level": 40,
                    "review_time": 1,
                    "backorder_quantity": 5,
                    "orders": {},
                },
                "adjacencies": [],
            },
            {
                "id": "C",
                "data": {
                    "llc": 1,
                    "e_lead_time": 3,
                    "lead_time_queue": [3, 7],
                    "stock": {"C": 200},
                    "pipeline": [],
                    "order_quantity": 150,
                    "reorder_level": 20,
                    "review_time": 1,
                    "orders": {"A": 0},
                },
                "adjacencies": [{"data": {"number": 2}, "item_to": "A"}],
            },
            {
                "id": "D",
                "data": {
                    "llc": 1,
                    "e_lead_time": 4,
                    "stock": {"D": 40},
                    "pipeline": [{"sku_code": "D", "eta": 2, "quantity": 200}],
                    "order_quantity": 200,
                    "reorder_level": 20,
                    "review_time": 2,
                    "orders": {"A": 0, "B": 15},
                },
                "adjacencies": [
                    {"data": {"number": 1}, "item_to": "A"},
                    {"data": {"number": 3}, "item_to": "B"},
                ],
            },
        ],
        auxiliary_data={
            "safety_stock_queue": {"A": {0: 1}},
        },
    )

    bill_of_material.simulate_period(1)

    assert bill_of_material.nodes["A"]["pipeline"] == [
        {"sku_code": "C", "eta": 1, "quantity": 60},
        {"sku_code": "D", "eta": 1, "quantity": 7},
    ]
    assert bill_of_material.nodes["A"]["stock"] == {"A": 5, "C": 5, "D": 0}
    assert bill_of_material.nodes["A"]["sales"] == {2: 10, 3: 10}
    assert bill_of_material.nodes["A"]["backorder_quantity"] == 0

    assert bill_of_material.nodes["B"]["pipeline"] == [
        {"sku_code": "D", "eta": 0, "quantity": 75},
        {"sku_code": "D", "eta": 2, "quantity": 33},
    ]
    assert bill_of_material.nodes["B"]["stock"] == {"B": 0, "D": 0}
    assert bill_of_material.nodes["B"]["sales"] == {2: 15, 3: 15}
    assert bill_of_material.nodes["B"]["backorder_quantity"] == 20

    assert bill_of_material.nodes["C"]["pipeline"] == []
    assert bill_of_material.nodes["C"]["stock"] == {"C": 140}
    assert bill_of_material.nodes["C"]["orders"] == {"A": 0}

    assert bill_of_material.nodes["D"]["pipeline"] == [
        {"sku_code": "D", "eta": 1, "quantity": 200},
    ]
    assert bill_of_material.nodes["D"]["stock"] == {"D": 0}
    assert bill_of_material.nodes["D"]["orders"] == {"A": 23, "B": 132}
