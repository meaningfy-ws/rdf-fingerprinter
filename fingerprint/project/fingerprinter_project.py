""" 
jinja_project
Created:  18/03/2019
Author: Eugeniu Costetchi
Email: costezki.eugen@gmail.com
"""
import pathlib
import shutil
from abc import abstractmethod

from fingerprint.context.context_generator import DataContextGenerator
from fingerprint.context.fingerprint_generator import ApplicationProfileContextGenerator, DiffContextGenerator
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
        # resolving the main document template
        self.resolve_main_document_name()

        # reading the prefix mappings
        self.namespace_mapping_dict = NamespaceMappingCSV(self.configuration["ns_file"]).to_dict()

        # data sets alpha beta gamma
        self.alpha, self.beta, self.gamma = None, None, None

        # helper properties, not really needed
        self.data_context = None
        self.document_content = None
        self.structural_columns = None
        self.diff_column_titles = None

        if "alpha" in self.configuration:
            self.alpha = build_data_source(self.configuration["alpha"]).read()
        if "beta" in self.configuration:
            self.beta = build_data_source(self.configuration["beta"]).read()
        if "gamma" in self.configuration:
            self.gamma = build_data_source(self.configuration["gamma"]).read()

        if "diff" in self.configuration:
            if "structural_columns" in self.configuration["diff"]:
                self.structural_columns = self.configuration["diff"]["structural_columns"]
            if "column_titles" in self.configuration["diff"]:
                self.diff_column_titles = self.configuration["diff"]["column_titles"]

    def resolve_paths(self):
        """
            turns the relative paths provided in the configuration file into absolute paths
        :return:
        """
        # attempts relative and absolute paths
        if "output" not in self.configuration or len(self.configuration["output"]) == 0:
            self.configuration["output"] = str(pathlib.Path.home() / "temp" / "rdf-fingerprinter")
        elif not self.configuration["output"] and not pathlib.Path(self.configuration["output"]).exists():
            str(self.path_to_project / pathlib.Path(self.configuration["output"]))

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

    def resolve_main_document_name(self):
        """
            In case not specified, resolves the template name by search for standard
            filenames such as
            - index.html
            - main.html

            The main document template must be a file name located within the /fragments folder
        :return:
        """
        if "document_template" not in self.configuration:
            # main_template_name = self.configuration["document_template"]
            if (self.path_to_template_fragments / "index.html").exists():
                self.configuration["document_template"] = "index.html"
            elif (self.path_to_template_fragments / "main.html").exists():
                self.configuration["document_template"] = "main.html"
        return self.configuration["document_template"]

    def make_data_context(self):
        if self.data_context is None:
            if isinstance(self.get_data_content_builder(), DataContextGenerator):
                self.data_context = self.get_data_content_builder().generate()
            elif isinstance(self.get_data_content_builder(), list):
                self.data_context = {}
                for cg in self.get_data_content_builder():
                    self.data_context.update(cg.generate())
            else:
                raise Exception(
                    "Unknown data context builder. Can handle one or a list of DataContextGenerator instances.")
        return self.data_context

    def get_document_builder(self):
        """
            returns a document builder. by default it is a JINJA document duilder. in the future more shall follow such as Latex, Mustache, etc
        :return:
        """
        return JinjaBuilder(data_context=self.make_data_context(),
                            config_context=self.configuration,
                            template_folder=self.path_to_template_fragments,
                            main_template_name=self.resolve_main_document_name())

    def make_document(self):
        """
            Build the document using the template file name provided in configuration["document_template"].
            If none is provided then will try to use "index.html" or "main.html"

            :return: the string of the entire document ready to be writen into the output folder
        """
        if self.document_content is None:
            self.document_content = self.get_document_builder().make_document()
        return self.document_content

    def get_data_content_builder(self):
        """
        Return a data context builder depending on the parameters.
        At the moment only the FingerprinterContext builder is available

        :return:
        """
        return [ApplicationProfileContextGenerator(alpha=self.alpha,
                                                   beta=self.beta,
                                                   namespace_mapping_dict=self.namespace_mapping_dict, ),
                DiffContextGenerator(alpha=self.alpha,
                                     beta=self.beta,
                                     structural_columns=self.structural_columns,
                                     column_titles=self.diff_column_titles
                                     ),
                ]

    def make_project(self):
        output_folder = pathlib.Path(self.configuration["output"])
        shutil.rmtree(str(output_folder), ignore_errors=True)
        shutil.copytree(str(self.path_to_static_resources), str(output_folder), copy_function=shutil.copy)

        # os.makedirs(str(output_folder))
        # .mkdir(parents=True, exist_ok=True)

        output_file_path = output_folder / self.resolve_main_document_name()

        with output_file_path.open("w", encoding="utf-8") as f:
            f.write(self.make_document())

        # todo: implement the diff statistics into the report
        # todo: work on copying the right files into the right place :)
