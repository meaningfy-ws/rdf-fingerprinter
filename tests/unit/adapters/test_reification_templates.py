"""The packaged reification templates run in rdflib over the reification sample (singleton-property-pattern §A, §C)."""

from pathlib import Path

import pytest
from rdflib import RDF, Dataset, Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, OWL, PROV

from fingerprint.adapters.queries import reification_query
from fingerprint.adapters.reification_catalogue import packaged_templates

EX = Namespace("http://example.org/")
DCAT = Namespace("http://www.w3.org/ns/dcat#")
SCHEMA = Namespace("http://schema.org/")
WIKIBASE = Namespace("http://wikiba.se/ontology#")
CRM = Namespace("http://www.cidoc-crm.org/cidoc-crm/")
SINGLETON = URIRef(str(RDF) + "singletonPropertyOf")
SAMPLE = Path(__file__).parents[2] / "test_data" / "reifications-source.ttl"
TEMPLATES = {t.id: t for t in packaged_templates()}


@pytest.fixture(scope="module")
def sample():
    """A dataset (graph_statement needs named graphs): the sample is its default graph and the named graph it describes."""
    dataset = Dataset()
    dataset.parse(SAMPLE)
    dataset.graph(EX.reifications).parse(SAMPLE)
    return dataset


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
    assert run(Dataset(), kind, "probe") is False


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


PROV_QUALIFIED = (
    "Association Attribution Communication Delegation Derivation End Generation Influence Invalidation PrimarySource "
    "Quotation Revision Start Usage"
).split()


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
    "prov_qualified": {PROV.Association, *(PROV[f"qualified{n}"] for n in PROV_QUALIFIED)},
    "dcat_qualified": {DCAT.qualifiedRelation, DCAT.qualifiedAttribution, DCAT.Relationship},
    "schema_role": {SCHEMA.OrganizationRole},
    "wikibase_statement": {WIKIBASE.Statement, EX.claimP1},
    "cidoc_property_of_property": {CRM.P01_has_domain, CRM.P02_has_range, CRM.PC14_carried_out_by},
}


@pytest.mark.parametrize("kind", list(HIDDEN))
def test_hidden_terms_of_the_sample(sample, kind):
    assert terms(sample, kind) == HIDDEN[kind]


def test_a_property_only_predicate_is_hidden_by_no_kind(sample):
    assert not any(
        RDF.Property in terms(sample, kind) or EX.legacy in terms(sample, kind) for kind in TEMPLATES if TEMPLATES[kind].hidden
    )


def test_graph_statement_counts_the_named_graphs_the_graph_describes(sample):
    assert run(sample, "graph_statement", "count") == {(Literal(1),)}
    assert TEMPLATES["graph_statement"].relations is None and TEMPLATES["graph_statement"].hidden is None


def test_nanopublication_counts_the_heads_and_hides_its_vocabulary(sample):
    NP = Namespace("http://www.nanopub.org/nschema#")
    assert run(sample, "nanopublication", "count") == {(Literal(2),)}
    assert terms(sample, "nanopublication") == {NP.Nanopublication, NP.hasAssertion, NP.hasProvenance, NP.hasPublicationInfo}


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


STAGE_THREE = [
    ("prov_qualified", EX.Run, PROV.qualifiedAssociation, EX.Team, PROV.hadRole),
    ("dcat_qualified", EX.Dataset, DCAT.qualifiedRelation, EX.Archive, DCAT.hadRole),
    ("schema_role", EX.Worker, SCHEMA.affiliation, EX.Firm, SCHEMA.startDate),
    ("wikibase_statement", EX.Item, EX.claimP1, EX.Place, EX.rank),
    ("cidoc_property_of_property", EX.Event, CRM.PC14_carried_out_by, EX.Actor, EX.note),
]


@pytest.mark.parametrize(("kind", "subject", "predicate", "target", "reifier"), STAGE_THREE)
def test_stage_three_kinds_name_the_relation_and_leave_out_the_link_properties(
    sample, kind, subject, predicate, target, reifier
):
    assert run(sample, kind, "relations") == {(subject, predicate, target, Literal(1))}
    assert run(sample, kind, "reifier-properties") == {(subject, predicate, target, reifier, Literal(1))}


@pytest.mark.parametrize("qualified", PROV_QUALIFIED)
def test_prov_qualified_names_the_relation_by_the_qualified_property_itself(qualified):
    graph = Graph()
    graph.add((EX.a, PROV[f"qualified{qualified}"], EX.q))
    graph.add((EX.a, RDF.type, EX.Run))
    graph.add((EX.q, PROV.entity, EX.b))
    assert run(graph, "prov_qualified", "relations") == {(EX.Run, PROV[f"qualified{qualified}"], None, Literal(1))}


def test_dcat_qualified_attribution_keeps_its_name_and_is_not_counted_by_prov():
    graph = Graph()
    graph.add((EX.d, RDF.type, EX.Dataset))
    graph.add((EX.d, DCAT.qualifiedAttribution, EX.q))
    graph.add((EX.q, PROV.agent, EX.org))
    assert run(graph, "dcat_qualified", "relations") == {(EX.Dataset, DCAT.qualifiedAttribution, None, Literal(1))}
    assert run(graph, "prov_qualified", "probe") is False


def test_schema_role_is_recognised_in_https_and_through_subclasses_only():
    graph = Graph()
    https = Namespace("https://schema.org/")
    graph.add((EX.a, https.member, EX.r))
    graph.add((EX.r, RDF.type, https.EmployeeRole))
    graph.add((EX.r, https.member, EX.org))
    assert run(graph, "schema_role", "probe") is True
    graph.remove((EX.r, RDF.type, https.EmployeeRole))
    graph.add((EX.r, RDF.type, EX.Other))
    assert run(graph, "schema_role", "probe") is False


def test_wikibase_statement_without_declarations_is_named_by_its_claim_predicate():
    graph = Graph()
    graph.add((EX.i, RDF.type, EX.Item))
    graph.add((EX.i, EX.claimP2, EX.st))
    graph.add((EX.st, RDF.type, WIKIBASE.Statement))
    assert run(graph, "wikibase_statement", "relations") == {(EX.Item, EX.claimP2, None, Literal(1))}
