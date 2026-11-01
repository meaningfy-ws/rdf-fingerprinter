"""The pattern view of a graph (llm-schema-tools P-2..P-5, rules §B). Facts from `tests/sample_data.py`, edge cases from
`tests/builders.py` and `model_copy` (lean-test-suite DEC-4, DEC-5)."""

import pytest

from fingerprint.domain.analytics import analyse
from fingerprint.domain.prefixes import PrefixTable
from fingerprint.domain.profile import NamespacePrefix, PrefixSource, ValueCount
from fingerprint.domain.views import GeneratorOptions, PatternBlock, PatternEdge, PatternGraph, TargetKind
from tests.builders import klass, literals, profile_run, prop, resources
from tests.sample_data import CONTINENTS, TREATIES, DatasetFacts

EX = "http://ex.org/"
XSD = "http://www.w3.org/2001/XMLSchema#"
RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
LANG_STRING = RDF + "langString"
A, B, C, D = (EX + letter for letter in "ABCD")
P, Q = EX + "p", EX + "q"


def _entry(prefix: str, namespace: str) -> NamespacePrefix:
    return NamespacePrefix(prefix=prefix, namespace=namespace, source=PrefixSource.packaged)


META_NS = EX + "meta/"
TABLE = PrefixTable(
    [_entry("ex", EX), _entry("xsd", XSD), _entry("rdf", RDF), _entry("exs", EX + "status/"), _entry("meta", META_NS)]
)
NOT_EXCLUDED: frozenset[str] = frozenset()


def view(*classes, table=TABLE, excluded=NOT_EXCLUDED, annotations=None, graph=None, **options) -> PatternGraph:
    from fingerprint.domain.patterns import pattern_view

    analysed = analyse(profile_run(*classes, graph=graph)).graphs[0]
    if annotations:
        analysed = analysed.model_copy(update={"term_annotations": annotations})
    return pattern_view(analysed, table, GeneratorOptions(**options), excluded=excluded, graph_label="g", slug="g")


def block(graph: PatternGraph, name: str) -> PatternBlock:
    return next(b for b in graph.blocks if b.name == name)


def edge_of(single: PatternGraph, name: str = "ex:p") -> PatternEdge:
    return next(e for e in single.blocks[0].edges if e.name == name)


def one_edge(*partitions, bins=None, instances=10, **fields) -> PatternEdge:
    """The edge of property `ex:p` of a class `ex:A` with `instances` instances."""
    histogram = {1: instances} if bins is None else bins
    return edge_of(view(klass(A, instances, prop(P, histogram, *partitions).model_copy(update=fields))))


# --- the sample profile: the named facts ---


def named(iri: str) -> str:
    return TABLE_OF_SAMPLE.curie(iri)


def _sample_table() -> PrefixTable:
    from tests import sample_data as s

    return PrefixTable(
        [
            _entry("euvoc", s.EUVOC),
            _entry("skos", s.SKOS),
            _entry("skosxl", s.SKOSXL),
            _entry("owl", s.OWL),
            _entry("rdf", s.RDF),
            _entry("rdfs", s.RDFS),
            _entry("dcterms", s.DCT),
            _entry("lvont", s.LEXVO),
            _entry("xsd", XSD),
            _entry("eli", "http://data.europa.eu/eli/ontology#"),
            _entry("lemon", "http://lemon-model.net/lemon#"),
        ]
    )


TABLE_OF_SAMPLE = _sample_table()
META = frozenset({"http://www.w3.org/2002/07/owl#", "http://www.w3.org/2000/01/rdf-schema#", RDF})


def sample_view(sample_analytics, facts: DatasetFacts, **options) -> PatternGraph:
    from fingerprint.domain.patterns import pattern_view

    graph = next(g for g in sample_analytics.graphs if g.graph == facts.graphs[-1])
    return pattern_view(
        graph, TABLE_OF_SAMPLE, GeneratorOptions(**options), excluded=META, graph_label=facts.name, slug=facts.name
    )


def test_the_continents_are_grouped_by_their_equal_instance_counts(sample_analytics):
    shown = sample_view(sample_analytics, CONTINENTS)
    assert [(b.name, b.instances) for b in shown.blocks] == [
        ("euvoc:Continent&skos:Concept", 6),
        ("owl:Ontology&skos:ConceptScheme", 1),
    ]


def test_the_treaties_are_grouped_by_their_equal_instance_counts(sample_analytics):
    shown = sample_view(sample_analytics, TREATIES)
    assert [(b.name, b.instances) for b in shown.blocks] == [
        ("euvoc:Treaty&skos:Concept", 104),
        ("owl:Ontology&skos:ConceptScheme", 1),
    ]


@pytest.mark.parametrize("facts", [CONTINENTS, TREATIES], ids=lambda f: f.name)
def test_a_block_has_one_edge_for_each_property_of_its_classes(sample_analytics, facts):
    shown = sample_view(sample_analytics, facts)
    for one in shown.blocks:
        expected = {named(p.iri) for c in facts.classes if named(c.iri) in one.name.split("&") for p in c.properties}
        assert [e.name for e in one.edges] == sorted(expected)


def test_the_continent_edges_read_as_the_pattern_schema_does(sample_analytics):
    edges = block(sample_view(sample_analytics, CONTINENTS), "euvoc:Continent&skos:Concept").edges
    texts = [e.text for e in edges]
    assert "-euvoc:startDate-> xsd:date =1952-07-24" in texts
    assert "-euvoc:status-> IRI d1" in texts
    assert "-skos:inScheme-> (:owl:Ontology&skos:ConceptScheme) d1" in texts


def test_the_treaty_edges_carry_coverage_histograms_and_ranges(sample_analytics):
    edges = block(sample_view(sample_analytics, TREATIES), "euvoc:Treaty&skos:Concept").edges
    texts = [e.text for e in edges]
    assert "-dcterms:replaces-> (:euvoc:Treaty&skos:Concept) 22/104" in texts
    assert "-eli:date_document-> xsd:date 83/104 1951-04-18..2012-02-02 d30" in texts
    assert "-euvoc:signatureLocation-> IRI 74/104 ×1-2 d13" in texts
    assert "-euvoc:officialJournalSeries-> xsd:string 92/104 C..P d3" in texts


# --- TC-P1: groups (N2) ---


def test_classes_with_the_same_subjects_are_one_group_even_through_a_third_class():
    shown = view(
        klass(A, 6, prop(P, {1: 6}, literals(6)), co_types=[(B, 6)]),
        klass(B, 6, co_types=[(C, 6)]),
        klass(C, 6, co_types=[(B, 6)]),
    )
    assert [b.name for b in shown.blocks] == ["ex:A&ex:B&ex:C"]
    assert shown.blocks[0].classes == [A, B, C]
    assert shown.blocks[0].shape == "ex:A"


def test_a_group_is_named_by_its_members_names_in_order():
    shown = view(klass(B, 3, co_types=[(A, 3)]), klass(A, 3))
    assert shown.blocks[0].name == "ex:A&ex:B"


def test_classes_sharing_only_some_subjects_are_not_grouped():
    shown = view(klass(A, 6, co_types=[(C, 3)]), klass(C, 6, co_types=[(A, 3)]))
    assert [b.name for b in shown.blocks] == ["ex:A", "ex:C"]


def test_a_class_with_more_instances_than_its_co_type_subjects_is_not_grouped():
    shown = view(klass(A, 6, co_types=[(B, 6)]), klass(B, 9))
    assert [b.name for b in shown.blocks] == ["ex:B", "ex:A"]


def test_a_class_read_in_first_n_mode_is_never_grouped():
    shown = view(klass(A, 100, observed=10, co_types=[(B, 10)]), klass(B, 100, observed=10, co_types=[(A, 10)]))
    assert [b.name for b in shown.blocks] == ["ex:A", "ex:B"]
    assert [b.observed for b in shown.blocks] == [10, 10]


def test_a_co_type_the_profile_does_not_list_is_ignored():
    assert [b.name for b in view(klass(A, 6, co_types=[(D, 6)])).blocks] == ["ex:A"]


def test_a_group_takes_each_property_once_from_the_first_member_that_has_it():
    shown = view(
        klass(A, 4, prop(P, {1: 3}, literals(3)), observed=None, co_types=[(B, 4)]),
        klass(B, 4, prop(P, {1: 4}, literals(4)), prop(Q, {1: 4}, literals(4)), co_types=[(A, 4)]),
    )
    assert [(e.name, e.text) for e in shown.blocks[0].edges] == [
        ("ex:p", "-ex:p-> xsd:string 3/4"),
        ("ex:q", "-ex:q-> xsd:string"),
    ]


# --- names and the IRIs that cannot be written (N1) ---


def test_an_iri_no_prefix_covers_is_written_in_full():
    other = "http://other.org/Thing"
    shown = view(klass(other, 1))
    assert shown.blocks[0].name == f"<{other}>"


def test_a_class_that_cannot_be_written_is_skipped_and_left_out():
    bad = EX + "bad iri"
    shown = view(klass(bad, 1), klass(A, 1))
    assert shown.skipped == [bad]
    assert [b.name for b in shown.blocks] == ["ex:A"]


def test_a_property_that_cannot_be_written_is_skipped_and_left_out():
    bad = EX + "bad p"
    shown = view(klass(A, 2, prop(bad, {1: 2}, literals(2)), prop(P, {1: 2}, literals(2))))
    assert shown.skipped == [bad]
    assert [e.name for e in shown.blocks[0].edges] == ["ex:p"]


def test_an_object_type_that_cannot_be_written_is_left_out_of_the_targets():
    bad = EX + "bad class"
    edge = one_edge(resources(5, bad), literals(5))
    assert [t.kind for t in edge.targets] == [TargetKind.datatype]


# --- TC-P2: nested groups (N7, P-4) ---


def blank_edges(instances_of_b, *objects, extra=()):
    """Class `ex:A` reaching blank nodes of `ex:B`, each by its own property with that many distinct objects."""
    properties = [
        prop(EX + f"p{n}", {1: 10}, resources(10, B, "blank_node").model_copy(update={"distinct_objects": count}))
        for n, count in enumerate(objects)
    ]
    return view(klass(A, 10, *properties), klass(B, instances_of_b), *extra)


def test_a_class_reached_only_by_blank_nodes_that_cover_its_instances_has_no_block():
    assert [b.name for b in blank_edges(5, 5).blocks] == ["ex:A"]


def test_a_class_whose_reaching_objects_fall_short_of_its_instances_keeps_its_block():
    assert [b.name for b in blank_edges(5, 3).blocks] == ["ex:A", "ex:B"]


def test_the_objects_of_different_properties_add_up():
    assert [b.name for b in blank_edges(5, 3, 2).blocks] == ["ex:A"]


def test_a_class_reached_by_an_iri_keeps_its_block():
    shown = view(klass(A, 10, prop(P, {1: 10}, resources(10, B, "iri"))), klass(B, 5))
    assert [b.name for b in shown.blocks] == ["ex:A", "ex:B"]


def test_a_class_nothing_reaches_keeps_its_block():
    assert [b.name for b in view(klass(A, 2), klass(B, 2)).blocks] == ["ex:A", "ex:B"]


def test_the_triples_count_when_the_partition_has_no_distinct_objects():
    only_triples = prop(P, {1: 10}, resources(7, B, "blank_node"))
    assert [b.name for b in view(klass(A, 10, only_triples), klass(B, 7)).blocks] == ["ex:A"]


def test_a_property_shared_by_the_members_of_a_group_counts_once():
    reach = prop(P, {1: 4}, resources(4, C, "blank_node").model_copy(update={"distinct_objects": 4}))
    shown = view(klass(A, 4, reach, co_types=[(B, 4)]), klass(B, 4, reach, co_types=[(A, 4)]), klass(C, 8))
    assert [b.name for b in shown.blocks] == ["ex:C", "ex:A&ex:B"]


def test_the_sample_blank_node_classes_have_no_block(sample_analytics):
    for facts in (CONTINENTS, TREATIES):
        names = {n for b in sample_view(sample_analytics, facts).blocks for n in b.name.split("&")}
        assert {"skosxl:Label", "euvoc:XlNotation", "euvoc:XlNote"}.isdisjoint(names)


# --- TC-P5: filters (P-3, P-10) ---


def excluded_ex():
    return frozenset({META_NS})


def test_a_hidden_namespace_member_stays_in_its_groups_name_and_classes():
    hidden = EX + "meta/H"
    shown = view(klass(A, 2, co_types=[(hidden, 2)]), klass(hidden, 2, co_types=[(A, 2)]), excluded=excluded_ex())
    assert [(b.name, b.classes) for b in shown.blocks] == [("ex:A&meta:H", [A, hidden])]
    assert shown.blocks[0].shape == "ex:A"
    assert shown.hidden_classes == 0


def test_a_group_without_a_shown_member_has_no_block_and_counts_as_hidden():
    hidden = EX + "meta/H"
    shown = view(klass(A, 2), klass(hidden, 2), excluded=excluded_ex())
    assert [b.name for b in shown.blocks] == ["ex:A"]
    assert shown.hidden_classes == 1


def test_an_edge_still_names_a_group_that_has_no_block():
    hidden = EX + "meta/H"
    shown = view(klass(A, 2, prop(P, {1: 2}, resources(2, hidden, "iri"))), klass(hidden, 2), excluded=excluded_ex())
    (target,) = shown.blocks[0].edges[0].targets
    assert (target.name, target.has_shape) == ("meta:H", False)


def test_classes_below_the_minimum_have_no_block():
    shown = view(klass(A, 1), klass(B, 5), klass(C, 5), min_instances=2)
    assert [b.name for b in shown.blocks] == ["ex:B", "ex:C"]
    assert shown.hidden_classes == 1


def test_only_the_largest_classes_keep_their_blocks_and_a_tie_goes_to_the_name():
    shown = view(klass(D, 9), klass(B, 5), klass(C, 5), klass(A, 1), max_classes=2)
    assert [b.name for b in shown.blocks] == ["ex:D", "ex:B"]
    assert shown.hidden_classes == 2


def test_the_minimum_applies_before_the_maximum():
    shown = view(klass(A, 9), klass(B, 1), klass(C, 5), min_instances=2, max_classes=5)
    assert [b.name for b in shown.blocks] == ["ex:A", "ex:C"]
    assert shown.hidden_classes == 1


def test_an_edge_to_a_group_with_a_block_says_so():
    shown = view(klass(A, 2, prop(P, {1: 2}, resources(2, B, "iri"))), klass(B, 2, co_types=[]))
    assert shown.blocks[0].edges[0].targets[0].has_shape is True


# --- the view of one graph ---


def test_the_view_carries_the_graph_its_label_and_its_slug():
    shown = view(klass(A, 1), graph="http://ex.org/g")
    assert (shown.graph, shown.graph_label, shown.slug) == ("http://ex.org/g", "g", "g")


def test_a_graph_without_classes_has_no_blocks():
    shown = view()
    assert (shown.blocks, shown.hidden_classes, shown.skipped) == ([], 0, [])


# --- TC-P4: edges and stat tokens (N3, N4, N5) ---


def test_edges_follow_the_property_names_in_order():
    shown = view(klass(A, 1, prop(Q, {1: 1}, literals(1)), prop(P, {1: 1}, literals(1))))
    assert [e.name for e in shown.blocks[0].edges] == ["ex:p", "ex:q"]


def test_an_edge_holds_its_property_depth_and_line():
    edge = one_edge(literals(10))
    assert (edge.property, edge.name, edge.depth, edge.text, edge.ending, edge.edges) == (
        P,
        "ex:p",
        1,
        "-ex:p-> xsd:string",
        "",
        [],
    )


@pytest.mark.parametrize(
    ("partitions", "expected"),
    [
        ((literals(10),), "xsd:string"),
        ((literals(10, XSD + "date"),), "xsd:date"),
        ((literals(10, None),), "xsd:string"),
        ((literals(10, None, "en"),), "rdf:langString @en"),
        ((literals(10, LANG_STRING, "en"),), "rdf:langString @en"),
        ((literals(5, LANG_STRING, "en"), literals(5, LANG_STRING, "fr")), "rdf:langString @2"),
        ((resources(10),), "IRI"),
        ((resources(10, None, "blank_node"),), "BNODE bn"),
        ((resources(10, B),), "(:ex:B)"),
        ((resources(5, B), resources(5, B)), "(:ex:B)"),
        ((resources(5, C), resources(5, B)), "(:ex:B|ex:C)"),
        ((resources(10, B, "blank_node"),), "(:ex:B) bn"),
        ((resources(4, B), literals(3), resources(2), resources(1, None, "blank_node")), "(:ex:B)|xsd:string|IRI|BNODE bn"),
        ((literals(5, XSD + "string"), literals(5, XSD + "date")), "xsd:date|xsd:string"),
        ((), "."),
    ],
)
def test_the_targets_of_an_edge(partitions, expected):
    assert one_edge(*partitions).text == f"-ex:p-> {expected}"


def test_the_targets_are_described_for_a_template():
    edge = one_edge(resources(4, B), literals(3), resources(2), resources(1, None, "blank_node"))
    assert [(t.kind, t.name) for t in edge.targets] == [
        (TargetKind.group, "ex:B"),
        (TargetKind.datatype, "xsd:string"),
        (TargetKind.iri, "IRI"),
        (TargetKind.blank_node, "BNODE"),
    ]
    assert edge.targets[0].classes == [B]


def test_an_edge_without_value_partitions_has_an_unknown_target():
    (target,) = one_edge().targets
    assert (target.kind, target.name) == (TargetKind.unknown, ".")


@pytest.mark.parametrize(
    ("bins", "instances", "tokens", "low", "high"),
    [
        ({1: 10}, 10, "", 1, 1),
        ({1: 7}, 10, " 7/10", 0, 1),
        ({2: 10}, 10, " ×2", 2, 2),
        ({1: 5, 3: 5}, 10, " ×1-3", 1, 3),
        ({1: 4, 2: 3}, 10, " 7/10 ×1-2", 0, 2),
        ({}, 10, " 0/10", None, None),
    ],
)
def test_coverage_and_multiplicity_tokens_with_the_counts_of_the_edge(bins, instances, tokens, low, high):
    edge = one_edge(literals(10), bins=bins, instances=instances)
    assert edge.text == f"-ex:p-> xsd:string{tokens}"
    assert (edge.min_count, edge.max_count) == (low, high)


def test_coverage_counts_against_the_instances_read_in_first_n_mode():
    shown = view(klass(A, 50000, prop(P, {1: 9000}, literals(9000)), observed=10000))
    assert shown.blocks[0].edges[0].text == "-ex:p-> xsd:string 9000/10000"


def test_coverage_is_written_against_the_instances_when_none_were_observed():
    uncounted = klass(A, 10, prop(P, {1: 4}, literals(4))).model_copy(update={"observed_instances": None})
    analysed = analyse(profile_run(uncounted)).graphs[0]
    from fingerprint.domain.patterns import pattern_view

    shown = pattern_view(analysed, TABLE, GeneratorOptions(), excluded=NOT_EXCLUDED, graph_label="g", slug="g")
    assert shown.blocks[0].edges[0].text == "-ex:p-> xsd:string 4/10"


@pytest.mark.parametrize(
    ("low", "high", "written"),
    [
        ("1951", "1951", " =1951"),
        ("1951", "2012", " 1951..2012"),
        ("Treaty of Rome", "Treaty of Rome", ' ="Treaty of Rome"'),
        ("1..2", "1..2", ' ="1..2"'),
        ("", "", ' =""'),
        ('say "x"', 'say "x"', ' ="say \\"x\\""'),
        ("a" * 70, "a" * 70, f' ="{"a" * 64}…"'),
        ("a" * 64, "a" * 64, f" ={'a' * 64}"),
        ("A C", "Z D", ' "A C".."Z D"'),
        ("x", None, " =x"),
    ],
)
def test_one_literal_datatype_gives_the_value_or_the_range_and_quotes_what_needs_it(low, high, written):
    part = literals(10, XSD + "date").model_copy(update={"min_value": low, "max_value": high})
    assert one_edge(part).text == f"-ex:p-> xsd:date{written}"


def test_a_range_is_followed_by_the_distinct_values():
    part = literals(10, XSD + "date").model_copy(update={"min_value": "a", "max_value": "b"})
    assert one_edge(part, distinct_objects=4).text == "-ex:p-> xsd:date a..b d4"


def test_a_single_value_replaces_the_distinct_values():
    part = literals(10, XSD + "date").model_copy(update={"min_value": "a", "max_value": "a"})
    assert one_edge(part, distinct_objects=1).text == "-ex:p-> xsd:date =a"


@pytest.mark.parametrize(
    "parts",
    [
        (literals(10, LANG_STRING, "en").model_copy(update={"min_value": "a", "max_value": "b"}),),
        (literals(5, XSD + "date"), literals(5, XSD + "string")),
        (literals(10, XSD + "date"),),
    ],
    ids=["language-tagged", "two datatypes", "no minimum recorded"],
)
def test_no_range_without_one_plain_literal_datatype_and_a_minimum(parts):
    assert ".." not in one_edge(*parts).text and "=" not in one_edge(*parts).text


@pytest.mark.parametrize(
    ("distinct", "tokens"),
    [(3, " d3"), (10, ""), (None, ""), (11, "")],
)
def test_the_distinct_values_are_written_when_fewer_than_the_triples(distinct, tokens):
    assert one_edge(literals(10), distinct_objects=distinct).text == f"-ex:p-> xsd:string{tokens}"


def test_a_property_found_but_not_measured_says_presence_only():
    shown = view(klass(A, 5, prop(P, presence_only=True)))
    edge = shown.blocks[0].edges[0]
    assert (edge.text, edge.presence_only, edge.min_count, edge.max_count) == ("-ex:p-> . presence", True, None, None)


def test_an_edge_to_a_class_of_another_graph_names_that_graph():
    graph = "http://ex.org/people"
    other = resources(2, B).model_copy(update={"object_class_graph": graph})
    (target,) = one_edge(other).targets
    assert (target.kind, target.name, target.classes, target.graph, target.has_shape) == (
        TargetKind.group,
        "ex:B",
        [B],
        graph,
        False,
    )
    assert one_edge(other).text == f"-ex:p-> (:ex:B @<{graph}>)"


def test_a_class_typed_in_this_graph_and_in_another_is_written_with_its_graph_only_for_the_other():
    here = "http://ex.org/here"
    same = resources(1, B).model_copy(update={"object_class_graph": here})
    other = resources(1, C).model_copy(update={"object_class_graph": "http://ex.org/there"})
    shown = view(klass(A, 2, prop(P, {1: 2}, same, other)), klass(B, 2), graph=here)
    assert shown.blocks[0].edges[0].text == "-ex:p-> (:ex:B|ex:C @<http://ex.org/there>)"


def test_an_object_type_with_an_unwritable_graph_is_left_out():
    other = resources(2, B).model_copy(update={"object_class_graph": "http://ex.org/bad graph"})
    assert [t.kind for t in one_edge(other).targets] == [TargetKind.unknown]


# --- TC-P7: a single IRI value (DEC-16) ---


def status(value="http://ex.org/status/active", distinct=1, top=True, kind="iri"):
    top_values = [ValueCount(value=value, triples=10)] if top else None
    return one_edge(resources(10, None, kind), distinct_objects=distinct, top_values=top_values)


def test_the_one_iri_value_is_written_as_a_name_with_its_prefix_declared():
    assert status().text == "-ex:p-> IRI =exs:active"


def test_the_one_iri_value_without_a_covering_prefix_is_written_in_full():
    assert status("http://other.org/a").text == "-ex:p-> IRI =<http://other.org/a>"


def test_without_top_values_the_distinct_count_is_written():
    assert status(top=False).text == "-ex:p-> IRI d1"
    assert one_edge(resources(10), distinct_objects=1, top_values=[]).text == "-ex:p-> IRI d1"


def test_a_value_that_cannot_be_written_is_left_to_the_distinct_count():
    assert status("http://ex.org/status/not written").text == "-ex:p-> IRI d1"


def test_more_than_one_object_gives_no_value():
    assert status(distinct=2).text == "-ex:p-> IRI d2"


def test_blank_node_objects_give_no_value():
    assert status(kind="blank_node").text == "-ex:p-> BNODE bn d1"


def test_mixed_iri_and_literal_objects_give_no_value():
    mixed = one_edge(resources(5), literals(5), distinct_objects=1, top_values=[ValueCount(value="x", triples=1)])
    assert mixed.text == "-ex:p-> xsd:string|IRI d1"


def test_a_literal_property_keeps_its_value_from_the_minimum():
    part = literals(10, XSD + "date").model_copy(update={"min_value": "2014", "max_value": "2014"})
    assert one_edge(part, distinct_objects=1, top_values=[ValueCount(value="2014", triples=10)]).text == (
        "-ex:p-> xsd:date =2014"
    )
