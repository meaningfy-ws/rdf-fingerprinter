"""The sample-data tooling: comparing profiles, the refresh decision, and the stored facts (lean-test-suite P-5)."""

from datetime import datetime

import pytest

from fingerprint.adapters.profile_file import load_profile
from fingerprint.domain.profile import ProfileRun
from tests.builders import klass, literals, profile_run, prop
from tests.refresh_sample_data import refreshed
from tests.sample_data import (
    CONTINENTS,
    REIFIED_COUNTS,
    REIFIED_HIDDEN_CLASSES,
    REIFIED_KINDS,
    REIFIED_ORDINARY_OWNER,
    REIFIED_ORDINARY_PREDICATE,
    REIFIED_PERSON,
    REIFIED_PERSON_RELATIONS,
    REIFIED_PROFILE,
    TREATIES,
    differences,
    same_profile,
)

NAME = "http://example.org/name"
AGE = "http://example.org/age"
PERSON = "http://example.org/Person"


def person(*props):
    return klass(PERSON, 3, *props)


def stamped(run: ProfileRun, tool_version="1.0.0") -> ProfileRun:
    return run.model_copy(
        update={"started_at": datetime(2026, 1, 1), "finished_at": datetime(2026, 1, 2), "tool_version": tool_version}
    )


def test_profiles_differing_only_in_timestamps_and_version_are_the_same():
    run = profile_run(person(prop(NAME, {1: 3}, literals(3))))
    assert same_profile(run, stamped(run, "9.9.9"))


def test_profiles_with_rows_in_another_order_are_the_same():
    a = profile_run(person(prop(NAME, {1: 3}, literals(3)), prop(AGE, {1: 3}, literals(3))))
    b = profile_run(person(prop(AGE, {1: 3}, literals(3)), prop(NAME, {1: 3}, literals(3))))
    assert same_profile(a, b)


def test_a_changed_property_is_named_with_its_class():
    stored = profile_run(person(prop(NAME, {1: 3}, literals(3))))
    fresh = profile_run(person(prop(NAME, {1: 2, 2: 1}, literals(4))))
    messages = differences(stored, fresh)
    assert messages and all(PERSON in m and NAME in m for m in messages) and not same_profile(stored, fresh)


def test_a_class_only_one_side_has_is_named():
    stored = profile_run(person())
    fresh = profile_run(person(), klass("http://example.org/Org", 1))
    assert differences(stored, fresh) == ["graph default: class http://example.org/Org only in the fresh profile"]


def test_a_property_only_one_side_has_is_named():
    stored = profile_run(person(prop(NAME, {1: 3}, literals(3))))
    fresh = profile_run(person())
    assert differences(stored, fresh) == [f"graph default class {PERSON}: property {NAME} only in the stored profile"]


def test_a_changed_instance_count_is_named_with_its_class():
    stored, fresh = profile_run(person()), profile_run(klass(PERSON, 4))
    assert any(PERSON in m and "instances differs (3 stored, 4 fresh)" in m for m in differences(stored, fresh))


def test_a_changed_setting_is_reported():
    assert differences(profile_run(person(), top_k=5), profile_run(person(), top_k=6)) == [
        "run: settings.top_k differs (5 stored, 6 fresh)"
    ]


def test_the_refresh_leaves_an_equal_profile_alone():
    run = profile_run(person(prop(NAME, {1: 3}, literals(3))))
    assert refreshed(stamped(run), run) is None


def test_the_refresh_keeps_the_stored_timestamps_and_version_on_new_data():
    stored = stamped(profile_run(person(prop(NAME, {1: 3}, literals(3)))))
    fresh = profile_run(person(prop(NAME, {1: 2, 2: 1}, literals(4))))
    new = refreshed(stored, fresh)
    assert (new.started_at, new.finished_at, new.tool_version) == (stored.started_at, stored.finished_at, "1.0.0")
    assert new.graphs == fresh.graphs


@pytest.mark.parametrize("facts", [CONTINENTS, TREATIES], ids=lambda f: f.name)
def test_the_stored_sample_profile_agrees_with_the_named_facts(facts, sample_analytics):
    for graph in (g for g in sample_analytics.graphs if g.graph in facts.graphs):
        classes = {c.class_iri: c for c in graph.class_partitions}
        assert {iri: c.instances for iri, c in classes.items()} == {c.iri: c.instances for c in facts.classes}
        for fact in facts.classes:
            seen = {p.property: (p.min, p.max) for p in classes[fact.iri].property_partitions}
            assert seen == {p.iri: (p.min, p.max) for p in fact.properties}, (graph.graph, fact.iri)


def test_the_stored_reified_profile_agrees_with_the_named_facts():
    (graph,) = load_profile(REIFIED_PROFILE).graphs
    classes = {c.class_iri: c for c in graph.class_partitions}
    assert list(graph.reification_kinds) == list(REIFIED_KINDS)
    assert {c.kind: c.count for c in graph.reification_counts} == dict(REIFIED_COUNTS)
    assert not set(REIFIED_HIDDEN_CLASSES) & set(classes)
    relations = classes[REIFIED_PERSON].reified_relations
    assert [
        (r.kind, r.property, r.object_class, r.statements, tuple((p.property, p.reifiers) for p in r.reifier_properties or ()))
        for r in relations
    ] == list(REIFIED_PERSON_RELATIONS)
    assert not classes[REIFIED_PERSON].property_partitions
    assert REIFIED_ORDINARY_PREDICATE in {p.property for p in classes[REIFIED_ORDINARY_OWNER].property_partitions}
