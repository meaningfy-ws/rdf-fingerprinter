"""The `fingerprint` command's readable-representations wiring: prefix lookup, options, one page."""

import pytest
from click.testing import CliRunner
from rdflib import Literal

from fingerprint.entrypoints.cli import main as cli
from fingerprint.service_layer import handlers
from tests.fakes import FakeSparql


@pytest.fixture
def fake(monkeypatch):
    fake = FakeSparql()
    fake.add("ex:p1", "a", "ex:Person")
    fake.add("ex:p1", "ex:name", Literal("n"))
    monkeypatch.setattr(handlers, "SparqlHttpClient", lambda endpoint, timeout: fake)
    return fake


@pytest.fixture
def lookups(monkeypatch):
    built = []

    class Recording:
        def __init__(self):
            built.append(self)

        def fetch(self):
            return []

    monkeypatch.setattr(cli, "PrefixCcList", Recording)
    return built


def run(tmp_path, *args):
    return CliRunner().invoke(cli.fingerprint_endpoint, ["-e", "http://fake/sparql", "-o", str(tmp_path), *args])


def test_the_lookup_is_used_when_switched_on(tmp_path, fake, lookups, monkeypatch):
    monkeypatch.setenv("RDF_FINGERPRINTER_PREFIX_LOOKUP", "true")
    assert run(tmp_path).exit_code == 0 and len(lookups) == 1


def test_the_lookup_stays_off_when_the_environment_says_false(tmp_path, fake, lookups, monkeypatch):
    monkeypatch.setenv("RDF_FINGERPRINTER_PREFIX_LOOKUP", "false")
    assert run(tmp_path).exit_code == 0 and lookups == []


@pytest.mark.parametrize("args", [["--module-size", "0"], ["--shapes-namespace", "urn:x y<"]])
def test_bad_generator_options_exit_2_before_any_query(tmp_path, fake, args):
    result = run(tmp_path, *args)
    assert result.exit_code == 2 and fake.queries == []
