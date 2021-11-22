from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterator

from .node import Node, Orders
from .receipt import Receipt
from .types import ControlStrategy, IdDict, ReleaseStrategy

logger = logging.getLogger(__name__)


class Inventory(IdDict[Node, int]):
    """Inventory level of a node"""

    def __missing__(self, key: str | Node) -> int:
        """When a key is missing, default to 0"""
        self.__setitem__(key, 0)
        return 0


@dataclass(frozen=True, eq=True)
class Edge:
    """A relation between to nodes

    Attributes:
        source (supplychain_simulation.node.Node): The predecessor of the `destination` Node
        destination (supplychain_simulation.node.Node): The successor of the `source` Node
        number (int): The amount of `source` needed to make `destination`
    """

    source: str
    destination: str
    number: int

    def __str__(self) -> str:
        return f"{self.source}->{self.destination}: {self.number}"

    @property
    def id(self) -> str:
        return f"{self.source}->{self.destination}"


class SupplyChain:
    _nodes: IdDict[Node, Node]
    _edges: IdDict[Edge, Edge]

    def __init__(
        self, nodes: list[Node] | None = None, edges: list[Edge] | None = None
    ):
        nodes = [] if nodes is None else nodes
        edges = [] if edges is None else edges
        # Convert the provided nodes and edges into dict for faster lookup
        self._nodes = IdDict({node: node for node in nodes})
        self._edges = IdDict({edge: edge for edge in edges})
        self.__post_init__()

    def __post_init__(self) -> None:
        """Make sure all edges are added to the correct node predecessors

        also ensure any edge defined on a node exists in self.edges
        """
        for edge in self._edges.values():
            if not self.node_exists(edge.source):
                raise ValueError(
                    f"Edge {edge} defines unknown source node {edge.source}"
                )
            if not self.node_exists(edge.destination):
                raise ValueError(
                    f"Edge {edge} defines unknown destination node {edge.destination}"
                )

            destination = self.nodes[edge.destination]
            if edge not in destination.predecessors:
                destination.predecessors.append(edge)

        for node in self.nodes.values():
            for edge in node.predecessors:
                if not self.edge_exists(edge):
                    self.add_edge(edge)

        self.set_llc()

    def add_node(self, node: Node) -> None:
        self.nodes[node] = node
        for edge in node.predecessors:
            if not self.edge_exists(edge):
                self.add_edge(edge)

    def get_node(self, node: str) -> Node:
        return self._nodes[node]

    def add_edge(self, edge: Edge) -> None:
        self._edges[edge] = edge

    def node_exists(self, node: str | Node) -> bool:
        return node in self._nodes

    def edge_exists(self, edge: str | Edge) -> bool:
        return edge in self._edges

    @property
    def nodes(self) -> IdDict[Node, Node]:
        """Iterate over all the nodes in the supplychain"""
        return self._nodes

    def set_llc(self) -> None:
        """Determine the low-level-code for each node"""
        for node in self.nodes.values():
            if node.supplier:
                continue

            echelon_nr = 0
            echelon: list[str] = [node.id]

            while len(echelon) > 0:
                echelon_next: list[str] = []

                for node_id in echelon:
                    if echelon_nr > self.nodes[node_id].llc:
                        self.nodes[node_id].llc = echelon_nr
                    echelon_next += [
                        edge.source for edge in self.nodes[node_id].predecessors
                    ]

                echelon_nr += 1
                echelon = list(set(echelon_next))

    @property
    def max_llc(self) -> int:
        """Return the maximum llc in the supplychain"""
        return max(node.llc for node in self.nodes.values())

    def nodes_by_llc(self, llc: int) -> Iterator[Node]:
        """Generator for all nodes with the specified llc"""
        return (node for node in self.nodes.values() if node.llc == llc)

    def inventory(self, node: Node) -> Inventory:
        """Return the inventory for a node"""
        inventory = Inventory()

        # Add the pipeline to the inventory
        for receipt in node.pipeline:
            inventory[receipt.sku_code] += receipt.quantity

        # Add orders and stocked items of predecessors
        for edge in node.predecessors:
            source = self.nodes[edge.source]
            inventory[source] += source.orders[node]
            inventory[source] += node.stock[source]

        # Add stock at the node itself
        inventory[node] += node.stock[node]

        # Subtract backorders for node
        inventory[node] -= node.backorders

        # Subtract outstanding orders
        inventory[node] -= sum(node.orders.values())

        return inventory

    def inventory_assemblies_feasible(self, node: Node) -> int:
        """Return the number of assemblies possible from stock and inventory"""
        inventory = self.inventory(node)
        return node.assemblies_feasible(inventory) + inventory[node]

    def create_orders(self, node: Node, quantity: int, period: int) -> None:
        """Create orders for all the parts needed to assemble the node"""
        # This assumes we do not have partial stock for the node assembly
        # as it will always place orders at all predecessors for the total quantity
        if quantity <= 0:
            return
        logger.debug(f"Node {node}: Creating orders")
        if node.intercompany:
            for edge in node.predecessors:
                self.nodes[edge.source].orders[edge.destination] += (
                    quantity * edge.number
                )
                logger.debug(f"\tNode {edge.source}: {quantity * edge.number}")
        else:
            receipt = Receipt(
                sku_code=node.id,
                eta=node.get_lead_time(period),
                quantity=quantity,
            )
            node.pipeline.add_receipt(receipt)
            logger.debug(f"\tNode {node}: {receipt} added to pipeline")

    def release_orders(self, node: Node, releases: Orders, period: int) -> None:
        """Add the releases to the pipeline of the appropriate node"""
        for release_node_id, quantity in releases.items():
            quantity = min(quantity, node.stock[node])
            # if nothing is being released, move to the next item.
            # this avoids creating a zero pipeline entry
            if quantity <= 0:
                continue
            release_node = self.nodes[release_node_id]
            receipt = Receipt(
                sku_code=node.id,
                eta=release_node.get_lead_time(period),
                quantity=quantity,
            )
            release_node.pipeline.add_receipt(receipt)
            logger.debug(f"\tNode {release_node}: {receipt} added to pipeline")

            node.stock[node] -= quantity
            node.orders[release_node] -= quantity


@dataclass
class Simulator:
    """SupplyChain Simulator

    Simulate a supplychain using the provided control and release strategy
    """

    supply_chain: SupplyChain
    control_strategy: ControlStrategy
    release_strategy: ReleaseStrategy

    def __post_init__(self) -> None:
        """Check if the provided strategies implement the correct interface"""
        # TODO: change to pydantic to add runtime type checking
        assert isinstance(self.control_strategy, ControlStrategy)
        assert isinstance(self.release_strategy, ReleaseStrategy)

    def run(self, *, start_period: int = 0, end_period: int) -> None:
        """Run the simulation for the provided periods"""
        logger.info(
            f"Simulate periods {start_period} -> {end_period},"
            f" {end_period-start_period+1} periods"
        )
        for period in range(start_period, end_period + 1):
            logger.info(f"Simulating period {period}")
            self.simulate_period(period)

    def simulate_period(self, period: int) -> None:
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
            node.satisfy_sales(period)

        # move pipeline
        for node in self.supply_chain.nodes.values():
            node.pipeline.update_pipeline()

        # starting at the end nodes, moving upstream
        for llc in range(self.supply_chain.max_llc + 1):
            for node in self.supply_chain.nodes_by_llc(llc):
                # determine order size
                order_quantity = self.control_strategy.get_order_quantity(
                    node=node, period=period
                )
                # create new orders
                self.supply_chain.create_orders(
                    node, quantity=order_quantity, period=period
                )
                # create order release
                order_releases = self.release_strategy.get_releases(node)
                # release orders
                self.supply_chain.release_orders(
                    node=node, releases=order_releases, period=period
                )
