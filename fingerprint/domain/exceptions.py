"""Errors raised by the pure domain rules."""


class IriRefError(ValueError):
    """An IRI that cannot be written as a SPARQL IRIREF."""

    def __init__(self, iri: str):
        super().__init__(f"not usable in a SPARQL query: {iri!r}")
        self.iri = iri
