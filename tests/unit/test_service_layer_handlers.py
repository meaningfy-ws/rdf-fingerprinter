#!/usr/bin/python3

# test_service_layer_handlers.py
# Date:  17/10/2020
# Author: Eugeniu Costetchi
# Email: costezki.eugen@gmail.com 

""" """
import json
from pathlib import Path

from bs4 import BeautifulSoup

from fingerprint.service_layer.handlers import generate_report_builder_config, generate_endpoint_fingerprint_report

try:
    import importlib.resources as pkg_resources
except ImportError:
    import importlib_resources as pkg_resources

import fingerprint_report_templates


def test_accessing_templates():
    with pkg_resources.path(fingerprint_report_templates, "fingerprint_report") as resource_path:
        assert "fingerprint_report" in str(resource_path)


def test_reading_template_config_json_file():
    with pkg_resources.path(fingerprint_report_templates, "fingerprint_report") as resource_path:
        config_dict = json.loads((resource_path / "config.json").read_bytes())
        assert "conf" in config_dict
        assert "template" in config_dict


def test_generate_report_builder_config():
    d = generate_report_builder_config(sparql_endpoint_url="url", graph="graph", external_template_location=None)
    assert "url" == d["conf"]["default_endpoint"]
    assert "graph" == d["conf"]["default_graph"]


def test_generate_endpoint_fingerprint_report_default_template(tmpdir):
    """
        given  an input endpoint
        when generate is executed
        the output folder has a report file
    :return:
    """
    output_path = tmpdir.mkdir("/output")

    output_file = generate_endpoint_fingerprint_report(sparql_endpoint_url='http://localhost:3030/dev/query',
                                                       output_location=str(output_path))

    with open(output_file, 'r') as file:
        soup = BeautifulSoup(file.read(), 'html.parser')

    main_title = soup.find('h1', attrs={'class': 'ui header center aligned reportTitle'}).text
    assert main_title == 'Structural fingerprint'

    class_instantiation_title = soup.find('h1', attrs={'class': 'ui header'}).text
    assert class_instantiation_title == 'Class instantiation shapes'

    tables = soup.find_all('table')
    assert len(tables) == 6

    classes_list = ['owl#Ontology', 'core#ConceptScheme', 'skos-xl#Label',
                    'core#Concept', 'euvoc#Continent', 'euvoc#XlNotation']

    def check_if_class_in_report(class_name, table_list):
        return any(class_name in table.text for table in table_list)

    for class_name in classes_list:
        assert check_if_class_in_report(class_name, tables)


def test_generate_endpoint_fingerprint_report_custom_template(tmpdir):
    output_path = tmpdir.mkdir("/output")

    custom_template_location = Path(__file__).parents[1] / 'test_data/custom_template'
    output_file = generate_endpoint_fingerprint_report(sparql_endpoint_url='http://localhost:3030/dev/query',
                                                       output_location=str(output_path),
                                                       external_template_location=custom_template_location)

    with open(output_file, 'r') as file:
        soup = BeautifulSoup(file.read(), 'html.parser')

    main_title = soup.find('h1').text
    assert main_title == 'Test structural fingerprint'
