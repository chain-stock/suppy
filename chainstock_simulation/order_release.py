from math import ceil

"""
A valid order release function is any function that returns
a list of dictionaries in the following format,
[
    {
        "sku_code": "A",
        "quantity": 20,
    },
    ...
]
"""


def fractional(orders, stock):

    # determine the total amount ordered
    order_total = sum(orders.values())
    # if there are no orders
    if order_total == 0:
        # release nothing
        return {c_str: 0 for c_str in orders.keys()}

    # shortage can not be negative
    shortage = max(order_total - stock, 0)

    # create an order release where the shortage is divided relative to the
    # share ordered by each sku.
    order_release = {}
    for q_str, order in orders.items():
        order_release[q_str] = ceil(order - shortage * (order / order_total))

    # In case the rounding caused more to be released than possible, reduce the largest
    # release by 1 until the total released equals the available stock.
    while sum(order_release.values()) > stock:
        max_order_release = max(order_release, key=lambda x: order_release[x])
        order_release[max_order_release] -= 1

    return order_release
