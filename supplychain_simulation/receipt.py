from dataclasses import dataclass


@dataclass
class Receipt:
    """An in-transit SKU"""

    eta: int
    sku_code: str
    quantity: int
