from __future__ import annotations

import json
from os import PathLike
from pathlib import Path
from typing import Any, Optional, Type, TypedDict, TypeVar, Union

from ..edge import Edge
from ..leadtime import LeadTime
from ..node import Node, Orders, Sales, Stock
from ..pipeline import Pipeline, Receipt
from ..simulator import SupplyChain

SalesJson = Union[list[list[int]], dict[str, list[int]]]
LeadTimeJson = Union[list[int], dict[str, int]]


class ReceiptDict(TypedDict):
    """Dict representation of an Receipt"""

    eta: int
    sku_code: str
    quantity: int


class NodeDict(TypedDict):
    """Dict representation of a Node"""

    id: str
    sales: SalesJson
    lead_time: LeadTimeJson
    backorders: int
    data: dict[Any, Any]
    pipeline: Optional[list[ReceiptDict]]
    stock: dict[str, int]
    orders: dict[str, int]


class EdgeDict(TypedDict):
    """Dict representation of an Edge"""

    source: str
    destination: str
    number: int


def supplychain_from_json(file: PathLike[str]) -> SupplyChain:
    """Convert a JSON file to a SupplyChain instance"""
    return supplychain_from_jsons(Path(file).read_text(encoding="utf-8"))


def supplychain_from_jsons(json_data: str | bytes) -> SupplyChain:
    """Convert JSON string to a SupplyChain instance"""

    data = json.loads(json_data)
    json_nodes: list[NodeDict] = data["nodes"]
    json_edges: list[EdgeDict] = data["edges"]

    nodes: list[Node] = []

    for _node in json_nodes:
        params: dict[str, Any] = {
            "id": _node["id"],
            "data": _node.get("data", {}),
            "backorders": _node.get("backorders", 0),
        }
        if sales := parse_sales(_node.get("sales")):
            params["sales"] = sales
        if lead_time := parse_leadtime(_node.get("lead_time")):
            params["lead_time"] = lead_time
        if pipeline := parse_pipeline(_node.get("pipeline")):
            params["pipeline"] = pipeline
        if stock := parse_stock(_node.get("stock")):
            params["stock"] = stock
        if orders := parse_orders(_node.get("orders")):
            params["orders"] = orders

        node = Node(**params)
        nodes.append(node)

    edges = [Edge(**edge) for edge in json_edges]

    return SupplyChain(nodes=nodes, edges=edges)


def parse_sales(sales: SalesJson | None, /) -> Sales | None:
    """Build a Sales object from the provided JSON data

    The json data can either be of type list[list[int]] or
    dict[str, list[int]] where the dict key is the period index
    """
    return parse_list_or_dict(sales, return_type=Sales)


def parse_leadtime(lead_time: LeadTimeJson | None, /) -> LeadTime | None:
    """Build a LeadTime object from the provided JSON data

    The json data can either be of type list[int] or dict[str, int]
    where the key is the period index
    """
    # TODO: allow setting the default for lead-time
    return parse_list_or_dict(lead_time, return_type=LeadTime)


def parse_pipeline(pipeline: list[ReceiptDict] | None) -> Pipeline | None:
    """Build a Pipeline object from the provided JSON data"""
    if not pipeline:
        return None
    return Pipeline([Receipt(**receipt) for receipt in pipeline])


def parse_stock(stock: dict[str, int] | None) -> Stock | None:
    """Build a Stock object from the provided JSON data"""
    if not stock:
        return None
    return Stock(**stock)


def parse_orders(orders: dict[str, int] | None) -> Orders | None:
    """Build an Orders object from the provided JSON data"""
    if not orders:
        return None
    return Orders(**orders)


ListOrDictType = Union[list[Any], dict[str, Any], None]
_Thing = TypeVar("_Thing", Sales, LeadTime)


def parse_list_or_dict(
    _thing: ListOrDictType, /, return_type: Type[_Thing]
) -> _Thing | None:
    """Accepts a list with lists of sales or a dict with sales per period

    so that:
    [[1,2], [3,4] == {"1":[1,2], "2":[3,4]}
    and:
    [1,2,3] == {"1":1, "2":2, "3":3}
    """
    if not _thing:
        return None

    if isinstance(_thing, list):
        thing = return_type({idx + 1: line for idx, line in enumerate(_thing)})
    elif isinstance(_thing, dict):
        thing = return_type({int(key): value for key, value in _thing.items()})
    else:
        raise ValueError(
            f"Unknown sales type {type(_thing)} ({_thing}), expected list or dict"
        )
    return thing
