from chainstock_simulation.billofmaterial import BillOfMaterialGraph


def test_import_json_data():
    bill_of_material = BillOfMaterialGraph(
        data=[{
            "id": "A",
            "data": {
                "added_value": 1,
                "review_period": 1,
                "e_lead_time": 1,
                "order_quantity": 1,
            },
            "adjacencies": [
                {"data": {"number": 1},
                 "item_to": "B", },
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
                    }
                },
                "adjacencies": [],
            }],
        sales_data={"B": {1: 10, 2: 20, 3: 5, 4: 10, 5: 20}},
        stock_data={"A": 1000, "B": 40},
        lead_time_data={"B": [2]},
        safety_stock_data={"B": 5},
        reorder_point_data={"B": 15},
    )

    expected = {
        'added_value': 1,
        'review_period': 1,
        'e_lead_time': 10,
        'order_quantity': 50,
        'e_demand': 10,
        's_demand': 10,
        'target': 0.95,
        'llc': 0,
        'sales_queue': {1: 10, 2: 20, 3: 5, 4: 10, 5: 20},
        'stock': 40,
        'lead_time_queue': [2],
        'safety_stock': 5,
        'reorder_point': 15
    }

    assert bill_of_material.nodes["B"] == expected
