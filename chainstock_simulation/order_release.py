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

    order_total = sum(orders.values())
    # shortage can not be negative
    shortage = max(order_total - stock, 0)

    order_release = {}
    for q_str, order in orders.items():
        order_release[q_str] = ceil(order - shortage * (order / order_total))

    while sum(order_release.values()) > stock:
        max_order_release = max(order_release, key=lambda x: order_release[x])
        order_release[max_order_release] -= 1

    return order_release
