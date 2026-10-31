"""One typed configuration read from `RDF_FINGERPRINTER_*` variables (domain-object-model DEC-6, P-7)."""

import ast
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
from fingerprint.service_layer.exceptions import UsageError
from fingerprint.service_layer.generators.generator import plain_label
from fingerprint.service_layer.settings import load_user_prefixes, resolve_settings
from tests.unit.fakes import FakeSparql

PACKAGE = Path(__file__).parents[2] / "fingerprint"


def test_defaults_are_todays_constants():
    config = FingerprintConfig(DefaultConfigResolver())
    assert config.profile_file == "profile.json"
    assert config.retry_backoff_seconds == (1, 4)
    assert config.timeout_markers == ("timeout", "time limit", "timed out", "estimated execution time")
    assert config.error_excerpt_length == 200
    assert config.shapes_namespace is None
    assert config.default_graph_label == "default graph"
    assert config.prefixes_file is None
    assert config.prefix_lookup is True
    assert config.packaged_prefixes_file.name == "prefixes.json" and config.packaged_prefixes_file.is_file()
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
                "RDF_FINGERPRINTER_PREFIX_LOOKUP": "off",
                "RDF_FINGERPRINTER_SHAPES_NAMESPACE": "http://ex.org/shapes/",
            }
        )
    )
    assert config.retry_backoff_seconds == (0.5, 2, 8)
    assert config.timeout_markers == ("deadline",)
    assert config.error_excerpt_length == 50
    assert config.prefixes_file == Path("/x/p.json")
    assert config.prefix_lookup is False
    assert config.shapes_namespace == "http://ex.org/shapes/"


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("RDF_FINGERPRINTER_RETRY_BACKOFF_SECONDS", "x"),
        ("RDF_FINGERPRINTER_RETRY_BACKOFF_SECONDS", "-1"),
        ("RDF_FINGERPRINTER_ERROR_EXCERPT_LENGTH", "0"),
        ("RDF_FINGERPRINTER_PROFILE_FILE", "a/b.json"),
        ("RDF_FINGERPRINTER_SHAPES_NAMESPACE", "urn:x y<"),
        ("RDF_FINGERPRINTER_PREFIX_LOOKUP", "maybe"),
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
    monkeypatch.setattr(handlers, "SparqlHttpClient", lambda endpoint, timeout: fake)
    monkeypatch.setenv("RDF_FINGERPRINTER_PROFILE_FILE", "run.json")
    handlers.fingerprint_report("http://fake", tmp_path, resolve_settings(env={}))
    assert (tmp_path / "run.json").is_file() and not (tmp_path / "profile.json").exists()


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


def test_an_unwritable_shapes_namespace_names_its_variable():
    with pytest.raises(ConfigError, match="RDF_FINGERPRINTER_SHAPES_NAMESPACE"):
        FingerprintConfig(MappingConfigResolver({"RDF_FINGERPRINTER_SHAPES_NAMESPACE": "urn:x y<"})).validate()


@pytest.mark.parametrize(
    "content",
    [None, "[]", '{"x\\n!include /etc/passwd\\n\'": "http://ex.org/"}', '{"ex:": "http://ex.org/a b"}'],
    ids=["missing", "not-an-object", "injected-name", "unwritable-namespace"],
)
def test_a_bad_prefixes_file_is_a_usage_error(tmp_path, monkeypatch, content):
    path = tmp_path / "prefixes.json"
    if content is not None:
        path.write_text(content)
    monkeypatch.setenv("RDF_FINGERPRINTER_PREFIXES_FILE", str(path))
    with pytest.raises(UsageError, match="RDF_FINGERPRINTER_PREFIXES_FILE"):
        load_user_prefixes()


def test_the_default_graph_label_is_written_as_plain_text(monkeypatch):
    monkeypatch.setenv("RDF_FINGERPRINTER_DEFAULT_GRAPH_LABEL", "x\n!include /etc/passwd")
    assert "\n" not in plain_label(None)


@pytest.mark.parametrize("arguments", [["--first-n", "0"], ["--concurrency", "0"]])
def test_an_invalid_cli_setting_exits_2_before_any_query(tmp_path, monkeypatch, arguments):
    monkeypatch.setattr(handlers, "SparqlHttpClient", lambda endpoint, timeout: pytest.fail("a query was sent"))
    result = CliRunner().invoke(fingerprint_endpoint, ["-e", "http://fake/sparql", "-o", str(tmp_path), *arguments])
    assert result.exit_code == 2 and "errors.pydantic.dev" not in result.output


def test_only_http_endpoints_are_queried(tmp_path, monkeypatch):
    monkeypatch.setattr(handlers, "SparqlHttpClient", lambda endpoint, timeout: pytest.fail("a query was sent"))
    result = CliRunner().invoke(fingerprint_endpoint, ["-e", "file:///etc/hostname", "-o", str(tmp_path)])
    assert result.exit_code == 2 and "http or https" in result.output


def test_the_modules_the_root_imports_never_import_it_back():
    """fingerprint/__init__.py holds the config (the settings pattern) and imports these; a module among them
    that imported `fingerprint` would make a circular import."""
    root = ast.parse((PACKAGE / "__init__.py").read_text())
    imported = {
        n.module for n in ast.walk(root) if isinstance(n, ast.ImportFrom) and (n.module or "").startswith("fingerprint.")
    }
    for module in imported:
        tree = ast.parse((PACKAGE.parent / (module.replace(".", "/") + ".py")).read_text())
        names = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        names |= {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
        assert "fingerprint" not in names, f"{module} imports the package root"
