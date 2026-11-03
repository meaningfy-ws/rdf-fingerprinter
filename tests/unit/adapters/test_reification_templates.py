"""The packaged reification templates run in rdflib over the reification sample (singleton-property-pattern §A, §C)."""

from pathlib import Path

import pytest
from rdflib import RDF, Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, OWL, PROV

from fingerprint.adapters.queries import reification_query
from fingerprint.adapters.reification_catalogue import packaged_templates

EX = Namespace("http://example.org/")
SINGLETON = URIRef(str(RDF) + "singletonPropertyOf")
SAMPLE = Path(__file__).parents[2] / "test_data" / "reifications-source.ttl"
TEMPLATES = {t.id: t for t in packaged_templates()}


@pytest.fixture(scope="module")
def sample():
    return Graph().parse(SAMPLE)


def run(graph, kind, section):
    result = graph.query(reification_query(TEMPLATES[kind], section, None))
    return result.askAnswer if section == "probe" else {tuple(row) for row in result}


def terms(graph, kind):
    return {term for (term,) in run(graph, kind, "hidden")}


@pytest.mark.parametrize("kind", list(TEMPLATES))
def test_every_kind_is_found_in_the_sample(sample, kind):
    assert run(sample, kind, "probe") is True


@pytest.mark.parametrize("kind", list(TEMPLATES))
def test_no_kind_is_found_in_an_empty_graph(kind):
    assert run(Graph(), kind, "probe") is False


def test_a_property_typed_predicate_with_the_singleton_marker_is_still_ordinary():
    graph = Graph()
    graph.add((EX.acme, EX.legacy, Literal("old")))
    graph.add((EX.legacy, RDF.type, RDF.Property))
    graph.add((EX.legacy, SINGLETON, EX.isRelatedTo))
    assert run(graph, "resource_as_predicate", "probe") is False


def test_a_predicate_typed_only_rdf_property_is_not_a_resource_as_predicate():
    graph = Graph()
    graph.add((EX.acme, EX.legacy, Literal("old")))
    graph.add((EX.legacy, RDF.type, RDF.Property))
    assert run(graph, "resource_as_predicate", "probe") is False


@pytest.mark.parametrize(
    ("kind", "relation", "reifier"),
    [
        (
            "rdf_statement",
            (EX.Person, EX.knows, EX.Person, Literal(1)),
            (EX.Person, EX.knows, EX.Person, DCTERMS.source, Literal(1)),
        ),
        (
            "owl_axiom",
            (EX.Person, EX.knows, EX.Person, Literal(1)),
            (EX.Person, EX.knows, EX.Person, DCTERMS.source, Literal(1)),
        ),
        ("negative_property_assertion", (EX.Person, EX.worksFor, EX.Org, Literal(1)), None),
    ],
)
def test_relations_and_reifier_properties_of_the_sample(sample, kind, relation, reifier):
    assert run(sample, kind, "relations") == {relation}
    assert run(sample, kind, "reifier-properties") == ({reifier} if reifier else set())


def test_resource_as_predicate_names_singletons_by_their_type_and_reports_the_marker_as_a_reifier(sample):
    assert run(sample, "resource_as_predicate", "relations") == {
        (EX.Person, EX.Link, EX.Org, Literal(2)),
        (EX.Person, EX.Procedure, EX.Org, Literal(1)),
    }
    assert run(sample, "resource_as_predicate", "reifier-properties") == {
        (EX.Person, EX.Link, EX.Org, SINGLETON, Literal(2)),
        (EX.Person, EX.Link, EX.Org, PROV.wasAttributedTo, Literal(1)),
    }


HIDDEN = {
    "rdf_statement": {RDF.Statement, RDF.subject, RDF.predicate, RDF.object},
    "resource_as_predicate": {EX.rel1, EX.rel2, EX.Link, EX.performs1, EX.Procedure},
    "owl_axiom": {OWL.Axiom, OWL.annotatedSource, OWL.annotatedProperty, OWL.annotatedTarget},
    "negative_property_assertion": {
        OWL.NegativePropertyAssertion,
        OWL.sourceIndividual,
        OWL.assertionProperty,
        OWL.targetIndividual,
        OWL.targetValue,
    },
    "triple_term": {URIRef(str(RDF) + "reifies")},
}


@pytest.mark.parametrize("kind", list(HIDDEN))
def test_hidden_terms_of_the_sample(sample, kind):
    assert terms(sample, kind) == HIDDEN[kind]


def test_a_property_only_predicate_is_hidden_by_no_kind(sample):
    assert not any(RDF.Property in terms(sample, kind) or EX.legacy in terms(sample, kind) for kind in TEMPLATES)


def test_triple_term_counts_the_reifies_triples(sample):
    assert run(sample, "triple_term", "count") == {(Literal(1),)}
    assert TEMPLATES["triple_term"].relations is None


def test_a_class_with_an_ordinary_instance_is_not_hidden():
    graph = Graph()
    graph.add((EX.a, EX.rel3, EX.b))
    graph.add((EX.rel3, RDF.type, EX.Mixed))
    graph.add((EX.other, RDF.type, EX.Mixed))
    assert EX.Mixed not in terms(graph, "resource_as_predicate")
    assert EX.rel3 in terms(graph, "resource_as_predicate")


def test_a_class_of_reifiers_only_is_hidden_for_every_kind():
    graph = Graph()
    graph.add((EX.st, RDF.type, EX.Claim))
    graph.add((EX.st, RDF.subject, EX.a))
    graph.add((EX.st, RDF.predicate, EX.p))
    graph.add((EX.st, RDF.object, EX.b))
    assert EX.Claim in terms(graph, "rdf_statement")
    graph.add((EX.plain, RDF.type, EX.Claim))
    assert EX.Claim not in terms(graph, "rdf_statement")


def test_a_triple_seen_through_two_graphs_counts_once():
    from rdflib import Dataset

    dataset = Dataset(default_union=True)
    for name in ("g1", "g2"):
        graph = dataset.graph(EX[name])
        graph.add((EX.alice, EX.rel1, EX.acme))
        graph.add((EX.rel1, RDF.type, EX.Link))
        graph.add((EX.alice, RDF.type, EX.Person))
    rows = {tuple(r) for r in dataset.query(reification_query(TEMPLATES["resource_as_predicate"], "relations", None))}
    assert rows == {(EX.Person, EX.Link, None, Literal(1))}
