""" 
data_source
Created:  08/03/2019
Author: Eugeniu Costetchi
Email: costezki.eugen@gmail.com

This module implements the abstract/generic data source and ways to access them.

"""
from abc import ABC, abstractmethod


class DataSource(ABC):
    """
    generic data source providing a tabular structure
    """

    @abstractmethod
    def read(self):
        pass

    @abstractmethod
    def header(self):
        pass


class CSVSource(DataSource):
    def __init__(self, file_path, configuration=None):
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
        # TODO implement and test
        pass

    def header(self):
        # TODO implement and test
        pass


class EndpointSource(DataSource):
    def __init__(self, url, query, graph=None):
        self.url = url
        self.query = query
        self.graph = graph

    def read(self):
        # TODO implement and test
        pass

    def header(self):
        # TODO implement and test
        pass
