"""Reading the labels and descriptions of an ontology file (llm-schema-tools P-7)."""

from pathlib import Path

from rdflib import Graph, Literal, URIRef
from rdflib.term import Node
from rdflib.util import guess_format

from fingerprint.adapters.exceptions import OntologyFileError
from fingerprint.domain.profile import AnnotationValue
from fingerprint.domain.vocabulary import (
    ALT_LABEL,
    SKOSXL,
    TERM_DESCRIPTION_PREDICATES,
    TERM_LABEL_PREDICATES,
)

PREDICATES = {URIRef(p) for p in (*TERM_LABEL_PREDICATES, ALT_LABEL, *TERM_DESCRIPTION_PREDICATES)}
SKOSXL_PREF_LABEL = URIRef(SKOSXL + "prefLabel")
SKOSXL_LITERAL_FORM = URIRef(SKOSXL + "literalForm")


def _value(term: Node, predicate: Node, literal: Literal) -> AnnotationValue:
    language = literal.language.lower() if literal.language else None  # RDF 1.1: tags compare without case
    return AnnotationValue(term=str(term), predicate=str(predicate), text=str(literal), language=language)


def load_ontology(path: str | Path) -> list[AnnotationValue]:
    """The label and description values of every IRI term in the file; raises OntologyFileError naming it."""
    try:
        graph = Graph().parse(path, format=guess_format(str(path)) or "turtle")
    except Exception as error:  # noqa: BLE001 - rdflib raises many parser types; a missing file raises OSError
        raise OntologyFileError(f"ontology file {path} cannot be read: {error}") from error
    values = [_value(s, p, o) for s, p, o in graph if isinstance(s, URIRef) and p in PREDICATES and isinstance(o, Literal)]
    for s, _, label in graph.triples((None, SKOSXL_PREF_LABEL, None)):
        if isinstance(s, URIRef):
            values += [
                _value(s, SKOSXL_PREF_LABEL, o) for o in graph.objects(label, SKOSXL_LITERAL_FORM) if isinstance(o, Literal)
            ]
    return values
