"""PlantUML class diagrams from the analytics (DEC-6): classes, attributes, associations, generalisations."""

import re

from fingerprint.adapters.template_renderer import JinjaTemplateRenderer
from fingerprint.domain.analytics import analyse
from fingerprint.service_layer.generators.plantuml import PlantumlGenerator
from tests.unit.fakes import EX, XSD, files, klass, literals, profile_run, prop, resources

PREFIXES = {"ex": EX, "xsd": XSD}


def diagram(run):
    generator = PlantumlGenerator(analyse(run), JinjaTemplateRenderer(prefixes=PREFIXES))
    (text,) = files(generator.serialize()).values()
    return text, generator


def aliases(text):
    return dict(re.findall(r'class "([^"]+)" as (\w+)', text))


def test_one_diagram_per_graph_between_start_and_end():
    text, _ = diagram(profile_run(klass(EX + "Person", 4)))
    assert text.count("@startuml") == 1 and text.count("@enduml") == 1 and text.strip().endswith("@enduml")


def test_class_with_an_attribute_and_an_implied_parent():
    run = profile_run(klass(EX + "Person", 4, prop(EX + "name", {1: 4}, literals(4)), co_types=[(EX + "Agent", 4)]))
    text, _ = diagram(run)
    names = aliases(text)
    assert list(names).count("ex:Person") == 1
    assert "ex:name : xsd:string [1]" in text
    assert f"{names['ex:Person']} ..|> {names['ex:Agent']}" in text


def test_declared_parent_is_a_solid_generalisation():
    run = profile_run(klass(EX + "Person", 4), klass(EX + "Agent", 4), edges=[(EX + "Person", EX + "Agent")])
    text, _ = diagram(run)
    names = aliases(text)
    assert f"{names['ex:Person']} --|> {names['ex:Agent']}" in text


def test_object_property_to_one_profiled_class_is_an_association():
    run = profile_run(
        klass(EX + "Person", 4, prop(EX + "livesIn", {1: 2}, resources(2, EX + "City"))),
        klass(EX + "City", 2),
    )
    text, _ = diagram(run)
    names = aliases(text)
    assert f'{names["ex:Person"]} --> "0..1" {names["ex:City"]} : ex:livesIn' in text
    assert "ex:livesIn :" not in text


def test_object_property_to_untyped_objects_stays_an_attribute():
    text, _ = diagram(profile_run(klass(EX + "Person", 4, prop(EX + "knows", {2: 4}, resources(8)))))
    assert "ex:knows : resource [2]" in text


def test_inherited_properties_are_not_repeated():
    run = profile_run(
        klass(EX + "Agent", 4, prop(EX + "name", {1: 4}, literals(4))),
        klass(EX + "Person", 4, prop(EX + "name", {1: 4}, literals(4))),
        edges=[(EX + "Person", EX + "Agent")],
    )
    text, _ = diagram(run)
    assert text.count("ex:name : xsd:string [1]") == 1


def test_unusual_and_unwritable_iris():
    bad = "http://ex.org/<script> x"
    run = profile_run(klass("http://ex.org/q?a=1&b='x'", 4, prop("http://ex.org/ș/ü", {1: 4}, literals(4))), klass(bad, 1))
    text, generator = diagram(run)
    assert len(aliases(text)) == 1 and "script" not in text and generator.skipped == [bad]


def test_an_unwritable_value_type_never_reaches_the_diagram():
    evil = "http://x/a\n}\n!include /etc/hostname\nclass X {"
    run = profile_run(klass(EX + "Person", 4, prop(EX + "p", {1: 4}, literals(4, datatype=evil))))
    text, generator = diagram(run)
    assert "!include" not in text and evil in generator.skipped
    assert "ex:p : value [1]" in text


def test_a_graph_label_is_plain_text_in_the_title():
    run = profile_run(klass(EX + "Person", 4), graph='http://g/%getenv("HOME")\n!include x')
    text, _ = diagram(run)
    (title,) = [line for line in text.splitlines() if line.startswith("title ")]
    assert "%" not in title and '"' not in title and "!include" not in text
