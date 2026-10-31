"""SHACL shapes from the analytics: one open node shape per class, graded by what the profile knows (DEC-5, AD-10)."""

import re
import urllib.parse
from importlib.resources import files
from pathlib import Path
from typing import Any

import fingerprint_report_templates
from fingerprint.domain.exceptions import IriRefError
from fingerprint.domain.generated.profile import (
    ClassAnalytics,
    GraphAnalytics,
    ObjectTypeScope,
    ParentSource,
    PrecisionMode,
    PropertyAnalytics,
)
from fingerprint.domain.iri import to_iriref, turtle_number, turtle_string, turtle_term
from fingerprint.service_layer.generators.generator import Generator, TemplateRenderer

SH = "http://www.w3.org/ns/shacl#"
RDF_LANG_STRING = "http://www.w3.org/1999/02/22-rdf-syntax-ns#langString"
FIXED_PREFIXES = {
    "sh": SH,
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "fp": "https://data.meaningfy.ws/fingerprint/",
}
DEFAULT_SHAPES_NAMESPACE = "urn:fingerprint:shape:"
_PN_PREFIX = re.compile(r"[A-Za-z][A-Za-z0-9_-]*")
# min, max per accepted label; exactly_n takes n for both
COUNTS = {"exactly_one": (1, 1), "zero_or_one": (None, 1), "one_or_more": (1, None), "zero_or_more": (None, None)}
NODE_KINDS = {
    frozenset({"literal"}): "sh:Literal",
    frozenset({"iri"}): "sh:IRI",
    frozenset({"blank_node"}): "sh:BlankNode",
    frozenset({"iri", "blank_node"}): "sh:BlankNodeOrIRI",
}


def _name(value: Any) -> str:
    """An enum member or the plain string the generated model stores (`use_enum_values`)."""
    return str(getattr(value, "value", value))


class ShaclGenerator(Generator):
    template_package = Path(str(files(fingerprint_report_templates) / "shacl_shapes"))
    file_name = "shapes-{slug}.ttl"
    check = "turtle"

    def __init__(
        self,
        analytics: Any,
        renderer: TemplateRenderer,
        template_location: str | Path | None = None,
        shapes_namespace: str | None = None,
    ):
        super().__init__(analytics, renderer, template_location)
        self.shapes_namespace = shapes_namespace or DEFAULT_SHAPES_NAMESPACE
        to_iriref(self.shapes_namespace)  # an unwritable namespace is the caller's error, raised at once
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
        if self.writable(cls.class_iri, {}) is None:
            return None
        sampled = cls.precision_mode == PrecisionMode.first_n
        counted = [("fp:instances", cls.instances), ("fp:observedInstances", cls.observed_instances)]
        annotations = [(p, turtle_number(v)) for p, v in counted if v is not None]
        annotations.append(("fp:precisionMode", turtle_string(_name(cls.precision_mode))))
        comments = []
        if sampled:
            comments.append(f"Profiled from the first {cls.observed_instances} of {cls.instances} instances.")
        if self.cross_graph:
            comments.append("sh:class constraints assume the object types' graphs are part of the data graph.")
        return {
            "shape": to_iriref(self.shapes_namespace + urllib.parse.quote(cls.class_iri, safe="")),
            "target": self.term(cls.class_iri),
            "annotations": annotations + [("rdfs:comment", turtle_string(" ".join(comments)))] * bool(comments),
            "_cls": cls,
        }

    def visit_property(self, graph: GraphAnalytics, cls: ClassAnalytics, prop: PropertyAnalytics) -> dict[str, Any] | None:
        if self.writable(prop.property, {}) is None:
            return None
        labelled = prop.cardinality_label is not None and not prop.presence_only
        constraints = self.counts(prop) + (self.value_constraints(prop) if labelled else [])
        annotations = []
        if prop.confidence is not None:
            annotations.append(("fp:confidence", turtle_number(prop.confidence)))
        if prop.label_support is not None:
            annotations.append(("fp:labelSupport", turtle_number(prop.label_support)))
        severity = self.severity(cls, prop, labelled, any(c.startswith("sh:class") for c in constraints))
        return {
            "path": self.term(prop.property),
            "constraints": constraints + ([f"sh:severity {severity}"] if severity else []),
            "annotations": annotations,
        }

    def end_graph(self, graph: GraphAnalytics, view: dict[str, Any]) -> None:
        for cls in view["classes"]:
            cls.pop("_cls")
        used = {p: self.term_prefixes[p] for p in sorted(self._used)}
        view["prefixes"] = sorted((FIXED_PREFIXES | used).items())
        view["graph_label"] = re.sub(r"[\r\n]", " ", graph.graph or "default graph")

    # --- the rules ---

    @staticmethod
    def counts(prop: PropertyAnalytics) -> list[str]:
        if prop.presence_only or prop.cardinality_label is None:
            return []
        label = _name(prop.cardinality_label)
        low, high = (prop.exact_count, prop.exact_count) if label == "exactly_n" else COUNTS[label]
        return [f"sh:minCount {low}"] * (low is not None) + [f"sh:maxCount {high}"] * (high is not None)

    def value_constraints(self, prop: PropertyAnalytics) -> list[str]:
        """Alternatives that every observed value satisfies: datatypes, classes (only when every resource is
        typed), and any resource when some are untyped; one alternative inline, several in sh:or."""
        partitions = prop.value_partitions or []
        if not partitions:
            return []
        kinds = frozenset(_name(p.node_kind) for p in partitions)
        resource_kinds = kinds - {"literal"}
        datatypes, classes, any_literal = set(), set(), False
        for p in partitions:
            if _name(p.node_kind) == "literal":
                datatype = p.datatype or (RDF_LANG_STRING if p.language else None)
                if datatype:
                    datatypes.add(datatype)
                else:
                    any_literal = True
            elif p.object_class:
                classes.add(p.object_class)
        untyped = bool(resource_kinds) and (prop.untyped_object_ratio or 0) > 0
        try:
            alternatives = [f"sh:datatype {self.term(d)}" for d in sorted(datatypes)]
            alternatives += [] if untyped else [f"sh:class {self.term(c)}" for c in sorted(classes)]
        except IriRefError as error:  # a value type that cannot be written: keep only the node kind
            self.skipped.append(error.iri)
            return [f"sh:nodeKind {NODE_KINDS[kinds]}"] if kinds in NODE_KINDS else []
        if any_literal:
            alternatives.append("sh:nodeKind sh:Literal")
        if untyped:
            alternatives.append(f"sh:nodeKind {NODE_KINDS[frozenset(resource_kinds)]}")
        node_kind = [f"sh:nodeKind {NODE_KINDS[kinds]}"] if kinds in NODE_KINDS else []
        if len(alternatives) == 1:
            return list(dict.fromkeys(alternatives + node_kind))
        return [f"sh:or ( {' '.join(f'[ {a} ]' for a in alternatives)} )"] + node_kind

    def severity(self, cls: ClassAnalytics, prop: PropertyAnalytics, labelled: bool, has_class: bool) -> str | None:
        """First matching rule (how-it-works, "How strong is a generated shape?")."""
        if not labelled or (prop.confidence or 0) < self.threshold:
            return "sh:Info"
        if (prop.label_support or 0) < 1 or cls.precision_mode == PrecisionMode.first_n:
            return "sh:Warning"
        if cls.class_iri in self._with_subclasses or (self.cross_graph and has_class):
            return "sh:Warning"
        return None
