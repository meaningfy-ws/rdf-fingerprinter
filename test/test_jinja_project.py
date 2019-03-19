import pathlib
import unittest

from fingerprint.project.jinja_project import FingerprinterProject


class MyTestCase(unittest.TestCase):

    def setUp(self):
        self.resources_folder = pathlib.Path(__file__).parents[1] / "resources" / "templates" / "pubap"

    def test_jinja_project(self):
        project = FingerprinterProject(str(self.resources_folder))
        assert "title" in project.configuration, "configuration as no title"
        assert "alpha" in project.configuration, "configuration has no description "

        assert len(project.namespace_mapping_dict) > 0, "the prefixes have not been resolved"
        assert project.alpha is not None, "is no alpha data source available"

        # print(project.make_data_context())
        # print(project.configuration)

        assert project.make_document() is not None, "no document is built"
        assert "<body>" in project.make_document(), "no html body available, something is not right"

        # todo: continue here, finish implementing the project


if __name__ == '__main__':
    unittest.main()
