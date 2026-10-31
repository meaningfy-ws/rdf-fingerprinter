"""The IRIREF guard every IRI passes before it is put into a SPARQL query (P-3)."""

import re

from fingerprint.domain.exceptions import IriRefError  # noqa: F401 — also importable from here (2.0)

# SPARQL 1.1 IRIREF excludes these characters and U+0000–U+0020.
_NOT_IRIREF = re.compile(r'[<>"{}|^`\\\x00-\x20]')


def to_iriref(iri: str) -> str:
    """Return `<iri>`; raise IriRefError when the IRI cannot be written as a SPARQL IRIREF."""
    if _NOT_IRIREF.search(iri):
        raise IriRefError(iri)
    return f"<{iri}>"
