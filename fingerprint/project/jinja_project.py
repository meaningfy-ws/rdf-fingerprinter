""" 
jinja_project
Created:  18/03/2019
Author: Eugeniu Costetchi
Email: costezki.eugen@gmail.com
"""
import pathlib
from abc import abstractmethod

from fingerprint.context.context_generator import TabularContextGenerator
from fingerprint.context.iri_utils import NamespaceMappingCSV
from fingerprint.document.jinja_builder import JinjaBuilder
from fingerprint.source.data_source import JSONDataSource, build_data_source


class FolderBasedProject(object):
    """
        The generic report generation project using a folder structure.
        Project is a folder that comes with a set of expectations with respect to its content.

        The expectations are as following:
            - configuration.json file with project configurations
            - /fragments sub-folder containing the document patterns (e.g. JINJA, Mustache, etc.),
                it is also the root for the templating engine file loader.
            - /static sub-folder that contains all the javascript, css, images and other static artifacts
                used in the final document
            - /data sub-folder that contains any data source, namespace definition or other content asset

        The configuration file is expected to have the following fields:
            - title - string
            - output - a relative or absolute folder where generated document shall be provided
            - alpha - data source object definition
            - beta - (optional) data source object definition
            - gamma - (optional) data source object definition

        a data source object contains the following mandatory:
            - file - the file name (relative path probably to data folder)
            - title - the title of the data source
    """

    def __init__(self, absolute_path_to_project):
        self.path_to_project = pathlib.Path(absolute_path_to_project)
        assert self.path_to_project.exists() and self.path_to_project.is_dir(), "there is no project folder"
        assert (self.path_to_project / "configuration.json").exists(), "there is no configuration.json file in the " \
                                                                       "project"
        assert (self.path_to_project / "fragments").exists(), "there is no /fragments folder in the project"
        assert (self.path_to_project / "static").exists(), " there is no /static folder in the projest"

        self.configuration = JSONDataSource(file_path=str(self.path_to_project / "configuration.json")).read()
        self.path_to_template_fragments = self.path_to_project / "fragments"
        self.path_to_static_resources = self.path_to_project / "static"

    @abstractmethod
    def make_document(self):
        """
            call the document builder to generate the final document
        :return: string document
        """
        pass

    @abstractmethod
    def make_project(self):
        """
            generate the document and eventually copy the ready product somewhere
        :return: None
        """
        pass

    @abstractmethod
    def make_data_context(self):
        """
            call the data context builder to generate the data context
        :return: data context dictionary
        """
        pass

    @abstractmethod
    def get_data_content_builder(self):
        """
            return a data context builder based on the configurations of the project
        :return:
        """
        pass

    @abstractmethod
    def get_document_builder(self):
        """
            return a document builder based on the configurations of the project
        :return:
        """
        pass

class FingerprinterProject(FolderBasedProject):
    def __init__(self, absolute_path_to_project):
        """
            The JINJA project is a folder that comes with a set of expectations with respect to its content.

        :param absolute_path_to_project:
        """
        super(FingerprinterProject, self).__init__(absolute_path_to_project=absolute_path_to_project)
        # resolving relative paths
        self.resolve_paths()

        # reading the prefix mappings
        self.namespace_mapping_dict = NamespaceMappingCSV(self.configuration["ns_file"]).to_dict()

        # data sets alpha beta gamma
        self.alpha, self.beta, self.gamma = None, None, None

        if "alpha" in self.configuration:
            self.alpha = build_data_source(self.configuration["alpha"]).read()
        if "beta" in self.configuration:
            self.beta = build_data_source(self.configuration["beta"]).read()
        if "gamma" in self.configuration:
            self.gamma = build_data_source(self.configuration["gamma"]).read()

    def resolve_paths(self):
        """
            turns the relative paths provided in the configuration file into absolute paths
        :return:
        """
        # attempts relative and absolute paths
        if not pathlib.Path(self.configuration["output"]).exists():
            self.configuration["output"] = str(self.path_to_project / pathlib.Path(self.configuration["output"]))

        if not pathlib.Path(self.configuration["ns_file"]).exists():
            self.configuration["ns_file"] = str(self.path_to_project / pathlib.Path(self.configuration["ns_file"]))

        if not pathlib.Path(self.configuration["alpha"]["file"]).exists():
            self.configuration["alpha"]["file"] = str(
                self.path_to_project / pathlib.Path(self.configuration["alpha"]["file"]))

        if "beta" in self.configuration and not pathlib.Path(self.configuration["beta"]["file"]).exists():
            self.configuration["beta"]["file"] = str(
                self.path_to_project / pathlib.Path(self.configuration["beta"]["file"]))

        if "gamma" in self.configuration and not pathlib.Path(self.configuration["gamma"]["file"]).exists():
            self.configuration["gamma"]["file"] = str(
                self.path_to_project / pathlib.Path(self.configuration["gamma"]["file"]))

    def make_data_context(self):
        results = {"alpha": TabularContextGenerator(self.alpha).generate()}
        if self.beta is not None:
            results["beta"] = TabularContextGenerator(self.beta).generate()
        if self.gamma is not None:
            results["gamma"] = TabularContextGenerator(self.gamma).generate()
        return results

    def make_document(self):
        """
            Build the document using the template file name provided in configuration["document_template"].
            If none is provided then will try to use "index.html" or "main.html"

            :return: the string of the entire document ready to be writen into the output folder
        """
        # todo: delegate to the jinja builder
        # call document builder
        if "document_template" in self.configuration:
            main_template_name = self.configuration["document_template"]
        elif (self.path_to_template_fragments / "index.html").exists():
            main_template_name = "index.html"
        elif (self.path_to_template_fragments / "main.html").exists():
            main_template_name = "main.html"

        builder = JinjaBuilder(data_context=self.make_data_context(),
                               config_context=self.configuration,
                               template_folder=self.path_to_template_fragments,
                               main_template_name=main_template_name)
        return builder.make_document()


