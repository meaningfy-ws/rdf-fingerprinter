"""The pitfall scan stage over FakeSparql (pitfall-scans › The pitfall scan stage; design D-4, D-5)."""

import logging
from types import SimpleNamespace

import pytest
from rdflib import URIRef

from fingerprint.adapters.exceptions import PermanentError
from fingerprint.adapters.pitfall_catalogue import packaged_checks
from fingerprint.adapters.queries import pitfall_count_query, pitfall_example_query
from fingerprint.domain.profile import NodeKind
from fingerprint.service_layer import collection
from fingerprint.service_layer.collection import collect
from fingerprint.service_layer.settings import resolve_settings
from tests.fakes import FakeSparql

EX = "http://example.org/"  # what the fake expands ex: to
OWL = "http://www.w3.org/2002/07/owl#"
DATA, SCHEMA = EX + "data", EX + "schema"
CHECKS = {c.check_id: c for c in packaged_checks()}


def store():
    fake = FakeSparql()
    fake.add("ex:a", "a", "ex:Person", graph=DATA)
    fake.add("ex:a", "ex:undeclared", "ex:b", graph=DATA)
    fake.add("ex:a", "ex:knows", "ex:b", graph=DATA)
    fake.add("ex:Person", "a", OWL + "Class", graph=SCHEMA)
    fake.add("ex:knows", "a", OWL + "ObjectProperty", graph=SCHEMA)
    return fake


def run(fake, checks=None, **cli):
    settings = resolve_settings(cli={"pitfall_scan": True, "depth": "classes", **cli}, env={})
    return collect("http://fake/sparql", settings, fake, list(CHECKS.values()) if checks is None else checks)


def results(run_, graph):
    profile = next(g for g in run_.graphs if (g.graph or "") == graph)
    return {r.check_id: r for r in profile.pitfalls or []}


def test_the_count_and_example_queries_wrap_the_check():
    check = CHECKS["p35_untyped_property"]
    count = pitfall_count_query(check.check_id, check.query, DATA, [SCHEMA])
    assert count.startswith("# PITFALL p35_untyped_property count\nPREFIX owl:")
    assert f"FROM <{DATA}> FROM <{SCHEMA}> WHERE {{ {{ SELECT ?entity" in count and "BOUND(?entity)" in count
    examples = pitfall_example_query(check.check_id, check.query, None, [SCHEMA], 3)
    assert "FROM" not in examples and examples.endswith("ORDER BY ?entity ?property ?value LIMIT 3")


def test_without_schema_graphs_every_check_runs_alone():
    profile = run(store(), selected_graphs=[DATA])
    found = results(profile, DATA)
    assert len(found) == len(CHECKS)
    assert found["p35_untyped_property"].count == 2  # ex:knows is undeclared without the schema


def test_aggregate_checks_count_zero_on_a_clean_graph_and_send_no_example_query():
    fake = FakeSparql()
    fake.add("ex:a", "ex:knows", "ex:b", graph=DATA)
    fake.add("ex:knows", "a", OWL + "ObjectProperty", graph=DATA)
    found = results(run(fake, selected_graphs=[DATA]), DATA)
    for check_id in ("p19_multiple_domains_or_ranges", "p35_untyped_property", "x_individual_as_predicate"):
        assert found[check_id].count == 0 and found[check_id].examples == []
        assert not [q for q in fake.sent("PITFALL") if q.startswith(f"# PITFALL {check_id} examples")]


def test_the_scan_runs_at_depth_graphs():
    found = results(run(store(), selected_graphs=[DATA], depth="graphs"), DATA)
    assert found["p35_untyped_property"].count == 2


def test_blank_node_entities():
    fake = FakeSparql()
    fake.add("ex:a", "ex:p", "ex:b", graph=DATA)
    from rdflib import BNode, URIRef

    fake.dataset.graph(URIRef(DATA)).add((BNode("x1"), URIRef(EX + "q"), URIRef(EX + "c")))
    check = CHECKS["p35_untyped_property"]
    custom = check.model_copy(update={"check_id": "subjects", "query": check.query.replace("?s ?entity ?o", "?entity ?s ?o")})
    found = results(run(fake, checks=[custom], selected_graphs=[DATA]), DATA)
    assert "blank_node" in {e.entity.kind for e in found["subjects"].examples}


@pytest.mark.parametrize("value", ["http://example.org/<bad>"])
def test_an_unwritable_schema_graph_is_a_usage_error(value):
    from fingerprint.service_layer.exceptions import UsageError

    with pytest.raises(UsageError, match="schema graph"):
        resolve_settings(cli={"schema_graphs": [value]}, env={})


def test_schema_graphs_from_the_environment_are_comma_separated():
    settings = resolve_settings(env={"RDF_FINGERPRINTER_SCHEMA_GRAPHS": f"{SCHEMA}, {EX}other"})
    assert settings.schema_graphs == [SCHEMA, EX + "other"]


def test_an_unbound_count_is_a_recorded_failure_not_a_crash():
    """Review: some stores answer an aggregate over nothing with one unbound row."""
    fake = store()
    fake.on("PITFALL", [{"n": None}], when=lambda q: " count\n" in q)
    profile = run(fake, checks=[CHECKS["p35_untyped_property"]], selected_graphs=[DATA])
    assert results(profile, DATA) == {}
    assert [f.check_id for f in profile.failures] == ["p35_untyped_property"]


def test_a_failed_emptiness_check_skips_the_graph_and_failed_examples_keep_the_count():
    fake = store()
    fake.add("ex:c", "ex:undeclared", "ex:d", graph=SCHEMA)  # a finding in the graph that is scanned
    fake.on("PITFALL", PermanentError("no"), when=lambda q: "PITFALL ask" in q, times=1)
    fake.on("PITFALL", PermanentError("no"), when=lambda q: " examples\n" in q)
    profile = run(fake, checks=[CHECKS["p35_untyped_property"]], selected_graphs=[DATA, SCHEMA])
    skipped, scanned = (next(g for g in profile.graphs if g.graph == iri) for iri in (DATA, SCHEMA))
    assert skipped.pitfalls is None
    assert scanned.pitfalls[0].count and not scanned.pitfalls[0].examples
    assert len(profile.failures) == 2


def test_an_unbound_example_term_is_left_out():
    fake = store()
    fake.on("PITFALL", [{"entity": None, "property": None, "value": None}], when=lambda q: " examples\n" in q)
    profile = run(fake, checks=[CHECKS["p35_untyped_property"]], selected_graphs=[DATA])
    (example, *_) = results(profile, DATA)["p35_untyped_property"].examples
    assert example.entity is None and example.property is None and example.value is None


# --- what a result, a failure and the log say (lean-test-suite: every field of the record is pinned) ---

LOGGER = "fingerprint.service_layer.collection"
ONE = CHECKS["p35_untyped_property"]
COUNT, EXAMPLES, ASK = (lambda q: " count\n" in q), (lambda q: " examples\n" in q), (lambda q: "PITFALL ask" in q)


def only_default_graph():
    fake = FakeSparql()
    fake.add("ex:a", "ex:undeclared", "ex:b")
    return fake


def test_a_result_carries_the_check_its_origin_its_examples_and_its_duration(monkeypatch):
    clock = iter([100.0, 100.1234567] * 4)
    monkeypatch.setattr(collection, "time", SimpleNamespace(monotonic=lambda: next(clock)))
    rows = [{"entity": URIRef(EX + "a"), "property": URIRef(EX + "p"), "value": "text"}]
    for origin, source in (("packaged", ONE.source), ("my/checks.rq", f"{ONE.source} (my/checks.rq)")):
        fake = store()
        fake.on("PITFALL", rows, when=EXAMPLES)
        check = ONE.model_copy(update={"description": "Describes it", "heuristic": True, "origin": origin})
        (result,) = run(fake, checks=[check], selected_graphs=[DATA], concurrency=1).graphs[0].pitfalls
        assert (result.title, result.description, result.importance, result.scope) == (
            ONE.title,
            "Describes it",
            ONE.importance,
            ONE.scope,
        )
        assert (result.source, result.heuristic, result.count, result.seconds) == (source, True, 2, 0.123)
        (example,) = result.examples
        assert (example.entity.text, example.entity.kind) == (EX + "a", NodeKind.iri)
        assert (example.property.text, example.value.text, example.value.kind) == (EX + "p", "text", NodeKind.literal)


def test_a_check_with_no_row_counts_zero_and_sends_no_example_query():
    fake = store()
    fake.on("PITFALL", [], when=COUNT)
    (result,) = run(fake, checks=[ONE], selected_graphs=[DATA]).graphs[0].pitfalls
    assert result.count == 0 and not [q for q in fake.sent("PITFALL") if EXAMPLES(q)]


def test_the_queries_of_a_check_name_it_and_join_the_schema_graphs():
    fake = store()
    run(fake, checks=[ONE], selected_graphs=[DATA], schema_graphs=[SCHEMA])
    count, examples = (next(q for q in fake.sent("PITFALL") if kind(q)) for kind in (COUNT, EXAMPLES))
    assert count.startswith(f"# PITFALL {ONE.check_id} count") and examples.startswith(f"# PITFALL {ONE.check_id} examples")
    assert f"FROM <{DATA}> FROM <{SCHEMA}>" in count and f"FROM <{SCHEMA}>" in examples


@pytest.mark.parametrize("graph, label", [(DATA, DATA), (None, "default")])
def test_a_failed_count_or_examples_is_recorded_with_its_graph_and_check(graph, label):
    for failing, step in ((COUNT, "count"), (EXAMPLES, "examples")):
        fake = store() if graph else only_default_graph()
        fake.on("PITFALL", PermanentError("denied"), when=failing)
        profile = run(fake, checks=[ONE], **({"selected_graphs": [graph]} if graph else {}))
        (failure,) = profile.failures
        assert failure.message == f"graph {label}: pitfall {ONE.check_id}: {step} failed: denied"
        assert (failure.query_kind, failure.graph, failure.check_id) == ("pitfall", graph, ONE.check_id)


def test_a_failed_emptiness_check_is_recorded_with_its_graph(caplog):
    fake = store()
    fake.on("PITFALL", PermanentError("denied"), when=ASK)
    (failure,) = run(fake, checks=[ONE], selected_graphs=[DATA]).failures
    assert failure.message == f"graph {DATA}: pitfall scan skipped, emptiness check failed: denied"
    assert (failure.graph, failure.check_id) == (DATA, None)


def test_the_scan_logs_an_empty_graph_and_the_findings_of_a_scanned_one(caplog):
    with caplog.at_level(logging.INFO, logger=LOGGER):
        run(only_default_graph(), checks=[ONE, CHECKS["p19_multiple_domains_or_ranges"]])
        run(FakeSparql(), checks=[ONE])
    assert "graph default: 2 pitfall checks, 1 with findings" in caplog.messages
    assert "graph default: empty; no pitfall scan" in caplog.messages


def test_only_the_default_graph_warns_that_it_ran_without_the_schema_graphs(caplog):
    unjoined = f"graph default: {collection.UNJOINED_DEFAULT}"
    for schema_graphs, graph, warns in (([SCHEMA], None, True), ([], None, False), ([SCHEMA], DATA, False)):
        caplog.clear()
        fake = only_default_graph() if graph is None else store()
        with caplog.at_level(logging.WARNING, logger=LOGGER):
            run(fake, checks=[ONE], schema_graphs=schema_graphs, **({"selected_graphs": [graph]} if graph else {}))
        assert (unjoined in caplog.messages) is warns
