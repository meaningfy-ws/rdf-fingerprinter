"""
test_data_source
Date: 10.03.19
Author: Eugeniu Costetchi
Email: costezki.eugen@gmail.com
"""
import pathlib
import unittest

import pandas as pd

from fingerprint.source.data_source import CSVSourceTabular, EndpointSourceTabular, JSONDataSource


class MyTestCase(unittest.TestCase):

    def setUp(self):
        self.file_name = pathlib.Path(__file__).resolve().parents[
                             1] / "resources" / "samples" / "fingerprint.rq_eurovoc44.log.csv"
        self.json_file_name = pathlib.Path(__file__).resolve().parents[
                                  1] / "resources" / "defaultValues.json"
        self.url = "http://publications.europa.eu/webapi/rdf/sparql"
        self.graph = "http://publications.europa.eu/resource/authority/human-sex"
        self.query = "select * where {<http://publications.europa.eu/resource/authority/human-sex> ?p ?o} limit 100"

    def test_CSV_source(self):
        ds = CSVSourceTabular(str(self.file_name))
        df = ds.read()
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert len(df.columns) > 0

    def test_endpoint_source(self):
        ds = EndpointSourceTabular(url=self.url, query=self.query, graph=self.graph)
        df = ds.read()
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert len(df) < 101
        assert len(df.columns) > 0

    def test_json_source(self):
        ds = JSONDataSource(self.json_file_name)
        data = ds.read()
        assert "title" in data, "there is a title in the config file"
        assert "type" in data, "there is a type in the config file"
        assert "output" in data, "there is a output in the config file"


if __name__ == '__main__':
    unittest.main()
