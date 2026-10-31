"""Namespaces, generated prefixes and the prefix table every output shortens IRIs with (namespace-prefixes).

Pure: no I/O. The rules are the spec's "Generated prefixes" rules 1–5 (readable-representations DEC-2, DEC-10).
"""

import re
import urllib.parse
from collections.abc import Iterable, Sequence

from fingerprint.domain.profile import NamespacePrefix, PrefixSource
from fingerprint.domain.vocabulary import FP, OWL, RDF, RDFS, SH, XSD

# The prefixes the outputs write themselves: no other namespace may take them.
STANDARD = {"rdf": RDF, "rdfs": RDFS, "owl": OWL, "xsd": XSD, "sh": SH, "fp": FP}
_VERSION = re.compile(r"v?\d+(\.\d+)*")
_NOT_PREFIX = re.compile(r"[^a-z0-9-]+")


def namespace_of(iri: str) -> str:
    """Up to the last `#` when no `/` follows it, else up to the last `/`; a `urn:` without either, the last `:`."""
    hash_at = iri.rfind("#")
    if hash_at >= 0 and "/" not in iri[hash_at + 1 :]:
        return iri[: hash_at + 1]
    slash_at = iri.rfind("/")
    if slash_at >= 0:
        return iri[: slash_at + 1]
    if iri.startswith("urn:"):
        return iri[: iri.rfind(":") + 1]
    return iri


def _parts(namespace: str) -> tuple[str, list[str], list[str]]:
    """(scheme, host labels without the port, path segments incl. a fragment's when it holds a `/`)."""
    if namespace.startswith("urn:"):
        return "urn", [], [part for part in namespace.split(":")[1:] if part]
    split = urllib.parse.urlsplit(namespace)
    segments = [part for part in split.path.split("/") if part]
    if "/" in split.fragment:
        segments += [part for part in split.fragment.split("/") if part]
    host = split.hostname or ""
    return split.scheme.lower(), [label for label in host.split(".") if label], segments


def path_segments(namespace: str) -> list[str]:
    return _parts(namespace)[2]


def is_reserved(prefix: str, namespace: str | None = None) -> bool:
    """Whether `prefix` may not name `namespace`: a standard prefix of another namespace, or a shape prefix."""
    if prefix == "shape" or prefix.endswith("-shape"):
        return True
    return prefix in STANDARD and STANDARD[prefix] != namespace


def _clean(text: str) -> str:
    cleaned = _NOT_PREFIX.sub("-", text.lower())
    cleaned = re.sub("-+", "-", cleaned).strip("-")
    if cleaned[:1].isdigit():
        cleaned = "n" + cleaned
    return cleaned or "ns"


def _parent_name(namespace: str, table: Sequence[NamespacePrefix]) -> str | None:
    """Rule 2: the most specific named namespace that this one extends by path segments or leading host labels."""
    scheme, labels, segments = _parts(namespace)
    best: tuple[int, str, list[str]] | None = None
    for known in table:
        k_scheme, k_labels, k_segments = _parts(known.namespace)
        if k_scheme != scheme:
            continue
        if k_labels == labels and len(k_segments) < len(segments) and segments[: len(k_segments)] == k_segments:
            extra = segments[len(k_segments) :]
        elif k_segments == segments and len(k_labels) < len(labels) and labels[len(labels) - len(k_labels) :] == k_labels:
            extra = labels[: len(labels) - len(k_labels)]
        else:
            continue
        rank = len(k_labels) + len(k_segments)
        if best is None or (rank, known.prefix) > (best[0], best[1]):
            best = (rank, known.prefix, extra)
    return None if best is None else _clean("-".join([best[1], *best[2]]))


def _own_name(namespace: str) -> str:
    """Rule 3: the last meaningful path segment, else the domain's own label."""
    _, labels, segments = _parts(namespace)
    for segment in reversed(segments):
        if not segment.isdigit() and not _VERSION.fullmatch(segment):
            return _clean(segment)
    if labels[:1] == ["www"]:
        labels = labels[1:]
    rest = labels[:-1]
    if len(labels) >= 3 and rest and len(rest[-1]) <= 3:
        rest = rest[:-1]
    return _clean(rest[-1] if rest else "")


def _depth(namespace: str) -> tuple[int, str]:
    _, labels, segments = _parts(namespace)
    return len(labels) + len(segments), namespace


def generate_prefixes(namespaces: Iterable[str], table: Sequence[NamespacePrefix]) -> list[NamespacePrefix]:
    """Prefixes for the namespaces `table` does not name, parents first (depth, then lexical order)."""
    named = {entry.namespace for entry in table}
    known = list(table)
    taken = {entry.prefix.lower() for entry in table}  # prefixes reach file names: compare case-insensitively
    generated = []
    for namespace in sorted(set(namespaces) - named, key=_depth):
        base = _parent_name(namespace, known) or _own_name(namespace)
        prefix, n = base, 1
        while prefix.lower() in taken or is_reserved(prefix):
            n += 1
            prefix = f"{base}{n}"
        entry = NamespacePrefix(prefix=prefix, namespace=namespace, source=PrefixSource.generated)
        known.append(entry)
        taken.add(prefix.lower())
        generated.append(entry)
    return generated


class PrefixTable:
    """A profile's namespace table, shortening each IRI by its longest namespace (DEC-10)."""

    def __init__(self, entries: Iterable[NamespacePrefix] | None):
        self.entries = list(entries or [])
        self._by_prefix = {e.prefix: e for e in self.entries}  # dict-ok: lookup index
        self._by_namespace = {e.namespace: e for e in self.entries}  # dict-ok: lookup index
        self._longest_first = sorted(self.entries, key=lambda e: len(e.namespace), reverse=True)
        self._cache: dict[str, NamespacePrefix | None] = {}  # dict-ok: memo of IRI → entry

    def entry_for(self, iri: str) -> NamespacePrefix | None:
        if iri not in self._cache:
            exact = self._by_namespace.get(namespace_of(iri))
            self._cache[iri] = exact or next((e for e in self._longest_first if iri.startswith(e.namespace)), None)
        return self._cache[iri]

    def shorten(self, iri: str) -> tuple[str, str] | None:
        """(prefix, local part), or None when no namespace begins the IRI."""
        entry = self.entry_for(iri)
        return None if entry is None else (entry.prefix, iri[len(entry.namespace) :])

    def curie(self, iri: str) -> str:
        """For display: `prefix:local`, or the IRI itself when no namespace begins it."""
        found = self.shorten(iri)
        return f"{found[0]}:{found[1]}" if found else iri

    def by_prefix(self, prefix: str) -> NamespacePrefix | None:
        return self._by_prefix.get(prefix)

    def by_namespace(self, namespace: str) -> NamespacePrefix | None:
        return self._by_namespace.get(namespace)

    def resolve(self, name: str) -> NamespacePrefix | None:
        """A `--exclude-namespace`/`--include-namespace` value: a prefix first, then a namespace IRI."""
        return self.by_prefix(name) or self.by_namespace(name)
