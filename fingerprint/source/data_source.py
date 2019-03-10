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


class TabularDataSource(ABC):
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

# todo implement, type cast, column rename , sort, column format