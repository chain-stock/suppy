import networkx as nx
import pandas as pd
import simplejson as json

from typing import Union, TextIO


class BillOfMaterialGraph(nx.DiGraph):


    def __init__(
            self, file=None, data=None,
            sales_data=None, stock_data=None,
            lead_time_data=None,
            safety_stock_data=None,
            reorder_point_data=None,
            **attr
    ):
        super(BillOfMaterialGraph, self).__init__()
        if data is not None:
            self.from_json(data=data)
        elif file is not None and file.lower().endswith('.json'):
            self.from_json(file=file)
        elif file is not None and file.lower().endswith(('.xlsx', '.xls')):
            self.from_excel(file=file)
        else:
            raise AttributeError(
                "Please provide a network by data or by file."
            )

        if not (safety_stock_data or reorder_point_data):
            raise AttributeError(
                "Please provide either safety stocks or reorder points."
            )

        nx.set_node_attributes(self, -1, "llc")
        for d_str in self.nodes:
            if self.out_degree(d_str) == 0:
                self.set_llc(d_str)

        if sales_data:
            for item_code, sales_queueu in sales_data.items():
                d = self.nodes.get(item_code, None)
                if d:
                    d["sales_queue"] = sales_queueu

        if stock_data:
            for item_code, stock in stock_data.items():
                d = self.nodes.get(item_code, None)
                if d:
                    d["stock"] = stock

        if lead_time_data:
            for item_code, lead_time_queueu in lead_time_data.items():
                d = self.nodes.get(item_code, None)
                if d:
                    d["lead_time_queue"] = lead_time_queueu

        if safety_stock_data:
            for item_code, safety_stock in safety_stock_data.items():
                d = self.nodes.get(item_code, None)
                if d:
                    d["safety_stock"] = safety_stock

        if reorder_point_data:
            for item_code, reorder_point in reorder_point_data.items():
                d = self.nodes.get(item_code, None)
                if d:
                    d["reorder_point"] = reorder_point


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
            self.add_node(node['id'], **node['data'])
            if node.get('adjacencies') is not None:
                for adj in node['adjacencies']:
                    self.add_edge(node['id'], adj['item_to'], **adj['data'])

        for d_str in self.nodes:
            if "customer_data" in self.nodes[d_str].keys():
                self.nodes[d_str]["e_demand"] = self.nodes[d_str]["customer_data"].pop("e_demand")
                self.nodes[d_str]["s_demand"] = self.nodes[d_str]["customer_data"].pop("s_demand")
                self.nodes[d_str]["target"] = self.nodes[d_str]["customer_data"].pop("target_service_level")
                self.nodes[d_str].pop("customer_data")


    def from_excel(self, file):
        """
        Instantiate self from data in Excel format.

        :param file: file(location) of the Excel data.
        """
        df_relations = pd.read_excel(
            file,
            sheet_name='Relation input',
            usecols=[
                'Item code',
                'Succesor Item code',
                'Number',
            ],
            converters={
                'Item code': str,
                'Succesor Item code': str,
                'Number': int,
            },
        )
        df_items = pd.read_excel(
            file,
            sheet_name='Item input',
            converters={
                'Item code': str,
                'EL': int,
                'AddValue': float,
                'RevPeriod': int,
                'LotSize': float,
            },
            usecols=["Item code", "EL", "AddValue", "RevPeriod", "LotSize"],
        )
        df_customers = pd.read_excel(
            file,
            sheet_name='Item customer input',
            converters={
                'Item code': str,
                'ED': float,
                'SD': float,
                'TargetP2': float,
            },
            usecols=["Item code", "ED", "SD", "TargetP2"],
        )

        df_items = df_items.rename(columns={
            "EL": "e_lead_time",
            "AddValue": "added_value",
            "RevPeriod": "review_period",
            "LotSize": "order_quantity",
        })

        df_customers = df_customers.rename(columns={
            "ED": "e_demand",
            "SD": "s_demand",
            "TargetP2": "target",
        })

        df_relations = df_relations.rename(columns={
            "Number": "number",
        })

        df_items_dict = df_items.set_index('Item code').to_dict('Index')
        df_customers_dict = df_customers.set_index('Item code').to_dict('Index')

        for item_code, values in df_customers_dict.items():
            df_items_dict[item_code].update(values)

        self.add_nodes_from([
            (key, value_dict) for key, value_dict in df_items_dict.items()
        ])

        self.add_weighted_edges_from([tuple(x) for x in df_relations.to_numpy()], weight='Number')


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