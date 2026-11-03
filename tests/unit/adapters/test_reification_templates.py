"""The packaged reification templates run in rdflib over the reification sample (singleton-property-pattern §A, §C)."""

from pathlib import Path

import pytest
from rdflib import RDF, BNode, Dataset, Graph, Literal, Namespace, URIRef
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
        (EX.Person, EX.Procedure, None, Literal(2)),
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
    "resource_as_predicate": {EX.rel1, EX.rel2, EX.Link, EX.performs1, EX.performs2, EX.performs3, EX.Procedure},
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
    "blank_nary": None,
    "structured_value": None,
}


@pytest.mark.parametrize("kind", list(HIDDEN))
def test_hidden_terms_of_the_sample(sample, kind):
    if (
        HIDDEN[kind] is None
    ):  # blank_nary and structured_value hide nothing: untyped nodes are not in the ordinary profile (P-20)
        assert TEMPLATES[kind].hidden is None
    else:
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


def test_blank_nary_and_structured_value_name_the_linking_predicate_and_list_the_node_properties(sample):
    assert run(sample, "blank_nary", "relations") == {(EX.Project, EX.role, None, Literal(1))}
    assert run(sample, "blank_nary", "reifier-properties") == {
        (EX.Project, EX.role, None, EX.agent, Literal(1)),
        (EX.Project, EX.role, None, EX.since, Literal(1)),
    }
    assert run(sample, "structured_value", "relations") == {(EX.Building, EX.height, None, Literal(1))}
    assert run(sample, "structured_value", "reifier-properties") == {(EX.Building, EX.height, None, EX.unit, Literal(1))}


def blank_node_graph(build):
    """A graph with ex:s a ex:A, and `build(graph, node)` describing the blank node ex:s ex:p points to."""
    graph = Graph()
    node = BNode()
    graph.add((EX.s, RDF.type, EX.A))
    graph.add((EX.s, EX.p, node))
    build(graph, node)
    return graph


def untyped(graph, node):
    graph.add((node, EX.agent, EX.x))


def typed(graph, node):
    graph.add((node, RDF.type, EX.Address))
    graph.add((node, EX.agent, EX.x))


def a_list(graph, node):
    graph.add((node, RDF.first, EX.x))
    graph.add((node, RDF.rest, RDF.nil))


def owl_restriction(graph, node):
    graph.add((node, OWL.onProperty, EX.q))
    graph.add((node, EX.agent, EX.x))


def shacl_construct(graph, node):
    graph.add((node, URIRef("http://www.w3.org/ns/shacl#path"), EX.q))


def statement(graph, node):
    graph.add((node, RDF.subject, EX.a))
    graph.add((node, EX.agent, EX.x))


def value_node(graph, node):
    graph.add((node, RDF.value, Literal(1)))


def twice_referenced(graph, node):
    untyped(graph, node)
    graph.add((EX.s, EX.p2, node))


def other_subject(graph, node):
    untyped(graph, node)
    graph.add((EX.s2, EX.p, node))


def no_properties(graph, node):
    graph.add((EX.s, EX.q, EX.x))  # the blank node stays a bare object; adding nothing about it


@pytest.mark.parametrize(
    "build",
    [typed, a_list, owl_restriction, shacl_construct, statement, value_node, twice_referenced, other_subject, no_properties],
)
def test_blank_nary_leaves_every_other_blank_node_alone(build):
    graph = blank_node_graph(build)
    assert run(graph, "blank_nary", "probe") is False
    assert run(graph, "blank_nary", "relations") == set()


def test_blank_nary_matches_an_untyped_node_referenced_once():
    graph = blank_node_graph(untyped)
    assert run(graph, "blank_nary", "probe") is True
    assert run(graph, "blank_nary", "relations") == {(EX.A, EX.p, None, Literal(1))}


def test_a_typed_value_node_is_no_structured_value_and_its_class_stays():
    graph = Graph()
    graph.add((EX.s, RDF.type, EX.A))
    graph.add((EX.s, EX.code, EX.n1))
    graph.add((EX.n1, RDF.value, Literal(1)))
    graph.add((EX.n1, RDF.type, EX.Notation))
    assert run(graph, "structured_value", "probe") is False
    assert run(graph, "structured_value", "relations") == set()
    assert TEMPLATES["structured_value"].hidden is None


# --- review fixes: both renderings, untyped objects, owned nodes, property-type vocabularies, claim predicates ---

NAMED = str(EX.reifications)


def run_both(turtle, kind, section):
    """The rows of a section rendered for the default graph and for a named graph (P-16); they must agree."""
    prefixes = (
        "@prefix ex: <http://example.org/> . @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> . "
        "@prefix prov: <http://www.w3.org/ns/prov#> . @prefix dcat: <http://www.w3.org/ns/dcat#> . "
        "@prefix dct: <http://purl.org/dc/terms/> . @prefix qb: <http://purl.org/linked-data/cube#> . "
        "@prefix wikibase: <http://wikiba.se/ontology#> . @prefix crm: <http://www.cidoc-crm.org/cidoc-crm/> . "
        "@prefix owl: <http://www.w3.org/2002/07/owl#> . @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> . "
    )
    default = Dataset()
    default.parse(data=prefixes + turtle, format="turtle")
    named = Dataset()
    named.graph(EX.reifications).parse(data=prefixes + turtle, format="turtle")
    template = TEMPLATES[kind]
    answers = []
    for dataset, graph in ((default, None), (named, NAMED)):
        result = dataset.query(reification_query(template, section, graph))
        answers.append(result.askAnswer if section == "probe" else {tuple(row) for row in result})
    assert answers[0] == answers[1]
    return answers[0]


@pytest.mark.parametrize(
    ("kind", "section"),
    [
        (t.id, s)
        for t in TEMPLATES.values()
        for s in ("relations", "reifier-properties", "hidden", "count")
        if getattr(t, s.replace("-", "_"))
    ],
)
def test_a_section_gives_the_same_rows_in_the_default_graph_and_in_a_named_graph(sample, kind, section):
    template = TEMPLATES[kind]
    default = {tuple(r) for r in sample.query(reification_query(template, section, None))}
    named = {tuple(r) for r in sample.query(reification_query(template, section, NAMED))}
    assert default == named


def test_resource_as_predicate_counts_statements_with_a_literal_or_untyped_object_in_the_sample(sample):
    named = {tuple(r) for r in sample.query(reification_query(TEMPLATES["resource_as_predicate"], "relations", NAMED))}
    assert (EX.Person, EX.Procedure, None, Literal(2)) in named
    assert (EX.Person, EX.Procedure, EX.Org, Literal(1)) in named


UNTYPED_OBJECTS = "ex:a a ex:A ; ex:rel1 ex:untyped ; ex:rel2 'text' . ex:rel1 a ex:Link . ex:rel2 a ex:Link ."


def test_resource_as_predicate_counts_untyped_and_literal_objects_in_both_renderings():
    assert run_both(UNTYPED_OBJECTS, "resource_as_predicate", "relations") == {(EX.A, EX.Link, None, Literal(2))}
    reifiers = run_both(UNTYPED_OBJECTS + " ex:rel1 ex:note 'x' .", "resource_as_predicate", "reifier-properties")
    assert (EX.A, EX.Link, None, EX.note, Literal(1)) in reifiers


UNTYPED_QUALIFIED = "ex:run a ex:Run ; prov:qualifiedAssociation [ prov:agent ex:t ; prov:hadRole ex:r ] ."


def test_an_untyped_qualified_node_is_one_relation_of_prov_and_none_of_blank_nary():
    assert run_both(UNTYPED_QUALIFIED, "prov_qualified", "relations") == {
        (EX.Run, PROV.qualifiedAssociation, None, Literal(1))
    }
    assert run_both(UNTYPED_QUALIFIED, "blank_nary", "probe") is False
    assert run_both(UNTYPED_QUALIFIED, "blank_nary", "relations") == set()


def test_an_untyped_dcat_qualified_node_is_one_relation_of_dcat_and_none_of_blank_nary():
    turtle = "ex:ds a ex:Dataset ; dcat:qualifiedRelation [ dct:relation ex:ds2 ; dcat:hadRole ex:x ] ."
    assert run_both(turtle, "dcat_qualified", "relations") == {(EX.Dataset, DCAT.qualifiedRelation, None, Literal(1))}
    assert run_both(turtle, "blank_nary", "probe") is False


def test_a_blank_node_with_the_crm_domain_and_range_is_left_to_cidoc():
    turtle = "ex:e a ex:Event . ex:e ex:p [ crm:P01_has_domain ex:e ; crm:P02_has_range ex:x ; ex:note 'n' ] ."
    assert run_both(turtle, "blank_nary", "probe") is False


QB = (
    "ex:refArea a rdf:Property, qb:DimensionProperty . ex:measure a qb:MeasureProperty . "
    "ex:CustomProperty rdfs:subClassOf owl:ObjectProperty . ex:linked a ex:CustomProperty . "
    "ex:obs a qb:Observation ; ex:refArea ex:BE ; ex:measure 1 ; ex:linked ex:BE . ex:BE a ex:Area ."
)


@pytest.mark.parametrize("section", ["probe", "relations", "reifier-properties", "hidden"])
def test_property_types_of_standard_vocabularies_make_no_resource_as_predicate(section):
    assert run_both(QB, "resource_as_predicate", section) in (False, set())


def test_a_type_that_is_not_a_property_type_still_makes_a_resource_as_predicate_next_to_qb_properties():
    turtle = QB + " ex:a a ex:A ; ex:rel1 ex:BE . ex:rel1 a ex:Link ."
    assert run_both(turtle, "resource_as_predicate", "relations") == {(EX.A, EX.Link, EX.Area, Literal(1))}
    assert run_both(turtle, "resource_as_predicate", "hidden") == {(EX.rel1,), (EX.Link,)}


CLAIMS = (
    "ex:i a ex:Item ; ex:claimP1 ex:st ; ex:claimP2 ex:st2 ; ex:claimP2 'plain' . "
    "ex:st a wikibase:Statement . ex:st2 a wikibase:Statement ."
)


def test_a_claim_predicate_is_hidden_only_when_every_use_points_to_a_statement():
    assert run_both(CLAIMS, "wikibase_statement", "hidden") == {(EX.claimP1,), (WIKIBASE.Statement,)}
