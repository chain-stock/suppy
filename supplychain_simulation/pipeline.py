from dataclasses import dataclass, field
from typing import Iterator


@dataclass
class Receipt:
    """An in-transit SKU"""

    eta: int
    sku_code: str
    quantity: int


@dataclass
class Pipeline:
    """Contains all receipts for a specific node"""

    receipts: list[Receipt] = field(default_factory=list)

    def __iter__(self) -> Iterator[Receipt]:
        """Return the receipts when iterating over the pipeline"""
        for receipt in self.receipts:
            yield receipt

    def pop_received(self) -> list[Receipt]:
        """Remove and return all receipts where the ETA is 0 or less"""
        received = [receipt for receipt in self.receipts if receipt.eta <= 0]
        self.receipts[:] = [receipt for receipt in self.receipts if receipt.eta > 0]
        return received

    def update_pipeline(self) -> None:
        """Decrease the ETA for all receipt in the pipeline by 1"""
        for receipt in self.receipts:
            receipt.eta -= 1

    def add_receipt(self, receipt: Receipt) -> None:
        """Add the provided receipt to the pipeline"""
        self.receipts.append(receipt)
