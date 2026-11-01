"""The pitfall scan stage over FakeSparql (pitfall-scans › The pitfall scan stage; design D-4, D-5)."""

import pytest

from fingerprint.adapters.exceptions import PermanentError
from fingerprint.adapters.pitfall_catalogue import packaged_checks
from fingerprint.adapters.queries import pitfall_count_query, pitfall_example_query
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
