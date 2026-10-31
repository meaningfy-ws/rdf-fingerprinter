"""Every collection query runs on the loaded test store (`make oxigraph-load-test-data`)."""

import pytest

from fingerprint.adapters.queries import QUERY_FILES, render, subjects_exact, subjects_limit, subjects_values
from fingerprint.adapters.sparql import SparqlWrapperClient
from tests import LOCAL_ENDPOINT

CONTINENTS = "http://publications.europa.eu/resources/authority/continents"
CONTINENT = "http://publications.europa.eu/ontology/euvoc#Continent"
PREF_LABEL = "http://www.w3.org/2008/05/skos-xl#prefLabel"


@pytest.fixture(scope="module")
def sparql():
    return SparqlWrapperClient(LOCAL_ENDPOINT, timeout_seconds=30)


@pytest.mark.parametrize("graph", [CONTINENTS, ""])
@pytest.mark.parametrize("scope", ["same_graph", "any_graph"])
@pytest.mark.parametrize("name", sorted(set(QUERY_FILES) - {"Q10"}))
def test_query_runs(sparql, name, graph, scope):
    text = render(
        name, graph, cls=CONTINENT, prop=PREF_LABEL, subjects=subjects_exact(graph, CONTINENT), scope=scope, limit=3, k=3
    )
    assert isinstance(sparql.select(text), list)


def test_presence_check_runs(sparql):
    assert sparql.ask(render("Q10", CONTINENTS, cls=CONTINENT, prop=PREF_LABEL)) is True


def test_named_graphs_are_listed(sparql):
    assert {row["g"] for row in sparql.select(render("Q0"))} >= {CONTINENTS}


def test_class_counts(sparql):
    counts = {row["c"]: int(row["instances"]) for row in sparql.select(render("Q3", CONTINENTS))}
    assert counts[CONTINENT] == 6


@pytest.mark.parametrize("name", ["Q5", "Q6", "Q7", "Q8"])
def test_first_n_sources_agree_with_exact_on_a_small_class(sparql, name):
    listed = [row["s"] for row in sparql.select(render("QS", CONTINENTS, cls=CONTINENT, limit=100))]
    sources = [
        subjects_exact(CONTINENTS, CONTINENT),
        subjects_values(listed),
        subjects_limit(CONTINENTS, CONTINENT, 100),
    ]
    results = [
        sorted(repr(sorted(r.items())) for r in sparql.select(render(name, CONTINENTS, cls=CONTINENT, subjects=s)))
        for s in sources
    ]
    assert results[0] == results[1] == results[2]
