"""The shared text of a reified relation (singleton-property-pattern P-11)."""

from hypothesis import given

from fingerprint.domain.profile import ReificationCount, ReificationKind
from fingerprint.domain.reifications import reification_note, relation_view
from tests.builders import EX, relation
from tests.unit.domain.strategies import reified_relations

PROV = "http://www.w3.org/ns/prov#"


def curie(iri: str) -> str | None:
    return None if "bad" in iri else iri.replace(EX, "ex:").replace(PROV, "prov:")


def test_a_relation_reads_in_the_pattern_notation():
    view = relation_view(relation(EX + "worksFor", EX + "Org", 2, (PROV + "wasAttributedTo", 1), (EX + "since", 2)), curie)
    assert (
        view.text
        == "~> ex:worksFor (:ex:Org) 2 statements via resource_as_predicate [reifiers: prov:wasAttributedTo 1, ex:since 2]"
    )
    assert (view.kind, view.property, view.object_class, view.statements) == (
        "resource as predicate",
        "ex:worksFor",
        "ex:Org",
        2,
    )
    assert view.reifier_text == "prov:wasAttributedTo 1, ex:since 2"


def test_an_unnamed_property_and_an_untyped_object_have_their_own_notation():
    view = relation_view(relation(None, None, 1, kind=ReificationKind.owl_axiom), curie)
    assert view.text == "~> unnamed (:?) 1 statement via owl_axiom"
    assert (view.object_class, view.reifier_text) == (None, None)


def test_a_relation_with_an_unwritable_term_is_left_out_and_an_unwritable_reifier_is_dropped():
    assert relation_view(relation(EX + "bad", EX + "Org", 1), curie) is None
    assert relation_view(relation(EX + "p", EX + "bad", 1), curie) is None
    assert relation_view(relation(EX + "p", None, 1, (EX + "bad", 1), (EX + "ok", 1)), curie).reifier_text == "ex:ok 1"


def test_the_note_names_the_kinds_and_each_count_when_any():
    kinds = [ReificationKind.rdf_statement, ReificationKind.resource_as_predicate]
    one = ReificationCount(kind=ReificationKind.triple_term, count=1)
    three = ReificationCount(kind=ReificationKind.nanopublication, count=3)
    assert reification_note(kinds, [one, three]) == (
        "Reifications found: RDF statement, resource as predicate; 1 triple term, 3 nanopublications."
    )
    assert reification_note(kinds, None) == "Reifications found: RDF statement, resource as predicate."
    assert reification_note(kinds, [ReificationCount(kind=ReificationKind.triple_term, count=0)]) == (
        "Reifications found: RDF statement, resource as predicate."
    )
    assert reification_note(None, None) is None


@given(reified_relations)
def test_the_notation_follows_the_relation_for_any_relation(rel):
    view = relation_view(rel, lambda iri: "n:" + iri.rsplit("/", 1)[-1])
    noun = "1 statement via" if rel.statements == 1 else f"{rel.statements} statements via"
    assert view.text.startswith("~> ")
    assert f" {noun} {ReificationKind(rel.kind).value}" in view.text
    assert (" unnamed " in view.text) == (rel.property is None)
    assert ("(:?)" in view.text) == (rel.object_class is None)
    expected = ", ".join(f"n:{r.property.rsplit('/', 1)[-1]} {r.reifiers}" for r in rel.reifier_properties or [])
    assert view.reifier_text == (expected or None)
    assert (" [reifiers: " in view.text) == bool(expected)
    if expected:
        assert view.text.endswith(f"[reifiers: {expected}]")
