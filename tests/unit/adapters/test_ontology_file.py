"""Reading label and description values from an ontology file (llm-schema-tools TC-O1)."""

import shutil

import pytest

from fingerprint.adapters.exceptions import OntologyFileError
from fingerprint.adapters.ontology_file import load_ontology
from fingerprint.domain.profile import AnnotationValue
from fingerprint.domain.vocabulary import DCTERMS, RDFS, SKOS, SKOSXL

ONTOLOGY = "tests/test_data/ontology/labels"
EUVOC = "http://publications.europa.eu/ontology/euvoc#"


def value(term, predicate, text, language=None):
    return AnnotationValue(term=term, predicate=predicate, text=text, language=language)


def test_the_label_fixture_gives_the_values_of_its_nine_predicates_and_the_skosxl_path():
    values = load_ontology(f"{ONTOLOGY}.ttl")
    assert value(SKOS + "Concept", SKOS + "prefLabel", "Concept", "en") in values
    assert value(SKOS + "Concept", SKOS + "definition", "An idea or notion; a unit of thought.", "en") in values
    assert value(EUVOC + "Treaty", RDFS + "label", "Vertrag", "de") in values
    assert value(SKOSXL + "altLabel", SKOS + "altLabel", "alternative label", "en") in values
    assert value("http://example.org/Widget", SKOSXL + "prefLabel", "Widget", "en") in values
    assert max(len(v.text) for v in values if v.term == DCTERMS + "type") > 200


def test_the_rdf_xml_twin_gives_the_same_values():
    assert sorted(load_ontology(f"{ONTOLOGY}.rdf"), key=repr) == sorted(load_ontology(f"{ONTOLOGY}.ttl"), key=repr)


def test_a_file_with_an_unknown_extension_is_read_as_turtle(tmp_path):
    copy = tmp_path / "labels.unknown"
    shutil.copy(f"{ONTOLOGY}.ttl", copy)
    assert load_ontology(copy) == load_ontology(f"{ONTOLOGY}.ttl")


def test_language_tags_are_lower_cased(tmp_path):
    path = tmp_path / "o.ttl"
    path.write_text('<http://e/a> <http://www.w3.org/2000/01/rdf-schema#label> "Person"@EN .')
    assert load_ontology(path) == [value("http://e/a", RDFS + "label", "Person", "en")]


@pytest.mark.parametrize("content", [None, "this is not RDF"])
def test_a_missing_or_non_rdf_file_names_the_file(tmp_path, content):
    path = tmp_path / "o.ttl"
    if content:
        path.write_text(content)
    with pytest.raises(OntologyFileError, match=f"ontology file {path} cannot be read"):
        load_ontology(path)


def test_the_values_come_in_a_deterministic_order():
    values = load_ontology(f"{ONTOLOGY}.ttl")
    assert values == sorted(values, key=lambda v: (v.term, v.predicate, v.language or "", v.text))


def test_a_literal_skosxl_pref_label_is_not_a_label(tmp_path):
    path = tmp_path / "o.ttl"
    path.write_text(f'<http://e/a> <{SKOSXL}prefLabel> "Direct" .')
    assert load_ontology(path) == []


def test_triples_in_the_named_graphs_of_a_trig_file_count(tmp_path):
    path = tmp_path / "o.trig"
    path.write_text(f'<http://e/g> {{ <http://e/a> <{RDFS}label> "Person"@en . }}')
    assert load_ontology(path) == [value("http://e/a", RDFS + "label", "Person", "en")]
