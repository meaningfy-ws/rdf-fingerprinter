"""Every output shows a class's reified relations the same way, and none when it has none (singleton-property-pattern P-11)."""

import pytest
from rdflib import RDFS, Graph, URIRef

from fingerprint.adapters.template_renderer import JinjaTemplateRenderer
from fingerprint.domain.analytics import analyse
from fingerprint.service_layer.representations import make_generator
from tests.builders import EX, klass, literals, profile_run, prop, relation
from tests.fakes import files

TEXT = "~> ex:worksFor (:ex:Org) 2 statements via singleton_property [reifiers: ex:source 1]"


def run(*reified):
    return profile_run(klass(EX + "Person", 5, prop(EX + "name", {1: 5}, literals(5)), reified=reified))


def worked():
    return run(relation(EX + "worksFor", EX + "Org", 2, (EX + "source", 1)))


def written(name, profile):
    return "\n".join(files(make_generator(name, analyse(profile), JinjaTemplateRenderer()).serialize()).values())


@pytest.mark.parametrize(
    ("name", "line"),
    [
        ("pattern", TEXT),
        ("shex", f"# {TEXT}"),
        ("puml", f"-- reified --\n  {TEXT[3:]}"),
    ],
)
def test_the_relation_is_written_as_its_notation(name, line):
    assert line in written(name, worked())


def test_shacl_notes_the_relation_on_the_node_shape_with_no_property_shape_for_it():
    graph = Graph().parse(data=written("shacl", worked()), format="turtle")
    comments = {str(o) for o in graph.objects(None, RDFS.comment)}
    assert f"Reified relation: {TEXT}" in comments
    assert not list(graph.subjects(URIRef("http://www.w3.org/ns/shacl#path"), URIRef(EX + "worksFor")))


@pytest.mark.parametrize("name", ["pattern", "shex", "shacl", "puml"])
def test_no_section_when_there_are_no_relations(name):
    assert "reif" not in written(name, run()).lower()
