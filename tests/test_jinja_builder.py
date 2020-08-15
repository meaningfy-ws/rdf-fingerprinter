""" 
test_jinja_builder
Created:  18/03/2019
Author: Eugeniu Costetchi
Email: costezki.eugen@gmail.com
"""

import pathlib
import unittest


class MyTestCase(unittest.TestCase):

    def setUp(self):
        self.resources_folder = pathlib.Path(__file__).parents[1] / "resources"
        self.template_folder = pathlib.Path(__file__).parents[1] / "resources" / "templates" / "pubap" / "fragments"
        self.output_file = self.template_folder.parent / "index.html"

        self.config = sample_description = {
            "title": "EuroVoc Fingerprint Report - From Old to New and Back",
            "type": "difference between two dataset fingerprints",
            "author": "Eugeniu Costetchi",
            "ns_file": str(self.resources_folder / "prefix.csv"),
            "output": str(self.output_file),
            "alpha": {
                "file": str(self.resources_folder / "samples" / "fingerprint.rq_eurovoc44.log.csv"),
                "title": "EuroVoc 4.4",
                "desc": "EuroVoc 4.4 was released a long time ago using EuroVoc Ontology."
            },
            "beta": {
                "file": str(self.resources_folder / "fingerprint.rq_EV45OLD.log.csv"),
                "title": "EuroVoc 4.5(bc)",
                "desc": "EuroVoc 4.5 backward compatible (bc) was released in July 2016 with SKOS-AP-EU and then converted to fit also the old profile of EuroVoc Ontology."
            }
        }

if __name__ == '__main__':
    unittest.main()
