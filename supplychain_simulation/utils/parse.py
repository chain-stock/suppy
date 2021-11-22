from __future__ import annotations

import json
from os import PathLike
from pathlib import Path
from typing import Any, Optional, Type, TypedDict, TypeVar, Union

from supplychain_simulation import Edge, LeadTime, Node, Sales, SupplyChain
from supplychain_simulation.node import Orders, Stock
from supplychain_simulation.pipeline import Pipeline
from supplychain_simulation.receipt import Receipt

ListOrDictType = Union[list[Any], dict[str, Any], None]


class ReceiptDict(TypedDict):
    """Dict representation of an Receipt"""

    eta: int
    sku_code: str
    quantity: int


class NodeDict(TypedDict):
    """Dict representation of a Node"""

    id: str
    sales: ListOrDictType
    lead_time: ListOrDictType
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
    return supplychain_from_jsons(Path(file).read_text())


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


def parse_sales(sales: ListOrDictType, /) -> Sales | None:
    return parse_list_or_dict(sales, return_type=Sales)


def parse_leadtime(lead_time: ListOrDictType, /) -> LeadTime | None:
    return parse_list_or_dict(lead_time, return_type=LeadTime)


def parse_pipeline(pipeline: list[ReceiptDict] | None) -> Pipeline | None:
    if not pipeline:
        return None
    return Pipeline([Receipt(**receipt) for receipt in pipeline])


def parse_stock(stock: dict[str, int] | None) -> Stock | None:
    if not stock:
        return None
    return Stock(**stock)


def parse_orders(orders: dict[str, int] | None) -> Orders | None:
    if not orders:
        return None
    return Orders(**orders)


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
