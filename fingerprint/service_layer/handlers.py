#!/usr/bin/python3

# handlers.py
# Date:  15/10/2020
# Author: Eugeniu Costetchi
# Email: costezki.eugen@gmail.com 

""" """

import json
import logging
import tempfile
from pathlib import Path
from shutil import copytree
from typing import Union, List

from eds4jinja2.builders.report_builder import ReportBuilder

try:
    import importlib.resources as pkg_resources
except ImportError:
    import importlib_resources as pkg_resources
import fingerprint_report_templates

logger = logging.getLogger(__name__)


def generate_endpoint_fingerprint_report(sparql_endpoint_url: str, output_location: Union[str, Path],
                                         graph: str = "") -> str:
    """
        Calculate the fingerprint of a given endpoint and write the report in the output location.
        Optionally the fingerprint calculation could be restricted to a particular named graph.
    :param graph: a valid URI
    :param sparql_endpoint_url:
    :param output_location:
    :return:
    """
    temp_dir = Path(output_location)
    temp_dir.mkdir(parents=True, exist_ok=True)
    with pkg_resources.path(fingerprint_report_templates, "fingerprint_report") as template_location:
        copytree(template_location, temp_dir, dirs_exist_ok=True)
    config_content = generate_report_builder_config(sparql_endpoint_url, graph)
    with open(Path(temp_dir) / 'config.json', 'w') as config_file:
        config_file.write(json.dumps(config_content))
    report_builder = ReportBuilder(target_path=temp_dir)
    report_builder.make_document()

    return Path(str(temp_dir)) / 'output' / str(config_content["template"])


# with tempfile.TemporaryDirectory() as temp_dir:
#     template_location = Path(__file__).parents[3] / 'resources/eds_templates/diff_report'
#     copytree(template_location, temp_dir, dirs_exist_ok=True)
#
#     with open(Path(temp_dir) / 'config.json', 'w') as config_file:
#         config_content = generate_report_builder_config(dataset)
#         config_file.write(dumps(config_content))
#
#     report_builder = ReportBuilder(target_path=temp_dir)
#     report_builder.make_document()


def generate_report_builder_config(sparql_endpoint_url, graph=""):
    """
        Read the default config json from the fingerprint_report and set the endpoint and the graph uri if necessary
    :param sparql_endpoint_url:
    :param graph:
    :return: the new configuration
    """
    with pkg_resources.path(fingerprint_report_templates, "fingerprint_report") as resource_path:
        config_dict = json.loads((resource_path / "config.json").read_bytes())
        config_dict["conf"]["default_endpoint"] = sparql_endpoint_url
        config_dict["conf"]["default_graph"] = graph
        return config_dict
