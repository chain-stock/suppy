from typing import TextIO, Union

import networkx as nx
import pandas as pd
import simplejson as json

from .control import r_s_q
from .order_release import fractional
from .utils import update_pipeline


class BillOfMaterialGraph(nx.DiGraph):
    def __init__(self, file=None, data=None, auxiliary_data=dict(), **attr):
        super(BillOfMaterialGraph, self).__init__()
        if data is not None:
            self.from_json(data=data)
        elif file is not None and file.lower().endswith(".json"):
            self.from_json(file=file)
        elif file is not None and file.lower().endswith((".xlsx", ".xls")):
            self.from_excel(file=file)
        else:
            raise AttributeError("Please provide a network by data or by file.")

        if not (
            "safety_stock_queue" in auxiliary_data.keys()
            or "reorder_point_queue" in auxiliary_data.keys()
        ):
            raise AttributeError(
                "Please provide either a safety stock or reorder point queue."
            )
        else:
            self.load_data(data=auxiliary_data)

        nx.set_node_attributes(self, -1, "llc")
        for d_str in self.nodes:
            if self.out_degree(d_str) == 0:
                self.set_llc(d_str)

    def load_data(self, data):
        for data_type, _data in data.items():
            for item_code, data_instance in _data.items():
                d = self.nodes.get(item_code, None)
                if isinstance(d, dict):
                    d[data_type] = data_instance

    def from_json(self, file=None, data: Union[str, list, dict, TextIO] = None):
        """
        Instantiate self from (json) data

        :param file: file(location) containing JSON data
        :param data: str or pre-loaded JSON data
        """
        if file is not None:
            with open(file) as json_file:
                data = json.load(json_file, parse_float=float, parse_int=int)
        elif data is not None:
            if isinstance(data, str):
                data = json.loads(data, parse_int=int, parse_float=float)
            else:
                try:
                    data = json.load(data, parse_int=int, parse_float=float)
                except AttributeError:
                    pass

        self.clear()

        for node in data:
            self.add_node(node["id"], **node["data"])
            if node.get("adjacencies") is not None:
                for adj in node["adjacencies"]:
                    self.add_edge(node["id"], adj["item_to"], **adj["data"])

        for d_str in self.nodes:
            if "customer_data" in self.nodes[d_str].keys():
                self.nodes[d_str]["e_demand"] = self.nodes[d_str]["customer_data"].pop(
                    "e_demand"
                )
                self.nodes[d_str]["s_demand"] = self.nodes[d_str]["customer_data"].pop(
                    "s_demand"
                )
                self.nodes[d_str]["target"] = self.nodes[d_str]["customer_data"].pop(
                    "target_service_level"
                )
                self.nodes[d_str].pop("customer_data")

    def from_excel(self, file):
        """
        Instantiate self from data in Excel format.

        :param file: file(location) of the Excel data.
        """
        df_relations = pd.read_excel(
            file,
            sheet_name="Relation input",
            usecols=[
                "Item code",
                "Succesor Item code",
                "Number",
            ],
            converters={
                "Item code": str,
                "Succesor Item code": str,
                "Number": int,
            },
        )
        df_items = pd.read_excel(
            file,
            sheet_name="Item input",
            converters={
                "Item code": str,
                "EL": int,
                "AddValue": float,
                "RevPeriod": int,
                "LotSize": float,
            },
            usecols=["Item code", "EL", "AddValue", "RevPeriod", "LotSize"],
        )
        df_customers = pd.read_excel(
            file,
            sheet_name="Item customer input",
            converters={
                "Item code": str,
                "ED": float,
                "SD": float,
                "TargetP2": float,
            },
            usecols=["Item code", "ED", "SD", "TargetP2"],
        )

        df_items = df_items.rename(
            columns={
                "EL": "e_lead_time",
                "AddValue": "added_value",
                "RevPeriod": "review_period",
                "LotSize": "order_quantity",
            }
        )

        df_customers = df_customers.rename(
            columns={
                "ED": "e_demand",
                "SD": "s_demand",
                "TargetP2": "target",
            }
        )

        df_relations = df_relations.rename(
            columns={
                "Number": "number",
            }
        )

        df_items_dict = df_items.set_index("Item code").to_dict("Index")
        df_customers_dict = df_customers.set_index("Item code").to_dict("Index")

        for item_code, values in df_customers_dict.items():
            df_items_dict[item_code].update(values)

        self.add_nodes_from(
            [(key, value_dict) for key, value_dict in df_items_dict.items()]
        )

        self.add_weighted_edges_from(
            [tuple(x) for x in df_relations.to_numpy()], weight="number"
        )

    def set_llc(self, k_str):

        echelon_nr = 0
        echelon = [k_str]

        while len(echelon) > 0:
            echelon_next = []

            for d_str in echelon:
                if echelon_nr > self.nodes[d_str]["llc"]:
                    self.nodes[d_str]["llc"] = echelon_nr
                echelon_next += list(self.predecessors(d_str))

            echelon_nr += 1
            echelon = list(set(echelon_next))

    def initialize_simulation(self):
        data_types = [
            "safety_stock",
            "reorder_point",
        ]

        # case specific data, to be removed
        for data_type in data_types:
            for d_str in self.nodes():
                queue = self.nodes[d_str].get(f"{data_type}_queue", dict())
                value = queue.get(0, None)
                if value:
                    self.nodes[d_str][data_type] = value

        # mandatory generic data
        for d_str in self.nodes():
            if not self.nodes[d_str].get("pipeline", None):
                self.nodes[d_str]["pipeline"] = dict()

            if "sales" in self.nodes[d_str].keys():
                self.nodes[d_str]["customer"] = True
                if not self.nodes[d_str].get("backorder_quantity", None):
                    self.nodes[d_str]["backorder_quantity"] = 0
            else:
                self.nodes[d_str]["customer"] = False

    def assemble(self, d_str):

        d = self.nodes[d_str]
        feasible = min(
            [
                int(d["stock"][c_str] / self.edges[(c_str, d_str)]["number"])
                for c_str in self.predecessors(d_str)
            ]
        )

        for c_str in self.predecessors(d_str):
            d["stock"][c_str] -= feasible * self.edges[(c_str, d_str)]["number"]
        d["stock"][d_str] += feasible

    def satisfy_backorders(self, d_str):

        d = self.nodes[d_str]
        if "backorder_quantity" in d.keys():
            feasible = min(d["stock"][d_str], d["backorder_quantity"])
            d["backorder_quantity"] -= feasible
            d["stock"][d_str] -= feasible

    def satisfy_sales(self, d_str, t):

        d = self.nodes[d_str]

        sales = d["sales"].pop(t, None)
        if sales:
            feasible = min(d["stock"][d_str], sales)
            d["stock"][d_str] -= feasible

            # is assumed to exist, set on sim init
            d["backorder_quantity"] += sales - feasible

    def release_orders(self, p_str, order_release):

        p = self.nodes[p_str]
        for q_str, orl in order_release.items():
            q = self.nodes[q_str]

            # decide lead time
            if q.get("lead_time_queue", []):
                lead_time = q["lead_time_queue"].pop(0)
            else:
                lead_time = q["e_lead_time"]

            # decide actual feasible release quantity
            release_quantity = min(orl, p["stock"][p_str])

            # release order
            q["pipeline"].append(
                {
                    "sku_code": p_str,
                    # we assume the order is released at the end of the day
                    "eta": lead_time + 1,
                    "quantity": release_quantity,
                }
            )

            # update stock according to the release
            p["stock"][p_str] -= release_quantity
            # update outstanding orders according to the release
            p["orders"][q_str] -= release_quantity

    def simulate(self, max_time):

        self.initialize_simulation()

        t = 1
        while t <= max_time:

            for d_str in self.nodes:
                # move pipeline
                d = self.nodes[d_str]
                d["pipeline"], receipts = update_pipeline(d["pipeline"])

                # accept receipts
                for receipt in receipts:
                    d["stock"][receipt["sku_code"]] += receipt["quantity"]

            # assemble / produce
            for d_str in self.nodes:
                self.assemble(d_str)

            # satisfy backorders
            for d_str in self.nodes:
                self.satisfy_backorders(d_str)

            # satisfy sales
            for d_str in self.nodes:
                # this should be refactored so we can explicitely
                # set customer nodes
                if "sales" in self.nodes[d_str].keys():
                    self.satisfy_sales(d_str)

            # starting at the end nodes, moving upstream
            for llc in range(max([self.nodes[d_str]["llc"] for d_str in self.nodes])):
                for d_str in (x for x in self.nodes if self.nodes[d_str]["llc"] == llc):
                    d = self.nodes[d_str]
                    # create order release
                    order_release = fractional(orders=d["orders"], stock=d["stock"])
                    # release orders
                    self.release_orders(sku_code=d_str, order_release=order_release)
                    # create new orders
                    orders = r_s_q(self.nodes[d_str], t)

            #     generate order releases (based on downstream demand, requires shortage allocation)
            #     generate orders (for upstream nodes / suppliers, based on controls)

            t += 1
