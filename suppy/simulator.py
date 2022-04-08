from __future__ import annotations

import logging
from dataclasses import dataclass
from os import PathLike
from typing import IO, Iterator, Optional

from tqdm import tqdm  # type: ignore
from typeguard import check_type

from .supplychain import SupplyChain
from .node import Node
from .types import ControlStrategy, ReleaseStrategy
from .utils.metrics import MetricsExporter, log_event, setup_metrics


@dataclass
class Simulator:
    """SupplyChain Simulator

    Simulate a supply-chain using the provided control and release strategy

    Arguments:
        supply_chain: the supply-chain to simulate
        control_strategy: Determines how orders are created during the simulation
            should adhere to the ControlStrategy Protocol
        release_strategy: Determines how orders are released from each Node during simulation
            should adhere to the ReleaseStrategy Protocol
        filename: File to write the metrics too
            outputs results to the current workingdirectory by default
        stream: Optional additional metrics stream to add.
        max_bytes: Maximum size of the output file
            A new file will be opened when max_bytes will be exceeded.
            default (0) will never create a new file
    Raises:
        ValueError: if the strategies don't implement the correct Protocol
    """

    supply_chain: SupplyChain
    control_strategy: ControlStrategy
    release_strategy: ReleaseStrategy
    filename: str | PathLike[str] | None = None
    max_bytes: int = 0
    stream: Optional[IO[str]] = None

    def __post_init__(self) -> None:
        """Check if the provided strategies implement the correct interface"""
        check_type("control_strategy", self.control_strategy, ControlStrategy)
        check_type("release_strategy", self.release_strategy, ReleaseStrategy)
        self._metrics: MetricsExporter | None = None

    @property
    def output(self) -> Iterator[PathLike[str]]:
        """Return the filename(s) of the metrics FileHandler"""
        if self._metrics:
            yield from self._metrics.output

    def run(
        self,
        start_or_end_period: int,
        /,
        end_period: Optional[int] = None,
        loops: Optional[int] = 1,
    ) -> None:
        """Run the simulation for a number of periods

        Arguments:
            start_or_end_period: period to start with if end_period is provided.
                period to end with, starting at 1 if end_period is not provided.
            end_period: period to end with
            loops: number of times the simulation from start to end period is run.
            The stock, orders, and pipeline are carried over from one loop to the next.
        """
        if end_period is None:
            start_period = 1
            end_period = start_or_end_period
        else:
            start_period = start_or_end_period

        # Check if all nodes have their llc set
        for node in self.supply_chain.nodes.values():
            if not isinstance(node.llc, int) or node.llc < 0:
                raise ValueError(f"{node} has an invalid llc: {node.llc}")

        self._metrics = setup_metrics(
            filename=self.filename, stream=self.stream, max_bytes=self.max_bytes
        )
        status = tqdm(total=loops * (end_period - start_period + 1))
        try:
            for loop in range(0, loops):
                for period in range(start_period, end_period + 1):
                    self.simulate_period(period=period, loop=loop)
                    status.update(1)
                    for node in self.supply_chain.nodes.values():
                        log_node_state(
                            node,
                            period=period + loop * (end_period - start_period + 1),
                            loop=loop,
                        )
        finally:
            self._metrics.stop_metrics()
            status.close()

    def simulate_period(self, period: int, loop: int) -> None:
        """Simulate a single period"""
        # accept receipts
        for node in self.supply_chain.nodes.values():
            node.satisfy_received_receipts()

        # assemble / produce
        for node in self.supply_chain.nodes.values():
            node.assemble()

        # satisfy backorders
        for node in self.supply_chain.nodes.values():
            node.satisfy_backorders()

        # satisfy sales
        for node in self.supply_chain.nodes.values():
            node.satisfy_sales(period=period, loop=loop)

        # move pipeline
        for node in self.supply_chain.nodes.values():
            node.pipeline.update_pipeline()

        # starting at the end nodes, moving upstream
        for llc in range(self.supply_chain.max_llc + 1):
            for node in self.supply_chain.nodes_by_llc(llc):
                # determine order size
                orders = self.control_strategy.get_orders(node=node, period=period)
                # create new orders
                self.supply_chain._create_orders(  # pylint: disable=protected-access
                    node, orders=orders, period=period
                )
                # create order release
                order_releases = self.release_strategy.get_releases(node)
                # release orders
                self.supply_chain._release_orders(  # pylint: disable=protected-access
                    node=node, releases=order_releases, period=period
                )


def log_node_state(node: Node, period: int, loop: int) -> None:
    """Add a debug metric of the state of node"""
    node_state = {
        "node.stock": node.stock.data,
        "node.backorders": node.backorders,
        "node.pipeline": [str(rcpt) for rcpt in node.pipeline],
        "node.orders": node.orders.data,
    }
    for event, value in node_state.items():
        log_event(
            level=logging.DEBUG,
            node=node,
            period=period,
            loop=loop,
            event=event,
            quantity=0,
            message=value,
        )
