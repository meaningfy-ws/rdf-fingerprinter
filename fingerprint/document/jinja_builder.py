""" 
jinja_builder
Created:  18/03/2019
Author: Eugeniu Costetchi
Email: costezki.eugen@gmail.com
"""
import jinja2

from fingerprint.document.report_builder import ReportBuilder


class JinjaBuilder(ReportBuilder):

    def __init__(self, data_context, config_context, template_folder, main_template_name):
        """
            Builds a document form a template using two top level data contexts.

        :param data_context: the data context available in the templates under the key "data"
        :param config_context: the configuration data context available in the templates under the key "configuration"
        :param template_folder: the folder where JINJA templates are found
        :param main_template_name: the main document template that will be used to generate the document

        """
        self.dataContext = data_context
        self.config_context = config_context
        self.templateLoader = jinja2.FileSystemLoader(searchpath=str(template_folder))
        self.templateEnv = jinja2.Environment(loader=self.templateLoader)
        self.document_template = self.templateEnv.get_template(main_template_name)

    def make_document(self):
        return self.document_template.render(data=self.dataContext, configuration=self.config_context)
