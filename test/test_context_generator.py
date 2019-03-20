"""
test_context_generator
Date: 10.03.19
Author: Eugeniu Costetchi
Email: costezki.eugen@gmail.com
"""

import pathlib
import unittest

from fingerprint.context.context_generator import TabularContextGenerator, AggregateTabularContextGenerator
from fingerprint.context.fingerprint_generator import ApplicationProfileContextGenerator
from fingerprint.context.iri_utils import NamespaceMappingCSV
from fingerprint.source.data_source import CSVSourceTabular
import pandas as pd


class MyTestCase(unittest.TestCase):

    def setUp(self):
        self.file_name = pathlib.Path(__file__).resolve().parents[1] \
                         / "resources" / "samples" / "fingerprint.rq_eurovoc44.log.csv"
        self.ns_file = pathlib.Path(__file__).resolve().parents[1] \
                       / "resources" / "prefix.csv"
        self.sample_tabular = CSVSourceTabular(str(self.file_name)).read()
        self.aggregator = ['stype', 'p']

        self.namespace_mapping_dict = NamespaceMappingCSV(str(self.ns_file)).to_dict()

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

    def test_fingerprinter_generator(self):
        apgen = ApplicationProfileContextGenerator(alpha=self.sample_tabular,
                                                   beta=self.sample_tabular,
                                                   namespace_mapping_dict=self.namespace_mapping_dict)
        dc = apgen.generate()
        assert dc is not None, "there is not data context generated "
        assert dc["alpha"] and dc["beta"], "there is no alpha and beta contexts"
        assert dc["alpha"]["application_profiles"] is not None, "there is no application profile"
        assert dc["alpha"]["class_statistics"] is not None, "there is no class statistics"
        assert dc["alpha"]["property_usages"] is not None, "there is no propeorty usage statistics"

        assert dc["beta"]["application_profiles"] is not None, "there is no application profile"
        assert dc["beta"]["class_statistics"] is not None, "there is no class statistics"
        assert dc["beta"]["property_usages"] is not None, "there is no propeorty usage statistics"


if __name__ == '__main__':
    unittest.main()
