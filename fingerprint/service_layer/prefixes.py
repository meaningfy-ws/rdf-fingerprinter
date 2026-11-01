"""Resolve the namespace table of a run: user file > saved table > packaged > prefix.cc > generated (namespace-prefixes).

Pure apart from the one optional prefix.cc fetch; running it on its own output gives the same table.
"""

import logging
from collections.abc import Iterable, Iterator, Sequence

from pydantic import BaseModel

from fingerprint import config
from fingerprint.adapters.prefixes import PrefixListSource, PrefixLookupError, load_packaged_prefixes, valid_prefix
from fingerprint.domain.exceptions import IriRefError
from fingerprint.domain.iri import to_iriref
from fingerprint.domain.prefixes import STANDARD, generate_prefixes, is_reserved, namespace_of
from fingerprint.domain.profile import NamespacePrefix, NodeKind, PitfallTerm, PrefixSource, ProfileRun
from fingerprint.domain.vocabulary import RDF

logger = logging.getLogger(__name__)

# The profile's IRI-valued fields: graphs, classes, properties, value types, parents and linked classes.
IRI_FIELDS = frozenset(
    {
        "graph",
        "class_iri",
        "property",
        "datatype",
        "object_class",
        "object_class_graph",
        "sub_class",
        "super_class",
        "subject_class",
        "parent",
    }
)


def _iris(value: object) -> Iterator[tuple[str, bool]]:
    """Each IRI the value holds, and whether it is a pitfall example's term."""
    if isinstance(value, PitfallTerm):  # a pitfall example's term: only IRIs have a namespace (pitfall-scans DEC-11)
        if value.kind == NodeKind.iri:
            yield value.text, True
        return
    if isinstance(value, BaseModel):
        for name in type(value).model_fields:
            if name == "settings" or name == "namespaces":
                continue
            item = getattr(value, name)
            if name in IRI_FIELDS and isinstance(item, str) and item:
                yield item, False
            else:
                yield from _iris(item)
    elif isinstance(value, list):
        for item in value:
            yield from _iris(item)


def _writable(namespace: str) -> bool:
    try:
        to_iriref(namespace)
    except IriRefError:
        return False
    return True


def used_namespaces(run: ProfileRun) -> set[str]:
    """The namespace of every IRI the profile holds, and rdf (types, and the analytics' rdf:langString);
    one that cannot be written as an IRI is left out."""
    iris = list(_iris(run))
    profiled = {namespace_of(iri) for iri, term in iris if not term} | {RDF}
    # the ontology's own IRI in a finding (a namespace without its `#` or `/`) adds none (pitfall-scans DEC-17)
    found = {namespace_of(iri) for iri, term in iris if term and iri + "#" not in profiled and iri + "/" not in profiled}
    return {ns for ns in profiled | found if _writable(ns)}


def resolve_namespaces[Run: ProfileRun](  # a raw run or its analytics: model_copy keeps the type
    run: Run,
    user: Sequence[NamespacePrefix] = (),
    packaged: Sequence[NamespacePrefix] | None = None,
    prefix_list: PrefixListSource | None = None,
) -> Run:
    """The run with its namespace table; `packaged` defaults to the packaged file, `prefix_list` None: no fetch."""
    used = used_namespaces(run)
    packaged = load_packaged_prefixes(config.packaged_prefixes_file) if packaged is None else packaged
    table: dict[str, NamespacePrefix] = {}  # dict-ok: lookup index namespace → entry
    holders: set[str] = set()

    def wanted(namespace: str) -> bool:  # used, or a named parent of a used namespace (rule 2 needs it)
        return namespace in used or any(u.startswith(namespace) for u in used)

    def offer(entries: Iterable[NamespacePrefix]) -> None:
        """One source: only its first prefix per namespace counts; when that one is skipped, the namespace
        falls to the next source, never to this source's next alias."""
        seen: set[str] = set()
        for entry in entries:
            if entry.namespace in seen:
                continue
            seen.add(entry.namespace)
            if entry.namespace in table or not wanted(entry.namespace):
                continue
            if not valid_prefix(entry.prefix, entry.namespace):  # e.g. a hand-edited profile.json
                logger.debug("prefix %r for %s skipped: not a prefix with a writable IRI", entry.prefix, entry.namespace)
                continue
            if is_reserved(entry.prefix, entry.namespace) or entry.prefix.lower() in holders:
                logger.debug("prefix %r for %s skipped: reserved or taken", entry.prefix, entry.namespace)
                continue
            table[entry.namespace] = entry
            holders.add(entry.prefix.lower())

    offer(user)  # first: a user prefix displaces a saved one, whose namespace then falls through
    offer(run.namespaces or [])
    offer(packaged)
    offer(NamespacePrefix(prefix=p, namespace=ns, source=PrefixSource.packaged) for p, ns in STANDARD.items())
    if prefix_list is not None and used - table.keys():
        try:
            offer(prefix_list.fetch())
        except PrefixLookupError as error:
            logger.warning("prefix.cc lookup failed: %s; generating prefixes", error)
    named = list(table.values())
    named += generate_prefixes(used - table.keys(), named)
    return run.model_copy(update={"namespaces": sorted((e for e in named if e.namespace in used), key=lambda e: e.prefix)})
