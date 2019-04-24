import pathlib
import unittest

from fingerprint.context.context_generator import DataContextGenerator
from fingerprint.document.report_builder import ReportBuilder
from fingerprint.project.fingerprinter_project import FingerprinterProject


class MyTestCase(unittest.TestCase):

    def setUp(self):
        self.resources_folder = pathlib.Path(__file__).parents[1] / "resources" / "templates" / "pubap"

    def test_jinja_project(self):
        project = FingerprinterProject(str(self.resources_folder))
        assert "title" in project.configuration, "configuration as no title"
        assert "alpha" in project.configuration, "configuration has no description "

        assert len(project.namespace_mapping_dict) > 0, "the prefixes have not been resolved"
        assert project.alpha is not None, "is no alpha data source available"

        # print(project.configuration)

        assert isinstance(project.get_document_builder(), ReportBuilder), "not a report builder"

        data_context_builder = project.get_data_content_builder()

        assert isinstance(data_context_builder, DataContextGenerator) or isinstance(data_context_builder,
                                                                                    list), "not a data context generator"

        assert isinstance(project.make_data_context(), dict), "the data context is not a dictionary object"

        assert project.make_document() is not None, "no document is built"
        assert "<body" in project.make_document(), "no html body available, something is not right"

        project.make_project()
        # todo: implement the diff statistics into the data context


if __name__ == '__main__':
    unittest.main()
