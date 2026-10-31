"""IRI rules: the IRIREF guard every IRI passes before it goes into SPARQL or Turtle (P-3), and Turtle/display terms."""

import re
from collections.abc import Mapping

from fingerprint.domain.exceptions import IriRefError  # noqa: F401 — also importable from here (2.0)

# SPARQL 1.1 IRIREF excludes these characters and U+0000–U+0020.
_NOT_IRIREF = re.compile(r'[<>"{}|^`\\\x00-\x20]')


def to_iriref(iri: str) -> str:
    """Return `<iri>`; raise IriRefError when the IRI cannot be written as a SPARQL IRIREF."""
    if _NOT_IRIREF.search(iri):
        raise IriRefError(iri)
    return f"<{iri}>"


# A conservative ASCII subset of Turtle's PN_LOCAL: anything else is written as a full IRI (P-7).
_SAFE_LOCAL = re.compile(r"[A-Za-z0-9_](?:[A-Za-z0-9_.-]*[A-Za-z0-9_-])?")
_STRING_ESCAPES = str.maketrans({"\\": "\\\\", '"': '\\"', "\n": "\\n", "\r": "\\r", "\t": "\\t"})


def split_curie(iri: str, prefixes: Mapping[str, str]) -> tuple[str, str] | None:  # dict-ok: prefix table
    """(prefix, local part) for the first prefix whose namespace starts the IRI (the report's rule)."""
    for prefix, namespace in prefixes.items():
        if iri.startswith(namespace):
            return prefix, iri[len(namespace) :]
    return None


def turtle_term(iri: str, prefixes: Mapping[str, str]) -> tuple[str, str | None]:  # dict-ok: prefix table
    """`prefix:local` when that is a valid Turtle name, else `<iri>`; also the prefix used, to declare it."""
    iriref = to_iriref(iri)
    found = split_curie(iri, prefixes)
    if found and _SAFE_LOCAL.fullmatch(found[1]):
        return f"{found[0]}:{found[1]}", found[0]
    return iriref, None


def turtle_string(text: str) -> str:
    return '"' + text.translate(_STRING_ESCAPES) + '"'


def turtle_number(value: float | int | bool) -> str:
    """An integer, a decimal rounded to four places (always with a dot), or a boolean, as Turtle writes them."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    text = f"{round(value, 4):.4f}".rstrip("0")
    return text + "0" if text.endswith(".") else text


def curie(iri: str, prefixes: Mapping[str, str]) -> str:  # dict-ok: prefix table
    """For display only: any matching namespace shortens the IRI, whatever its local part."""
    found = split_curie(iri, prefixes)
    return f"{found[0]}:{found[1]}" if found else iri
