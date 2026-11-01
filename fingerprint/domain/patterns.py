"""The pattern view of a graph (llm-schema-tools P-2; rules §B of the design). Pure: no I/O.

`pattern_view` turns one graph's analytics into the `PatternGraph` the pattern schema and the ShExC are
written from. Every rule that decides what a line says lives here, not in a template.
"""

import json
import re
from bisect import bisect_left
from collections.abc import Iterable
from dataclasses import dataclass
from itertools import groupby

from fingerprint.domain.exceptions import IriRefError
from fingerprint.domain.iri import to_iriref, turtle_term
from fingerprint.domain.prefixes import PrefixTable, namespace_of
from fingerprint.domain.profile import (
    CardinalityBin,
    ClassAnalytics,
    GraphAnalytics,
    NodeKind,
    PrecisionMode,
    PropertyAnalytics,
    ValuePartition,
)
from fingerprint.domain.views import EdgeTarget, GeneratorOptions, PatternBlock, PatternEdge, PatternGraph, TargetKind
from fingerprint.domain.vocabulary import RDF_LANG_STRING, XSD_STRING

VALUE_LIMIT = 64  # characters of a value in a stat token (P-8)
_BARE_VALUE = re.compile(r'[^\s"]+')
IRI, BNODE, UNKNOWN = "IRI", "BNODE", "."
_ORDER = (TargetKind.group, TargetKind.datatype, TargetKind.iri, TargetKind.blank_node)  # the order targets are written


class _Lookup[V]:
    """A read-only map over sorted keys, by bisection: the domain composes no dicts (domain-object-model DEC-1)."""

    def __init__(self, pairs: Iterable[tuple[str, V]]):
        self._pairs = sorted(pairs, key=lambda pair: pair[0])
        self._keys = [key for key, _ in self._pairs]

    def get(self, key: str) -> V | None:
        at = bisect_left(self._keys, key)
        return self._pairs[at][1] if at < len(self._keys) and self._keys[at] == key else None


class _Namer:
    """Step 1: how an IRI is written, and the IRIs that cannot be (they are skipped, not broken)."""

    def __init__(self, table: PrefixTable):
        self.table = table
        self.skipped: set[str] = set()

    def name(self, iri: str) -> str | None:
        try:
            return turtle_term(iri, self.table)[0]
        except IriRefError:
            self.skipped.add(iri)
            return None


@dataclass(frozen=True)
class _Group:
    """Classes that always occur together (N2): one block, named by its members."""

    name: str
    members: tuple[ClassAnalytics, ...]  # in name order
    shape: str  # the ShExC label: the first shown member's name
    shown: bool  # some member's namespace is not excluded

    @property
    def instances(self) -> int:
        return self.members[0].instances

    @property
    def classes(self) -> list[str]:
        return [member.class_iri for member in self.members]


@dataclass(frozen=True)
class _Link:
    """A value partition that reaches a group of this graph."""

    source: int
    property: str
    target: int
    partition: ValuePartition


@dataclass(frozen=True)
class _Alternative:
    kind: TargetKind
    text: str
    target: EdgeTarget


@dataclass(frozen=True)
class _Spec:
    """One property of a group, ready to be an edge."""

    property: str
    name: str
    targets: tuple[EdgeTarget, ...]
    head: str  # the line after the indent, without a nesting ending
    stats: str
    low: int | None
    high: int | None
    presence_only: bool


# --- step 5: stat tokens and value quoting ---


def quoted(value: str) -> str:
    """A value bare when it reads as one word of a line, else a JSON string cut at 64 characters."""
    if _BARE_VALUE.fullmatch(value) and ".." not in value and len(value) <= VALUE_LIMIT:
        return value
    cut = value[:VALUE_LIMIT] + ("…" if len(value) > VALUE_LIMIT else "")
    return json.dumps(cut, ensure_ascii=False)


def _objects(partition: ValuePartition) -> int:
    return partition.distinct_objects if partition.distinct_objects is not None else partition.triples or 0


def _values_per_subject(histogram: list[CardinalityBin] | None) -> tuple[int, int] | None:
    counts = [bin_.values_per_subject for bin_ in histogram or []]
    return (min(counts), max(counts)) if counts else None


def _multiplicity(bounds: tuple[int, int] | None) -> list[str]:
    if bounds is None or bounds == (1, 1):
        return []
    low, high = bounds
    return [f"×{low}" if low == high else f"×{low}-{high}"]


def _languages(partitions: list[ValuePartition]) -> list[str]:
    tags = sorted({p.language for p in partitions if p.language})
    if not tags:
        return []
    return [f"@{tags[0]}" if len(tags) == 1 else f"@{len(tags)}"]


def _datatype(partition: ValuePartition) -> str:
    return partition.datatype or (RDF_LANG_STRING if partition.language else XSD_STRING)


def _literal_range(partitions: list[ValuePartition]) -> tuple[list[str], bool]:
    """(`=v` or `lo..hi`, whether it is one value): only for one plain literal datatype with a minimum."""
    literals = [p for p in partitions if p.node_kind == NodeKind.literal]
    if len(literals) != 1 or _datatype(literals[0]) == RDF_LANG_STRING or literals[0].min_value is None:
        return [], False
    low = literals[0].min_value
    high = low if literals[0].max_value is None else literals[0].max_value
    if low == high:
        return [f"={quoted(low)}"], True
    return [f"{quoted(low)}..{quoted(high)}"], False


def _single_iri(prop: PropertyAnalytics, partitions: list[ValuePartition]) -> str | None:
    """The one IRI every object is, from the top values (depth `rich_values` or deeper)."""
    only_iris = bool(partitions) and all(p.node_kind == NodeKind.iri for p in partitions)
    if only_iris and prop.distinct_objects == 1 and prop.top_values:
        return prop.top_values[0].value
    return None


def _fewer_distinct(prop: PropertyAnalytics) -> bool:
    return prop.distinct_objects is not None and prop.total_triples is not None and prop.distinct_objects < prop.total_triples


def _tokens(prop: PropertyAnalytics, partitions: list[ValuePartition], bounds, value_name: str | None) -> list[str]:
    """The tokens after coverage, in the order the table of step 5 gives."""
    tokens = _multiplicity(bounds)
    if any(p.node_kind == NodeKind.blank_node for p in partitions):
        tokens.append("bn")
    tokens += _languages(partitions)
    value, single = _literal_range(partitions)
    tokens += value
    if value_name:
        tokens.append(f"={value_name}")
    if not (single or value_name) and _fewer_distinct(prop):
        tokens.append(f"d{prop.distinct_objects}")
    return tokens


# --- the builder ---


class _Builder:
    def __init__(self, graph: GraphAnalytics, table: PrefixTable, options: GeneratorOptions, excluded: frozenset[str]):
        self.graph = graph
        self.table = table
        self.options = options
        self.excluded = excluded
        self.namer = _Namer(table)
        classes = [(name, c) for c in graph.class_partitions or [] if (name := self.namer.name(c.class_iri)) is not None]
        self.groups = self._groups(sorted(classes, key=lambda pair: pair[0]))
        self.group_of = _Lookup((member.class_iri, i) for i, g in enumerate(self.groups) for member in g.members)
        self.nested = self._nested()
        self.kept = self._kept()

    # step 2
    def _shown(self, class_iri: str) -> bool:
        entry = self.table.entry_for(class_iri)
        return (entry.namespace if entry else namespace_of(class_iri)) not in self.excluded

    def _groups(self, named: list[tuple[str, ClassAnalytics]]) -> list[_Group]:
        index = _Lookup((c.class_iri, i) for i, (_, c) in enumerate(named))
        parent = list(range(len(named)))

        def find(i: int) -> int:
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i

        for i, (_, c) in enumerate(named):
            for co in c.co_types or []:
                j = index.get(co.class_iri or "")
                if j is not None and co.subjects == c.instances == named[j][1].instances:
                    parent[find(i)] = find(j)
        roots = sorted((find(i), i) for i in range(len(named)))
        groups = [self._group([named[i] for _, i in run]) for _, run in groupby(roots, key=lambda r: r[0])]
        return sorted(groups, key=lambda g: g.name)

    def _group(self, named: list[tuple[str, ClassAnalytics]]) -> _Group:
        shown = [name for name, c in named if self._shown(c.class_iri)]
        return _Group(
            name="&".join(name for name, _ in named),
            members=tuple(c for _, c in named),
            shape=(shown or [named[0][0]])[0],
            shown=bool(shown),
        )

    # step 3
    def _other_graph(self, partition: ValuePartition) -> bool:
        return bool(partition.object_class_graph) and partition.object_class_graph != self.graph.graph

    def _target_group(self, partition: ValuePartition) -> int | None:
        if not partition.object_class or self._other_graph(partition):
            return None
        return self.group_of.get(partition.object_class)

    def _links(self) -> list[_Link]:
        return [
            _Link(source, prop.property, target, partition)
            for source, group in enumerate(self.groups)
            for member in group.members
            for prop in member.property_partitions or []
            for partition in prop.value_partitions or []
            if (target := self._target_group(partition)) is not None
        ]

    def _nested(self) -> list[bool]:
        nested = [False] * len(self.groups)
        reaching = sorted(self._links(), key=lambda link: link.target)
        for target, run in groupby(reaching, key=lambda link: link.target):
            nested[target] = self._is_nested(self.groups[target], list(run))
        return nested

    @staticmethod
    def _is_nested(group: _Group, links: list[_Link]) -> bool:
        """P-4: only blank nodes reach it, and the distinct objects reaching it cover its instances."""
        if any(link.partition.node_kind != NodeKind.blank_node for link in links):
            return False
        by_edge = sorted(links, key=lambda link: (link.source, link.property))
        reached = sum(
            max(_objects(link.partition) for link in run)
            for _, run in groupby(by_edge, key=lambda link: (link.source, link.property))
        )
        return reached >= group.instances

    # step 4
    def _kept(self) -> list[int]:
        """The named groups that get a block, largest first."""
        named = [i for i, g in enumerate(self.groups) if g.shown and not self.nested[i]]
        named.sort(key=lambda i: (-self.groups[i].instances, self.groups[i].name))
        named = [i for i in named if self.groups[i].instances >= (self.options.min_instances or 0)]
        return named[: self.options.max_classes] if self.options.max_classes else named

    def hidden_classes(self) -> int:
        hidden = [i for i, nested in enumerate(self.nested) if not nested and i not in self.kept]
        return sum(len(self.groups[i].members) for i in hidden)

    # step 5
    def _class_alternative(self, partition: ValuePartition) -> _Alternative | None:
        target = self._target_group(partition)
        if target is not None:
            group = self.groups[target]
            shape = target in self.kept
            return _Alternative(
                TargetKind.group,
                group.name,
                EdgeTarget(kind=TargetKind.group, name=group.name, classes=group.classes, has_shape=shape),
            )
        iri = partition.object_class or ""
        name = self.namer.name(iri)
        graph = partition.object_class_graph if self._other_graph(partition) else None
        if name is None or (graph and not _writable(graph)):
            return None
        text = f"{name} @{to_iriref(graph)}" if graph else name
        return _Alternative(
            TargetKind.group, text, EdgeTarget(kind=TargetKind.group, name=name, classes=[iri], graph=graph, has_shape=False)
        )

    def _alternative(self, partition: ValuePartition) -> _Alternative | None:
        if partition.object_class:
            return self._class_alternative(partition)
        if partition.node_kind == NodeKind.literal:
            name = self.namer.name(_datatype(partition))
            return (
                None
                if name is None
                else _Alternative(TargetKind.datatype, name, EdgeTarget(kind=TargetKind.datatype, name=name))
            )
        kind, text = (TargetKind.iri, IRI) if partition.node_kind == NodeKind.iri else (TargetKind.blank_node, BNODE)
        return _Alternative(kind, text, EdgeTarget(kind=kind, name=text))

    def _alternatives(self, partitions: list[ValuePartition]) -> list[_Alternative]:
        found = [alt for p in partitions if (alt := self._alternative(p)) is not None]
        found.sort(key=lambda alt: (_ORDER.index(alt.kind), alt.text))
        return [next(run) for _, run in groupby(found, key=lambda alt: (alt.kind, alt.text))]

    @staticmethod
    def _target_text(alternatives: list[_Alternative]) -> str:
        groups = [alt.text for alt in alternatives if alt.kind == TargetKind.group]
        parts = [f"(:{'|'.join(groups)})"] if groups else []
        parts += [alt.text for alt in alternatives if alt.kind != TargetKind.group]
        return "|".join(parts) or UNKNOWN

    def _spec(self, name: str, prop: PropertyAnalytics, owner: ClassAnalytics) -> _Spec:
        partitions = prop.value_partitions or []
        alternatives = self._alternatives(partitions)
        bounds = _values_per_subject(prop.cardinality_histogram)
        seen, observed = prop.subjects_with_property, owner.observed_instances or owner.instances
        partial = seen is not None and seen < observed
        iri = _single_iri(prop, partitions)
        if prop.presence_only:
            tokens = ["presence"]
        else:
            tokens = ([f"{seen}/{observed}"] if partial else []) + _tokens(
                prop, partitions, bounds, self.namer.name(iri) if iri else None
            )
        stats = " ".join(tokens)
        line = f"-{name}-> {self._target_text(alternatives)}" + (f" {stats}" if stats else "")
        return _Spec(
            property=prop.property,
            name=name,
            targets=tuple(alt.target for alt in alternatives) or (EdgeTarget(kind=TargetKind.unknown, name=UNKNOWN),),
            head=line,
            stats=stats,
            low=None if bounds is None else (0 if partial else bounds[0]),
            high=None if bounds is None else bounds[1],
            presence_only=bool(prop.presence_only),
        )

    def specs(self, group: _Group) -> list[_Spec]:
        """One spec for each property name of the group, from the first member that has it."""
        rows = [
            (name, order, prop, member)
            for order, member in enumerate(group.members)
            for prop in member.property_partitions or []
            if (name := self.namer.name(prop.property)) is not None
        ]
        rows.sort(key=lambda row: (row[0], row[1]))
        return [
            self._spec(name, prop, member)
            for name, _, prop, member in (next(run) for _, run in groupby(rows, key=lambda r: r[0]))
        ]

    # the blocks
    def edge(self, spec: _Spec) -> PatternEdge:
        return PatternEdge(
            property=spec.property,
            name=spec.name,
            depth=1,
            targets=list(spec.targets),
            text=spec.head,
            stats=spec.stats,
            ending="",
            min_count=spec.low,
            max_count=spec.high,
            presence_only=spec.presence_only,
            edges=[],
        )

    def block(self, index: int) -> PatternBlock:
        group = self.groups[index]
        first = group.members[0]
        first_n = first.precision_mode == PrecisionMode.first_n
        return PatternBlock(
            name=group.name,
            classes=group.classes,
            shape=group.shape,
            instances=group.instances,
            observed=first.observed_instances if first_n else None,
            nested=False,
            edges=[self.edge(spec) for spec in self.specs(group)],
        )


def _writable(iri: str) -> bool:
    try:
        to_iriref(iri)
    except IriRefError:
        return False
    return True


def pattern_view(
    graph: GraphAnalytics,
    table: PrefixTable,
    options: GeneratorOptions,
    *,
    excluded: frozenset[str],
    graph_label: str,
    slug: str,
) -> PatternGraph:
    """The pattern view of one graph. `excluded` are the namespaces whose classes are hidden (the generator's
    `excluded_namespaces`); `graph_label` and `slug` name the graph for the output file."""
    builder = _Builder(graph, table, options, excluded)
    blocks = [builder.block(i) for i in builder.kept]
    return PatternGraph(
        graph=graph.graph,
        graph_label=graph_label,
        slug=slug,
        hidden_classes=builder.hidden_classes(),
        blocks=blocks,
        nested_blocks=[],
        prefixes=[],
        glossary=[],
        skipped=sorted(builder.namer.skipped),
    )
