"""PlantUML class diagrams from the analytics: one diagram per graph, own and refined properties (DEC-6)."""

from importlib.resources import files
from pathlib import Path
from typing import Any

import fingerprint_report_templates
from fingerprint.domain.generated.profile import ClassAnalytics, GraphAnalytics, PropertyAnalytics
from fingerprint.domain.iri import curie
from fingerprint.service_layer.generators.generator import Generator, TemplateRenderer

MULTIPLICITY = {"exactly_one": "1", "zero_or_one": "0..1", "one_or_more": "1..*", "zero_or_more": "0..*"}
SHOWN = {"own", "refined"}


def _name(value: Any) -> str:
    return str(getattr(value, "value", value))


class PlantumlGenerator(Generator):
    template_package = Path(str(files(fingerprint_report_templates) / "plantuml_diagram"))
    file_name = "diagram-{slug}.puml"

    def __init__(self, analytics: Any, renderer: TemplateRenderer, template_location: str | Path | None = None):
        super().__init__(analytics, renderer, template_location)
        self._aliases: dict[str, str] = {}
        self._parents: dict[str, str] = {}

    def label(self, iri: str) -> str:
        return curie(iri, self.prefixes)

    def visit_graph(self, graph: GraphAnalytics) -> dict[str, Any] | None:
        # Aliases make every name safe to quote: the labels are CURIEs of IRIs the hooks accepted.
        writable = sorted(c.class_iri for c in graph.class_partitions or [] if self.writable(c.class_iri, {}) is not None)
        self._aliases = {iri: f"C{n}" for n, iri in enumerate(writable, 1)}
        self._parents = {}
        return super().visit_graph(graph)

    def visit_class(self, graph: GraphAnalytics, cls: ClassAnalytics) -> dict[str, Any] | None:
        if cls.class_iri not in self._aliases:
            return None
        alias = self._aliases[cls.class_iri]
        generalisations = []
        for parent in sorted(cls.parents or [], key=lambda p: p.parent):
            if self.writable(parent.parent, {}) is None:
                continue
            arrow = "--|>" if _name(parent.source) == "declared" else "..|>"
            generalisations.append(f"{alias} {arrow} {self.alias(parent.parent)}")
        return {"alias": alias, "label": self.label(cls.class_iri), "generalisations": generalisations, "links": []}

    def visit_property(self, graph: GraphAnalytics, cls: ClassAnalytics, prop: PropertyAnalytics) -> dict[str, Any] | None:
        if _name(prop.inheritance) not in SHOWN or self.writable(prop.property, {}) is None:
            return None
        multiplicity = self.multiplicity(prop)
        classes = {p.object_class for p in prop.value_partitions or [] if p.object_class}
        target = next(iter(classes)) if len(classes) == 1 else None
        if target in self._aliases and not prop.untyped_object_ratio and _name(prop.property_kind) == "object_property":
            return {"association": f'"{multiplicity}" {self._aliases[target]} : {self.label(prop.property)}'}
        return {"attribute": f"{self.label(prop.property)} : {self.types(prop)} [{multiplicity}]"}

    def end_graph(self, graph: GraphAnalytics, view: dict[str, Any]) -> None:
        for cls in view["classes"]:
            cls["attributes"] = [p["attribute"] for p in cls["properties"] if "attribute" in p]
            cls["links"] = [f"{cls['alias']} --> {p['association']}" for p in cls["properties"] if "association" in p]
        view["parent_boxes"] = [{"alias": a, "label": self.label(iri)} for iri, a in self._parents.items()]
        view["graph_label"] = (graph.graph or "default graph").replace("\n", " ").replace("\r", " ")

    def alias(self, iri: str) -> str:
        """A profiled class's alias, or a box for a parent not profiled in this graph."""
        if iri in self._aliases:
            return self._aliases[iri]
        return self._parents.setdefault(iri, f"P{len(self._parents) + 1}")

    @staticmethod
    def multiplicity(prop: PropertyAnalytics) -> str:
        label = _name(prop.cardinality_label) if prop.cardinality_label else "zero_or_more"
        return str(prop.exact_count) if label == "exactly_n" else MULTIPLICITY[label]

    def types(self, prop: PropertyAnalytics) -> str:
        names = [self.label(t) for t in prop.value_types or []]
        if (prop.untyped_object_ratio or 0) > 0 or (not names and _name(prop.property_kind) == "object_property"):
            names.append("resource")
        return " | ".join(names) or "value"
