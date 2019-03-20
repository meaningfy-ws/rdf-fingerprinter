""" 
DataContextGenerator
Created:  08/03/2019
Author: Eugeniu Costetchi
Email: costezki.eugen@gmail.com

This module implements context data object generation functionality.

"""

from abc import ABC, abstractmethod


class DataContextGenerator(ABC):
    """
    generic data context generator
    """

    @abstractmethod
    def generate(self):
        """
        Generates the data context object from a tabular data source
        :return: DataContext or dict
        """


class TabularContextGenerator(DataContextGenerator):
    def __init__(self, tabular):
        self.tabular = tabular

    def generate(self):
        return {"tabular": self.tabular}


class AggregateTabularContextGenerator(DataContextGenerator):
    def __init__(self, tabular, aggregator):
        """

        :param source: data frame object
        :param aggregator: provides rules for how the dataset shall be aggregated i.e.
                            it specifies which column(s) act as an aggregator.
        """
        self.tabular = tabular
        self.aggregator = aggregator

    def generate(self):
        groups = self.tabular.groupby(by=self.aggregator)
        results = [{"group_name": name, "group_data_frame": group} for name, group in groups]
        return {"aggregator": self.aggregator,
                "groups": results}

