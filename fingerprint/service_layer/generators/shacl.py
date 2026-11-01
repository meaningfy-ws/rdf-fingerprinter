"""SHACL shapes from the analytics: one open node shape per class, graded by what the profile knows (DEC-5, AD-10)."""

import re
from pathlib import Path
from typing import NamedTuple

from fingerprint import config
from fingerprint.domain.analytics import label_bounds
from fingerprint.domain.iri import _SAFE_LOCAL, to_iriref, turtle_number, turtle_string, turtle_term
from fingerprint.domain.profile import (
    ClassAnalytics,
    GraphAnalytics,
    NodeKind,
    ObjectTypeScope,
    ParentSource,
    PrecisionMode,
    ProfileAnalytics,
    PropertyAnalytics,
)
from fingerprint.domain.shapes import shape_iri
from fingerprint.domain.views import (
    Annotation,
    GeneratorOptions,
    NodeShape,
    OutputCheck,
    PrefixDeclaration,
    PropertyShape,
    ShapeSeverity,
    ShapesGraph,
)
from fingerprint.domain.vocabulary import FP, RDF, RDF_LANG_STRING, RDFS, SH, XSD
from fingerprint.service_layer.generators.generator import Generator, TemplateRenderer, graph_slug, plain_label
from fingerprint_report_templates import packaged

FIXED_PREFIXES = {"sh": SH, "xsd": XSD, "rdf": RDF, "rdfs": RDFS, "fp": FP}
_PN_PREFIX = re.compile(r"[A-Za-z][A-Za-z0-9_-]*")
LITERAL, IRI, BLANK_NODE = NodeKind.literal.value, NodeKind.iri.value, NodeKind.blank_node.value
NODE_KINDS = {
    frozenset({LITERAL}): "sh:Literal",
    frozenset({IRI}): "sh:IRI",
    frozenset({BLANK_NODE}): "sh:BlankNode",
    frozenset({IRI, BLANK_NODE}): "sh:BlankNodeOrIRI",
}


class Values(NamedTuple):
    """What a property's value partitions say about its values."""

    kinds: frozenset[str]
    datatypes: set[str]
    classes: set[str]
    any_literal: bool  # some literals have neither a datatype nor a language


class ShaclGenerator(Generator):
    template_package = packaged("shacl_shapes")
    file_name = "shapes-{slug}.ttl"
    check = OutputCheck.turtle

    def __init__(
        self,
        analytics: ProfileAnalytics,
        renderer: TemplateRenderer,
        template_location: str | Path | None = None,
        options: GeneratorOptions | None = None,
    ):
        super().__init__(analytics, renderer, template_location, options)
        self.shapes_namespace = self.options.shapes_namespace or config.shapes_namespace
        if self.shapes_namespace:
            to_iriref(self.shapes_namespace)  # an unwritable namespace is the caller's usage error (IriRefError)
        self.threshold = analytics.settings.acceptance_threshold
        self.cross_graph = analytics.settings.object_type_scope == ObjectTypeScope.any_graph
        self._used: dict[str, str] = {}  # dict-ok: lookup index of the prefixes this graph's file declares
        self._shapes: set[str] = set()
        self._with_subclasses: set[str] = set()

    def term(self, iri: str) -> str:
        text, prefix = turtle_term(iri, self.table)
        if prefix and _PN_PREFIX.fullmatch(prefix):
            self._used[prefix] = self.table.by_prefix(prefix).namespace  # type: ignore[union-attr]
            return text
        return to_iriref(iri)

    def shape(self, cls: ClassAnalytics, prop: PropertyAnalytics | None = None) -> str:
        """The shape IRI as Turtle, unique in the file: later duplicates get -2, -3, … in IRI order (DEC-6)."""
        iri, prefix, namespace = shape_iri(cls.class_iri, prop.property if prop else None, self.table, self.shapes_namespace)
        unique, n = iri, 1
        while unique in self._shapes:
            n += 1
            unique = f"{iri}-{n}"
        self._shapes.add(unique)
        local = unique[len(namespace) :]
        if _SAFE_LOCAL.fullmatch(local):
            self._used[prefix] = namespace
            return f"{prefix}:{local}"
        return to_iriref(unique)

    # --- hooks ---

    def visit_graph(self, graph: GraphAnalytics) -> bool:
        self._used = {}  # dict-ok: lookup index
        self._shapes = set()
        declared = {e.super_class for e in graph.declared_subclass_edges or []}
        declared |= {
            p.parent for c in graph.class_partitions or [] for p in c.parents or [] if p.source == ParentSource.declared
        }
        self._with_subclasses = declared
        return True

    def visit_class(self, graph: GraphAnalytics, cls: ClassAnalytics) -> bool:
        return self.accepts(cls.class_iri)

    def visit_property(self, graph: GraphAnalytics, cls: ClassAnalytics, prop: PropertyAnalytics) -> PropertyShape | None:
        if not self.accepts(prop.property):
            return None
        labelled = prop.cardinality_label is not None and not prop.presence_only
        value_constraints, has_class = self.value_constraints(prop) if labelled else ([], False)
        constraints = self.counts(prop) + value_constraints
        annotations = []
        if prop.confidence is not None:
            annotations.append(Annotation(predicate="fp:confidence", value=turtle_number(prop.confidence)))
        if prop.label_support is not None:
            annotations.append(Annotation(predicate="fp:labelSupport", value=turtle_number(prop.label_support)))
        return PropertyShape(
            shape=self.shape(cls, prop),
            path=self.term(prop.property),
            constraints=constraints,
            severity=self.severity(cls, prop, labelled, has_class),
            annotations=annotations,
        )

    def end_class(self, graph: GraphAnalytics, cls: ClassAnalytics, properties: list[PropertyShape]) -> NodeShape:
        annotations = [Annotation(predicate=p, value=turtle_number(v)) for p, v in self.counted(cls) if v is not None]
        annotations.append(
            Annotation(predicate="fp:precisionMode", value=turtle_string(PrecisionMode(cls.precision_mode).value))
        )
        comments = []
        if cls.precision_mode == PrecisionMode.first_n:
            comments.append(f"Profiled from the first {cls.observed_instances} of {cls.instances} instances.")
        if self.cross_graph:
            comments.append("sh:class constraints assume the object types' graphs are part of the data graph.")
        if comments:
            annotations.append(Annotation(predicate="rdfs:comment", value=turtle_string(" ".join(comments))))
        return NodeShape(
            shape=self.shape(cls),
            target=self.term(cls.class_iri),
            annotations=annotations,
            property_shapes=properties,
        )

    def end_graph(self, graph: GraphAnalytics, classes: list[NodeShape]) -> ShapesGraph:
        used = [(p, ns) for p, ns in sorted(self._used.items()) if p not in FIXED_PREFIXES]  # fixed: same IRI
        prefixes = sorted([*FIXED_PREFIXES.items(), *used])
        return ShapesGraph(
            graph_label=plain_label(graph.graph),
            slug=graph_slug(graph.graph),
            excluded_note=self.excluded_note(graph),
            prefixes=[PrefixDeclaration(prefix=p, namespace=ns) for p, ns in prefixes],
            node_shapes=classes,
        )

    # --- the rules ---

    @staticmethod
    def counted(cls: ClassAnalytics) -> list[tuple[str, int | None]]:
        return [("fp:instances", cls.instances), ("fp:observedInstances", cls.observed_instances)]

    @staticmethod
    def counts(prop: PropertyAnalytics) -> list[str]:
        if prop.presence_only:
            return []
        low, high = label_bounds(prop.cardinality_label, prop.exact_count)
        constraints = []
        if low is not None:
            constraints.append(f"sh:minCount {low}")
        if high is not None:
            constraints.append(f"sh:maxCount {high}")
        return constraints

    @staticmethod
    def values(prop: PropertyAnalytics) -> Values:
        datatypes: set[str] = set()
        classes: set[str] = set()
        any_literal = False
        for p in prop.value_partitions or []:
            if p.node_kind == NodeKind.literal:
                datatype = p.datatype or (RDF_LANG_STRING if p.language else None)
                if datatype:
                    datatypes.add(datatype)
                else:
                    any_literal = True
            elif p.object_class:
                classes.add(p.object_class)
        kinds = frozenset(NodeKind(p.node_kind).value for p in prop.value_partitions or [])
        return Values(kinds, datatypes, classes, any_literal)

    def value_constraints(self, prop: PropertyAnalytics) -> tuple[list[str], bool]:
        """Alternatives every observed value satisfies: datatypes, classes (only when every resource is typed)
        and any resource when some are untyped; one alternative inline, several in sh:or. The flag says whether
        an sh:class constraint was written, which the severity rule needs."""
        values = self.values(prop)
        if not values.kinds:
            return [], False
        node_kind = [f"sh:nodeKind {NODE_KINDS[values.kinds]}"] if values.kinds in NODE_KINDS else []
        if not all(self.accepts(t) for t in sorted(values.datatypes | values.classes)):
            return node_kind, False  # a value type that cannot be written: keep only the node kind
        resource_kinds = values.kinds - {LITERAL}
        untyped = bool(resource_kinds) and (prop.untyped_object_ratio or 0) > 0
        alternatives = [f"sh:datatype {self.term(d)}" for d in sorted(values.datatypes)]
        if not untyped:
            alternatives += [f"sh:class {self.term(c)}" for c in sorted(values.classes)]
        if values.any_literal:
            alternatives.append("sh:nodeKind sh:Literal")
        if untyped:
            alternatives.append(f"sh:nodeKind {NODE_KINDS[frozenset(resource_kinds)]}")
        has_class = bool(values.classes) and not untyped
        if len(alternatives) == 1:
            inline = alternatives if alternatives == node_kind else alternatives + node_kind
            return inline, has_class
        return [f"sh:or ( {' '.join(f'[ {a} ]' for a in alternatives)} )"] + node_kind, has_class

    def severity(self, cls: ClassAnalytics, prop: PropertyAnalytics, labelled: bool, has_class: bool) -> ShapeSeverity:
        """First matching rule (how-it-works, "How strong is a generated shape?")."""
        if not labelled or (prop.confidence or 0) < self.threshold:
            return ShapeSeverity.info
        if (prop.label_support or 0) < 1 or cls.precision_mode == PrecisionMode.first_n:
            return ShapeSeverity.warning
        if cls.class_iri in self._with_subclasses or (self.cross_graph and has_class):
            return ShapeSeverity.warning
        return ShapeSeverity.violation
