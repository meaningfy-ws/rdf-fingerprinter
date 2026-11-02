"""Choosing the label, alt labels, description and notes of each term (llm-schema-split DEC-5, DEC-9)."""

from collections.abc import Iterable
from itertools import groupby

from fingerprint.domain.profile import AnnotationValue, LangText, TermAnnotation
from fingerprint.domain.vocabulary import (
    ALT_LABEL_PREDICATES,
    NOTE_PREDICATES,
    TERM_DESCRIPTION_PREDICATES,
    TERM_LABEL_PREDICATES,
)

PREFERRED_LANGUAGE = "en"


def language_order(language: str | None) -> tuple[bool, str]:
    return (language is not None, language or "")


def _per_language(values: list[AnnotationValue], predicates: tuple[str, ...]) -> list[LangText]:
    """For each language the smallest text of the first predicate that has a value in it; untagged first."""
    chosen = []
    for language in sorted({v.language for v in values}, key=language_order):
        for predicate in predicates:
            texts = [v.text for v in values if v.language == language and v.predicate == predicate]
            if texts:
                chosen.append(LangText(text=min(texts), language=language))
                break
    return chosen


def _distinct(texts: Iterable[LangText]) -> list[LangText]:
    """The distinct (language, text) pairs, untagged first, then by language, then by text."""
    pairs = {(t.language, t.text) for t in texts}
    return [
        LangText(text=text, language=language) for language, text in sorted(pairs, key=lambda p: (language_order(p[0]), p[1]))
    ]


def _every(values: list[AnnotationValue], predicates: tuple[str, ...]) -> list[LangText]:
    return _distinct(LangText(text=v.text, language=v.language) for v in values if v.predicate in predicates)


def select_annotations(values: Iterable[AnnotationValue]) -> list[TermAnnotation]:
    """The annotations kept for each term that has any of the four fields, terms sorted by IRI."""
    selected = []
    for term, group in groupby(sorted(values, key=lambda v: v.term), key=lambda v: v.term):
        rows = list(group)
        descriptions = _per_language(rows, TERM_DESCRIPTION_PREDICATES)
        unselected = [t for t in _every(rows, TERM_DESCRIPTION_PREDICATES) if t not in descriptions]
        annotation = TermAnnotation(
            term=term,
            labels=_per_language(rows, TERM_LABEL_PREDICATES),
            alt_labels=_every(rows, ALT_LABEL_PREDICATES),
            descriptions=descriptions,
            notes=_distinct([*_every(rows, NOTE_PREDICATES), *unselected]),
        )
        if annotation.labels or annotation.alt_labels or descriptions or annotation.notes:
            selected.append(annotation)
    return selected


def _first(entries: list[TermAnnotation], field: str) -> list[LangText]:
    return next((getattr(e, field) for e in entries if getattr(e, field)), [])


def merge_annotations(ontology: list[TermAnnotation], data: list[TermAnnotation]) -> list[TermAnnotation]:
    """Per term and field, the ontology's texts when it gives any, else the data's (llm-schema-tools P-7)."""
    ranked = sorted([(a.term, 0, a) for a in ontology] + [(a.term, 1, a) for a in data], key=lambda r: r[:2])
    merged = []
    for term, group in groupby(ranked, key=lambda r: r[0]):
        entries = [entry for _, _, entry in group]
        merged.append(
            TermAnnotation(
                term=term,
                labels=_first(entries, "labels"),
                alt_labels=_first(entries, "alt_labels"),
                descriptions=_first(entries, "descriptions"),
                notes=_first(entries, "notes"),
            )
        )
    return merged


def shown(texts: list[LangText] | None) -> LangText | None:
    """The text a reader sees: the untagged one, else English, else the smallest language tag."""
    if not texts:
        return None
    return min(texts, key=lambda t: (t.language is not None, t.language != PREFERRED_LANGUAGE, t.language or ""))
