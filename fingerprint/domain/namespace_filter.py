"""The namespace filters: which namespaces the outputs hide or exclude (namespace-filter DEC-6, DEC-7).

Pure: no I/O. `namespace_filter` turns the user's values into two sets of namespaces; the hidden set stays a
class-level rule of the generators, the excluded set is removed from the analytics once (`exclude_terms`).
"""

from collections.abc import Callable, Collection
from typing import TypeVar

from fingerprint.domain.analytics import value_type_indicators
from fingerprint.domain.prefixes import PrefixTable, namespace_of
from fingerprint.domain.profile import (
    ClassAnalytics,
    ExcludedTerms,
    GraphAnalytics,
    NamespaceUse,
    NodeKind,
    ProfileAnalytics,
    PropertyAnalytics,
)
from fingerprint.domain.views import FilterMatch, FilterOption, GeneratorOptions, NamespaceFilter
from fingerprint.domain.vocabulary import OWL, RDF, RDFS, SH

# The meta vocabularies no output shows by default (readable-representations DEC-8).
META_NAMESPACES = frozenset({RDF, RDFS, OWL, SH})


def namespace_filter(options: GeneratorOptions, table: PrefixTable) -> NamespaceFilter:
    """The hidden set (meta namespaces less the included) and the excluded set (matched by an exclude value, less
    the included), with one match per distinct value, excludes first."""
    matches = [
        FilterMatch(option=option, name=name, namespaces=[e.namespace for e in table.match(name)])
        for option, names in (
            (FilterOption.exclude, options.exclude_namespaces),
            (FilterOption.include, options.include_namespaces),
        )
        for name in dict.fromkeys(names or [])  # dict-ok: order-keeping dedupe
    ]

    def namespaces(option: FilterOption) -> set[str]:
        return {namespace for m in matches if m.option == option for namespace in m.namespaces or []}

    included = namespaces(FilterOption.include)
    return NamespaceFilter(
        hidden=sorted(META_NAMESPACES - included),
        excluded=sorted(namespaces(FilterOption.exclude) - included),
        matches=matches,
    )


_VALUE_TYPE_FIELDS = {"value_types", "dominant_value_type", "type_purity", "untyped_object_ratio"}
_Item = TypeVar("_Item")


def namespace_uses(analytics: ProfileAnalytics, table: PrefixTable) -> list[NamespaceUse]:
    """Per namespace of the table, in table order: the instances of its classes plus the subjects of its
    properties, over every class and graph (fingerprint-report "Namespace table order")."""
    uses = [0] * len(table.entries)
    position = {e.namespace: i for i, e in enumerate(table.entries)}  # dict-ok: lookup index namespace → row

    def count(iri: str, n: int | None) -> None:
        entry = table.entry_for(iri)
        if entry:
            uses[position[entry.namespace]] += n or 0

    for graph in analytics.graphs or []:
        for cls in graph.class_partitions or []:
            count(cls.class_iri, cls.instances)
            for prop in cls.property_partitions or []:
                count(prop.property, prop.subjects_with_property)
    return [NamespaceUse(namespace=e.namespace, uses=n) for e, n in zip(table.entries, uses, strict=True)]


class _Removal:
    """Removes the IRIs of the excluded namespaces from one graph and remembers which, per position."""

    def __init__(self, excluded: Collection[str], table: PrefixTable):
        self.excluded = frozenset(excluded)
        self.table = table
        self.classes: set[str] = set()
        self.properties: set[str] = set()
        self.values: set[str] = set()

    def namespace(self, iri: str) -> str:
        entry = self.table.entry_for(iri)
        return entry.namespace if entry else namespace_of(iri)

    def gone(self, iri: str | None, seen: set[str]) -> bool:
        """Whether `iri` is excluded; it is then noted in `seen`."""
        if iri and self.namespace(iri) in self.excluded:
            seen.add(iri)
            return True
        return False

    def keep(self, items: list[_Item] | None, iri_of: Callable[[_Item], str | None], seen: set[str]) -> list[_Item] | None:
        return None if items is None else [item for item in items if not self.gone(iri_of(item), seen)]

    def terms(self) -> list[ExcludedTerms]:
        found = {self.namespace(iri) for iri in self.classes | self.properties | self.values}

        def count(seen: set[str], namespace: str) -> int:
            return sum(self.namespace(iri) == namespace for iri in seen)

        return [
            ExcludedTerms(
                namespace=namespace,
                classes=count(self.classes, namespace),
                properties=count(self.properties, namespace),
                values=count(self.values, namespace),
            )
            for namespace in sorted(found)
        ]

    def prop(self, prop: PropertyAnalytics) -> PropertyAnalytics:
        """A kept property: object classes cleared (and the value types re-derived), a single excluded value dropped."""
        partitions, cleared = [], False
        for part in prop.value_partitions or []:
            if self.gone(part.object_class, self.classes):
                part = part.model_copy(update={"object_class": None, "object_class_graph": None})
                cleared = True
            partitions.append(part)
        if cleared:
            indicators = value_type_indicators(partitions, prop.total_triples or 0)
            prop = prop.model_copy(
                update={"value_partitions": partitions, **indicators.model_dump(include=_VALUE_TYPE_FIELDS)}
            )
        if prop.top_values and _is_single_iri(prop) and self.gone(prop.top_values[0].value, self.values):
            prop = prop.model_copy(update={"top_values": prop.top_values[1:]})
        return prop

    def cls(self, cls: ClassAnalytics) -> ClassAnalytics:
        """A kept class: excluded properties, co-types and parents dropped."""
        props = self.keep(cls.property_partitions, lambda p: p.property, self.properties) or []
        return cls.model_copy(
            update={
                "property_partitions": [self.prop(p) for p in props],
                "co_types": self.keep(cls.co_types, lambda c: c.class_iri, self.classes),
                "parents": self.keep(cls.parents, lambda p: p.parent, self.classes),
            }
        )

    def graph(self, graph: GraphAnalytics) -> GraphAnalytics:
        kept = self.keep(graph.class_partitions, lambda c: c.class_iri, self.classes) or []
        return graph.model_copy(
            update={
                "class_partitions": [self.cls(c) for c in kept],
                "term_annotations": self.keep(graph.term_annotations, lambda a: a.term, set()),
                "excluded_terms": self.terms(),
            }
        )


def _is_single_iri(prop: PropertyAnalytics) -> bool:
    """Whether the first top value is the one IRI every object is, the only top value an output writes (P-7)."""
    partitions = prop.value_partitions or []
    only_iris = bool(partitions) and all(p.node_kind == NodeKind.iri for p in partitions)
    return only_iris and prop.distinct_objects == 1


def exclude_terms(analytics: ProfileAnalytics, excluded: Collection[str], table: PrefixTable) -> ProfileAnalytics:
    """The analytics without the terms of the `excluded` namespaces, at the positions an output writes (design §B).

    Every other value stays as analysed, except the four value-type fields of a property that lost an object class.
    Each graph notes what was removed (`excluded_terms`): the distinct IRIs per namespace and position, those under
    a dropped class or property not counted since no output would write them. `namespace_uses` is set from the
    analytics before anything is removed. Returns copies; the input is unchanged."""
    graphs = [_Removal(excluded, table).graph(graph) for graph in analytics.graphs or []]
    return analytics.model_copy(update={"graphs": graphs, "namespace_uses": namespace_uses(analytics, table)})


def note_text(terms: list[ExcludedTerms] | None, table: PrefixTable) -> str | None:
    """`prefix (classes c, properties p, values v)` per namespace in prefix order, joined by `; `; None for none."""

    def prefix(namespace: str) -> str:
        entry = table.by_namespace(namespace)
        return entry.prefix if entry else namespace

    if not terms:
        return None
    return "; ".join(
        f"{prefix(t.namespace)} (classes {t.classes}, properties {t.properties}, values {t.values})"
        for t in sorted(terms, key=lambda t: prefix(t.namespace))
    )
