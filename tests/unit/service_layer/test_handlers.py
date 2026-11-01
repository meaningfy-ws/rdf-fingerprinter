"""The library entry `fingerprint_report` (fingerprint-report › Library outcomes)."""

import logging
from pathlib import Path

import pytest

from fingerprint.adapters.sparql import QueryTimeout
from fingerprint.domain.profile import NamespacePrefix, Settings
from fingerprint.domain.views import GeneratorOptions
from fingerprint.service_layer import handlers
from fingerprint.service_layer.exceptions import UsageError
from fingerprint.service_layer.handlers import fingerprint_report
from tests.fakes import FakeSparql


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
def store():
    """An in-memory store with one instance of one class, in a namespace no packaged list names."""
    store = FakeSparql()
    store.add("http://unique.example/ns#t1", "a", THING)
    return store


def test_the_default_client_talks_to_the_endpoint_with_the_settings_timeout(store, monkeypatch, tmp_path):
    made = []  # no public parameter builds the client, so the name in `handlers` is replaced

    def client(endpoint, timeout):
        made.append((endpoint, timeout))
        return store

    monkeypatch.setattr(handlers, "SparqlHttpClient", client)
    fingerprint_report("http://e/sparql", tmp_path, Settings(timeout_seconds=7), renderer=Recorder())
    assert made == [("http://e/sparql", 7)] and store.queries


def test_the_prefix_lists_resolve_the_namespaces_of_the_saved_profile(store, tmp_path):
    def prefix_of_thing(**lists):
        _, run = fingerprint_report("http://e/sparql", tmp_path, Settings(), sparql=store, renderer=Recorder(), **lists)
        return {e.namespace: e.prefix for e in run.namespaces}["http://unique.example/ns#"]

    user = [NamespacePrefix(prefix="mine", namespace="http://unique.example/ns#", source="user")]
    assert prefix_of_thing(user_prefixes=user) == "mine"
    assert prefix_of_thing(prefix_list=PrefixCc()) == "uniq"
    assert prefix_of_thing() not in ("mine", "uniq")


def test_the_document_comes_first_and_the_other_formats_follow_through_the_same_renderer(store, tmp_path):
    renderer = Recorder()
    report, _ = fingerprint_report("http://e/sparql", tmp_path, Settings(), sparql=store, formats=["shacl"], renderer=renderer)
    assert [(package, names) for package, names, _ in renderer.calls] == [
        ("fingerprint_report", ["main.html"]),
        ("shacl_shapes", [renderer.calls[1][1][0]]),
    ]
    assert report == tmp_path / "main.html" and renderer.calls[1][1][0].startswith("shapes-default")


def test_the_options_reach_every_format_and_unknown_filters_are_warned_once(store, tmp_path, caplog):
    options = GeneratorOptions(shapes_namespace="https://shapes.ex/", exclude_namespaces=["nope"])
    with caplog.at_level(logging.WARNING):
        fingerprint_report("http://e/sparql", tmp_path, Settings(), sparql=store, formats=["shacl"], options=options)
    assert "https://shapes.ex/" in (tmp_path / next(p.name for p in tmp_path.glob("shapes-*.ttl"))).read_text()
    assert [m for m in caplog.messages if "nope" in m] == ["--exclude-namespace nope: no such namespace; ignored"]


def test_a_saved_profile_survives_a_failing_render(store, tmp_path):
    class Broken(Recorder):
        def make(self, *args, **kwargs):
            raise RuntimeError("render failed")

    with pytest.raises(RuntimeError):
        fingerprint_report("http://e/sparql", tmp_path, Settings(), sparql=store, renderer=Broken())
    assert (tmp_path / "profile.json").is_file()


@pytest.mark.parametrize("formats, noted", [(["doc"], True), ([], False)])
def test_asking_for_the_document_format_is_noted_not_written_twice(store, tmp_path, caplog, formats, noted):
    renderer = Recorder()
    with caplog.at_level(logging.INFO):
        fingerprint_report("http://e/sparql", tmp_path, Settings(), sparql=store, formats=formats, renderer=renderer)
    assert any("main.html is the document" in m for m in caplog.messages) is noted
    assert [package for package, _, _ in renderer.calls] == ["fingerprint_report"]


def test_the_outcome_is_logged_with_the_report_path(store, tmp_path, caplog):
    with caplog.at_level(logging.INFO):
        report, _ = fingerprint_report("http://e/sparql", tmp_path, Settings(), sparql=store, renderer=Recorder())
    assert any(str(report) in m for m in caplog.messages)


def test_failures_are_logged_with_their_number(store, tmp_path, caplog):
    store.on("Q4", QueryTimeout("timed out"))
    with caplog.at_level(logging.INFO):
        report, run = fingerprint_report("http://e/sparql", tmp_path, Settings(), sparql=store, renderer=Recorder())
    assert f"report written to {report} with {len(run.failures)} failures" in caplog.messages and run.failures


def test_a_library_scan_without_checks_uses_the_packaged_catalogue(store, tmp_path):
    _, run = fingerprint_report("http://e/sparql", tmp_path, Settings(pitfall_scan=True), sparql=store, renderer=Recorder())
    assert any(g.pitfalls is not None for g in run.graphs) or store.sent("PITFALL")
