"""The application-profile document: one HTML file in the SEMIC / SHACL Play style (DEC-7)."""

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from fingerprint.domain.analytics import multiplicity
from fingerprint.domain.generated.profile import (
    ClassAnalytics,
    GraphAnalytics,
    PrecisionMode,
    ProfileAnalytics,
    PropertyAnalytics,
)
from fingerprint.service_layer.generators.generator import (
    DEFAULT_GRAPH_LABEL,
    Generator,
    TemplateRenderer,
    graph_slug,
)
from fingerprint_report_templates import packaged

ABSENT = "—"


class DocumentGenerator(Generator):
    template_package = packaged("profile_document")
    file_name = "profile.html"
    per_graph = False
    autoescape = True  # endpoint data is untrusted (DEC-4)

    def __init__(
        self,
        analytics: ProfileAnalytics,
        renderer: TemplateRenderer,
        template_location: str | Path | None = None,
        diagrams: Mapping[str, str] | None = None,
    ):
        """`diagrams`: the PlantUML source per graph slug, composed by the representations service."""
        super().__init__(analytics, renderer, template_location)
        self.diagrams = dict(diagrams or {})

    # --- hooks: every class and property is shown, written or not; unwritable IRIs are caveats (P-8) ---

    def visit_graph(self, graph: GraphAnalytics) -> dict[str, Any] | None:
        slug = graph_slug(graph.graph)
        return {"slug": slug, "label": graph.graph or DEFAULT_GRAPH_LABEL, "diagram": self.diagrams.get(slug, "")}

    def visit_class(self, graph: GraphAnalytics, cls: ClassAnalytics) -> dict[str, Any] | None:
        self.accepts(cls.class_iri)
        sampled = cls.precision_mode == PrecisionMode.first_n
        parents = sorted(cls.parents or [], key=lambda p: p.parent)
        return {
            "iri": cls.class_iri,
            "label": self.label(cls.class_iri),
            "anchor": f"{graph_slug(graph.graph)}-{graph_slug(cls.class_iri)}",
            "instances": cls.instances,
            "precision": f"first {cls.observed_instances} of {cls.instances}" if sampled else "exact",
            "sampled": sampled,
            "parents": [{"label": self.label(p.parent), "source": p.source} for p in parents],
        }

    def visit_property(self, graph: GraphAnalytics, cls: ClassAnalytics, prop: PropertyAnalytics) -> dict[str, Any] | None:
        self.accepts(prop.property)
        for value_type in prop.value_types or []:
            self.accepts(value_type)
        return {
            "iri": prop.property,
            "label": self.label(prop.property),
            "types": [self.label(t) for t in prop.value_types or []],
            "cardinality": multiplicity(prop.cardinality_label, prop.exact_count) if prop.cardinality_label else ABSENT,
            "usage": ABSENT if prop.confidence is None else f"{round(prop.confidence * 100)} %",
            "inheritance": prop.inheritance or ABSENT,
        }

    def serialize(self) -> dict[str, str]:
        graphs = self.view()
        analytics = self.analytics
        sampled = [
            {"graph": g["label"], "class": c["label"], "precision": c["precision"]}
            for g in graphs
            for c in g["classes"]
            if c["sampled"]
        ]
        failures = [
            {
                "graph": f.graph or DEFAULT_GRAPH_LABEL,
                "class": self.label(f.class_iri) if f.class_iri else ABSENT,
                "measurement": f.query_kind,
                "message": f.message,
            }
            for f in analytics.failures or []
        ]
        overview = {
            "endpoint": analytics.endpoint,
            "started_at": analytics.started_at,
            "finished_at": analytics.finished_at,
            "tool_version": analytics.tool_version,
            "settings": sorted(analytics.settings.model_dump(mode="json").items()),
        }
        view = {
            "graphs": graphs,
            "overview": overview,
            "namespaces": sorted(self.namespaces.items()),
            "caveats": {"sampled": sampled, "failures": failures, "skipped": list(self.skipped)},
        }
        return {self.file_name: self._render(view)}
