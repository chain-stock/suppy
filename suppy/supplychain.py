from __future__ import annotations

import json
from os import PathLike
from pathlib import Path
from typing import  Iterator, overload

from tqdm import tqdm  # type: ignore

from .edge import Edge
from .node import Node, Orders
from .pipeline import Receipt
from .types import IdDict
from .utils.parse import SupplyChainJSONEncoder, supplychain_from_dict


class Inventory(IdDict[Node, int]):
    """Inventory level of a node"""

    def __missing__(self, key: str | Node) -> int:
        """When a key is missing, default to 0"""
        self.__setitem__(key, 0)
        return 0


class SupplyChain:
    """The supply-chain to simulate

    A supply-chain consists of Nodes and Edges between those Nodes
    Edges can be supplied either through `edges` or as part of the Node.predecessors field

    Arguments:
        nodes: The list of Nodes in the supply-chain
        edges: The list of edges in the supply-chain
            Will be used to set the `Node.predecessors`

    Raises:
        ValueError: if an Edge is defined while its source or destination Node does not exist

    """

    nodes: IdDict[Node, Node]
    edges: IdDict[Edge, Edge]

    def __init__(
        self, nodes: list[Node] | None = None, edges: list[Edge] | None = None
    ):
        nodes = [] if nodes is None else nodes
        edges = [] if edges is None else edges
        # Convert the provided nodes and edges into dict for easy lookup
        self.nodes = IdDict({node: node for node in nodes})
        self.edges = IdDict({edge: edge for edge in edges})
        self.__post_init__()

    def __post_init__(self) -> None:
        """Initialize the Node"""
        self._check_edges()
        self._check_nodes()
        self._set_llc()

    def _check_edges(self) -> None:
        """Check if all provided edges are valid and add them to the `Node.predecessors`"""
        for edge in self.edges.values():
            if not self.node_exists(edge.source):
                raise ValueError(f"{edge} defines unknown source node {edge.source}")
            if not self.node_exists(edge.destination):
                raise ValueError(
                    f"{edge} defines unknown destination node {edge.destination}"
                )

            destination = self.nodes[edge.destination]
            if edge not in destination.predecessors:
                destination.predecessors.append(edge)

    def _check_nodes(self) -> None:
        """Add any Edge defined on a Node.predecessors to the list of edges"""
        for node in self.nodes.values():
            for edge in node.predecessors:
                if edge.destination != node.id:
                    raise ValueError(
                        f"Node {node} defined a predecessor "
                        f"with a destination that is not Node {node}: {edge}"
                    )
                # Add/Overwrite the edge so node.predecessors has precedence over the edges list
                self.edges[edge] = edge

    def node_exists(self, node: str | Node) -> bool:
        """Return True if `node` is part of this supply-chain

        A Node is considered a match if `node.id` exists in this supply-chain
        no further equality check is done
        """
        return node in self.nodes

    def edge_exists(self, edge: str | Edge) -> bool:
        """Return True if `edge` is part of this supply-chain

        An edge is considered a match if `edge.id` exists in this supply-chain
        no further equality check is done
        """
        return edge in self.edges

    @overload
    def to_json(self) -> str:
        ...

    @overload
    def to_json(self, filename: PathLike[str]) -> None:
        ...

    def to_json(self, filename: PathLike[str] | None = None) -> str | None:
        """Serialize the SupplyChain to JSON

        Arguments:
            filename: Optional path-like object to write the JSON to
            If the file already exists it will be replaced

        Returns:
            JSON encoded string or None
        """
        if filename is None:
            return json.dumps(self, cls=SupplyChainJSONEncoder)
        filepath = Path(filename)
        filepath.parent.mkdir(exist_ok=True, parents=True)
        with filepath.open(encoding="utf8", mode="w") as _file:
            json.dump(self, _file, cls=SupplyChainJSONEncoder)
        return None

    @classmethod
    def from_json(cls, data: PathLike[str] | str) -> SupplyChain:
        """Build a SupplyChain from JSON

        Arguments:
            data: A path-like object to read the JSON from
                or a JSON encoded string

        Returns:
            A SuppyChain instance initialized from JSON
        """
        if isinstance(data, str):
            return cls(**supplychain_from_dict(json.loads(data)))
        with Path(data).open(encoding="utf8") as _file:
            return cls(**supplychain_from_dict(json.load(_file)))

    def _set_llc(self) -> None:
        """Set the low-level-code for each node"""
        for node in self.nodes.values():

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
        """Return the maximum llc in the supply-chain"""
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

    def _create_orders(self, node: Node, orders: Orders, period: int) -> None:
        """Create orders for all the parts needed to assemble the node

        orders can contain orders for both the node itself and for other nodes
        If the order is for the current node, explode the bom and
        place the orders at the node's predecessors.

        If the order is for another node,
        place an order at that node to be sent to the current node
        """
        # This assumes we do not have partial stock for the node assembly
        # as it will always place orders at all predecessors for the total quantity
        for order_node_id, quantity in orders.items():
            if quantity <= 0:
                continue
            if node.id == order_node_id:
                if node.intercompany:
                    # explode the bom
                    for edge in node.predecessors:
                        self.nodes[edge.source].orders[node] += quantity * edge.number
                else:
                    receipt = Receipt(
                        sku_code=node.id,
                        eta=node.get_lead_time(period),
                        quantity=quantity,
                    )
                    node.pipeline.add_receipt(receipt)
            else:
                order_node = self.nodes[order_node_id]
                order_node.orders[node] += quantity

    def _release_orders(self, node: Node, releases: Orders, period: int) -> None:
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

            node.stock[node] -= quantity
            node.orders[release_node] -= quantity