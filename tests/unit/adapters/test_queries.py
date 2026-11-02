import re

import pytest

from fingerprint.adapters.queries import (
    QUERY_FILES,
    render,
    subjects_exact,
    subjects_limit,
    subjects_values,
    terms_values,
    type_lookup,
)
from fingerprint.domain.vocabulary import (
    ALT_LABEL_PREDICATES,
    DCTERMS,
    NOTE_PREDICATES,
    RDFS,
    SKOS,
    SKOSXL,
    TERM_DESCRIPTION_PREDICATES,
    TERM_LABEL_PREDICATES,
)

G = "http://example.org/g"
C = "http://example.org/Person"


def compact(text: str) -> str:
    return " ".join(text.split())


def test_every_query_starts_with_its_name_and_has_no_open_placeholder():
    for name in QUERY_FILES:
        text = render(name, G, cls=C, prop=C, subjects=subjects_exact(G, C), scope="same_graph", limit=10, k=5)
        assert text.startswith(f"# {name} ")
        assert "$" not in text, name


def test_named_graph_wraps_patterns_and_default_graph_does_not():
    assert "GRAPH <http://example.org/g> { ?s ?p ?o . }" in compact(render("Q2", G))
    assert compact(render("Q2", None)).endswith("{ ?s ?p ?o . } GROUP BY ?p")


def test_default_graph_counts_distinct_instances():
    assert "COUNT(DISTINCT ?s)" in render("Q3", "")
    assert "COUNT(?s)" in render("Q3", G)
    assert "SELECT DISTINCT ?s" in render("QS", "", cls=C, limit=3)


@pytest.mark.parametrize("name", ["Q5", "Q6", "Q7", "Q8", "Q11"])
def test_exact_mode_binds_the_class_inside_the_query(name):
    text = compact(render(name, G, cls=C, subjects=subjects_exact(G, C), scope="same_graph"))
    assert "GRAPH <http://example.org/g> { ?s a <http://example.org/Person> . }" in text
    assert "VALUES ?c" not in text


def test_first_n_lists_the_instances_once():
    text = compact(render("Q5", G, subjects=subjects_values(["http://e/a", "http://e/b"])))
    assert text.count("VALUES ?s { <http://e/a> <http://e/b> }") == 1


def test_blank_node_fallback_uses_a_limit_subquery():
    assert (
        compact(subjects_limit(G, C, 7))
        == "{ SELECT ?s { GRAPH <http://example.org/g> { ?s a <http://example.org/Person> . } } LIMIT 7 }"
    )


def test_type_lookup_per_scope():
    assert compact(type_lookup(G, "same_graph")) == "OPTIONAL { GRAPH <http://example.org/g> { ?o a ?t . } }"
    assert "GRAPH ?tg" in type_lookup(G, "any_graph")


@pytest.mark.parametrize("name", ["Q5", "Q6", "Q7", "Q11"])
def test_rdf_type_is_not_a_property_row(name):
    assert re.search(r"\?p != rdf:type", render(name, G, cls=C, subjects=subjects_exact(G, C), scope="same_graph"))


def test_unusable_iri_is_refused():
    with pytest.raises(ValueError):
        render("Q3b", G, cls="http://example.org/a b")


def test_term_annotation_query_lists_its_terms_and_an_unwritable_term_is_refused():
    text = render("Q12", G, terms=terms_values(["http://e/a", "http://e/b"]))
    assert "VALUES ?t { <http://e/a> <http://e/b> }" in compact(text)
    assert terms_values([]) == "" and "VALUES ?t { }" in compact(render("Q12", G))
    with pytest.raises(ValueError):
        terms_values(["http://e/a b"])


def test_term_annotation_query_asks_for_every_predicate_of_the_vocabulary():
    text = compact(render("Q12", G))
    prefixes = {SKOS: "skos:", SKOSXL: "skosxl:", RDFS: "rdfs:", DCTERMS: "dcterms:"}

    def curie(iri):
        namespace = next(ns for ns in prefixes if iri.startswith(ns))
        return prefixes[namespace] + iri.removeprefix(namespace)

    everything = (*TERM_LABEL_PREDICATES, *ALT_LABEL_PREDICATES, *TERM_DESCRIPTION_PREDICATES, *NOTE_PREDICATES)
    for predicate in (p for p in everything if not p.startswith(SKOSXL)):
        assert curie(predicate) in text, predicate
    for predicate in (p for p in everything if p.startswith(SKOSXL)):
        assert f"{curie(predicate)}/skosxl:literalForm" in text, predicate
        assert f"BIND({curie(predicate)} AS ?p)" in text, predicate
