"""The enriched ShExC view of a graph (llm-schema-tools P-2, P-9, design §D; TC-S1). Facts from `tests/sample_data.py`,
edge cases from `tests/builders.py` and `model_copy` (lean-test-suite DEC-4, DEC-5)."""

import pytest

from fingerprint.domain.analytics import analyse
from fingerprint.domain.patterns import pattern_view
from fingerprint.domain.prefixes import PrefixTable
from fingerprint.domain.profile import LangText, NamespacePrefix, PrefixSource, TermAnnotation
from fingerprint.domain.shex import shex_view
from fingerprint.domain.views import GeneratorOptions, PatternGraph, ShexConstraint, ShexSchema
from tests.builders import klass, literals, profile_run, prop, resources
from tests.sample_data import CONTINENTS
from tests.unit.domain.test_patterns import TABLE, sample_view

EX = "http://ex.org/"
XSD = "http://www.w3.org/2001/XMLSchema#"
A, B, C, D, E = (EX + letter for letter in "ABCDE")
P, Q = EX + "p", EX + "q"


def pattern(*classes, table=TABLE, graph=None, annotations=None, **options) -> PatternGraph:
    analysed = analyse(profile_run(*classes, graph=graph)).graphs[0]
    if annotations:
        analysed = analysed.model_copy(update={"term_annotations": annotations})
    return pattern_view(analysed, table, GeneratorOptions(**options), excluded=frozenset(), graph_label="g", slug="g")


def schema(*classes, **kwargs) -> ShexSchema:
    return shex_view(pattern(*classes, **kwargs))


def constraints(*classes, shape=0, **kwargs) -> list[ShexConstraint]:
    return schema(*classes, **kwargs).shapes[shape].constraints


def blank(property_iri, target, distinct=4, subjects=4):
    """A property reaching `distinct` blank nodes of `target`, on `subjects` subjects."""
    reached = resources(distinct, target, "blank_node").model_copy(update={"distinct_objects": distinct})
    return prop(property_iri, {1: subjects}, reached)


def one(*partitions, bins=None, instances=10) -> ShexConstraint:
    (only,) = constraints(klass(A, instances, prop(P, {1: instances} if bins is None else bins, *partitions)))
    return only


# --- the shape of a block ---


def test_a_block_is_a_shape_labelled_with_its_first_shown_member_and_commented_with_its_header():
    shape = schema(klass(B, 3, prop(P, {1: 3}, literals(3))), klass(A, 3, co_types=[(B, 3)])).shapes[0]
    assert (shape.label, shape.comment, shape.blank) == ("ex:A", "(:ex:A&ex:B) 3", None)
    assert [c.predicate for c in shape.constraints] == ["ex:p"]


def test_the_view_carries_the_graph_its_slug_the_hidden_count_and_the_skipped_iris():
    shown = schema(klass(A, 5), klass(EX + "bad iri", 5), klass(B, 1), min_instances=2)
    assert (shown.graph_label, shown.slug, shown.hidden_classes) == ("g", "g", 1)
    assert shown.skipped == [EX + "bad iri"]


# --- cardinality ---


@pytest.mark.parametrize(
    "bins, expected",
    [
        ({1: 10}, None),
        ({1: 4}, "?"),
        ({3: 10}, "{3}"),
        ({2: 5, 3: 5}, "{2,3}"),
        ({1: 2, 74: 5}, "{0,74}"),
        (None, "*"),
    ],
)
def test_the_cardinality_follows_the_smallest_and_largest_count_per_instance(bins, expected):
    partitions = literals(10)
    only = constraints(klass(A, 10, prop(P, bins, partitions) if bins is not None else prop(P, {}, partitions)))[0]
    assert only.cardinality == expected


def test_a_property_found_but_not_measured_has_no_bounds_and_stars():
    (only,) = constraints(klass(A, 10, prop(P, presence_only=True)))
    assert (only.cardinality, only.comment, only.value) == ("*", "presence", ".")


# --- values ---


def test_a_datatype_is_itself_and_untyped_objects_are_iri_or_bnode():
    assert one(literals(10)).value == "xsd:string"
    assert one(resources(10)).value == "IRI"
    assert one(resources(10, kind="blank_node")).value == "BNODE"


def test_several_alternatives_are_joined_by_or_without_duplicates():
    both = one(literals(5), resources(5), resources(5, kind="blank_node"), literals(5, XSD + "date"))
    assert both.value == "(xsd:date OR xsd:string OR IRI OR BNODE)"
    assert one(resources(5, C), resources(5, D)).value == "IRI"


def test_a_class_with_a_block_is_a_shape_reference_and_its_group_text_leads_the_comment():
    shown = schema(klass(A, 10, prop(P, {1: 10}, resources(10, B))), klass(B, 10))
    (only,) = shown.shapes[0].constraints
    assert (only.value, only.comment, only.cardinality) == ("@ex:B", "(:ex:B)", None)


def test_a_class_with_no_shape_in_the_file_is_iri():
    hidden = pattern(klass(A, 10, prop(P, {1: 10}, resources(10, B))), klass(B, 10)).model_copy(update={"nested_blocks": []})
    reduced = hidden.model_copy(update={"blocks": hidden.blocks[:1]})
    assert shex_view(reduced).shapes[0].constraints[0].value == "IRI"


def test_a_class_typed_in_another_graph_is_iri_and_names_its_graph_in_the_comment():
    other = resources(10, B).model_copy(update={"object_class_graph": "http://ex.org/g2"})
    only = one(other)
    assert (only.value, only.comment) == ("IRI", "(:ex:B @<http://ex.org/g2>)")


def test_an_edge_without_comment_parts_writes_none():
    only = one(resources(10))
    assert (only.value, only.comment) == ("IRI", None)


def test_statistics_follow_the_group_text_in_the_comment():
    only = one(resources(5, B), bins={2: 5})
    assert only.comment == "(:ex:B) 5/10 ×2"


# --- nested groups ---


def test_a_nested_group_reached_by_one_edge_is_written_inline_with_its_edges_one_level_deeper():
    shown = schema(klass(A, 4, blank(P, B)), klass(B, 4, prop(Q, {1: 4}, literals(4))))
    (open_,) = shown.shapes[0].constraints
    assert (open_.value, open_.comment, open_.cardinality, open_.depth) == ("BNODE", "(:ex:B) bn", None, 1)
    (inner,) = open_.inline
    assert (inner.predicate, inner.value, inner.depth) == ("ex:q", "xsd:string", 2)
    assert len(shown.shapes) == 1


def test_an_inline_group_without_edges_has_an_empty_body():
    (open_,) = constraints(klass(A, 4, blank(P, B)), klass(B, 4))
    assert open_.inline == []


def test_a_nested_group_reached_by_two_edges_is_one_shape_referenced_from_both():
    shown = schema(klass(A, 4, blank(P, C), blank(Q, C)), klass(C, 4, prop(EX + "r", {1: 4}, literals(4))), klass(D, 2))
    assert [(c.predicate, c.value, c.inline, c.comment) for c in shown.shapes[0].constraints] == [
        ("ex:p", "BNODE @ex:C", None, "(:ex:C) bn"),
        ("ex:q", "BNODE @ex:C", None, "(:ex:C) bn"),
    ]
    named = shown.shapes[-1]
    assert (named.label, named.blank, named.comment) == ("ex:C", True, "(:ex:C) 4")
    assert [(c.predicate, c.depth) for c in named.constraints] == [("ex:r", 1)]


def test_a_group_expanded_nowhere_is_bnode_with_a_comment_on_the_hops_and_has_no_shape():
    shown = schema(
        klass(A, 4, blank(EX + "a", B)),
        klass(B, 4, blank(EX + "b", C)),
        klass(C, 4, blank(EX + "c", D), prop(EX + "d", {1: 4}, resources(4, kind="blank_node"))),
        klass(D, 4),
    )
    (top,) = shown.shapes[0].constraints
    (second,) = top.inline
    third, bare = second.inline
    assert (third.value, third.comment, third.inline, third.depth) == ("BNODE", "(:ex:D) bn … deeper than 3 hops", None, 3)
    assert (bare.value, bare.comment) == ("BNODE", "bn")
    assert len(shown.shapes) == 1


def test_a_hidden_class_beside_a_group_expanded_nowhere_is_iri_not_bnode():
    deep = [
        klass(A, 4, blank(EX + "a", B)),
        klass(B, 4, blank(EX + "b", C)),
        klass(C, 4, prop(EX + "c", {1: 4}, resources(4, E), blank(EX + "x", D).value_partitions[0])),
        klass(D, 4),
        klass(E, 1),
    ]
    leaf = schema(*deep, min_instances=2).shapes[0].constraints[0].inline[0].inline[0]
    assert (leaf.predicate, leaf.value) == ("ex:c", "(BNODE OR IRI)")


def test_two_level_three_edges_into_a_group_expanded_nowhere_are_both_bnode():
    deep = [
        klass(A, 4, blank(EX + "a", B)),
        klass(B, 4, blank(EX + "b", C), blank(EX + "x", D)),
        klass(C, 4, blank(EX + "c", E), blank(EX + "y", E)),
        klass(D, 4),
        klass(E, 4),
    ]
    shown = schema(*deep)
    assert [s.label for s in shown.shapes] == ["ex:A"]
    leaves = [c for outer in shown.shapes[0].constraints for c in outer.inline[0].inline or []]
    assert {c.value for c in leaves if c.predicate in {"ex:c", "ex:y"}} == {"BNODE"}


def test_an_edge_into_two_nested_groups_inlines_the_first_and_merges_the_other_into_bnode():
    both = prop(P, {1: 4}, *(resources(4, t, "blank_node").model_copy(update={"distinct_objects": 4}) for t in (B, C)))
    (only,) = constraints(klass(A, 4, both), klass(B, 4, prop(Q, {1: 4}, literals(4))), klass(C, 4))
    assert (only.value, only.comment, [c.predicate for c in only.inline]) == (
        "BNODE",
        "(:ex:B|ex:C) bn … deeper than 3 hops",
        ["ex:q"],
    )


def test_an_inline_group_beside_other_alternatives_follows_them_without_parentheses():
    mixed = prop(P, {1: 4}, literals(4), resources(4, B, "blank_node").model_copy(update={"distinct_objects": 4}))
    (only,) = constraints(klass(A, 4, mixed), klass(B, 4))
    assert (only.value, only.inline) == ("xsd:string OR BNODE", [])


# --- IRIs PyShExC rejects ---


BAD = EX + "q?a=1&b='x'"


def test_a_block_whose_class_holds_an_equals_sign_is_left_out_and_listed():
    shown = schema(klass(A, 2), klass(BAD, 2))
    assert [s.label for s in shown.shapes] == ["ex:A"]
    assert shown.skipped_terms == [BAD]


def test_a_group_with_a_member_that_holds_an_equals_sign_is_labelled_with_its_first_writable_member():
    odd = EX + "Aa=1"  # sorts before ex:B
    shown = schema(
        klass(B, 3, prop(P, {1: 3}, literals(3))),
        klass(odd, 3, co_types=[(B, 3)]),
        klass(C, 3, prop(Q, {1: 3}, resources(3, B))),
    )
    assert [s.label for s in shown.shapes] == ["ex:B", "ex:C"]
    assert shown.shapes[0].comment.startswith("(:<http://ex.org/Aa=1>&ex:B)")
    assert [c.value for c in shown.shapes[1].constraints] == ["@ex:B"]
    assert shown.skipped_terms == [odd]


def test_a_property_that_holds_an_equals_sign_is_left_out_and_listed():
    shown = schema(klass(A, 2, prop(BAD, {1: 2}, literals(2)), prop(P, {1: 2}, literals(2))))
    assert ([c.predicate for c in shown.shapes[0].constraints], shown.skipped_terms) == (["ex:p"], [BAD])


def test_a_datatype_that_holds_an_equals_sign_is_left_out_of_the_value():
    (only,) = constraints(klass(A, 2, prop(P, {1: 2}, literals(2, XSD + "a=b"), resources(2))))
    assert only.value == "IRI"
    assert schema(klass(A, 2, prop(P, {1: 2}, literals(2, XSD + "a=b")))).skipped_terms == [XSD + "a=b"]


def test_a_datatype_left_out_leaves_the_unknown_target_when_nothing_else_remains():
    (only,) = constraints(klass(A, 2, prop(P, {1: 2}, literals(2, XSD + "a=b"))))
    assert only.value == "."


def test_a_target_class_that_holds_an_equals_sign_has_no_shape_to_refer_to():
    (only,) = constraints(klass(A, 2, prop(P, {1: 2}, resources(2, BAD))), klass(BAD, 2))
    assert only.value == "IRI"


def test_a_nested_group_that_holds_an_equals_sign_is_plain_bnode():
    nested = [klass(A, 4, blank(P, BAD)), klass(BAD, 4, prop(Q, {1: 4}, literals(4)))]
    shown = schema(*nested)
    (only,) = shown.shapes[0].constraints
    assert (only.value, only.inline, shown.skipped_terms) == ("BNODE", None, [BAD])
    twice = schema(klass(A, 4, blank(P, BAD), blank(Q, BAD)), klass(BAD, 4))
    assert [s.label for s in twice.shapes] == ["ex:A"]
    assert [c.value for c in twice.shapes[0].constraints] == ["BNODE", "BNODE"]


def test_a_prefix_whose_namespace_holds_an_equals_sign_is_not_declared():
    table = PrefixTable(
        [NamespacePrefix(prefix="ex", namespace=EX, source=PrefixSource.packaged)]
        + [NamespacePrefix(prefix="q", namespace=EX + "q?a=", source=PrefixSource.packaged)]
    )
    shown = schema(klass(A, 2), klass(EX + "q?a=1", 2), table=table)
    assert [p.prefix for p in shown.prefixes] == ["ex"]
    assert shown.skipped_terms == [EX + "q?a=1"]


# --- glossary and prefixes ---


def test_the_prefixes_are_the_pattern_views():
    pat = pattern(klass(A, 2, prop(P, {1: 2}, literals(2))))
    assert shex_view(pat).prefixes == pat.prefixes


def test_the_glossary_is_none_or_the_pattern_s_lines():
    assert schema(klass(A, 2)).glossary == ["glossary: none"]
    note = TermAnnotation(term=A, labels=[LangText(text="Thing", language="en")])
    assert schema(klass(A, 2), annotations=[note]).glossary == ["glossary", 'ex:A "Thing"@en']


def test_the_sample_continents_in_shex_skip_nothing_and_have_three_shapes(sample_analytics):
    shown = shex_view(sample_view(sample_analytics, CONTINENTS))
    assert ([s.label for s in shown.shapes][1], len(shown.shapes), shown.skipped_terms) == ("skos:ConceptScheme", 3, [])
