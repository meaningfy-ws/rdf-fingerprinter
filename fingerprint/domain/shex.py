"""The enriched ShExC view of a graph (llm-schema-tools P-2, P-9; design §D). Pure: no I/O.

`shex_view` maps the pattern view (`fingerprint.domain.patterns`) to the shapes the ShExC template lays out. The
statistics stay in `#` comments, so they cost no syntax; every file has to parse with PyShExC (tests only, DEC-27).
"""

from collections.abc import Iterable

from fingerprint.domain.iri import to_iriref
from fingerprint.domain.patterns import BNODE, IRI, UNKNOWN
from fingerprint.domain.views import (
    EdgeTarget,
    PatternBlock,
    PatternEdge,
    PatternGraph,
    ShexConstraint,
    ShexSchema,
    ShexShape,
    TargetKind,
)

REJECTED = "="  # PyShExC rejects "=" in an IRIREF, however it is written (design, Dependencies)
ELLIPSIS = " …"  # the pattern ending of an edge into a group expanded nowhere
DEEPER = "… deeper than 3 hops"
GLOSSARY, NO_GLOSSARY = "glossary", "glossary: none"


def _unique(values: Iterable[str]) -> list[str]:
    found: list[str] = []
    for value in values:
        if value not in found:
            found.append(value)
    return found


def _cardinality(edge: PatternEdge) -> str | None:
    """`?` for 0-1, nothing for exactly 1, `{a}`, `{a,b}`; `*` when the profile has no counts per instance."""
    low, high = edge.min_count, edge.max_count
    if low is None or high is None:
        return "*"
    if (low, high) == (1, 1):
        return None
    if (low, high) == (0, 1):
        return "?"
    return f"{{{low}}}" if low == high else f"{{{low},{high}}}"


def _group_text(target: EdgeTarget) -> str:
    return target.name if target.graph is None else f"{target.name} @{to_iriref(target.graph)}"


def _comment(edge: PatternEdge) -> str | None:
    """The group text of the targets, the statistics, and the note on an edge into a group expanded nowhere."""
    groups = [_group_text(t) for t in edge.targets or [] if t.kind == TargetKind.group]
    parts = [f"(:{'|'.join(groups)})"] if groups else []
    parts += [edge.stats] if edge.stats else []
    parts += [DEEPER] if edge.ending == ELLIPSIS else []
    return " ".join(parts) or None


class _Shex:
    def __init__(self, view: PatternGraph):
        self.view = view
        self.blocks = view.blocks or []
        self.nested = view.nested_blocks or []
        self.skipped = {iri for block in [*self.blocks, *self.nested] for iri in block.classes or [] if REJECTED in iri}

    # --- what ShExC can write ---

    @staticmethod
    def _writable(block: PatternBlock) -> bool:
        return not any(REJECTED in iri for iri in block.classes or [])

    def _shape_label(self, name: str) -> str | None:
        """The label of the shape of the group named `name`, if the file has one."""
        return next((b.shape for b in self.blocks if b.name == name and self._writable(b)), None)

    def _expand(self, name: str) -> str:
        """The IRI a datatype's name stands for."""
        if name.startswith("<"):
            return name[1:-1]
        prefix, _, local = name.partition(":")
        return next((p.namespace for p in self.view.prefixes or [] if p.prefix == prefix), "") + local

    # --- values ---

    def _nested(self, target: EdgeTarget) -> PatternBlock | None:
        if target.kind != TargetKind.group or target.graph is not None or target.has_shape:
            return None
        return next((b for b in self.nested if b.name == target.name), None)

    def _inlined(self, target: EdgeTarget) -> bool:
        """A nested group that this edge alone reaches is written inside the edge."""
        nested = self._nested(target)
        return nested is not None and self._writable(nested) and nested.reaching_edges == 1

    def _class(self, edge: PatternEdge, target: EdgeTarget) -> str:
        if target.graph is not None:
            return IRI
        if target.has_shape:
            label = self._shape_label(target.name)
            return IRI if label is None else f"@{label}"
        nested = self._nested(target)
        if nested is None:  # a hidden class, or a nested group expanded nowhere
            return BNODE if edge.ending == ELLIPSIS else IRI
        if self._writable(nested) and (nested.reaching_edges or 0) > 1:
            return f"{BNODE} @{nested.shape}"
        return BNODE

    def _datatype(self, target: EdgeTarget) -> str | None:
        iri = self._expand(target.name)
        if REJECTED in iri:
            self.skipped.add(iri)
            return None
        return target.name

    def _alternative(self, edge: PatternEdge, target: EdgeTarget) -> str | None:
        match target.kind:
            case TargetKind.group:
                return self._class(edge, target)
            case TargetKind.datatype:
                return self._datatype(target)
            case TargetKind.iri:
                return IRI
            case TargetKind.blank_node:
                return BNODE
            case _:
                return UNKNOWN

    def _value(self, edge: PatternEdge, inline: bool) -> str:
        """One alternative as it is; several as `(a OR b)`, or, before an inline `{`, bare with `BNODE` last."""
        found = [text for target in edge.targets or [] if (text := self._alternative(edge, target)) is not None]
        alternatives = _unique(found) or [UNKNOWN]
        if inline:
            return " OR ".join([*(a for a in alternatives if a != BNODE), BNODE])
        return alternatives[0] if len(alternatives) == 1 else f"({' OR '.join(alternatives)})"

    # --- shapes ---

    def _constraint(self, edge: PatternEdge) -> ShexConstraint | None:
        if REJECTED in edge.property:
            self.skipped.add(edge.property)
            return None
        inline = any(self._inlined(target) for target in edge.targets or [])
        return ShexConstraint(
            predicate=edge.name,
            value=self._value(edge, inline),
            cardinality=_cardinality(edge),
            comment=_comment(edge),
            inline=self._constraints(edge.edges) if inline else None,
            depth=edge.depth,
        )

    def _constraints(self, edges: list[PatternEdge] | None) -> list[ShexConstraint]:
        return [c for edge in edges or [] if (c := self._constraint(edge)) is not None]

    def _shape(self, block: PatternBlock, *, blank: bool | None) -> ShexShape:
        return ShexShape(
            label=block.shape or block.name, comment=block.header, blank=blank, constraints=self._constraints(block.edges)
        )

    def schema(self) -> ShexSchema:
        shapes = [self._shape(b, blank=None) for b in self.blocks if self._writable(b)]
        shapes += [self._shape(b, blank=True) for b in self.nested if self._writable(b) and (b.reaching_edges or 0) > 1]
        entries = [entry.line for entry in self.view.glossary or []]
        return ShexSchema(
            graph_label=self.view.graph_label,
            slug=self.view.slug,
            skipped=self.view.skipped,
            hidden_classes=self.view.hidden_classes,
            prefixes=[p for p in self.view.prefixes or [] if REJECTED not in p.namespace],
            shapes=shapes,
            glossary=[GLOSSARY, *entries] if entries else [NO_GLOSSARY],
            skipped_terms=sorted(self.skipped),
        )


def shex_view(view: PatternGraph) -> ShexSchema:
    """The ShExC view of one graph's pattern view."""
    return _Shex(view).schema()
