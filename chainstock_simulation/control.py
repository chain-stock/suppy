from math import ceil


def r_s_q(d, inventory, t):
    order_quantity = 0
    if (t % d["review_time"] == 0) & (inventory < d["reorder_level"]):
        order_quantity = (
            ceil((d["reorder_level"] - inventory) / d["order_quantity"])
            * d["order_quantity"]
        )

    return order_quantity
