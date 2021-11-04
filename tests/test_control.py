import chainstock_simulation.control as control


def test_r_s_q_order():
    d = {
        "reorder_level": 7,
        "review_time": 8,
        "order_quantity": 9,
    }
    inventory = 5
    t = 16

    assert control.r_s_q(d=d, inventory=inventory, t=t) == 9


def test_r_s_q_no_order():
    d = {
        "reorder_level": 7,
        "review_time": 8,
        "order_quantity": 9,
    }

    inventory = 5
    t = 17
    assert control.r_s_q(d=d, inventory=inventory, t=t) == 0

    inventory = 7
    t = 16
    assert control.r_s_q(d=d, inventory=inventory, t=t) == 0
