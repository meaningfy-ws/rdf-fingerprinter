"""The IRIREF guard every IRI passes before it is put into a SPARQL query (P-3)."""

import re

# SPARQL 1.1 IRIREF excludes these characters and U+0000–U+0020.
_NOT_IRIREF = re.compile(r'[<>"{}|^`\\\x00-\x20]')


class IriRefError(ValueError):
    """An IRI that cannot be written as a SPARQL IRIREF."""

    def __init__(self, iri: str):
        super().__init__(f"not usable in a SPARQL query: {iri!r}")
        self.iri = iri


def to_iriref(iri: str) -> str:
    """Return `<iri>`; raise IriRefError when the IRI cannot be written as a SPARQL IRIREF."""
    if _NOT_IRIREF.search(iri):
        raise IriRefError(iri)
    return f"<{iri}>"
