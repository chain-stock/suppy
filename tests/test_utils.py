import chainstock_simulation.utils as utils


def test_update_pipeline():
    pipeline = [
        {"sku_code": "A", "eta": 10, "quantity": 1},
        {"sku_code": "B", "eta": 1, "quantity": 5},
    ]

    pipeline = utils.update_pipeline(pipeline)

    assert pipeline == [
        {"sku_code": "A", "eta": 9, "quantity": 1},
        {"sku_code": "B", "eta": 0, "quantity": 5},
    ]
