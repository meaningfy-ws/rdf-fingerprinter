"""How the `fingerprint` command reads the configuration (domain-object-model DEC-6, P-7)."""

import pytest
from click.testing import CliRunner

from fingerprint.entrypoints.cli.main import fingerprint_endpoint
from fingerprint.service_layer import handlers


def test_a_badly_typed_variable_exits_2_before_any_query(tmp_path, monkeypatch):
    """Scenario: A badly typed variable."""
    monkeypatch.setattr(handlers, "SparqlHttpClient", lambda endpoint, timeout: pytest.fail("a query was sent"))
    result = CliRunner().invoke(
        fingerprint_endpoint,
        ["-e", "http://fake/sparql", "-o", str(tmp_path)],
        env={"RDF_FINGERPRINTER_RETRY_BACKOFF_SECONDS": "x"},
    )
    assert result.exit_code == 2 and "RDF_FINGERPRINTER_RETRY_BACKOFF_SECONDS" in result.output
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("arguments", [["--first-n", "0"], ["--concurrency", "0"]])
def test_an_invalid_cli_setting_exits_2_before_any_query(tmp_path, monkeypatch, arguments):
    monkeypatch.setattr(handlers, "SparqlHttpClient", lambda endpoint, timeout: pytest.fail("a query was sent"))
    result = CliRunner().invoke(fingerprint_endpoint, ["-e", "http://fake/sparql", "-o", str(tmp_path), *arguments])
    assert result.exit_code == 2 and "errors.pydantic.dev" not in result.output


def test_only_http_endpoints_are_queried(tmp_path, monkeypatch):
    monkeypatch.setattr(handlers, "SparqlHttpClient", lambda endpoint, timeout: pytest.fail("a query was sent"))
    result = CliRunner().invoke(fingerprint_endpoint, ["-e", "file:///etc/hostname", "-o", str(tmp_path)])
    assert result.exit_code == 2 and "http or https" in result.output
