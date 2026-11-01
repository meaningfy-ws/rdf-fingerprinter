"""Each packaged pitfall check finds its pitfall, and only it (pitfall-scans › The packaged catalogue).

One positive and one negative Turtle snippet per check, and the entity the positive one must name. The checks run
directly with rdflib on the snippet; the wrapping for an endpoint is tested in test_service_layer_pitfall_scan.py.
"""

import pytest
from rdflib import Graph, URIRef

from fingerprint.adapters.pitfall_catalogue import packaged_checks

P = """@prefix ex: <http://ex.org/> . @prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> . @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix dcterms: <http://purl.org/dc/terms/> .
"""
EX = "http://ex.org/"
OWL = "http://www.w3.org/2002/07/owl#"

# id: (positive, negative, expected entity)
FIXTURES = {
    "p04_unconnected_class": ("ex:Lonely a owl:Class .", "ex:A a owl:Class . ex:B a owl:Class ; rdfs:subClassOf ex:A .", EX + "Lonely"),
    "p05_wrong_inverse": (
        "ex:p owl:inverseOf ex:q ; rdfs:domain ex:A ; rdfs:range ex:B . ex:q rdfs:domain ex:C ; rdfs:range ex:A .",
        "ex:p owl:inverseOf ex:q ; rdfs:domain ex:A ; rdfs:range ex:B . ex:q rdfs:domain ex:B ; rdfs:range ex:A .",
        EX + "p",
    ),
    "p06_class_cycle": ("ex:A rdfs:subClassOf ex:B . ex:B rdfs:subClassOf ex:A .", "ex:A rdfs:subClassOf ex:B .", EX + "A"),
    "p07_merged_concepts": ("ex:CatsAndDogs a owl:Class .", "ex:Cat a owl:Class .", EX + "CatsAndDogs"),
    "p08_missing_comment": ("ex:A a owl:Class .", 'ex:A a owl:Class ; rdfs:comment "c" .', EX + "A"),
    "p10_no_disjointness": ("ex:o a owl:Ontology .", "ex:o a owl:Ontology . ex:A owl:disjointWith ex:B .", EX + "o"),
    "p11_missing_domain_or_range": (
        "ex:p a owl:ObjectProperty ; rdfs:domain ex:A .",
        "ex:p a owl:ObjectProperty ; rdfs:domain ex:A ; rdfs:range ex:B .",
        EX + "p",
    ),
    "p12_p30_same_name_not_equivalent": (
        "ex:Person a owl:Class . <http://other.org/Person> a owl:Class .",
        "ex:Person a owl:Class ; owl:equivalentClass <http://other.org/Person> . <http://other.org/Person> a owl:Class .",
        EX + "Person",
    ),
    "p13_missing_inverse": (
        "ex:p a owl:ObjectProperty .",
        "ex:p a owl:ObjectProperty ; owl:inverseOf ex:q . ex:q a owl:ObjectProperty .",
        EX + "p",
    ),
    "p19_multiple_domains_or_ranges": ("ex:p rdfs:domain ex:A, ex:B .", "ex:p rdfs:domain ex:A .", EX + "p"),
    "p20_label_longer_than_comment": (
        'ex:A rdfs:label "A long label"@en ; rdfs:comment "short"@en .',
        'ex:A rdfs:label "A"@en ; rdfs:comment "A longer comment"@en .',
        EX + "A",
    ),
    "p21_miscellaneous_class": ("ex:OtherThings a owl:Class .", "ex:Thing a owl:Class .", EX + "OtherThings"),
    "p22_class_naming": ("ex:thing a owl:Class .", "ex:Thing a owl:Class .", EX + "thing"),
    "p24_recursive_definition": ("ex:A rdfs:subClassOf ex:A .", "ex:A rdfs:subClassOf ex:B .", EX + "A"),
    "p25_inverse_of_itself": ("ex:p owl:inverseOf ex:p .", "ex:p owl:inverseOf ex:q .", EX + "p"),
    "p26_inverse_of_symmetric": ("ex:p a owl:SymmetricProperty ; owl:inverseOf ex:q .", "ex:p a owl:SymmetricProperty .", EX + "p"),
    "p27_wrong_equivalent_properties": (
        "ex:p owl:equivalentProperty ex:q ; rdfs:domain ex:A . ex:q rdfs:domain ex:B .",
        "ex:p owl:equivalentProperty ex:q ; rdfs:domain ex:A . ex:q rdfs:domain ex:A .",
        EX + "p",
    ),
    "p28_p29_wrong_symmetric_or_transitive": (
        "ex:p a owl:SymmetricProperty ; rdfs:domain ex:A ; rdfs:range ex:B .",
        "ex:p a owl:SymmetricProperty ; rdfs:domain ex:A ; rdfs:range ex:A .",
        EX + "p",
    ),
    "p32_classes_same_label": (
        'ex:A a owl:Class ; rdfs:label "Thing"@en . ex:B a owl:Class ; rdfs:label "thing"@en .',
        'ex:A a owl:Class ; rdfs:label "Thing"@en . ex:B a owl:Class ; rdfs:label "Other"@en .',
        EX + "A",
    ),
    "p33_single_property_chain": ("ex:p owl:propertyChainAxiom ( ex:q ) .", "ex:p owl:propertyChainAxiom ( ex:q ex:r ) .", EX + "p"),
    "p34_untyped_class": ("ex:x a ex:Undeclared .", "ex:x a ex:Declared . ex:Declared a owl:Class .", EX + "Undeclared"),
    "p35_untyped_property": ("ex:x ex:undeclared ex:y .", "ex:x ex:declared ex:y . ex:declared a owl:ObjectProperty .", EX + "undeclared"),
    "p36_iri_with_file_extension": ("<http://ex.org/onto.owl> a owl:Ontology .", "<http://ex.org/onto> a owl:Ontology .", EX + "onto.owl"),
    "p38_no_ontology_declaration": ("ex:A a owl:Class .", "ex:o a owl:Ontology .", OWL + "Ontology"),
    "p41_no_license": ("ex:o a owl:Ontology .", "ex:o a owl:Ontology ; dcterms:license <http://x.org/l> .", EX + "o"),
    "x_punning_class_and_property": ("ex:C a owl:Class . ex:i a ex:C . ex:s ex:C ex:o .", "ex:i a ex:C .", EX + "C"),
    "x_individual_as_predicate": (
        "ex:r a ex:Rel . ex:s ex:r ex:o .",
        "ex:r a owl:ObjectProperty . ex:s ex:r ex:o .",
        EX + "r",
    ),
    "x_domain_violation": ("ex:p rdfs:domain ex:A . ex:s ex:p ex:o .", "ex:p rdfs:domain ex:A . ex:s ex:p ex:o ; a ex:A .", EX + "p"),
    "x_range_violation": (
        "ex:p a owl:ObjectProperty ; rdfs:range ex:B . ex:s ex:p ex:o .",
        "ex:p a owl:ObjectProperty ; rdfs:range ex:B . ex:s ex:p ex:o . ex:o a ex:B .",
        EX + "p",
    ),
}
CHECKS = {c.check_id: c for c in packaged_checks()}


def rows(check_id, turtle):
    return list(Graph().parse(data=P + turtle, format="turtle").query(CHECKS[check_id].query))


def test_every_packaged_check_has_a_fixture():
    assert sorted(FIXTURES) == sorted(CHECKS)


@pytest.mark.parametrize("check_id", sorted(FIXTURES))
def test_the_check_finds_its_pitfall_and_only_it(check_id):
    positive, negative, entity = FIXTURES[check_id]
    found = rows(check_id, positive)
    assert URIRef(entity) in {r[0] for r in found}, found
    assert rows(check_id, negative) == []
