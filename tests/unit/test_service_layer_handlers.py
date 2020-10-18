#!/usr/bin/python3

# test_service_layer_handlers.py
# Date:  17/10/2020
# Author: Eugeniu Costetchi
# Email: costezki.eugen@gmail.com 

""" """
import json
import shutil
from pathlib import Path

from fingerprint.service_layer.handlers import generate_report_builder_config, generate_endpoint_fingerprint_report

try:
    import importlib.resources as pkg_resources
except ImportError:
    import importlib_resources as pkg_resources

import fingerprint_report_templates

TEST_ENDPOINT = "http://localhost:3020/dev/query"
OUTPUT_LOCATION = "./output"


def test_accessing_templates():
    with pkg_resources.path(fingerprint_report_templates, "fingerprint_report") as resource_path:
        assert "fingerprint_report" in str(resource_path)


def test_reading_template_confing_json_file():
    with pkg_resources.path(fingerprint_report_templates, "fingerprint_report") as resource_path:
        config_dict = json.loads((resource_path / "config.json").read_bytes())
        assert "conf" in config_dict
        assert "template" in config_dict


def test_generate_report_builder_config():
    d = generate_report_builder_config(sparql_endpoint_url="url", graph="graph")
    assert "url" == d["conf"]["default_endpoint"]
    assert "graph" == d["conf"]["default_graph"]


def test_generate_endpoint_fingerprint_report():
    """
        given  an input endpoint
        when generate is executed
        the output folder has a report file
    :return:
    """
    output_location = Path(OUTPUT_LOCATION)
    shutil.rmtree(output_location, ignore_errors=True)
    output_location.mkdir(parents=True, exist_ok=True)
    output_file = generate_endpoint_fingerprint_report(sparql_endpoint_url=TEST_ENDPOINT,
                                                       output_location=OUTPUT_LOCATION)
    assert output_file.exists()
