"""The namespace filters: which namespaces a user's values hide or exclude (namespace-filter, TC-F2)."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from fingerprint.domain.analytics import analyse
from fingerprint.domain.namespace_filter import (
    META_NAMESPACES,
    exclude_terms,
    namespace_filter,
    namespace_uses,
    namespaces_with_terms,
    note_text,
)
from fingerprint.domain.prefixes import PrefixTable, namespace_of
from fingerprint.domain.profile import (
    ExcludedTerms,
    IncomingLink,
    Inheritance,
    NamespacePrefix,
    NamespaceUse,
    NodeKind,
    PitfallResult,
    PredicatePartition,
    PrefixSource,
    ProfileAnalytics,
    TermAnnotation,
    ValueCount,
)
from fingerprint.domain.views import FilterMatch, FilterOption, GeneratorOptions
from fingerprint.domain.vocabulary import OWL, RDF, RDFS, SH
from tests import builders
from tests.unit.domain.strategies import FILTER_NAMESPACES, filter_runs

EX = "http://example.org/"
REL = EX + "rel/"
ORG = "http://org.example/"
XSD = builders.XSD
TABLE = PrefixTable(
    NamespacePrefix(prefix=prefix, namespace=namespace, source=PrefixSource.packaged)
    for prefix, namespace in [
        ("ex", EX),
        ("rel", EX + "rel/"),
        ("relx", EX + "relx/"),
        ("org", "http://org.example/"),
        ("owl", OWL),
        ("rdfs", RDFS),
    ]
)


def filtered(exclude=(), include=()):
    return namespace_filter(GeneratorOptions(exclude_namespaces=list(exclude), include_namespaces=list(include)), TABLE)


def test_the_meta_vocabularies_are_the_four_the_outputs_hide():
    assert META_NAMESPACES == {RDF, RDFS, OWL, SH}


def test_with_no_options_only_the_meta_namespaces_are_hidden():
    result = filtered()
    assert result.hidden == sorted(META_NAMESPACES) and result.excluded == [] and result.matches == []


def test_the_default_options_are_the_same_as_none():
    assert namespace_filter(GeneratorOptions(), TABLE) == filtered()


def test_excluded_is_what_the_exclude_values_match_in_iri_order():
    result = filtered(exclude=["rel*", "org"])
    assert result.excluded == [EX + "rel/", EX + "relx/", "http://org.example/"]
    assert result.hidden == sorted(META_NAMESPACES)


def test_include_wins_over_exclude_and_over_the_default_hiding():
    result = filtered(exclude=[EX], include=["ex", "owl"])
    assert result.excluded == [EX + "rel/", EX + "relx/"]
    assert result.hidden == sorted(META_NAMESPACES - {OWL})


def test_an_include_with_nothing_to_undo_changes_nothing_else():
    result = filtered(include=["org"])
    assert result.excluded == [] and result.hidden == sorted(META_NAMESPACES)


def test_a_meta_namespace_can_be_excluded_by_name():
    assert filtered(exclude=["rdfs"]).excluded == [RDFS]


def test_each_value_gets_one_match_excludes_first_in_the_order_given():
    result = filtered(exclude=["rel*", "nope"], include=["ex"])
    assert result.matches == [
        FilterMatch(option=FilterOption.exclude, name="rel*", namespaces=[EX + "rel/", EX + "relx/"]),
        FilterMatch(option=FilterOption.exclude, name="nope", namespaces=[]),
        FilterMatch(option=FilterOption.include, name="ex", namespaces=[EX]),
    ]


def test_a_value_given_twice_is_matched_once():
    assert len(filtered(exclude=["rel", "rel"], include=["ex", "ex"]).matches) == 2


# --- exclude_terms and namespace_uses (TC-F3, TC-F4) ---


def with_value(p, **fields):
    return p.model_copy(update=fields)


def filter_world(**graph) -> ProfileAnalytics:
    """One graph, the analytics of the design's §I profile plus a hub, a mixed property and a parent in `rel`."""
    person = builders.klass(
        EX + "Person",
        10,
        builders.prop(EX + "name", {1: 10}, builders.literals(10)),
        builders.prop(EX + "knows", {1: 10}, builders.resources(10, EX + "Person")),
        with_value(builders.prop(EX + "memberOf", {1: 10}, builders.resources(10, ORG + "Unit")), distinct_objects=2),
        builders.prop(REL + "r1", {1: 1}, builders.resources(1, EX + "Person")),
        builders.prop(REL + "r2", {1: 1}, builders.resources(1, EX + "Person")),
        with_value(
            builders.prop(EX + "hub", {1: 10}, builders.resources(10)),
            distinct_objects=1,
            top_values=[ValueCount(value=REL + "hub", triples=10)],
        ),
        with_value(
            builders.prop(EX + "ref", {1: 10}, builders.resources(8), builders.literals(2)),
            distinct_objects=1,
            top_values=[ValueCount(value=REL + "ref", triples=8)],
        ),
        with_value(
            builders.prop(EX + "pair", {1: 10}, builders.resources(10)),
            distinct_objects=2,
            top_values=[ValueCount(value=REL + "pair", triples=6)],
        ),
        with_value(
            builders.prop(EX + "blank", {1: 10}, builders.resources(10, kind="blank_node")),
            distinct_objects=1,
            top_values=[ValueCount(value=REL + "blank", triples=10)],
        ),
    ).model_copy(update={"incoming_links": [IncomingLink(subject_class=ORG + "Unit", property=REL + "r1", triples=1)]})
    unit = builders.klass(ORG + "Unit", 2, builders.prop(EX + "name", {1: 2}, builders.literals(2)))
    agent = builders.klass(
        EX + "Agent", 5, builders.prop(EX + "name", {1: 5}, builders.literals(5)), co_types=[(ORG + "Member", 5)]
    )
    base = builders.klass(REL + "Base", 5, builders.prop(EX + "name", {1: 5}, builders.literals(5)))
    raw = builders.profile_run(
        person,
        unit,
        agent,
        base,
        edges=[(EX + "Agent", REL + "Base")],
        failures=[
            builders.failure(ORG + "Unit", "boom"),
            builders.failure(EX + "Person", "boom").model_copy(update={"property": REL + "r1"}),
        ],
    )
    pitfall = PitfallResult(check_id="c", title="t", importance="minor", scope="data", source="s", count=1)
    notes = [TermAnnotation(term=t) for t in (EX + "Person", REL + "r1", ORG + "Unit")]
    graph_fields = dict(
        pitfalls=[pitfall], term_annotations=notes, predicate_partitions=[PredicatePartition(property=REL + "r1", triples=1)]
    )
    raw = raw.model_copy(update={"graphs": [raw.graphs[0].model_copy(update={**graph_fields, **graph})]})
    return analyse(raw)


def classes(analytics, graph=0):
    return {c.class_iri: c for c in analytics.graphs[graph].class_partitions}


def properties(klass):
    return {p.property: p for p in klass.property_partitions}


def terms(analytics, graph=0):
    return analytics.graphs[graph].excluded_terms


def test_excluding_nothing_changes_only_the_notes_and_the_uses():
    before = filter_world()
    after = exclude_terms(before, set(), TABLE)
    assert terms(after) == []
    assert after.namespace_uses == namespace_uses(before, TABLE)
    assert after.model_copy(update={"namespace_uses": None, "graphs": before.graphs}) == before
    assert after.graphs[0].model_copy(update={"excluded_terms": None}) == before.graphs[0]
    assert (
        after.model_copy(update={"namespace_uses": None}).graphs[0].model_copy(update={"excluded_terms": None})
        == (before.graphs[0])
    )


def test_an_excluded_property_is_dropped_from_every_class():
    person = properties(classes(exclude_terms(filter_world(), {REL}, TABLE))[EX + "Person"])
    assert REL + "r1" not in person and REL + "r2" not in person and EX + "name" in person


def test_an_excluded_class_is_dropped_with_its_properties():
    after = exclude_terms(filter_world(), {ORG}, TABLE)
    assert ORG + "Unit" not in classes(after) and EX + "Person" in classes(after)


def test_an_excluded_object_class_is_cleared_and_the_value_types_follow_the_remaining_partitions():
    before = properties(classes(filter_world())[EX + "Person"])[EX + "memberOf"]
    member_of = properties(classes(exclude_terms(filter_world(), {ORG}, TABLE))[EX + "Person"])[EX + "memberOf"]
    (partition,) = member_of.value_partitions
    assert (partition.object_class, partition.object_class_graph, partition.triples) == (None, None, 10)
    assert (before.value_types, before.dominant_value_type, before.untyped_object_ratio) == ([ORG + "Unit"], ORG + "Unit", 0.0)
    assert (member_of.value_types, member_of.dominant_value_type, member_of.type_purity) == (None, None, None)
    assert member_of.untyped_object_ratio == 1.0
    assert (member_of.total_triples, member_of.subjects_with_property) == (before.total_triples, before.subjects_with_property)


def test_a_property_that_lost_no_object_class_keeps_its_value_types():
    before = properties(classes(filter_world())[EX + "Person"])[EX + "knows"]
    after = properties(classes(exclude_terms(filter_world(), {ORG}, TABLE))[EX + "Person"])[EX + "knows"]
    assert after == before


def test_a_co_type_and_a_parent_are_dropped():
    before = classes(filter_world())[EX + "Agent"]
    agent = classes(exclude_terms(filter_world(), {ORG, REL}, TABLE))[EX + "Agent"]
    assert [p.parent for p in before.parents] == [REL + "Base", ORG + "Member"]
    assert agent.co_types == [] and agent.parents == []


def test_a_property_inherited_from_an_excluded_parent_stays_inherited():
    agent = classes(exclude_terms(filter_world(), {REL}, TABLE))[EX + "Agent"]
    assert properties(agent)[EX + "name"].inheritance == Inheritance.inherited


def test_an_annotation_of_an_excluded_term_is_dropped():
    after = exclude_terms(filter_world(), {REL, ORG}, TABLE)
    assert [n.term for n in after.graphs[0].term_annotations] == [EX + "Person"]


def test_a_graph_without_annotations_stays_without():
    assert exclude_terms(filter_world(term_annotations=None), {REL}, TABLE).graphs[0].term_annotations is None


def test_an_excluded_single_value_leaves_the_property_no_top_value():
    person = properties(classes(exclude_terms(filter_world(), {REL}, TABLE))[EX + "Person"])
    assert person[EX + "hub"].top_values == []


def test_a_single_value_that_is_not_excluded_is_kept():
    person = properties(classes(exclude_terms(filter_world(), {ORG}, TABLE))[EX + "Person"])
    assert [v.value for v in person[EX + "hub"].top_values] == [REL + "hub"]


@pytest.mark.parametrize("name", ["ref", "pair", "blank"])
def test_top_values_are_kept_when_no_single_iri_is_written(name):
    """`ref` has a literal partition, `pair` two distinct objects, `blank` blank nodes: no output writes a value."""
    before = properties(classes(filter_world())[EX + "Person"])[EX + name]
    after = properties(classes(exclude_terms(filter_world(), {REL}, TABLE))[EX + "Person"])[EX + name]
    assert after.top_values == before.top_values


def test_datatypes_pitfalls_failures_links_edges_and_predicates_are_not_filtered():
    before = filter_world()
    after = exclude_terms(before, {REL, ORG, XSD}, TABLE)
    graph, kept = after.graphs[0], before.graphs[0]
    assert graph.pitfalls == kept.pitfalls
    assert graph.predicate_partitions == kept.predicate_partitions
    assert graph.declared_subclass_edges == kept.declared_subclass_edges
    assert after.failures == before.failures and len(after.failures) == 2
    assert properties(classes(after)[EX + "Person"])[EX + "name"] == properties(classes(before)[EX + "Person"])[EX + "name"]
    assert classes(after)[EX + "Person"].incoming_links == classes(before)[EX + "Person"].incoming_links


def test_the_input_is_not_changed():
    before = filter_world()
    snapshot = before.model_dump()
    exclude_terms(before, {REL, ORG}, TABLE)
    assert before.model_dump() == snapshot


def test_namespaces_not_in_the_table_are_told_by_their_own_namespace():
    after = exclude_terms(filter_world(), {XSD, "http://other.example/"}, PrefixTable([]))
    assert terms(after) == [] and ORG + "Unit" in classes(after)


def test_the_uses_are_the_instances_of_the_classes_plus_the_subjects_of_the_properties_in_table_order():
    assert namespace_uses(filter_world(), TABLE) == [
        NamespaceUse(namespace=namespace, uses=uses)
        for namespace, uses in [(EX, 97), (REL, 7), (EX + "relx/", 0), (ORG, 2), (OWL, 0), (RDFS, 0)]
    ]


def test_the_uses_are_the_unfiltered_ones_whatever_is_excluded():
    assert exclude_terms(filter_world(), {REL, ORG}, TABLE).namespace_uses == namespace_uses(filter_world(), TABLE)


def test_an_iri_no_namespace_of_the_table_begins_counts_for_nobody():
    assert namespace_uses(filter_world(), PrefixTable([])) == []


def test_a_namespace_has_terms_when_it_has_uses_or_a_noted_term_and_none_when_neither():
    after = exclude_terms(filter_world(), {EX + "relx/", REL}, TABLE)
    assert namespaces_with_terms(after) == {EX, REL, ORG}  # relx: no use, no term; unfiltered analytics: no note
    assert namespaces_with_terms(filter_world()) == set()  # not filtered: no uses set, nothing noted


def counted(excluded):
    return terms(exclude_terms(filter_world(), excluded, TABLE))


def test_a_class_counts_once_whether_a_class_an_object_class_a_co_type_or_a_parent():
    assert counted({ORG}) == [ExcludedTerms(namespace=ORG, classes=2, properties=0, values=0)]  # Unit, Member
    assert counted({REL})[0].classes == 1  # Base: a class and Agent's parent


def test_properties_and_single_values_are_counted_where_they_are_written():
    assert counted({REL}) == [ExcludedTerms(namespace=REL, classes=1, properties=2, values=1)]


def test_nothing_under_a_dropped_class_is_counted():
    """`rel:Base` and `ex:Person` are dropped with their properties: only what a kept class still held counts."""
    assert counted({EX}) == [ExcludedTerms(namespace=EX, classes=2, properties=1, values=0)]


def test_namespaces_with_a_count_are_listed_in_namespace_order_and_the_others_omitted():
    assert [t.namespace for t in counted({ORG, REL, EX + "relx/", XSD})] == [REL, ORG]


def test_each_graph_counts_its_own_terms():
    analytics = filter_world()
    clean = analytics.graphs[0].model_copy(
        update={"class_partitions": [classes(analytics)[EX + "Person"].model_copy(update={"property_partitions": []})]}
    )
    after = exclude_terms(analytics.model_copy(update={"graphs": [analytics.graphs[0], clean]}), {REL}, TABLE)
    assert terms(after, 0)[0].properties == 2 and terms(after, 1) == []


def test_a_run_with_no_graphs_has_no_terms_to_exclude():
    empty = ProfileAnalytics(settings=builders.profile_run().settings)
    after = exclude_terms(empty, {REL}, TABLE)
    assert after.graphs == [] and {u.uses for u in after.namespace_uses} == {0}


def test_absent_class_and_property_lists_stay_absent():
    bare = filter_world().graphs[0].model_copy(update={"class_partitions": None})
    assert exclude_terms(filter_world().model_copy(update={"graphs": [bare]}), {REL}, TABLE).graphs[0].class_partitions is None
    person = classes(filter_world())[EX + "Person"].model_copy(update={"property_partitions": None})
    graph = filter_world().graphs[0].model_copy(update={"class_partitions": [person]})
    kept = exclude_terms(filter_world().model_copy(update={"graphs": [graph]}), {REL}, TABLE)
    assert kept.graphs[0].class_partitions[0].property_partitions is None


def test_uses_already_set_are_kept_by_a_second_pass():
    once = exclude_terms(filter_world(), {EX}, TABLE)
    assert once.namespace_uses != namespace_uses(once, TABLE)
    assert exclude_terms(once, {EX}, TABLE).namespace_uses == once.namespace_uses


# --- note_text (TC-F6) ---


def test_the_note_names_each_namespace_by_prefix_in_prefix_order():
    rel = ExcludedTerms(namespace=REL, classes=0, properties=2, values=0)
    org = ExcludedTerms(namespace=ORG, classes=1, properties=0, values=3)
    assert note_text([rel], TABLE) == "rel (classes 0, properties 2, values 0)"
    assert note_text([rel, org], TABLE) == "org (classes 1, properties 0, values 3); rel (classes 0, properties 2, values 0)"


@pytest.mark.parametrize("empty", [[], None])
def test_there_is_no_note_without_excluded_terms(empty):
    assert note_text(empty, TABLE) is None


def test_a_namespace_without_a_prefix_is_named_by_its_iri():
    assert note_text([ExcludedTerms(namespace=XSD, classes=1, properties=0, values=0)], TABLE) == (
        f"{XSD} (classes 1, properties 0, values 0)"
    )


# --- exclude_terms on random runs (TC-F5) ---

FOLLOWS = {
    "graph": {"class_partitions", "term_annotations", "excluded_terms"},
    "class": {"property_partitions", "co_types", "parents"},
    "property": {
        "value_partitions",
        "top_values",
        "value_types",
        "dominant_value_type",
        "type_purity",
        "untyped_object_ratio",
    },
}
excluded_sets = st.sets(st.sampled_from(FILTER_NAMESPACES))


def analysed(run):
    return analyse(run), PrefixTable(run.namespaces)


def is_excluded(iri, excluded, table):
    entry = table.entry_for(iri)
    return (entry.namespace if entry else namespace_of(iri)) in excluded


def pairs(before, after):
    """(graph before, graph after), then (class before, class after) and (property before, property after) of the kept ones."""
    for graph_before, graph_after in zip(before.graphs, after.graphs, strict=True):
        yield "graph", graph_before, graph_after
        kept = classes_by_iri(graph_before)
        for cls in graph_after.class_partitions:
            yield "class", kept[cls.class_iri], cls
            before_props = {p.property: p for p in kept[cls.class_iri].property_partitions}
            for prop in cls.property_partitions:
                yield "property", before_props[prop.property], prop


def classes_by_iri(graph):
    return {c.class_iri: c for c in graph.class_partitions}


@given(filter_runs(), excluded_sets)
def test_no_excluded_iri_is_left_at_a_filtered_position(run, excluded):
    before, table = analysed(run)
    after = exclude_terms(before, excluded, table)
    for graph in after.graphs:
        assert not any(is_excluded(a.term, excluded, table) for a in graph.term_annotations or [])
        for cls in graph.class_partitions:
            assert not is_excluded(cls.class_iri, excluded, table)
            assert not any(is_excluded(c.class_iri, excluded, table) for c in cls.co_types or [])
            assert not any(is_excluded(p.parent, excluded, table) for p in cls.parents)
            for prop in cls.property_partitions:
                assert not is_excluded(prop.property, excluded, table)
                assert not any(
                    is_excluded(v.object_class, excluded, table) for v in prop.value_partitions or [] if v.object_class
                )
                parts = prop.value_partitions or []
                if parts and all(v.node_kind == NodeKind.iri for v in parts) and prop.distinct_objects == 1:
                    assert not any(is_excluded(v.value, excluded, table) for v in prop.top_values or [])


@given(filter_runs(), excluded_sets)
def test_filtering_twice_is_filtering_once_but_for_the_notes(run, excluded):
    once = exclude_terms(*analysed(run)[:1], excluded, PrefixTable(run.namespaces))
    twice = exclude_terms(once, excluded, PrefixTable(run.namespaces))
    assert twice.model_dump(exclude={"graphs"}) == once.model_dump(exclude={"graphs"})
    for graph_once, graph_twice in zip(once.graphs, twice.graphs, strict=True):
        assert graph_twice.model_dump(exclude={"excluded_terms"}) == graph_once.model_dump(exclude={"excluded_terms"})
        assert graph_twice.excluded_terms == []


@given(filter_runs(), excluded_sets)
def test_the_input_analytics_are_not_changed(run, excluded):
    before, table = analysed(run)
    snapshot = before.model_dump()
    exclude_terms(before, excluded, table)
    assert before.model_dump() == snapshot


@given(filter_runs())
def test_with_nothing_excluded_only_the_notes_and_the_uses_are_set(run):
    before, table = analysed(run)
    after = exclude_terms(before, set(), table)
    assert after.namespace_uses == namespace_uses(before, table)
    assert after.model_copy(update={"namespace_uses": None, "graphs": before.graphs}) == before
    for graph_before, graph_after in zip(before.graphs, after.graphs, strict=True):
        assert graph_after.excluded_terms == []
        assert graph_after.model_copy(update={"excluded_terms": None}) == graph_before


@given(filter_runs(), excluded_sets)
def test_every_unchanged_field_of_a_kept_term_is_as_analysed(run, excluded):
    """Instances, triples, subjects, inheritance, the graph's totals and the rest: only the `follows` fields change."""
    before, table = analysed(run)
    after = exclude_terms(before, excluded, table)
    assert after.model_dump(exclude={"graphs", "namespace_uses"}) == before.model_dump(exclude={"graphs", "namespace_uses"})
    for level, kept_before, kept_after in pairs(before, after):
        assert kept_after.model_dump(exclude=FOLLOWS[level]) == kept_before.model_dump(exclude=FOLLOWS[level])


@given(filter_runs(), excluded_sets)
def test_a_property_keeps_its_value_types_unless_it_lost_an_object_class(run, excluded):
    before, table = analysed(run)
    after = exclude_terms(before, excluded, table)
    for level, prop_before, prop_after in pairs(before, after):
        if level == "property":
            lost = any(
                is_excluded(v.object_class, excluded, table) for v in prop_before.value_partitions or [] if v.object_class
            )
            if not lost:
                assert prop_after.value_partitions == prop_before.value_partitions
                assert prop_after.model_dump(include=FOLLOWS["property"] - {"top_values"}) == prop_before.model_dump(
                    include=FOLLOWS["property"] - {"top_values"}
                )
            assert prop_after.top_values in (prop_before.top_values, [])
            assert [p.triples for p in prop_after.value_partitions or []] == [
                p.triples for p in prop_before.value_partitions or []
            ]
