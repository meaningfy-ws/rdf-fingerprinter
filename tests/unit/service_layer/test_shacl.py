"""SHACL shapes from the analytics: counts, value constraints, severity, annotations (DEC-5, AD-10)."""

import pytest
from rdflib import RDFS, Graph, Namespace, URIRef
from rdflib.collection import Collection

from fingerprint.adapters.template_renderer import JinjaTemplateRenderer
from fingerprint.domain.analytics import analyse
from fingerprint.domain.views import GeneratorOptions
from fingerprint.service_layer.generators.shacl import ShaclGenerator
from tests.builders import XSD, klass, literals, profile_run, prop, resources
from tests.fakes import EX, files

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


def test_one_class_is_a_class_and_iri_constraint():
    g = shapes(person(prop(EX + "livesIn", {1: 4}, resources(4, EX + "City"))))
    ps = property_shape(g, EX + "Person", EX + "livesIn")
    assert g.value(ps, SH["class"]) == URIRef(EX + "City") and g.value(ps, SH.nodeKind) == SH.IRI


def test_mixed_values_are_an_or_of_alternatives():
    g = shapes(person(prop(EX + "v", {1: 4}, literals(2, XSD + "integer"), resources(2, EX + "City"))))
    ps = property_shape(g, EX + "Person", EX + "v")
    alternatives = list(Collection(g, g.value(ps, SH["or"])))
    assert {(g.value(a, SH.datatype), g.value(a, SH["class"])) for a in alternatives} == {
        (URIRef(XSD + "integer"), None),
        (None, URIRef(EX + "City")),
    }


def test_class_constraints_under_cross_graph_types_are_at_most_warning():
    run = profile_run(
        klass(EX + "Person", 4, prop(EX + "livesIn", {1: 4}, resources(4, EX + "City"))), object_type_scope="any_graph"
    )
    g = shapes(run)
    assert g.value(property_shape(g, EX + "Person", EX + "livesIn"), SH.severity) == SH.Warning


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


def only_text(generator):
    (text,) = files(generator.serialize()).values()
    return text


# --- rules the first tests left open (lean-test-suite 7.5) ---


def configured(*props, instances=4, observed=None, **settings):
    """A Person class with `props`, profiled with these settings."""
    return profile_run(klass(EX + "Person", instances, *props, observed=observed), **settings)


def severity_of(run, prop_iri=EX + "p", cls=EX + "Person"):
    g = shapes(run)
    return g.value(property_shape(g, cls, prop_iri), SH.severity)


def test_a_property_without_a_label_has_no_value_constraints_and_is_info():
    run = configured(prop(EX + "p", {1: 2}, literals(2)), instances=0, acceptance_threshold=0)  # no label
    g = shapes(run)
    ps = property_shape(g, EX + "Person", EX + "p")
    assert g.value(ps, SH.datatype) is None and g.value(ps, SH.nodeKind) is None
    assert g.value(ps, SH.severity) == SH.Info


def test_confidence_equal_to_the_threshold_is_enough():
    assert severity_of(configured(prop(EX + "p", {1: 4}, literals(4)), acceptance_threshold=1.0)) is None


def test_the_profiles_confidence_and_support_are_annotations():
    g = shapes(configured(prop(EX + "p", {1: 9, 2: 1}, literals(11)), instances=10, acceptance_threshold=0.8))
    ps = property_shape(g, EX + "Person", EX + "p")
    assert (float(g.value(ps, FP.confidence)), float(g.value(ps, FP.labelSupport))) == (1.0, 0.9)


def test_implied_subclasses_do_not_weaken_their_parent():
    run = profile_run(
        klass(EX + "Agent", 4, prop(EX + "p", {1: 4}, literals(4))), klass(EX + "Person", 4, co_types=[(EX + "Agent", 4)])
    )
    assert severity_of(run, cls=EX + "Agent") is None


@pytest.mark.parametrize(
    "partition, scope, severity",
    [
        (literals(4), "any_graph", None),  # no sh:class written, so no cross-graph doubt
        (resources(4, EX + "City"), "same_graph", None),  # sh:class written, but the graphs are the same
        (resources(4, EX + "City"), "any_graph", SH.Warning),
        (resources(4, "http://x/a b"), "any_graph", None),  # the class cannot be written, so it is not a constraint
        (None, "any_graph", None),  # no value partitions at all
        (resources(4), "any_graph", None),  # untyped objects: no class
    ],
)
def test_only_a_written_class_constraint_is_doubtful_across_graphs(partition, scope, severity):
    partitions = [partition] if partition else []
    run = configured(prop(EX + "p", {1: 4}, *partitions), object_type_scope=scope)
    assert severity_of(run) == severity


def test_a_sampled_cross_graph_class_explains_itself_in_one_comment():
    run = configured(
        prop(EX + "p", {1: 10}, resources(10, EX + "City")), instances=50, observed=10, object_type_scope="any_graph"
    )
    g = shapes(run)
    (comment,) = g.objects(node_shape(g, EX + "Person"), RDFS.comment)
    assert str(comment) == (
        "Profiled from the first 10 of 50 instances. "
        "sh:class constraints assume the object types' graphs are part of the data graph."
    )


def test_any_literal_next_to_a_datatype_is_an_alternative():
    g = shapes(person(prop(EX + "p", {1: 4}, literals(2), literals(2, datatype=None))))
    ps = property_shape(g, EX + "Person", EX + "p")
    alternatives = list(Collection(g, g.value(ps, SH["or"])))
    assert {(g.value(a, SH.datatype), g.value(a, SH.nodeKind)) for a in alternatives} == {
        (URIRef(XSD + "string"), None),
        (None, SH.Literal),
    }


def test_any_literal_alone_is_one_node_kind_not_an_empty_or():
    g = shapes(person(prop(EX + "p", {1: 4}, literals(4, datatype=None))))
    assert g.value(property_shape(g, EX + "Person", EX + "p"), SH["or"]) is None


def test_a_node_kind_is_written_once():
    run = person(prop(EX + "p", {1: 4}, resources(4)))
    assert only_text(ShaclGenerator(analyse(run), JinjaTemplateRenderer())).count("sh:nodeKind sh:IRI") == 1


def test_the_header_names_the_graph_in_plain_characters():
    run = person(prop(EX + "p", {1: 4}, literals(4)))
    run = run.model_copy(update={"graphs": [run.graphs[0].model_copy(update={"graph": "http://g/%x"})]})
    header = only_text(ShaclGenerator(analyse(run), JinjaTemplateRenderer())).splitlines()[0]
    assert header.endswith("— http://g/_x")
