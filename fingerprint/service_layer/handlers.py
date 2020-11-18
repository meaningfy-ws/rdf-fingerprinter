#!/usr/bin/python3

# handlers.py
# Date:  15/10/2020
# Author: Eugeniu Costetchi
# Email: costezki.eugen@gmail.com 

""" """

import json
import logging
from pathlib import Path
from typing import Union

from eds4jinja2.builders.report_builder import ReportBuilder

try:
    import importlib.resources as pkg_resources
except ImportError:
    import importlib_resources as pkg_resources
import fingerprint_report_templates

logger = logging.getLogger(__name__)


def generate_endpoint_fingerprint_report(sparql_endpoint_url: str, output_location: Union[str, Path],
                                         graph: str = "", external_template_location: Union[str, Path] = None) -> str:
    """
        Calculate the fingerprint of a given endpoint and write the report in the output location.
        Optionally the fingerprint calculation could be restricted to a particular named graph.
    :param sparql_endpoint_url: URL to fingerprint
    :param output_location: location of where to generate the report
    :param graph: a valid URI
    :param external_template_location: location of custom template (if None -> use the default template)
    :return: path to the main report document
    """
    location = Path(output_location)
    if not location.exists() or not location.is_dir():
        raise NotADirectoryError("The output location must be a folder")

    template_location = external_template_location if external_template_location else \
        pkg_resources.path(fingerprint_report_templates, "fingerprint_report").__enter__()

    updated_config_content = generate_report_builder_config(sparql_endpoint_url, graph, external_template_location)
    report_builder = ReportBuilder(target_path=template_location, additional_config=updated_config_content,
                                   output_path=location)
    report_builder.make_document()
    return location / updated_config_content["template"]


def generate_report_builder_config(sparql_endpoint_url, graph, external_template_location):
    """
        Read the default config json from the fingerprint_report and set the endpoint and the graph uri if necessary
    :param sparql_endpoint_url: URL to fingerprint
    :param graph: a valid URI
    :param external_template_location: location of custom template
    :return: the new configuration
    """
    template_location = external_template_location if external_template_location else \
        pkg_resources.path(fingerprint_report_templates, "fingerprint_report").__enter__()

    config_dict = json.loads((template_location / "config.json").read_bytes())
    config_dict["conf"]["default_endpoint"] = sparql_endpoint_url
    config_dict["conf"]["default_graph"] = graph
    return config_dict
