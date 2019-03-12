"""
test_context_generator
Date: 10.03.19
Author: Eugeniu Costetchi
Email: costezki.eugen@gmail.com
"""

import pathlib
import unittest

from fingerprint.context.context_generator import TabularContextGenerator, AggregateTabularContextGenerator
from fingerprint.source.data_source import CSVSourceTabular
import pandas as pd


class MyTestCase(unittest.TestCase):

    def setUp(self):
        self.file_name = pathlib.Path(__file__).resolve().parents[
                             1] / "resources" / "samples" / "fingerprint.rq_eurovoc44.log.csv"
        self.sample_tabular = CSVSourceTabular(str(self.file_name)).read()
        self.aggregator = ['stype', 'p']

    def test_tabular_context(self):
        context = TabularContextGenerator(self.sample_tabular).generate()
        assert isinstance(context, dict), "It is a dictionary"
        assert "tabular" in context, "Has 'tabular' key"
        assert isinstance(context["tabular"], pd.DataFrame), "Has a data frame 'tabular'"

    def test_aggregate_tabular_context(self):
        context = AggregateTabularContextGenerator(self.sample_tabular, self.aggregator).generate()
        assert isinstance(context, dict), "It is a dictionary"
        assert "aggregator" in context, "Has 'aggregator' key"
        assert set(context["aggregator"]) == set(self.aggregator), "it is the expected aggregator"
        assert "groups" in context, "Has 'group' key"
        assert len(context["groups"]) > 0, "there are some groups inside"
        assert isinstance(context["groups"][0]["group_data_frame"], pd.DataFrame), "the group item is a pandas " \
                                                                                   "data frame "


if __name__ == '__main__':
    unittest.main()
