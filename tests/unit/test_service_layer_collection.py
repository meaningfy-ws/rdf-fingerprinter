"""Error-matrix rows and query selection of `collect` (design.md "Error matrix", "Which queries run")."""

import io
import logging
import urllib.error

import pytest
from pydantic import ValidationError
from rdflib import Literal

from fingerprint.adapters.sparql import EndpointUnreachable, PermanentError, QueryTimeout, redact
from fingerprint.service_layer.collection import collect
from fingerprint.service_layer.settings import UsageError, resolve_settings
from tests.unit.fakes import EX, FakeSparql

TIMEOUT, REJECTED = QueryTimeout("timed out"), PermanentError("400 unsupported", 400)


@pytest.fixture
def fake():
    fake = FakeSparql()
    for i in range(2):
        fake.add(f"ex:p{i}", "a", "ex:Person")
        fake.add(f"ex:p{i}", "ex:name", Literal(f"n{i}"))
    return fake


def run(fake, **cli):
    return collect("http://user:secret@fake/sparql?key=k", resolve_settings(cli=cli, env={}), fake)


def kinds(result):
    return [(f.query_kind, f.message) for f in result.failures]


@pytest.mark.parametrize(
    "query, error, cli, kind, message",
    [
        ("Q4", TIMEOUT, {}, "declared_hierarchy", "declared hierarchy not read"),
        ("Q2a", REJECTED, {"graph_statistics": True}, "predicate_partitions", "predicates not listed"),
        ("Q1", TIMEOUT, {"graph_statistics": True}, "triples", "Q1 timed out after 60 s"),
        ("QU", REJECTED, {"graph_statistics": True}, "untyped_subjects", "QU failed"),
    ],
)
def test_discovery_failures_are_recorded(fake, query, error, cli, kind, message):
    fake.on("Q2", TIMEOUT)  # so Q2a runs
    fake.on(query, error)
    (failure,) = [f for f in run(fake, **cli).failures]
    assert failure.query_kind == kind and message in failure.message


def test_q2_timeout_falls_back_to_q2a(fake):
    fake.on("Q2", TIMEOUT)
    graph = run(fake, graph_statistics=True).graphs[0]
    assert {p.property for p in graph.predicate_partitions} == {EX + "name", "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"}
    assert all(p.triples is None for p in graph.predicate_partitions)


@pytest.mark.parametrize("error", [TIMEOUT, REJECTED])
def test_class_counts_fall_back_per_class_without_a_failure(fake, error):
    fake.on("Q3", error)
    result = run(fake)
    assert not result.failures and result.graphs[0].class_partitions[0].instances == 2


def test_classes_not_listed(fake):
    fake.on("Q3", TIMEOUT)
    fake.on("Q3a", TIMEOUT)
    result = run(fake)
    assert kinds(result) == [("class_partitions", "graph default: classes not listed: timed out")]
    assert not result.graphs[0].class_partitions


def test_one_class_count_times_out(fake):
    fake.add("ex:c", "a", "ex:City")
    fake.on("Q3", TIMEOUT)
    fake.on("Q3b", TIMEOUT, when=lambda q: "City" in q)
    result = run(fake)
    assert [c.class_iri for c in result.graphs[0].class_partitions] == [EX + "Person"]
    assert [f.class_iri for f in result.failures] == [EX + "City"]


def test_blank_node_class_is_skipped(fake):
    fake.add("ex:x", "a", "_:anonymous")
    result = run(fake)
    assert [f.query_kind for f in result.failures] == ["class_partitions"]
    assert "not usable in a SPARQL query" in result.failures[0].message


def test_authorisation_refused_mid_run_fails_only_that_query(fake):
    refused = urllib.error.HTTPError("http://fake", 403, "forbidden", {}, io.BytesIO(b""))  # type: ignore[arg-type]
    fake.on("Q5", refused)
    result = run(fake)
    assert [(f.query_kind, f.attempts) for f in result.failures] == [("cardinality_votes", 1)]


def test_unreachable_endpoint_is_named_without_credentials(fake):
    fake.on("Q0", urllib.error.URLError(ConnectionRefusedError("refused")))
    with pytest.raises(EndpointUnreachable) as raised:
        run(fake)
    assert "cannot reach endpoint http://fake/sparql" in str(raised.value) and "secret" not in str(raised.value)


def test_profile_records_the_endpoint_without_credentials(fake):
    assert run(fake).endpoint == "http://fake/sparql"


def test_default_depth_sends_only_its_queries(fake):
    run(fake)
    sent = {q.lstrip("# ").split()[0] for q in fake.queries}
    assert sent == {"Q0", "Q4", "Q3", "Q5", "Q6", "Q7", "Q8"}


def test_failures_are_logged(fake, caplog):
    fake.on("Q4", TIMEOUT)
    with caplog.at_level(logging.WARNING):
        run(fake)
    assert "declared hierarchy not read" in caplog.text


@pytest.mark.parametrize(
    "kwargs",
    [
        {"env": {"RDF_FINGERPRINTER_ACCEPTANCE_THRESHOLD": "0"}},
        {"env": {"RDF_FINGERPRINTER_ACCEPTANCE_THRESHOLD": "0.0"}},
        {"env": {}, "config": {"acceptance_threshold": 0}},
    ],
)
def test_zero_threshold_is_refused_from_every_source(kwargs):
    with pytest.raises(UsageError):
        resolve_settings(**kwargs)


def test_profile_objects_are_read_only(fake):
    result = run(fake)
    with pytest.raises(ValidationError):
        result.endpoint = "http://other"


@pytest.mark.parametrize(
    "url, shown",
    [
        ("https://user:pw@host:8890/sparql?key=abc", "https://host:8890/sparql"),
        ("http://localhost:7878/query", "http://localhost:7878/query"),
    ],
)
def test_redact(url, shown):
    assert redact(url) == shown
