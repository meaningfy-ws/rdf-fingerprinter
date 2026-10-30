#!/usr/bin/python3

# test_service_layer_handlers.py
# Date:  17/10/2020
# Author: Eugeniu Costetchi
# Email: costezki.eugen@gmail.com

""" """

import json
from importlib.resources import files

import pytest

import fingerprint_report_templates
from fingerprint.service_layer.handlers import generate_endpoint_fingerprint_report, generate_report_builder_config


def test_accessing_templates():
    assert (files(fingerprint_report_templates) / "fingerprint_report" / "config.json").is_file()


def test_reading_template_config_json_file():
    config_dict = json.loads((files(fingerprint_report_templates) / "fingerprint_report" / "config.json").read_bytes())
    assert "conf" in config_dict
    assert "template" in config_dict


def test_generate_report_builder_config():
    d = generate_report_builder_config(sparql_endpoint_url="url", selected_graphs=["graph"], external_template_location=None)
    assert "url" == d["conf"]["default_endpoint"]
    assert "graph" in d["conf"]["selected_graphs"]


def test_generate_endpoint_fingerprint_report_requires_an_existing_folder(tmp_path):
    with pytest.raises(NotADirectoryError):
        generate_endpoint_fingerprint_report(sparql_endpoint_url="url", output_location=tmp_path / "missing")
