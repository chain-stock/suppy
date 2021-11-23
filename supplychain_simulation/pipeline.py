from collections import UserList
from dataclasses import dataclass


@dataclass
class Receipt:
    """An in-transit SKU"""

    eta: int
    sku_code: str
    quantity: int


class Pipeline(UserList[Receipt]):
    """Contains all receipts for a specific node"""

    def pop_received(self) -> list[Receipt]:
        """Remove and return all receipts where the ETA is 0 or less"""
        received = [receipt for receipt in self if receipt.eta <= 0]
        self.data[:] = [receipt for receipt in self if receipt.eta > 0]
        return received

    def update_pipeline(self) -> None:
        """Decrease the ETA for all receipt in the pipeline by 1"""
        for receipt in self:
            receipt.eta -= 1

    def add_receipt(self, receipt: Receipt) -> None:
        """Add the provided receipt to the pipeline"""
        self.append(receipt)
