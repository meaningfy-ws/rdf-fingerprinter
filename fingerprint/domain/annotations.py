"""Choosing the label and description of each term (llm-schema-tools DEC-17, DEC-20, P-7)."""

from collections.abc import Iterable
from itertools import groupby

from fingerprint.domain.profile import AnnotationValue, LangText, TermAnnotation
from fingerprint.domain.vocabulary import ALT_LABEL, TERM_DESCRIPTION_PREDICATES, TERM_LABEL_PREDICATES

PREFERRED_LANGUAGE = "en"


def _per_language(values: list[AnnotationValue], predicates: tuple[str, ...]) -> list[LangText]:
    """For each language the smallest text of the first predicate that has a value in it; untagged first."""
    chosen = []
    for language in sorted({v.language for v in values}, key=lambda tag: (tag is not None, tag or "")):
        for predicate in predicates:
            texts = [v.text for v in values if v.language == language and v.predicate == predicate]
            if texts:
                chosen.append(LangText(text=min(texts), language=language))
                break
    return chosen


def select_annotations(values: Iterable[AnnotationValue]) -> list[TermAnnotation]:
    """The labels and descriptions kept for each term that has any, terms sorted by IRI."""
    selected = []
    for term, group in groupby(sorted(values, key=lambda v: v.term), key=lambda v: v.term):
        rows = list(group)
        labels = _per_language(rows, TERM_LABEL_PREDICATES) or _per_language(rows, (ALT_LABEL,))
        descriptions = _per_language(rows, TERM_DESCRIPTION_PREDICATES)
        if labels or descriptions:
            selected.append(TermAnnotation(term=term, labels=labels, descriptions=descriptions))
    return selected


def merge_annotations(ontology: list[TermAnnotation], data: list[TermAnnotation]) -> list[TermAnnotation]:
    """Per term and field, the ontology's texts when it gives any, else the data's (P-7)."""
    ranked = sorted([(a.term, 0, a) for a in ontology] + [(a.term, 1, a) for a in data], key=lambda r: r[:2])
    merged = []
    for term, group in groupby(ranked, key=lambda r: r[0]):
        entries = [entry for _, _, entry in group]
        labels = next((e.labels for e in entries if e.labels), [])
        descriptions = next((e.descriptions for e in entries if e.descriptions), [])
        merged.append(TermAnnotation(term=term, labels=labels, descriptions=descriptions))
    return merged


def shown(texts: list[LangText] | None) -> LangText | None:
    """The text a reader sees: the untagged one, else English, else the smallest language tag."""
    if not texts:
        return None
    return min(texts, key=lambda t: (t.language is not None, t.language != PREFERRED_LANGUAGE, t.language or ""))
