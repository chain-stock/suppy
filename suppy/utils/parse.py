from collections import UserDict, UserList
from dataclasses import asdict, is_dataclass
from json import JSONEncoder
from typing import Any, Optional, TypedDict, TypeVar, Union

from typeguard import check_type

from ..edge import Edge
from ..leadtime import LeadTime
from ..node import Node, Orders, Sales, Stock
from ..pipeline import Pipeline, Receipt

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


class EdgeDict(TypedDict):
    """Dict representation of an Edge"""

    source: str
    destination: str
    number: int


class NodeDict(NodeDictId, total=False):
    """Dict representation of a Node"""

    sales: SalesJson
    lead_time: Union[LeadTimeDict, int]
    backorders: int
    data: dict[Any, Any]
    pipeline: Optional[list[ReceiptDict]]
    stock: dict[str, int]
    orders: dict[str, int]
    llc: Optional[int]
    predecessors: Optional[list[EdgeDict]]


class JsonSupplyChain(TypedDict, total=False):
    """Dict representation of the JSON file-format"""

    nodes: list[NodeDict]
    edges: list[EdgeDict]


def supplychain_from_dict(data: JsonSupplyChain) -> dict[str, Any]:
    """Convert a dict to a dict of SupplyChain parameters"""
    # Type-check the data
    check_type("json", data, JsonSupplyChain)
    json_nodes = data.get("nodes", [])
    json_edges = data.get("edges", [])

    nodes: list[Node] = []

    for _node in json_nodes:
        params: dict[str, Any] = {}
        if sales := parse_sales(_node.pop("sales", None)):
            params["sales"] = sales
        if lead_time := parse_leadtime(_node.pop("lead_time", None)):
            params["lead_time"] = lead_time
        if pipeline := parse_pipeline(_node.pop("pipeline", None)):
            params["pipeline"] = pipeline
        if stock := parse_stock(_node.pop("stock", None)):
            params["stock"] = stock
        if orders := parse_orders(_node.pop("orders", None)):
            params["orders"] = orders
        if predecessors := _node.pop("predecessors", None):
            params["predecessors"] = [Edge(**edge) for edge in predecessors]
        for key, value in _node.items():
            params[key] = value

        node = Node(**params)
        nodes.append(node)

    edges = [Edge(**edge) for edge in json_edges]

    return dict(nodes=nodes, edges=edges)


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
    return LeadTime(**lead_time)


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


def dict_factory(mapping: list[tuple[str, Any]]) -> dict[str, Any]:
    """dict_factory for dataclasses.asdict

    Removes any attribute that starts with "_" from the generated dict
    """
    mapping = [
        (key, value)
        for key, value in mapping
        if not key.startswith("_") and not value is None
    ]
    return dict(mapping)


class SupplyChainJSONEncoder(JSONEncoder):
    """JSON Encoder for SupplyChain instances

    Example:
        ```
        json.dumps(SupplyChain(), cls=SupplyChainJSONEncoder)
        ```
    """

    def default(self, o: Any) -> Any:
        """Return a JSON serializable representation of obj

        Adds the ability to serialize dataclasses, SupplyChain and UserDict/List
        """
        if hasattr(o, "nodes") and hasattr(o, "edges"):
            return {
                "edges": list(o.edges.values()),
                "nodes": list(o.nodes.values()),
            }
        if is_dataclass(o):
            return asdict(o, dict_factory=dict_factory)
        if isinstance(o, (UserDict, UserList)):
            return o.data
        return super().default(o)
