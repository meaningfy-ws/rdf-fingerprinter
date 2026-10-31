"""SHACL shapes from the analytics: one open node shape per class, graded by what the profile knows (DEC-5, AD-10)."""

import re
import urllib.parse
from pathlib import Path
from typing import Any, NamedTuple

from fingerprint.domain.analytics import label_bounds
from fingerprint.domain.iri import to_iriref, turtle_number, turtle_string, turtle_term
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
from fingerprint.domain.vocabulary import FP, RDF, RDF_LANG_STRING, RDFS, SH, XSD
from fingerprint.service_layer.generators.generator import Generator, TemplateRenderer
from fingerprint_report_templates import packaged

FIXED_PREFIXES = {"sh": SH, "xsd": XSD, "rdf": RDF, "rdfs": RDFS, "fp": FP}
DEFAULT_SHAPES_NAMESPACE = "urn:fingerprint:shape:"
INFO, WARNING = "sh:Info", "sh:Warning"  # sh:Violation is the default: no sh:severity is written
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
    check = "turtle"

    def __init__(
        self,
        analytics: ProfileAnalytics,
        renderer: TemplateRenderer,
        template_location: str | Path | None = None,
        shapes_namespace: str | None = None,
    ):
        super().__init__(analytics, renderer, template_location)
        self.shapes_namespace = shapes_namespace or DEFAULT_SHAPES_NAMESPACE
        to_iriref(self.shapes_namespace)  # an unwritable namespace is the caller's usage error (IriRefError)
        # Prefixes usable in Turtle, never redefining the ones the shapes themselves need.
        self.term_prefixes = {
            p: ns for p, ns in self.prefixes.items() if _PN_PREFIX.fullmatch(p) and FIXED_PREFIXES.get(p, ns) == ns
        }
        self.threshold = analytics.settings.acceptance_threshold
        self.cross_graph = analytics.settings.object_type_scope == ObjectTypeScope.any_graph
        self._used: set[str] = set()
        self._with_subclasses: set[str] = set()

    def term(self, iri: str) -> str:
        text, prefix = turtle_term(iri, self.term_prefixes)
        if prefix:
            self._used.add(prefix)
        return text

    # --- hooks ---

    def visit_graph(self, graph: GraphAnalytics) -> dict[str, Any] | None:
        self._used = set()
        declared = {e.super_class for e in graph.declared_subclass_edges or []}
        declared |= {
            p.parent for c in graph.class_partitions or [] for p in c.parents or [] if p.source == ParentSource.declared
        }
        self._with_subclasses = declared
        return super().visit_graph(graph)

    def visit_class(self, graph: GraphAnalytics, cls: ClassAnalytics) -> dict[str, Any] | None:
        if not self.accepts(cls.class_iri):
            return None
        annotations = [(p, turtle_number(v)) for p, v in self.counted(cls) if v is not None]
        annotations.append(("fp:precisionMode", turtle_string(PrecisionMode(cls.precision_mode).value)))
        comments = []
        if cls.precision_mode == PrecisionMode.first_n:
            comments.append(f"Profiled from the first {cls.observed_instances} of {cls.instances} instances.")
        if self.cross_graph:
            comments.append("sh:class constraints assume the object types' graphs are part of the data graph.")
        if comments:
            annotations.append(("rdfs:comment", turtle_string(" ".join(comments))))
        return {
            "shape": to_iriref(self.shapes_namespace + urllib.parse.quote(cls.class_iri, safe="")),
            "target": self.term(cls.class_iri),
            "annotations": annotations,
        }

    def visit_property(self, graph: GraphAnalytics, cls: ClassAnalytics, prop: PropertyAnalytics) -> dict[str, Any] | None:
        if not self.accepts(prop.property):
            return None
        labelled = prop.cardinality_label is not None and not prop.presence_only
        constraints = self.counts(prop) + (self.value_constraints(prop) if labelled else [])
        has_class = any(c.startswith("sh:class") or "[ sh:class" in c for c in constraints)
        severity = self.severity(cls, prop, labelled, has_class)
        if severity:
            constraints.append(f"sh:severity {severity}")
        annotations = []
        if prop.confidence is not None:
            annotations.append(("fp:confidence", turtle_number(prop.confidence)))
        if prop.label_support is not None:
            annotations.append(("fp:labelSupport", turtle_number(prop.label_support)))
        return {"path": self.term(prop.property), "constraints": constraints, "annotations": annotations}

    def end_graph(self, graph: GraphAnalytics, view: dict[str, Any]) -> None:
        used = {p: self.term_prefixes[p] for p in sorted(self._used)}
        view["prefixes"] = sorted((FIXED_PREFIXES | used).items())

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

    def value_constraints(self, prop: PropertyAnalytics) -> list[str]:
        """Alternatives every observed value satisfies: datatypes, classes (only when every resource is typed)
        and any resource when some are untyped; one alternative inline, several in sh:or."""
        values = self.values(prop)
        if not values.kinds:
            return []
        node_kind = [f"sh:nodeKind {NODE_KINDS[values.kinds]}"] if values.kinds in NODE_KINDS else []
        if not all(self.accepts(t) for t in sorted(values.datatypes | values.classes)):
            return node_kind  # a value type that cannot be written: keep only the node kind
        resource_kinds = values.kinds - {LITERAL}
        untyped = bool(resource_kinds) and (prop.untyped_object_ratio or 0) > 0
        alternatives = [f"sh:datatype {self.term(d)}" for d in sorted(values.datatypes)]
        if not untyped:
            alternatives += [f"sh:class {self.term(c)}" for c in sorted(values.classes)]
        if values.any_literal:
            alternatives.append("sh:nodeKind sh:Literal")
        if untyped:
            alternatives.append(f"sh:nodeKind {NODE_KINDS[frozenset(resource_kinds)]}")
        if len(alternatives) == 1:
            return list(dict.fromkeys(alternatives + node_kind))
        return [f"sh:or ( {' '.join(f'[ {a} ]' for a in alternatives)} )"] + node_kind

    def severity(self, cls: ClassAnalytics, prop: PropertyAnalytics, labelled: bool, has_class: bool) -> str | None:
        """First matching rule (how-it-works, "How strong is a generated shape?")."""
        if not labelled or (prop.confidence or 0) < self.threshold:
            return INFO
        if (prop.label_support or 0) < 1 or cls.precision_mode == PrecisionMode.first_n:
            return WARNING
        if cls.class_iri in self._with_subclasses or (self.cross_graph and has_class):
            return WARNING
        return None
