"""Reading the labels, alt labels, descriptions and notes of an ontology file (llm-schema-split DEC-5)."""

from pathlib import Path

from rdflib import Dataset, Literal, URIRef
from rdflib.term import Node
from rdflib.util import guess_format

from fingerprint.adapters.exceptions import OntologyFileError
from fingerprint.domain.profile import AnnotationValue
from fingerprint.domain.vocabulary import (
    ALT_LABEL_PREDICATES,
    NOTE_PREDICATES,
    SKOSXL,
    TERM_DESCRIPTION_PREDICATES,
    TERM_LABEL_PREDICATES,
)

ANNOTATION_PREDICATES = (*TERM_LABEL_PREDICATES, *ALT_LABEL_PREDICATES, *TERM_DESCRIPTION_PREDICATES, *NOTE_PREDICATES)
# skosxl labels count only through skosxl:literalForm, as in Q12
SKOSXL_LABELS = tuple(URIRef(p) for p in ANNOTATION_PREDICATES if p.startswith(SKOSXL))
PREDICATES = {URIRef(p) for p in ANNOTATION_PREDICATES} - set(SKOSXL_LABELS)
SKOSXL_LITERAL_FORM = URIRef(SKOSXL + "literalForm")


def _value(term: Node, predicate: Node, literal: Literal) -> AnnotationValue:
    language = literal.language.lower() if literal.language else None  # RDF 1.1: tags compare without case
    return AnnotationValue(term=str(term), predicate=str(predicate), text=str(literal), language=language)


def load_ontology(path: str | Path) -> list[AnnotationValue]:
    """The annotation values of every IRI term in the file; raises OntologyFileError naming it."""
    try:
        graph = Dataset(default_union=True)  # TriG and N-Quads: named graphs count, as in Q12
        graph.parse(path, format=guess_format(str(path)) or "turtle")
    except Exception as error:  # noqa: BLE001 - rdflib raises many parser types; a missing file raises OSError
        raise OntologyFileError(f"ontology file {path} cannot be read: {error}") from error
    values = [
        _value(s, p, o)
        for s, p, o in graph.triples((None, None, None))
        if isinstance(s, URIRef) and p in PREDICATES and isinstance(o, Literal)
    ]
    for predicate in SKOSXL_LABELS:
        for s, _, label in graph.triples((None, predicate, None)):
            if isinstance(s, URIRef):
                values += [
                    _value(s, predicate, o) for o in graph.objects(label, SKOSXL_LITERAL_FORM) if isinstance(o, Literal)
                ]
    return sorted(values, key=lambda v: (v.term, v.predicate, v.language or "", v.text))
