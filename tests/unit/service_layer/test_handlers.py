"""The library entry `fingerprint_report` (fingerprint-report › Library outcomes)."""

from importlib.resources import files

import pytest

import fingerprint_report_templates
from fingerprint.domain.profile import Settings
from fingerprint.domain.views import GeneratorOptions
from fingerprint.service_layer.exceptions import UsageError
from fingerprint.service_layer.handlers import fingerprint_report
from tests.fakes import FakeSparql


def test_the_report_package_is_packaged():
    assert (files(fingerprint_report_templates) / "fingerprint_report" / "config.json").is_file()


def test_a_missing_output_folder_is_refused_before_any_query(tmp_path):
    sparql = FakeSparql()
    with pytest.raises(NotADirectoryError):
        fingerprint_report("http://e/sparql", tmp_path / "missing", Settings(), sparql=sparql)
    assert sparql.sent("") == []


def test_bad_options_are_usage_errors_before_any_query(tmp_path):
    sparql = FakeSparql()
    with pytest.raises(UsageError, match="shapes-namespace"):
        fingerprint_report(
            "http://e/sparql", tmp_path, Settings(), options=GeneratorOptions(shapes_namespace="urn:x y<"), sparql=sparql
        )
    assert sparql.sent("") == []
