import json
from os import PathLike
from pathlib import Path
from typing import Any, Optional, TypedDict, TypeVar, Union

from typeguard import check_type

from ..edge import Edge
from ..leadtime import LeadTime
from ..node import Node, Orders, Sales, Stock
from ..pipeline import Pipeline, Receipt
from ..simulator import SupplyChain

SalesJson = Union[list[list[int]], dict[str, list[int]]]
LeadTimeQueueJson = Union[list[int], dict[str, int]]


class LeadTimeDict(TypedDict, total=False):
    """Dict representation of a LeadTime"""

    queue: LeadTimeQueueJson
    default: int


class ReceiptDict(TypedDict):
    """Dict representation of an Receipt"""

    eta: int
    sku_code: str
    quantity: int


class NodeDictId(TypedDict):
    """Mandatory keys for the Node dict"""

    id: str


class NodeDict(NodeDictId, total=False):
    """Dict representation of a Node"""

    sales: SalesJson
    lead_time: Union[LeadTimeDict, int]
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


class JsonSupplyChain(TypedDict, total=False):
    """Dict representation of the JSON file-format"""

    nodes: list[NodeDict]
    edges: list[EdgeDict]


def supplychain_from_json(file: PathLike[str]) -> SupplyChain:
    """Convert a JSON file to a SupplyChain instance"""
    return supplychain_from_jsons(Path(file).read_text(encoding="utf-8"))


def supplychain_from_jsons(json_data: Union[str, bytes]) -> SupplyChain:
    """Convert JSON string to a SupplyChain instance"""

    data: JsonSupplyChain = json.loads(json_data)
    # Type-check the data
    check_type("json", data, JsonSupplyChain)
    json_nodes = data.get("nodes", [])
    json_edges = data.get("edges", [])

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


def parse_sales(sales: Optional[SalesJson], /) -> Optional[Sales]:
    """Build a Sales object from the provided JSON data

    The json data can either be of type list[list[int]] or
    dict[str, list[int]] where the dict key is the period index
    """
    return Sales(parse_list_or_dict(sales))


def parse_leadtime(lead_time: Union[LeadTimeDict, int, None], /) -> Optional[LeadTime]:
    """Build a LeadTime object from the provided JSON data

    Options:
    1: `"lead_time": {"queue": [1,2,3], default: 42}` -> 42 except for the first 3 periods
    2: `"lead_time": {"queue":{"23":4, "24":5}, default: 42}` -> 42 except in period 23 and 24
    3: `"lead_time": 42` -> 42
    """
    if not lead_time:
        return None
    if isinstance(lead_time, int):
        return LeadTime(default=lead_time)

    default = lead_time.get("default")
    queue = lead_time.get("queue")
    return LeadTime(parse_list_or_dict(queue), default=default)


def parse_pipeline(pipeline: Optional[list[ReceiptDict]]) -> Optional[Pipeline]:
    """Build a Pipeline object from the provided JSON data"""
    if not pipeline:
        return None
    return Pipeline([Receipt(**receipt) for receipt in pipeline])


def parse_stock(stock: Optional[dict[str, int]]) -> Optional[Stock]:
    """Build a Stock object from the provided JSON data"""
    if not stock:
        return None
    return Stock(**stock)


def parse_orders(orders: Optional[dict[str, int]]) -> Optional[Orders]:
    """Build an Orders object from the provided JSON data"""
    if not orders:
        return None
    return Orders(**orders)


ListOrDictType = Union[list[Any], dict[str, Any], None]
_Thing = TypeVar("_Thing", Sales, LeadTime)


def parse_list_or_dict(_thing: ListOrDictType, /) -> Optional[dict[int, Any]]:
    """Accepts a list with lists of sales or a dict with sales per period

    so that:
    [[1,2], [3,4] == {"1":[1,2], "2":[3,4]}
    and:
    [1,2,3] == {"1":1, "2":2, "3":3}
    """
    if not _thing:
        return None

    if isinstance(_thing, list):
        return {idx + 1: line for idx, line in enumerate(_thing)}
    if isinstance(_thing, dict):
        return {int(key): value for key, value in _thing.items()}
    return None
