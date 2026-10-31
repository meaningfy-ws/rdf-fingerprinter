"""One typed configuration read from `RDF_FINGERPRINTER_*` variables (domain-object-model DEC-6, P-7)."""

import subprocess
import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

from fingerprint import FingerprintConfig
from fingerprint.adapters.config_resolver import DefaultConfigResolver, EnvConfigResolver, MappingConfigResolver
from fingerprint.adapters.exceptions import ConfigError
from fingerprint.domain.profile import Settings, SettingsOverride
from fingerprint.entrypoints.cli.main import fingerprint_endpoint
from fingerprint.service_layer import handlers
from fingerprint.service_layer.settings import resolve_settings
from tests.unit.fakes import FakeSparql


def test_defaults_are_todays_constants():
    config = FingerprintConfig(DefaultConfigResolver())
    assert config.profile_file == "profile.json"
    assert config.retry_backoff_seconds == (1, 4)
    assert config.timeout_markers == ("timeout", "time limit", "timed out", "estimated execution time")
    assert config.error_excerpt_length == 200
    assert config.shapes_namespace == "urn:fingerprint:shape:"
    assert config.default_graph_label == "default graph"
    assert config.prefixes_file.name == "prefixes.json" and config.prefixes_file.is_file()
    assert config.settings_override() == SettingsOverride()
    config.validate()


def test_values_are_coerced():
    config = FingerprintConfig(
        MappingConfigResolver(
            {
                "RDF_FINGERPRINTER_RETRY_BACKOFF_SECONDS": "0.5, 2,8",
                "RDF_FINGERPRINTER_TIMEOUT_MARKERS": "Deadline,",
                "RDF_FINGERPRINTER_ERROR_EXCERPT_LENGTH": "50",
                "RDF_FINGERPRINTER_PREFIXES_FILE": "/x/p.json",
            }
        )
    )
    assert config.retry_backoff_seconds == (0.5, 2, 8)
    assert config.timeout_markers == ("deadline",)
    assert config.error_excerpt_length == 50
    assert config.prefixes_file == Path("/x/p.json")


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("RDF_FINGERPRINTER_RETRY_BACKOFF_SECONDS", "x"),
        ("RDF_FINGERPRINTER_RETRY_BACKOFF_SECONDS", "-1"),
        ("RDF_FINGERPRINTER_ERROR_EXCERPT_LENGTH", "0"),
        ("RDF_FINGERPRINTER_PROFILE_FILE", "a/b.json"),
        ("RDF_FINGERPRINTER_SHAPES_NAMESPACE", ""),
        ("RDF_FINGERPRINTER_FIRST_N", "0"),
        ("RDF_FINGERPRINTER_COMPLETENESS_CHECK", "maybe"),
    ],
)
def test_validate_names_the_bad_variable(name: str, value: str):
    with pytest.raises(ConfigError, match=name):
        FingerprintConfig(MappingConfigResolver({name: value})).validate()


def test_values_resolve_on_access(monkeypatch):
    config = FingerprintConfig(EnvConfigResolver())
    monkeypatch.setenv("RDF_FINGERPRINTER_PROFILE_FILE", "a.json")
    assert config.profile_file == "a.json"
    monkeypatch.setenv("RDF_FINGERPRINTER_PROFILE_FILE", "b.json")
    assert config.profile_file == "b.json"


def test_import_resolves_nothing(tmp_path):
    code = "import fingerprint.entrypoints.cli.main, fingerprint.service_layer.handlers"
    env = {"RDF_FINGERPRINTER_RETRY_BACKOFF_SECONDS": "x", "PATH": ""}
    result = subprocess.run([sys.executable, "-c", code], cwd=tmp_path, env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_the_override_has_the_settings_fields():
    assert set(SettingsOverride.model_fields) == set(Settings.model_fields)


def test_a_variable_changes_a_default(tmp_path, monkeypatch):
    """Scenario: A variable changes a default."""
    fake = FakeSparql()
    fake.add("ex:p", "a", "ex:Person")
    monkeypatch.setattr(handlers, "SparqlWrapperClient", lambda endpoint, timeout: fake)
    monkeypatch.setenv("RDF_FINGERPRINTER_PROFILE_FILE", "run.json")
    handlers.fingerprint_report("http://fake", tmp_path, resolve_settings(env={}))
    assert (tmp_path / "run.json").is_file() and not (tmp_path / "profile.json").exists()


def test_a_badly_typed_variable_exits_2_before_any_query(tmp_path, monkeypatch):
    """Scenario: A badly typed variable."""
    monkeypatch.setattr(handlers, "SparqlWrapperClient", lambda endpoint, timeout: pytest.fail("a query was sent"))
    result = CliRunner().invoke(
        fingerprint_endpoint,
        ["-e", "http://fake/sparql", "-o", str(tmp_path)],
        env={"RDF_FINGERPRINTER_RETRY_BACKOFF_SECONDS": "x"},
    )
    assert result.exit_code == 2 and "RDF_FINGERPRINTER_RETRY_BACKOFF_SECONDS" in result.output
    assert list(tmp_path.iterdir()) == []
