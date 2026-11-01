"""The library entry `fingerprint_report` (fingerprint-report › Library outcomes)."""

import logging
from importlib.resources import files
from pathlib import Path

import pytest

import fingerprint_report_templates
from fingerprint.domain.profile import NamespacePrefix, Settings
from fingerprint.domain.views import GeneratorOptions
from fingerprint.service_layer import handlers
from fingerprint.service_layer.exceptions import UsageError
from fingerprint.service_layer.handlers import fingerprint_report
from tests import builders
from tests.fakes import FakeSparql


def test_the_report_package_is_packaged():
    assert (files(fingerprint_report_templates) / "fingerprint_report" / "config.json").is_file()


def test_a_missing_output_folder_is_refused_before_any_query(tmp_path):
    sparql = FakeSparql()
    with pytest.raises(NotADirectoryError, match=f"{tmp_path / 'missing'} is not an existing folder"):
        fingerprint_report("http://e/sparql", tmp_path / "missing", Settings(), sparql=sparql)
    assert sparql.queries == []


def test_bad_options_are_usage_errors_before_any_query(tmp_path):
    sparql = FakeSparql()
    with pytest.raises(UsageError, match="shapes-namespace"):
        fingerprint_report(
            "http://e/sparql", tmp_path, Settings(), options=GeneratorOptions(shapes_namespace="urn:x y<"), sparql=sparql
        )
    assert sparql.queries == []


# --- the order of the steps and what each is handed (lean-test-suite 7.5) ---

THING = "http://unique.example/ns#Thing"


class Recorder:
    """A renderer port that records each format's call and names the files it would write."""

    def __init__(self):
        self.calls = []

    def make(self, package, outputs, *, folder, **kwargs):
        self.calls.append((Path(package).name, [name for name, _ in outputs], kwargs))
        return [Path(folder) / name for name, _ in outputs]


class PrefixCc:
    def fetch(self):
        return [NamespacePrefix(prefix="uniq", namespace="http://unique.example/ns#", source="prefix_cc")]


@pytest.fixture
def collected(monkeypatch):
    """`collect` answers with a one-class run and remembers how it was called."""
    seen = {}

    def collect(endpoint, settings, sparql):
        seen.update(endpoint=endpoint, settings=settings, sparql=sparql)
        return builders.profile_run(builders.klass(THING, 1))

    monkeypatch.setattr(handlers, "collect", collect)
    return seen


def test_the_default_client_talks_to_the_endpoint_with_the_settings_timeout(collected, monkeypatch, tmp_path):
    made = []

    class Client(FakeSparql):
        def __init__(self, endpoint, timeout):
            super().__init__()
            made.append((endpoint, timeout))

    monkeypatch.setattr(handlers, "SparqlHttpClient", Client)
    fingerprint_report("http://e/sparql", tmp_path, Settings(timeout_seconds=7), renderer=Recorder())
    assert made == [("http://e/sparql", 7)] and isinstance(collected["sparql"], Client)


def test_the_prefix_lists_resolve_the_namespaces_of_the_saved_profile(collected, tmp_path):
    user = [NamespacePrefix(prefix="mine", namespace="http://unique.example/ns#", source="user")]
    _, run = fingerprint_report("http://e/sparql", tmp_path, Settings(), user_prefixes=user, renderer=Recorder())
    assert {e.namespace: e.prefix for e in run.namespaces}["http://unique.example/ns#"] == "mine"
    _, run = fingerprint_report("http://e/sparql", tmp_path, Settings(), prefix_list=PrefixCc(), renderer=Recorder())
    assert {e.namespace: e.prefix for e in run.namespaces}["http://unique.example/ns#"] == "uniq"
    _, run = fingerprint_report("http://e/sparql", tmp_path, Settings(), renderer=Recorder())
    assert {e.namespace: e.prefix for e in run.namespaces}["http://unique.example/ns#"] not in ("mine", "uniq")


def test_the_document_comes_first_and_the_other_formats_follow_through_the_same_renderer(collected, tmp_path):
    renderer = Recorder()
    report, _ = fingerprint_report("http://e/sparql", tmp_path, Settings(), formats=["shacl"], renderer=renderer)
    assert [(package, names) for package, names, _ in renderer.calls] == [
        ("fingerprint_report", ["main.html"]),
        ("shacl_shapes", [renderer.calls[1][1][0]]),
    ]
    assert report == tmp_path / "main.html" and renderer.calls[1][1][0].startswith("shapes-default")


def test_the_options_reach_every_format_and_unknown_filters_are_warned_once(collected, tmp_path, caplog):
    options = GeneratorOptions(shapes_namespace="https://shapes.ex/", exclude_namespaces=["nope"])
    with caplog.at_level(logging.WARNING):
        fingerprint_report("http://e/sparql", tmp_path, Settings(), formats=["shacl"], options=options)
    assert "https://shapes.ex/" in (tmp_path / next(p.name for p in tmp_path.glob("shapes-*.ttl"))).read_text()
    assert [m for m in caplog.messages if "nope" in m] == ["--exclude-namespace nope: no such namespace; ignored"]


def test_a_saved_profile_survives_a_failing_render(collected, tmp_path):
    class Broken(Recorder):
        def make(self, *args, **kwargs):
            raise RuntimeError("render failed")

    with pytest.raises(RuntimeError):
        fingerprint_report("http://e/sparql", tmp_path, Settings(), renderer=Broken())
    assert (tmp_path / "profile.json").is_file()


@pytest.mark.parametrize("formats, noted", [(["doc"], True), ([], False)])
def test_asking_for_the_document_format_is_noted_not_written_twice(collected, tmp_path, caplog, formats, noted):
    renderer = Recorder()
    with caplog.at_level(logging.INFO):
        fingerprint_report("http://e/sparql", tmp_path, Settings(), formats=formats, renderer=renderer)
    assert ("main.html is the document; no second page is written" in caplog.messages) is noted
    assert [package for package, _, _ in renderer.calls] == ["fingerprint_report"]


def test_the_outcome_is_logged_with_the_report_path(collected, tmp_path, caplog):
    with caplog.at_level(logging.INFO):
        report, _ = fingerprint_report("http://e/sparql", tmp_path, Settings(), renderer=Recorder())
    assert f"fingerprint report written to {report}" in caplog.messages


def test_failures_are_logged_with_their_number(collected, monkeypatch, tmp_path, caplog):
    failing = builders.profile_run(
        builders.klass(THING, 1), failures=[builders.failure(THING, "a"), builders.failure(THING, "b")]
    )
    monkeypatch.setattr(handlers, "collect", lambda *args: failing)
    with caplog.at_level(logging.INFO):
        report, run = fingerprint_report("http://e/sparql", tmp_path, Settings(), renderer=Recorder())
    assert f"report written to {report} with 2 failures" in caplog.messages and len(run.failures) == 2
