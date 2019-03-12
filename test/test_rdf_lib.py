import os
import pathlib
import unittest
import rdflib
from SPARQLWrapper import SPARQLWrapper, XML, JSON

class MyRDFLibTest(unittest.TestCase):

    def setUp(self):
        self.testFile = pathlib.Path(__file__).parents[1] / "resources" / "samples" / "rdf" / "continents-source-ap.rdf"
        self.testEndpoint = "http://publications.europa.eu/webapi/rdf/sparql"
        self.g = rdflib.Graph()

    def test_load(self):
        self.g.parse(str(self.testFile))
        assert len(self.g) > 0

    def test_prepare_query(self):
        self.g.parse(str(self.testFile))
        res = self.g.query("""
        SELECT DISTINCT ?s
        WHERE {
            ?s ?p ?o .
        } LIMIT 10
        """)
        assert len(res) > 0

    def test_query(self):
        sparql = SPARQLWrapper(self.testEndpoint)
        sparql.setQuery("""
            prefix skos: <http://www.w3.org/2004/02/skos/core#>
            select * 
            from <http://publications.europa.eu/resource/authority/continent>
            where
            {
             ?c skos:inScheme <http://publications.europa.eu/resource/authority/continent>
            } limit 100    
        """)
        sparql.setReturnFormat(XML)
        results = sparql.query().convert()
        print(results)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        print(results)

    def test_read_config_file(self):
        pass

if __name__ == '__main__':
    unittest.main()
