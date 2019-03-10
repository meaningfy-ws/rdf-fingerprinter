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
        Generates the data context object from the Data Source
        :return: DataContext object
        """
        pass


class CSVContextGenerator(DataContextGenerator):
    def __init__(self, source):
        self.source = source

    def generate(self):
        # TODO implement and test
        pass


class CSVAggregateContextGenerator(DataContextGenerator):
    def __init__(self, source, aggregator):
        """

        :param source: DataSource object
        :param aggregator: provides rules for how the dataset shall be aggregated i.e.
                            it specifies which column(s) act as an aggregator.
        """
        self.source = source
        self.aggregator = aggregator
        pass

    def generate(self):
        # TODO implement and test
        pass
