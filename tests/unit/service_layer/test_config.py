"""How the service layer reads the configuration (domain-object-model DEC-6, P-7)."""

import pytest

from fingerprint.service_layer import handlers
from fingerprint.service_layer.exceptions import UsageError
from fingerprint.service_layer.generators.generator import plain_label
from fingerprint.service_layer.settings import load_user_prefixes, resolve_settings
from tests.fakes import FakeSparql


def test_a_variable_changes_a_default(tmp_path, monkeypatch):
    """Scenario: A variable changes a default."""
    fake = FakeSparql()
    fake.add("ex:p", "a", "ex:Person")
    monkeypatch.setattr(handlers, "SparqlHttpClient", lambda endpoint, timeout: fake)
    monkeypatch.setenv("RDF_FINGERPRINTER_PROFILE_FILE", "run.json")
    handlers.fingerprint_report("http://fake", tmp_path, resolve_settings(env={}))
    assert (tmp_path / "run.json").is_file() and not (tmp_path / "profile.json").exists()


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
