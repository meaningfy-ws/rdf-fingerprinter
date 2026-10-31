"""PlantUML class diagrams from the analytics: one diagram per graph, own and refined properties (DEC-6)."""

from pathlib import Path
from typing import Any

from fingerprint.domain.analytics import multiplicity
from fingerprint.domain.generated.profile import (
    ClassAnalytics,
    GraphAnalytics,
    Inheritance,
    ParentSource,
    ProfileAnalytics,
    PropertyAnalytics,
    PropertyKind,
)
from fingerprint.service_layer.generators.generator import Generator, TemplateRenderer
from fingerprint_report_templates import packaged

DIAGRAMMED_INHERITANCE = {Inheritance.own.value, Inheritance.refined.value}


class PlantumlGenerator(Generator):
    template_package = packaged("plantuml_diagram")
    file_name = "diagram-{slug}.puml"

    def __init__(self, analytics: ProfileAnalytics, renderer: TemplateRenderer, template_location: str | Path | None = None):
        super().__init__(analytics, renderer, template_location)
        self._aliases: dict[str, str] = {}
        self._parents: dict[str, str] = {}

    def visit_graph(self, graph: GraphAnalytics) -> dict[str, Any] | None:
        # Aliases make every name safe to quote: the labels are CURIEs of IRIs the hooks accepted.
        accepted = sorted(c.class_iri for c in graph.class_partitions or [] if self.accepts(c.class_iri))
        self._aliases = {iri: f"C{n}" for n, iri in enumerate(accepted, 1)}
        self._parents = {}
        return super().visit_graph(graph)

    def visit_class(self, graph: GraphAnalytics, cls: ClassAnalytics) -> dict[str, Any] | None:
        if cls.class_iri not in self._aliases:
            return None
        alias = self._aliases[cls.class_iri]
        generalisations = []
        for parent in sorted(cls.parents or [], key=lambda p: p.parent):
            if self.accepts(parent.parent):
                arrow = "--|>" if parent.source == ParentSource.declared else "..|>"
                generalisations.append(f"{alias} {arrow} {self.alias(parent.parent)}")
        return {"alias": alias, "label": self.label(cls.class_iri), "generalisations": generalisations}

    def visit_property(self, graph: GraphAnalytics, cls: ClassAnalytics, prop: PropertyAnalytics) -> dict[str, Any] | None:
        if prop.inheritance not in DIAGRAMMED_INHERITANCE or not self.accepts(prop.property):
            return None
        uml = multiplicity(prop.cardinality_label, prop.exact_count)
        classes = {p.object_class for p in prop.value_partitions or [] if p.object_class}
        target = next(iter(classes)) if len(classes) == 1 else None
        if target in self._aliases and not prop.untyped_object_ratio and prop.property_kind == PropertyKind.object_property:
            return {"association": f'"{uml}" {self._aliases[target]} : {self.label(prop.property)}'}
        return {"attribute": f"{self.label(prop.property)} : {self.types(prop)} [{uml}]"}

    def end_graph(self, graph: GraphAnalytics, view: dict[str, Any]) -> None:
        for cls in view["classes"]:
            cls["attributes"] = [p["attribute"] for p in cls["properties"] if "attribute" in p]
            cls["links"] = [f"{cls['alias']} --> {p['association']}" for p in cls["properties"] if "association" in p]
        view["parent_boxes"] = [{"alias": a, "label": self.label(iri)} for iri, a in self._parents.items()]

    def alias(self, iri: str) -> str:
        """A profiled class's alias, or a box for a parent not profiled in this graph."""
        if iri in self._aliases:
            return self._aliases[iri]
        return self._parents.setdefault(iri, f"P{len(self._parents) + 1}")

    def types(self, prop: PropertyAnalytics) -> str:
        """The value types as labels; an IRI that cannot be written is left out and recorded (P-8)."""
        names = [self.label(t) for t in prop.value_types or [] if self.accepts(t)]
        if (prop.untyped_object_ratio or 0) > 0 or (not names and prop.property_kind == PropertyKind.object_property):
            names.append("resource")
        return " | ".join(names) or "value"
