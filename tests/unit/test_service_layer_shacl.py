"""SHACL shapes from the analytics: counts, value constraints, severity, annotations (DEC-5, AD-10)."""

import pytest
from rdflib import RDF, Graph, Literal, Namespace, URIRef
from rdflib.collection import Collection

from fingerprint.adapters.template_renderer import JinjaTemplateRenderer
from fingerprint.domain.analytics import analyse
from fingerprint.domain.views import GeneratorOptions
from fingerprint.service_layer.generators.shacl import ShaclGenerator
from tests.unit.fakes import EX, XSD, files, klass, literals, profile_run, prop, resources

SH = Namespace("http://www.w3.org/ns/shacl#")
FP = Namespace("https://data.meaningfy.ws/fingerprint/")


def shapes(run, shapes_namespace=None) -> Graph:
    options = GeneratorOptions(shapes_namespace=shapes_namespace)
    texts = files(ShaclGenerator(analyse(run), JinjaTemplateRenderer(), options=options).serialize())
    (text,) = texts.values()
    return Graph().parse(data=text, format="turtle")


def node_shape(g: Graph, cls: str):
    (shape,) = g.subjects(SH.targetClass, URIRef(cls))
    return shape


def property_shape(g: Graph, cls: str, path: str):
    for ps in g.objects(node_shape(g, cls), SH.property):
        if g.value(ps, SH.path) == URIRef(path):
            return ps
    raise AssertionError(f"no property shape for {path}")


def person(*props, instances=4, **kwargs):
    return profile_run(klass(EX + "Person", instances, *props, **kwargs))


@pytest.mark.parametrize(
    "bins, min_count, max_count",
    [
        ({1: 4}, 1, 1),
        ({1: 2}, None, 1),
        ({1: 2, 3: 2}, 1, None),
        ({1: 1, 3: 1}, None, None),
        ({3: 4}, 3, 3),
    ],
)
def test_counts_follow_the_accepted_label(bins, min_count, max_count):
    g = shapes(person(prop(EX + "name", bins, literals(4))))
    ps = property_shape(g, EX + "Person", EX + "name")
    assert g.value(ps, SH.minCount) == (None if min_count is None else Literal(min_count))
    assert g.value(ps, SH.maxCount) == (None if max_count is None else Literal(max_count))


def test_one_datatype_is_a_datatype_and_literal_constraint():
    g = shapes(person(prop(EX + "name", {1: 4}, literals(4))))
    ps = property_shape(g, EX + "Person", EX + "name")
    assert g.value(ps, SH.datatype) == URIRef(XSD + "string") and g.value(ps, SH.nodeKind) == SH.Literal


def test_one_class_is_a_class_and_iri_constraint():
    g = shapes(person(prop(EX + "livesIn", {1: 4}, resources(4, EX + "City"))))
    ps = property_shape(g, EX + "Person", EX + "livesIn")
    assert g.value(ps, SH["class"]) == URIRef(EX + "City") and g.value(ps, SH.nodeKind) == SH.IRI


def test_untyped_objects_allow_any_resource_and_no_class():
    g = shapes(person(prop(EX + "knows", {1: 4}, resources(2, EX + "Person"), resources(2))))
    ps = property_shape(g, EX + "Person", EX + "knows")
    assert g.value(ps, SH["class"]) is None and g.value(ps, SH.nodeKind) == SH.IRI


def test_mixed_values_are_an_or_of_alternatives():
    g = shapes(person(prop(EX + "v", {1: 4}, literals(2, XSD + "integer"), resources(2, EX + "City"))))
    ps = property_shape(g, EX + "Person", EX + "v")
    alternatives = list(Collection(g, g.value(ps, SH["or"])))
    assert {(g.value(a, SH.datatype), g.value(a, SH["class"])) for a in alternatives} == {
        (URIRef(XSD + "integer"), None),
        (None, URIRef(EX + "City")),
    }


def test_a_language_tagged_literal_without_datatype_is_a_lang_string():
    g = shapes(person(prop(EX + "label", {1: 4}, literals(4, datatype=None, language="ro"))))
    ps = property_shape(g, EX + "Person", EX + "label")
    assert g.value(ps, SH.datatype) == RDF.langString


@pytest.mark.parametrize(
    "props, kwargs, severity",
    [
        ((prop(EX + "p", presence_only=True),), {}, SH.Info),
        ((prop(EX + "p", {1: 1}, literals(1)),), {}, SH.Info),  # confidence 0.25 < 0.8
        ((prop(EX + "p", {1: 9, 2: 1}, literals(11)),), {"instances": 10}, SH.Warning),  # support 0.9
        ((prop(EX + "p", {1: 4}, literals(4)),), {"instances": 10, "observed": 4}, SH.Warning),  # first-N
        ((prop(EX + "p", {1: 4}, literals(4)),), {}, None),
    ],
)
def test_severity_follows_what_the_profile_knows(props, kwargs, severity):
    run = profile_run(klass(EX + "Person", kwargs.pop("instances", 4), *props, **kwargs), acceptance_threshold=0.8)
    g = shapes(run)
    assert g.value(property_shape(g, EX + "Person", EX + "p"), SH.severity) == severity


def test_a_class_with_declared_subclasses_is_at_most_warning():
    run = profile_run(klass(EX + "Agent", 4, prop(EX + "p", {1: 4}, literals(4))), edges=[(EX + "Person", EX + "Agent")])
    g = shapes(run)
    assert g.value(property_shape(g, EX + "Agent", EX + "p"), SH.severity) == SH.Warning


def test_class_constraints_under_cross_graph_types_are_at_most_warning():
    run = profile_run(
        klass(EX + "Person", 4, prop(EX + "livesIn", {1: 4}, resources(4, EX + "City"))), object_type_scope="any_graph"
    )
    g = shapes(run)
    assert g.value(property_shape(g, EX + "Person", EX + "livesIn"), SH.severity) == SH.Warning


def test_a_sampled_class_is_annotated():
    g = shapes(person(prop(EX + "p", {1: 10}, literals(10)), instances=50, observed=10))
    shape = node_shape(g, EX + "Person")
    assert (g.value(shape, FP.instances), g.value(shape, FP.observedInstances)) == (Literal(50), Literal(10))
    assert g.value(shape, FP.precisionMode) == Literal("first_n")


def test_shapes_are_open_and_named_under_the_given_namespace():
    g = shapes(person(prop(EX + "p", {1: 4}, literals(4))), shapes_namespace="https://shapes.ex/")
    shape = node_shape(g, EX + "Person")
    assert str(shape) == "https://shapes.ex/ex-Person"
    assert (shape, RDF.type, SH.NodeShape) in g and g.value(shape, SH.closed) is None
    assert str(property_shape(g, EX + "Person", EX + "p")) == "https://shapes.ex/ex-Person-ex-p"


def test_shapes_are_named_after_the_class_namespace_by_default():
    run = profile_run(
        klass("http://ex.org/a#Thing", 1), klass("http://ex.org/a/Thing", 1, prop(EX + "p", {1: 1}, literals(1)))
    )
    g = shapes(run)
    assert str(node_shape(g, "http://ex.org/a#Thing")) == "http://ex.org/a/shape/Thing"
    assert str(node_shape(g, "http://ex.org/a/Thing")) == "http://ex.org/a/shape/Thing-2"
    assert str(property_shape(g, "http://ex.org/a/Thing", EX + "p")) == "http://ex.org/a/shape/Thing-ex-p"
    assert (property_shape(g, "http://ex.org/a/Thing", EX + "p"), RDF.type, SH.PropertyShape) in g


def test_unusual_iris_stay_valid_turtle():
    run = profile_run(klass("http://ex.org/q?a=1&b='x'", 4, prop("http://ex.org/ș/ü", {1: 4}, literals(4))))
    g = shapes(run)
    assert property_shape(g, "http://ex.org/q?a=1&b='x'", "http://ex.org/ș/ü") is not None


def test_an_unwritable_class_is_left_out():
    bad = "http://ex.org/<script>alert(1)</script> x"
    run = profile_run(klass(bad, 4), klass(EX + "Person", 4))
    generator = ShaclGenerator(analyse(run), JinjaTemplateRenderer())
    (text,) = files(generator.serialize()).values()
    assert "script" not in text and generator.skipped == [bad]


def test_one_file_per_graph():
    run = profile_run(klass(EX + "Person", 4), graph="http://ex.org/graphs/people")
    names = list(files(ShaclGenerator(analyse(run), JinjaTemplateRenderer()).serialize()))
    assert len(names) == 1 and names[0].startswith("shapes-people-") and names[0].endswith(".ttl")


def test_a_language_tagged_literal_without_datatype_conforms():
    import pyshacl

    run = person(prop(EX + "label", {1: 4}, literals(4, datatype=None, language="ro")))
    data = Graph().parse(
        data="".join(f'<{EX}p{i}> a <{EX}Person> ; <{EX}label> "x"@ro .\n' for i in range(4)), format="turtle"
    )
    _, results, _ = pyshacl.validate(data, shacl_graph=shapes(run), inference="none")
    assert not list(results.subjects(SH.resultSeverity, SH.Violation))


def test_an_unwritable_property_is_left_out():
    bad = "http://ex.org/a b"
    run = person(prop(bad, {1: 4}, literals(4)), prop(EX + "ok", {1: 4}, literals(4)))
    generator = ShaclGenerator(analyse(run), JinjaTemplateRenderer())
    g = Graph().parse(data=only_text(generator), format="turtle")
    assert generator.skipped == [bad] and property_shape(g, EX + "Person", EX + "ok") is not None
    assert len(list(g.objects(node_shape(g, EX + "Person"), SH.property))) == 1


def test_a_literal_with_neither_datatype_nor_language_is_any_literal():
    g = shapes(person(prop(EX + "p", {1: 4}, literals(4, datatype=None))))
    ps = property_shape(g, EX + "Person", EX + "p")
    assert g.value(ps, SH.nodeKind) == SH.Literal and g.value(ps, SH.datatype) is None


def test_an_unwritable_value_type_keeps_only_the_node_kind():
    generator = ShaclGenerator(
        analyse(person(prop(EX + "p", {1: 4}, literals(4, datatype="http://x/a b")))), JinjaTemplateRenderer()
    )
    g = Graph().parse(data=only_text(generator), format="turtle")
    ps = property_shape(g, EX + "Person", EX + "p")
    assert g.value(ps, SH.datatype) is None and g.value(ps, SH.nodeKind) == SH.Literal
    assert generator.skipped == ["http://x/a b"]


def test_a_class_with_no_observed_instances_has_a_shape_without_properties():
    g = shapes(profile_run(klass(EX + "Empty", 0)))
    assert not list(g.objects(node_shape(g, EX + "Empty"), SH.property))


def only_text(generator):
    (text,) = files(generator.serialize()).values()
    return text
