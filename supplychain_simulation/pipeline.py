from dataclasses import dataclass, field
from typing import Iterator

from supplychain_simulation.receipt import Receipt


@dataclass
class Pipeline:
    """Contains all receipts for a specific node"""

    receipts: list[Receipt] = field(default_factory=list)

    def __iter__(self) -> Iterator[Receipt]:
        for receipt in self.receipts:
            yield receipt

    def pop_received(self) -> list[Receipt]:
        """Remove and return all receipts where the ETA is 0"""
        received = [receipt for receipt in self.receipts if receipt.eta == 0]
        self.receipts[:] = [receipt for receipt in self.receipts if receipt.eta != 0]
        return received

    def update_pipeline(self) -> None:
        for receipt in self.receipts:
            receipt.eta -= 1

    def add_receipt(self, receipt: Receipt) -> None:
        self.receipts.append(receipt)
