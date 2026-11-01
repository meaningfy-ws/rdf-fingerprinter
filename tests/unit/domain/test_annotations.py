"""Selecting, merging and showing the labels and descriptions of terms (llm-schema-tools DEC-17, DEC-20, P-7)."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from fingerprint.domain.annotations import merge_annotations, select_annotations, shown
from fingerprint.domain.profile import AnnotationValue, LangText, TermAnnotation
from fingerprint.domain.vocabulary import (
    ALT_LABEL,
    DCTERMS,
    RDFS,
    SKOS,
    SKOSXL,
    TERM_DESCRIPTION_PREDICATES,
    TERM_LABEL_PREDICATES,
)
from tests.unit.domain.strategies import annotation_values

PERSON = "http://ex.org/Person"
PREF, XL_PREF, LABEL, TITLE = TERM_LABEL_PREDICATES
DEFINITION, COMMENT, DESCRIPTION, SCOPE = TERM_DESCRIPTION_PREDICATES


def row(predicate: str, text: str, language: str | None = None, term: str = PERSON) -> AnnotationValue:
    return AnnotationValue(term=term, predicate=predicate, text=text, language=language)


def texts(*pairs: tuple[str, str | None]) -> list[LangText]:
    return [LangText(text=t, language=lang) for t, lang in pairs]


def test_the_vocabulary_lists_the_predicates_in_priority_order():
    assert TERM_LABEL_PREDICATES == (SKOS + "prefLabel", SKOSXL + "prefLabel", RDFS + "label", DCTERMS + "title")
    assert ALT_LABEL == SKOS + "altLabel"
    assert TERM_DESCRIPTION_PREDICATES == (SKOS + "definition", RDFS + "comment", DCTERMS + "description", SKOS + "scopeNote")


# --- TC-A1 ---


def test_labels_and_descriptions_are_chosen_per_language():
    values = [
        row(LABEL, "Person", "en"),
        row(PREF, "Human", "en"),
        row(LABEL, "Personne", "fr"),
        row(TITLE, "Mensch", "de"),
        row(COMMENT, "A person", "en"),
        row(DEFINITION, "A human being", "en"),
        row(SCOPE, "Une personne", "fr"),
    ]
    assert select_annotations(values) == [
        TermAnnotation(
            term=PERSON,
            labels=texts(("Mensch", "de"), ("Human", "en"), ("Personne", "fr")),
            descriptions=texts(("A human being", "en"), ("Une personne", "fr")),
        )
    ]


def test_the_smallest_text_wins_within_a_language_and_predicate():
    assert select_annotations([row(LABEL, "B"), row(LABEL, "A")])[0].labels == texts(("A", None))


def test_untagged_values_come_first():
    assert [t.language for t in select_annotations([row(LABEL, "x", "en"), row(LABEL, "y")])[0].labels] == [None, "en"]


def test_an_alternative_label_is_only_a_fallback():
    assert select_annotations([row(ALT_LABEL, "Body", "en")])[0].labels == texts(("Body", "en"))
    values = [row(ALT_LABEL, "Body", "en"), row(TITLE, "Person", "de")]
    assert select_annotations(values)[0].labels == texts(("Person", "de"))


def test_a_term_with_only_a_description_is_kept():
    assert select_annotations([row(COMMENT, "A person")]) == [
        TermAnnotation(term=PERSON, labels=[], descriptions=texts(("A person", None)))
    ]


@pytest.mark.parametrize("values", [[], [row(RDFS + "seeAlso", "x")]])
def test_no_label_or_description_gives_no_entry(values):
    assert select_annotations(values) == []


def test_terms_are_sorted_by_iri():
    values = [row(LABEL, "b", term="http://ex.org/b"), row(LABEL, "a", term="http://ex.org/a")]
    assert [a.term for a in select_annotations(values)] == ["http://ex.org/a", "http://ex.org/b"]


# --- TC-A2 ---


def as_values(annotations: list[TermAnnotation]) -> list[AnnotationValue]:
    return [
        row(predicate, t.text, t.language, a.term)
        for a in annotations
        for predicate, field in ((PREF, a.labels), (DEFINITION, a.descriptions))
        for t in field or []
    ]


@given(annotation_values())
def test_selection_is_idempotent(values):
    selected = select_annotations(values)
    assert select_annotations(as_values(selected)) == selected


@given(annotation_values(), st.randoms())
def test_selection_ignores_the_order_of_the_input(values, random):
    shuffled = list(values)
    random.shuffle(shuffled)
    assert select_annotations(shuffled) == select_annotations(values)


@given(annotation_values())
def test_selection_keeps_one_text_per_language_and_field(values):
    for annotation in select_annotations(values):
        for field in (annotation.labels, annotation.descriptions):
            languages = [t.language for t in field or []]
            assert len(languages) == len(set(languages))


# --- TC-A3 ---


def entry(labels=(), descriptions=(), term: str = PERSON) -> TermAnnotation:
    return TermAnnotation(term=term, labels=texts(*labels), descriptions=texts(*descriptions))


def test_the_ontology_wins_for_each_field_it_gives():
    ontology = [entry(labels=[("Person", "en")])]
    data = [entry(labels=[("Persoon", "nl")], descriptions=[("Iemand", "nl")])]
    assert merge_annotations(ontology, data) == [entry(labels=[("Person", "en")], descriptions=[("Iemand", "nl")])]


def test_a_term_in_one_source_is_kept_and_terms_are_sorted():
    other = "http://ex.org/A"
    merged = merge_annotations([entry(labels=[("P", None)])], [entry(descriptions=[("d", None)], term=other)])
    assert [a.term for a in merged] == [other, PERSON]
    assert merged[0] == entry(descriptions=[("d", None)], term=other)
    assert merged[1] == entry(labels=[("P", None)])


def test_an_ontology_entry_with_descriptions_only_keeps_the_data_labels():
    merged = merge_annotations(
        [entry(descriptions=[("New", "en")])], [entry(labels=[("Old", "en")], descriptions=[("Older", "en")])]
    )
    assert merged == [entry(labels=[("Old", "en")], descriptions=[("New", "en")])]


def test_merging_nothing_gives_nothing():
    assert merge_annotations([], []) == []


# --- shown ---


@pytest.mark.parametrize(
    "given, expected",
    [
        ([("Begriff", "de"), ("Concept", "en"), ("C", None)], ("C", None)),
        ([("Begriff", "de"), ("Concept", "en")], ("Concept", "en")),
        ([("Begriff", "de"), ("Concept", "fr")], ("Begriff", "de")),
        ([("Concept", "fr"), ("Begriff", "de")], ("Begriff", "de")),
    ],
)
def test_the_text_shown_is_untagged_then_english_then_the_smallest_language(given, expected):
    assert shown(texts(*given)) == LangText(text=expected[0], language=expected[1])


@pytest.mark.parametrize("empty", [None, []])
def test_nothing_is_shown_without_texts(empty):
    assert shown(empty) is None
