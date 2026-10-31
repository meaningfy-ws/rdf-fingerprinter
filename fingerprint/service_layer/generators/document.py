"""The application-profile document: one HTML file in the SEMIC / SHACL Play style (DEC-7)."""

from importlib.resources import files
from pathlib import Path
from typing import Any

import fingerprint_report_templates
from fingerprint.domain.exceptions import IriRefError
from fingerprint.domain.generated.profile import ClassAnalytics, GraphAnalytics, PrecisionMode, PropertyAnalytics
from fingerprint.domain.iri import to_iriref
from fingerprint.service_layer.generators.generator import Generator, TemplateRenderer, graph_slug
from fingerprint.service_layer.generators.plantuml import PlantumlGenerator
from fingerprint.service_layer.generators.shacl import ShaclGenerator


def _name(value: Any) -> str:
    return str(getattr(value, "value", value))


def _writable(iri: str) -> bool:
    try:
        to_iriref(iri)
    except IriRefError:
        return False
    return True


class DocumentGenerator(Generator):
    template_package = Path(str(files(fingerprint_report_templates) / "profile_document"))
    file_name = "profile.html"
    per_graph = False
    autoescape = True  # endpoint data is untrusted (DEC-4)

    def __init__(self, analytics: Any, renderer: TemplateRenderer, template_location: str | Path | None = None):
        super().__init__(analytics, renderer, template_location)
        self._namespaces: dict[str, str] = {}
        self._diagrams = {}
        for name, text in PlantumlGenerator(analytics, renderer).serialize().items():
            self._diagrams[name.removeprefix("diagram-").removesuffix(".puml")] = text

    def label(self, iri: str) -> str:
        """A CURIE for display, remembering the namespace for the namespaces section."""
        for prefix, namespace in self.prefixes.items():
            if iri.startswith(namespace):
                self._namespaces[prefix] = namespace
                return f"{prefix}:{iri[len(namespace) :]}"
        return iri

    # --- hooks: every class and property is shown, written or not (P-8) ---

    def visit_graph(self, graph: GraphAnalytics) -> dict[str, Any] | None:
        slug = graph_slug(graph.graph)
        return {
            "graph": graph.graph,
            "slug": slug,
            "label": graph.graph or "default graph",
            "files": [ShaclGenerator.file_name.format(slug=slug), PlantumlGenerator.file_name.format(slug=slug)],
            "diagram": self._diagrams.get(slug, ""),
        }

    def visit_class(self, graph: GraphAnalytics, cls: ClassAnalytics) -> dict[str, Any] | None:
        if not _writable(cls.class_iri):
            self.skipped.append(cls.class_iri)
        sampled = cls.precision_mode == PrecisionMode.first_n
        return {
            "iri": cls.class_iri,
            "label": self.label(cls.class_iri),
            "anchor": f"{graph_slug(graph.graph)}-{graph_slug(cls.class_iri)}",
            "instances": cls.instances,
            "precision": f"first {cls.observed_instances} of {cls.instances}" if sampled else "exact",
            "sampled": sampled,
            "parents": [(self.label(p.parent), _name(p.source)) for p in sorted(cls.parents or [], key=lambda p: p.parent)],
        }

    def visit_property(self, graph: GraphAnalytics, cls: ClassAnalytics, prop: PropertyAnalytics) -> dict[str, Any] | None:
        if not _writable(prop.property):
            self.skipped.append(prop.property)
        return {
            "iri": prop.property,
            "label": self.label(prop.property),
            "types": [self.label(t) for t in prop.value_types or []],
            "cardinality": PlantumlGenerator.multiplicity(prop) if prop.cardinality_label else "—",
            "usage": "—" if prop.confidence is None else f"{round(prop.confidence * 100)} %",
            "inheritance": _name(prop.inheritance) if prop.inheritance else "—",
        }

    def serialize(self) -> dict[str, str]:
        graphs = self.view()
        a = self.analytics
        caveats = {
            "sampled": [(g["label"], c["label"], c["precision"]) for g in graphs for c in g["classes"] if c["sampled"]],
            "failures": [
                (f.graph or "default graph", self.label(f.class_iri) if f.class_iri else "—", _name(f.query_kind), f.message)
                for f in a.failures or []
            ],
            "skipped": list(dict.fromkeys(self.skipped)),
        }
        overview = {
            "endpoint": a.endpoint,
            "started_at": a.started_at,
            "finished_at": a.finished_at,
            "tool_version": a.tool_version,
            "settings": sorted(a.settings.model_dump(mode="json").items()),
        }
        view = {
            "graphs": graphs,
            "overview": overview,
            "namespaces": sorted(self._namespaces.items()),
            "caveats": caveats,
        }
        return {self.file_name: self._render(view)}
