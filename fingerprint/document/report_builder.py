""" 
report_generator
Created:  08/03/2019
Author: Eugeniu Costetchi
Email: costezki.eugen@gmail.com

this module implements the report generation functionality.
"""

from abc import ABC, abstractmethod


class ReportBuilder(ABC):
    """
        generic report builder
    """

    @abstractmethod
    def make_document(self):
        pass


# class HTMLReportBuilder(ReportBuilder):
