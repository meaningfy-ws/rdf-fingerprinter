"""Selecting, merging and showing the labels and descriptions of terms (llm-schema-tools DEC-17, DEC-20, P-7)."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from fingerprint.domain.annotations import merge_annotations, select_annotations, shown
from fingerprint.domain.profile import AnnotationValue, LangText, TermAnnotation
from fingerprint.domain.vocabulary import (
    ALT_LABEL_PREDICATES,
    DCTERMS,
    NOTE_PREDICATES,
    RDFS,
    SKOS,
    SKOSXL,
    TERM_DESCRIPTION_PREDICATES,
    TERM_LABEL_PREDICATES,
)
from tests.unit.domain.strategies import annotation_values

PERSON = "http://ex.org/Person"
PREF, XL_PREF, LABEL, TITLE = TERM_LABEL_PREDICATES
ALT, XL_ALT = ALT_LABEL_PREDICATES
DEFINITION, COMMENT, DESCRIPTION = TERM_DESCRIPTION_PREDICATES
SCOPE, NOTE, EXAMPLE, EDITORIAL, HISTORY, CHANGE = NOTE_PREDICATES


def row(predicate: str, text: str, language: str | None = None, term: str = PERSON) -> AnnotationValue:
    return AnnotationValue(term=term, predicate=predicate, text=text, language=language)


def texts(*pairs: tuple[str, str | None]) -> list[LangText]:
    return [LangText(text=t, language=lang) for t, lang in pairs]


def annotated(term: str = PERSON, **fields: list[LangText]) -> TermAnnotation:
    """A selected annotation: the four fields not given are empty lists."""
    return TermAnnotation(term=term, **{"labels": [], "alt_labels": [], "descriptions": [], "notes": [], **fields})


def test_the_vocabulary_lists_the_predicates_in_priority_order():
    assert TERM_LABEL_PREDICATES == (SKOS + "prefLabel", SKOSXL + "prefLabel", RDFS + "label", DCTERMS + "title")
    assert ALT_LABEL_PREDICATES == (SKOS + "altLabel", SKOSXL + "altLabel")
    assert TERM_DESCRIPTION_PREDICATES == (SKOS + "definition", RDFS + "comment", DCTERMS + "description")
    assert NOTE_PREDICATES == tuple(
        SKOS + name for name in ("scopeNote", "note", "example", "editorialNote", "historyNote", "changeNote")
    )


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
        annotated(
            labels=texts(("Mensch", "de"), ("Human", "en"), ("Personne", "fr")),
            descriptions=texts(("A human being", "en")),
            notes=texts(("A person", "en"), ("Une personne", "fr")),
        )
    ]


def test_the_smallest_text_wins_within_a_language_and_predicate():
    assert select_annotations([row(LABEL, "B"), row(LABEL, "A")])[0].labels == texts(("A", None))


def test_untagged_values_come_first():
    assert [t.language for t in select_annotations([row(LABEL, "x", "en"), row(LABEL, "y")])[0].labels] == [None, "en"]


def test_an_alternative_label_is_never_a_label():
    only_alt = select_annotations([row(ALT, "Body", "en")])[0]
    assert only_alt.labels == [] and only_alt.alt_labels == texts(("Body", "en"))
    both = select_annotations([row(XL_ALT, "Body", "en"), row(TITLE, "Person", "de")])[0]
    assert both.labels == texts(("Person", "de")) and both.alt_labels == texts(("Body", "en"))


def test_the_worked_example_of_the_design():
    values = [
        row(PREF, "Person", "en"),
        row(ALT, "Human", "en"),
        row(ALT, "Body", "en"),
        row(ALT, "Mensch", "de"),
        row(COMMENT, "A human being", "en"),
        row(COMMENT, "Also a legal person", "en"),
        row(SCOPE, "Use for people", "en"),
    ]
    assert select_annotations(values) == [
        annotated(
            labels=texts(("Person", "en")),
            alt_labels=texts(("Mensch", "de"), ("Body", "en"), ("Human", "en")),
            descriptions=texts(("A human being", "en")),
            notes=texts(("Also a legal person", "en"), ("Use for people", "en")),
        )
    ]


def test_alt_labels_and_notes_are_distinct_and_sorted_by_language_then_text():
    values = [row(ALT, "b", "en"), row(XL_ALT, "b", "en"), row(ALT, "z"), row(ALT, "a", "en")]
    values += [row(NOTE, "n2"), row(EXAMPLE, "n2"), row(CHANGE, "n1", "fr"), row(HISTORY, "n0", "en"), row(EDITORIAL, "e")]
    (found,) = select_annotations(values)
    assert found.alt_labels == texts(("z", None), ("a", "en"), ("b", "en"))
    assert found.notes == texts(("e", None), ("n2", None), ("n0", "en"), ("n1", "fr"))


def test_a_second_definition_in_one_language_becomes_a_note():
    (found,) = select_annotations([row(DEFINITION, "B def", "en"), row(DEFINITION, "A def", "en")])
    assert found.descriptions == texts(("A def", "en")) and found.notes == texts(("B def", "en"))


def test_a_description_repeated_by_another_predicate_is_not_also_a_note():
    (found,) = select_annotations([row(DEFINITION, "Same", "en"), row(COMMENT, "Same", "en")])
    assert found.descriptions == texts(("Same", "en")) and found.notes == []


def test_a_term_with_only_a_description_is_kept():
    assert select_annotations([row(COMMENT, "A person")]) == [annotated(descriptions=texts(("A person", None)))]


def test_a_term_with_only_notes_is_kept():
    assert select_annotations([row(SCOPE, "Internal", "en")]) == [annotated(notes=texts(("Internal", "en")))]


@pytest.mark.parametrize("values", [[], [row(RDFS + "seeAlso", "x")]])
def test_no_annotation_gives_no_entry(values):
    assert select_annotations(values) == []


def test_terms_are_sorted_by_iri():
    values = [row(LABEL, "b", term="http://ex.org/b"), row(LABEL, "a", term="http://ex.org/a")]
    assert [a.term for a in select_annotations(values)] == ["http://ex.org/a", "http://ex.org/b"]


# --- TC-A2 ---


def as_values(annotations: list[TermAnnotation]) -> list[AnnotationValue]:
    return [
        row(predicate, t.text, t.language, a.term)
        for a in annotations
        for predicate, field in ((PREF, a.labels), (ALT, a.alt_labels), (DEFINITION, a.descriptions), (NOTE, a.notes))
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


def entry(labels=(), descriptions=(), term: str = PERSON, alt_labels=(), notes=()) -> TermAnnotation:
    return annotated(
        term, labels=texts(*labels), alt_labels=texts(*alt_labels), descriptions=texts(*descriptions), notes=texts(*notes)
    )


def test_the_ontology_wins_for_each_field_it_gives():
    ontology = [entry(labels=[("Person", "en")])]
    data = [entry(labels=[("Persoon", "nl")], descriptions=[("Iemand", "nl")])]
    assert merge_annotations(ontology, data) == [entry(labels=[("Person", "en")], descriptions=[("Iemand", "nl")])]


@pytest.mark.parametrize("field", ["labels", "alt_labels", "descriptions", "notes"])
def test_the_ontology_wins_each_of_the_four_fields_on_its_own(field):
    ontology = entry(**{field: [("O", "en")]})
    data = entry(labels=[("L", "nl")], alt_labels=[("A", "nl")], descriptions=[("D", "nl")], notes=[("N", "nl")])
    merged = merge_annotations([ontology], [data])[0]
    for name in ("labels", "alt_labels", "descriptions", "notes"):
        assert getattr(merged, name) == getattr(ontology if name == field else data, name)


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


def test_a_term_repeated_within_one_source_keeps_the_first_that_gives_texts():
    first, second = (TermAnnotation(term=PERSON, labels=texts((name, None))) for name in ("First", "Second"))
    merged = merge_annotations([first, second], [])
    assert [t.text for t in merged[0].labels] == ["First"]
