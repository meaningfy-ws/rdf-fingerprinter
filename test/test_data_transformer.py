import pathlib
import unittest

from fingerprint.context.data_transformer import ColumnRenamer, StringReplacer
from fingerprint.context.iri_utils import discover_base_uris, NamespaceReducer, normalise_namespace_mapping_dict
from fingerprint.source.data_source import CSVSourceTabular


class MyTestCase(unittest.TestCase):
    def setUp(self):
        self.file_name = pathlib.Path(__file__).resolve().parents[
                             1] / "resources" / "samples" / "test.csv"
        self.sample_tabular = CSVSourceTabular(str(self.file_name)).read()
        self.aggregator = ['stype', 'p']
        self.prefixes = {"http://eurovoc.europa.eu/schema#": "evo:",
                         "http://www.w3.org/2004/02/skos/core#": "skos:",
                         "http://www.w3.org/2008/05/skos-xl#": "skoxl:",
                         "http://www.w3.org/1999/02/22-rdf-syntax-ns#": "rdf:",
                         "http://www.w3.org/2001/XMLSchema#": "xsd:",
                         "http://www.w3.org/2000/01/rdf-schema#": "rdfs:",
                         "http://purl.org/dc/terms/": "dct:",
                         "http://purl.org/dc/elements/1.1/": "dc:",
                         "http://www.w3.org/2002/07/owl#": "owl:",
                         "http://publications.europa.eu/ontology/euvoc#": "euvoc:",
                         "http://art.uniroma2.it/ontologies/vocbench#": "vb:",
                         "http://lexvo.org/ontology#": "lexvo:",
                         "http://lemon-model.net/lemon#": "lemon:",
                         "http://rdfs.org/ns/void#": "void:",
                         "http://publications.europa.eu/ontology/authority/": "ato:",
                         "http://publications.europa.eu/resource/authority/": "atr:",
                         "http://publications.europa.eu/ontology/datatype#": "atdt:",
                         "http://publications.europa.eu/mdr/": "atmdr:",
                         "http://www.w3.org/2003/01/geo/wgs84_pos#": "geowgs:",
                         "http://www.w3.org/ns/org#": "org:",
                         "http://xmlns.com/foaf/0.1/": "foaf:", }

    def test_column_renamer(self):
        renamer = ColumnRenamer(self.sample_tabular, {"stype": "Subject Type", "p": "Property"})
        new_df = renamer.transform()
        assert "Subject Type" in new_df.columns, "there is Subject Type column"
        assert "Property" in new_df.columns, "there is Property column"

    def test_value_replacer(self):
        caster = StringReplacer(self.sample_tabular, target_columns=None,
                                value_mapping_dict={"http://eurovoc.europa.eu/schema#Country": "evo:",
                                                    "http://www.w3.org/1999/02/22-rdf-syntax-ns#type": "a"})
        new_df = caster.transform()
        assert True in new_df[self.aggregator[0]].isin(
            ["evo:", "skos:"]), "the namespace evo: has been identified and replaced"
        assert True in new_df[self.aggregator[1]].isin(
            ["evo:", "skos:"]), "the namespace skos: has been identified and replaced"

    def test_namespace_discoverer(self):
        x = discover_base_uris(self.sample_tabular)
        assert "http://www.w3.org/2000/01/rdf-schema#" in x.keys(), "RDFS namespace is discovered"
        assert "ns0" in x.values(), "namespaces are numbered"

        y = discover_base_uris(self.sample_tabular,
                               known_uris={"http://www.w3.org/2000/01/rdf-schema#": "the great RDF schema"})
        assert "http://www.w3.org/2000/01/rdf-schema#" in y.keys(), "RDFS namespace is discovered"
        assert "the great RDF schema" in y.values(), "prefixes known a priori"

    def test_namespace_replacer(self):
        ns = discover_base_uris(self.sample_tabular,
                                known_uris={'http://www.w3.org/2000/01/rdf-schema#': 'rdfs:',
                                            "http://www.w3.org/2008/05/skos-xl#": "skosxl"})
        rd = NamespaceReducer(self.sample_tabular,
                              target_columns=self.aggregator,
                              namespace_mapping_dict=ns)
        df = rd.transform()
        assert True in df["p"].isin(["rdfs:label", "skosxl:literalForm"]), \
            "RDFS label and skosxl literal form is in p column"


if __name__ == '__main__':
    unittest.main()
