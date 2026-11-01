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

from fingerprint.domain.annotations import shown as shown_text
from fingerprint.domain.exceptions import IriRefError
from fingerprint.domain.iri import to_iriref, turtle_term
from fingerprint.domain.prefixes import PrefixTable, namespace_of
from fingerprint.domain.profile import (
    CardinalityBin,
    ClassAnalytics,
    GraphAnalytics,
    LangText,
    NodeKind,
    PrecisionMode,
    PropertyAnalytics,
    ValuePartition,
)
from fingerprint.domain.views import (
    CoTypeNote,
    EdgeTarget,
    GeneratorOptions,
    GlossaryEntry,
    PatternBlock,
    PatternEdge,
    PatternGraph,
    PrefixDeclaration,
    TargetKind,
    ViaLink,
)
from fingerprint.domain.vocabulary import RDF_LANG_STRING, XSD_STRING

VALUE_LIMIT = 64  # characters of a value in a stat token (P-8)
DESCRIPTION_LIMIT = 200  # characters of a glossary description (P-8)
MAX_LEVEL = 3  # edges sit at levels 1-3 (P-5)
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
    """One way an edge's values can be written, with the IRIs that way names."""

    kind: TargetKind
    text: str
    target: EdgeTarget
    terms: tuple[str, ...]


@dataclass(frozen=True)
class _Stats:
    tokens: tuple[str, ...]
    low: int | None
    high: int | None
    values: tuple[str, ...]  # the IRI a `=name` token writes


@dataclass(frozen=True)
class _Spec:
    """One property of a group, ready to be an edge at any level."""

    property: str
    name: str
    targets: tuple[EdgeTarget, ...]
    head: str  # the line after the indent, without a nesting ending
    stats: str
    low: int | None
    high: int | None
    presence_only: bool
    groups: tuple[tuple[int, int], ...]  # (group reached, the largest triples of a partition reaching it)
    terms: tuple[str, ...]  # every IRI the line writes, but a value
    values: tuple[str, ...]  # the IRI a `=name` token writes: it feeds the prefixes, never the glossary (DEC-16)


# --- step 5: stat tokens and value quoting ---


def quoted(value: str) -> str:
    """A value bare when it reads as one word of a line, else a JSON string cut at 64 characters."""
    if _BARE_VALUE.fullmatch(value) and ".." not in value and len(value) <= VALUE_LIMIT:
        return value
    cut = value[:VALUE_LIMIT] + ("…" if len(value) > VALUE_LIMIT else "")
    return json.dumps(cut, ensure_ascii=False)


def _first_n(*classes: ClassAnalytics) -> bool:
    return any(c.precision_mode == PrecisionMode.first_n for c in classes)


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
    one = literals[0] if len(literals) == 1 else None
    if one is None or _datatype(one) == RDF_LANG_STRING or one.min_value is None or one.max_value is None:
        return [], False
    low, high = one.min_value, one.max_value
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

# --- the builder ---


class _Builder:
    def __init__(self, graph: GraphAnalytics, table: PrefixTable, options: GeneratorOptions, excluded: frozenset[str]):
        self.graph = graph
        self.table = table
        self.options = options
        self.excluded = excluded
        self.namer = _Namer(table)
        self.used: set[str] = set()  # the IRIs the view writes: they decide the prefixes and the glossary
        self.valued: set[str] = set()  # the IRIs it writes as values: prefixes only, no labels (DEC-16)
        classes = [(name, c) for c in graph.class_partitions or [] if (name := self.namer.name(c.class_iri)) is not None]
        self.groups = self._groups(sorted(classes, key=lambda pair: pair[0]))
        self.group_of = _Lookup((member.class_iri, i) for i, g in enumerate(self.groups) for member in g.members)
        self.nested = self._nested()
        self.kept = self._kept()
        self.specs_of = [self._specs(group) for group in self.groups]
        self.owner = self._assign()
        self.expanded = [i for i, owner in enumerate(self.owner) if owner is not None]
        self.in_view = sorted([*self.kept, *self.expanded])
        self.reaching = self._reaching()

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
                if j is not None and co.subjects == c.instances == named[j][1].instances and not _first_n(c, named[j][1]):
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
        """Members of the named groups without a block, and of the nested groups no edge of the view reaches."""
        hidden = [i for i, nested in enumerate(self.nested) if (i not in self.kept if not nested else self.reaching[i] == 0)]
        return sum(len(self.groups[i].members) for i in hidden)

    # step 5
    def _class_alternative(self, partition: ValuePartition) -> _Alternative | None:
        target = self._target_group(partition)
        if target is not None:
            group = self.groups[target]
            shape = target in self.kept
            edge_target = EdgeTarget(kind=TargetKind.group, name=group.name, classes=group.classes, has_shape=shape)
            return _Alternative(TargetKind.group, group.name, edge_target, tuple(group.classes))
        iri = partition.object_class or ""
        name = self.namer.name(iri)
        graph = partition.object_class_graph if self._other_graph(partition) else None
        if name is None:
            return None
        if graph and not _writable(graph):
            self.namer.skipped.add(graph)
            graph = None
        text = f"{name} @{to_iriref(graph)}" if graph else name
        edge_target = EdgeTarget(kind=TargetKind.group, name=name, classes=[iri], graph=graph, has_shape=False)
        return _Alternative(TargetKind.group, text, edge_target, (iri,))

    def _alternative(self, partition: ValuePartition) -> _Alternative | None:
        if partition.object_class:
            return self._class_alternative(partition)
        if partition.node_kind == NodeKind.literal:
            datatype = _datatype(partition)
            name = self.namer.name(datatype)
            if name is None:
                return None
            return _Alternative(TargetKind.datatype, name, EdgeTarget(kind=TargetKind.datatype, name=name), (datatype,))
        kind, text = (TargetKind.iri, IRI) if partition.node_kind == NodeKind.iri else (TargetKind.blank_node, BNODE)
        return _Alternative(kind, text, EdgeTarget(kind=kind, name=text), ())

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

    def _stats(self, prop: PropertyAnalytics, owner: ClassAnalytics, partitions: list[ValuePartition]) -> _Stats:
        if prop.presence_only:
            return _Stats(("presence",), None, None, ())
        bounds = _values_per_subject(prop.cardinality_histogram)
        seen, observed = prop.subjects_with_property, owner.observed_instances or owner.instances
        partial = seen is not None and seen < observed
        iri = _single_iri(prop, partitions)
        value_name = self.namer.name(iri) if iri else None
        tokens = ([f"{seen}/{observed}"] if partial else []) + _tokens(prop, partitions, bounds, value_name)
        low = None if bounds is None else (0 if partial else bounds[0])
        return _Stats(tuple(tokens), low, bounds and bounds[1], (iri,) if iri and value_name else ())

    def _spec(self, name: str, prop: PropertyAnalytics, owner: ClassAnalytics) -> _Spec:
        partitions = prop.value_partitions or []
        alternatives = self._alternatives(partitions)
        stats = self._stats(prop, owner, partitions)
        text = " ".join(stats.tokens)
        reached = sorted((t, p.triples or 0) for p in partitions if (t := self._target_group(p)) is not None)
        return _Spec(
            property=prop.property,
            name=name,
            targets=tuple(alt.target for alt in alternatives) or (EdgeTarget(kind=TargetKind.unknown, name=UNKNOWN),),
            head=f"-{name}-> {self._target_text(alternatives)}" + (f" {text}" if text else ""),
            stats=text,
            low=stats.low,
            high=stats.high,
            presence_only=bool(prop.presence_only),
            groups=tuple((t, max(triples for _, triples in run)) for t, run in groupby(reached, key=lambda r: r[0])),
            terms=(prop.property, *(iri for alt in alternatives for iri in alt.terms)),
            values=stats.values,
        )

    def _specs(self, group: _Group) -> list[_Spec]:
        """One spec for each property name of the group, from the first member that has it."""
        rows = [
            (name, order, prop, member)
            for order, member in enumerate(group.members)
            for prop in member.property_partitions or []
            if (name := self.namer.name(prop.property)) is not None
        ]
        rows.sort(key=lambda row: (row[0], row[1]))
        firsts = (next(run) for _, run in groupby(rows, key=lambda row: row[0]))
        return [self._spec(name, prop, member) for name, _, prop, member in firsts]

    # step 6
    def _assign(self) -> list[tuple[int, str] | None]:
        """P-5: at levels 1 and 2, each nested group not yet assigned goes under its best reaching edge: the one
        with the most triples, then by source name, then property name. An edge takes one group, the first by
        name; the others go to their next best edge, or wait for a later level. Level-3 edges never expand a group."""
        owner: list[tuple[int, str] | None] = [None] * len(self.groups)
        frontier = [(i, spec) for i in self.kept for spec in self.specs_of[i]]
        for _ in range(MAX_LEVEL - 1):
            candidates = sorted(
                (target, -triples, self.groups[i].name, spec.name, i, spec.property)
                for i, spec in frontier
                for target, triples in spec.groups
                if self.nested[target] and owner[target] is None
            )
            assigned = []
            for target, run in groupby(candidates, key=lambda c: c[0]):
                free = next(((source, prop) for *_, source, prop in run if (source, prop) not in owner), None)
                if free is not None:  # an edge expands one group only: the first by name that it is best for
                    owner[target] = free
                    assigned.append(target)
            frontier = [(i, spec) for i in assigned for spec in self.specs_of[i]]
        return owner

    def _reaching(self) -> list[int]:
        """For each group, the distinct (source group, property) edges of the view that reach it."""
        edges = sorted({(t, i, spec.property) for i in self.in_view for spec in self.specs_of[i] for t, _ in spec.groups})
        counts = [0] * len(self.groups)
        for target, run in groupby(edges, key=lambda e: e[0]):
            counts[target] = len(list(run))
        return counts

    def _ending(self, nested: list[int], expanded: list[int]) -> str:
        if any(self.owner[t] is None for t in nested):
            return " …"  # a target expanded nowhere: a level-3 edge, or a group this edge's first target left out
        return "" if expanded else " ^" if nested else ""  # else expanded under another edge

    def _edge(self, source: int, spec: _Spec, level: int) -> PatternEdge:
        self.used.update(spec.terms)
        self.valued.update(spec.values)
        nested = [t for t, _ in spec.groups if self.nested[t]]
        expanded = [t for t in nested if self.owner[t] == (source, spec.property)]
        ending = self._ending(nested, expanded)
        return PatternEdge(
            property=spec.property,
            name=spec.name,
            depth=level,
            targets=list(spec.targets),
            text=spec.head + ending,
            stats=spec.stats,
            ending=ending,
            min_count=spec.low,
            max_count=spec.high,
            presence_only=spec.presence_only,
            edges=[edge for t in expanded for edge in self._edges(t, level + 1)],
        )

    def _edges(self, index: int, level: int) -> list[PatternEdge]:
        return [self._edge(index, spec, level) for spec in self.specs_of[index]]

    # steps 7 and 8
    def _via(self, target: int) -> list[tuple[int, _Spec]]:
        """N6: the (source, property) edges of the view that reach the group, by source name and property."""
        found = [(i, spec) for i in self.in_view for spec in self.specs_of[i] if any(t == target for t, _ in spec.groups)]
        return sorted(found, key=lambda pair: (self.groups[pair[0]].name, pair[1].name))

    def _co_types(self, group: _Group) -> list[tuple[str, CoTypeNote]]:
        """The shown classes outside the group that its subjects also have, most subjects first."""
        rows = sorted(
            (co.class_iri, -(co.subjects or 0))
            for member in group.members
            for co in member.co_types or []
            if co.class_iri and co.class_iri not in group.classes and self._shown(co.class_iri)
        )
        best = [next(run) for _, run in groupby(rows, key=lambda row: row[0])]
        named = [(-negative, name, iri) for iri, negative in best if (name := self.namer.name(iri)) is not None]
        return [
            (iri, CoTypeNote(name=name, subjects=subjects))
            for subjects, name, iri in sorted(named, key=lambda n: (-n[0], n[1]))
        ]

    @staticmethod
    def _header(group: _Group, notes: list[CoTypeNote], via: list[ViaLink]) -> str:
        first = group.members[0]
        text = f"(:{group.name}) {group.instances}"
        if first.precision_mode == PrecisionMode.first_n:
            text += f" ~{first.observed_instances} first_n"
        if notes:
            text += " co " + ", ".join(f"{note.name} {note.subjects}" for note in notes)
        if via:
            text += " via " + ", ".join(f"(:{link.source})-{link.property}" for link in via)
        return text

    def block(self, index: int) -> PatternBlock:
        """The block of a named group. The IRIs of its header count as written; a via source and edge are
        written elsewhere, as a block or an expanded group, and as an edge."""
        group = self.groups[index]
        co_types = self._co_types(group)
        via = self._via(index)
        self.used.update(group.classes)
        self.used.update(iri for iri, _ in co_types)
        links = [ViaLink(source=self.groups[i].name, property=spec.name) for i, spec in via]
        notes = [note for _, note in co_types]
        return self._block(index, notes, links, nested=False)

    def nested_block(self, index: int) -> PatternBlock:
        """The own block of an expanded nested group, its edges from level 1 (for the ShExC)."""
        return self._block(index, [note for _, note in self._co_types(self.groups[index])], [], nested=True)

    def _block(self, index: int, notes: list[CoTypeNote], via: list[ViaLink], *, nested: bool) -> PatternBlock:
        group = self.groups[index]
        first = group.members[0]
        first_n = first.precision_mode == PrecisionMode.first_n
        return PatternBlock(
            name=group.name,
            classes=group.classes,
            shape=group.shape,
            instances=group.instances,
            observed=first.observed_instances if first_n else None,
            nested=nested,
            reaching_edges=self.reaching[index] if nested else None,
            co_types=notes,
            via=via,
            header=self._header(group, notes, via),
            edges=self._edges(index, 1),
        )

    # steps 9 and 10
    def glossary(self) -> list[GlossaryEntry]:
        """N9: the labels and descriptions of the terms the view writes, by name."""
        notes = _Lookup((note.term, note) for note in self.graph.term_annotations or [])
        written = sorted((name, iri) for iri in self.used if (name := self.namer.name(iri)) is not None)
        lines = [(name, iri, notes.get(iri)) for name, iri in written]
        entries = [
            GlossaryEntry(term=iri, name=name, line=line)
            for name, iri, note in lines
            if note is not None and (line := _glossary_line(name, shown_text(note.labels), shown_text(note.descriptions)))
        ]
        return entries

    def prefixes(self) -> list[PrefixDeclaration]:
        """N8: the prefixes of the names written, sorted."""
        declared = set()
        for iri in self.used | self.valued:
            prefix, entry = turtle_term(iri, self.table)[1], self.table.entry_for(iri)
            if prefix is not None and entry is not None:
                declared.add((prefix, entry.namespace))
        return [PrefixDeclaration(prefix=prefix, namespace=namespace) for prefix, namespace in sorted(declared)]


def _one_line(text: str) -> str:
    return " ".join(text.split())


def _glossary_line(name: str, label: LangText | None, description: LangText | None) -> str | None:
    """`name "label"@lang: description`, either part optional; the description cut at 200 characters."""
    line = name
    if label is not None:
        line += " " + json.dumps(_one_line(label.text), ensure_ascii=False) + (f"@{label.language}" if label.language else "")
    if description is not None:
        text = _one_line(description.text)
        line += ": " + text[:DESCRIPTION_LIMIT] + ("…" if len(text) > DESCRIPTION_LIMIT else "")
    return None if line == name else line


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
    nested_blocks = [builder.nested_block(i) for i in builder.expanded]
    return PatternGraph(
        graph=graph.graph,
        graph_label=graph_label,
        slug=slug,
        hidden_classes=builder.hidden_classes(),
        blocks=blocks,
        nested_blocks=nested_blocks,
        prefixes=builder.prefixes(),
        glossary=builder.glossary(),
        skipped=sorted(builder.namer.skipped),
    )
