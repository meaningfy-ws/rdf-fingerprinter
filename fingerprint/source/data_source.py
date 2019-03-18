""" 
data_source
Created:  08/03/2019
Author: Eugeniu Costetchi
Email: costezki.eugen@gmail.com

This module implements the abstract/generic data source and ways to access them.

"""
from abc import ABC, abstractmethod
import pandas as pd
from SPARQLWrapper import SPARQLWrapper, CSV
import json


class DataSource(ABC):
    """
    generic data source providing a tabular structure such as pandas data frame
    """

    @abstractmethod
    def read(self):
        pass


class TabularDataSource(DataSource):
    """
    generic data source providing a tabular structure such as pandas data frame
    """

    @abstractmethod
    def read(self):
        pass


class CSVSourceTabular(TabularDataSource):
    def __init__(self, file_path, configuration={}):
        """
            A Data source from a CSV file that shall be read with the given configuration parameters.
            The configuration parameters are the same as those of the Pandas.read_csv() available
            here https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.read_csv.html.

        :param file_path: absolute path to the file
        :param configuration: a dictionary that is forwarded as pandas.read_csv parameters
        """
        self.file_path = file_path
        self.configuration = configuration

    def read(self):
        return pd.read_csv(self.file_path, **self.configuration)


class EndpointSourceTabular(TabularDataSource):
    def __init__(self, url, query, graph=None):
        self.endpoint = SPARQLWrapper(url)
        if graph:
            self.endpoint.addDefaultGraph(graph)
        self.endpoint.setQuery(query)
        self.endpoint.setReturnFormat(CSV)

    def read(self):
        tabular = self.endpoint.queryAndConvert()
        return pd.read_csv(pd.compat.StringIO(str(tabular, "utf-8")))


class JSONDataSource(DataSource):
    def __init__(self, file_path, configuration={}):
        """
            A Data source from a JSON file that shall be read with the given configuration parameters.
            The configuration parameters are the same as those of the json.loads() available
            here https://docs.python.org/3/library/json.html#json.loads.

        :param file_path: absolute path to the file
        :param configuration: a dictionary that is forwarded as json.loads() parameters
        """
        self.file_path = file_path
        self.configuration = configuration

    def read(self):
        with open(self.file_path, encoding='utf-8') as data_file:
            data = json.loads(data_file.read(), **self.configuration)
            return data


def build_data_source(configuration_dict):
    """
    Creates a data source corresponding to the description dict. The tests implemented so far:
        - file key ends in csv, then return CSV source
        - file key ends in json, then return JSON source
        - no file key but there is endpoint key, return Endpoint source
    :param configuration_dict:
    :return:
    """
    if "file" in configuration_dict:
        if configuration_dict["file"].endswith(".csv"):
            return CSVSourceTabular(file_path=configuration_dict["file"])
        elif configuration_dict["file"].endswith(".json"):
            return JSONDataSource(file_path=configuration_dict["file"])
    elif "endpoint" in configuration_dict:
        graph = configuration_dict["graph"] if "graph" in configuration_dict else None
        return EndpointSourceTabular(url=configuration_dict["endpoint"],
                                     query=configuration_dict["query"],
                                     graph=graph)
