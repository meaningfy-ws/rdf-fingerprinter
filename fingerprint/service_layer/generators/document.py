"""The application-profile document: one HTML file in the SEMIC / SHACL Play style (DEC-7)."""

from pathlib import Path

from fingerprint import config
from fingerprint.domain.analytics import multiplicity
from fingerprint.domain.profile import (
    ClassAnalytics,
    GraphAnalytics,
    PrecisionMode,
    ProfileAnalytics,
    PropertyAnalytics,
)
from fingerprint.domain.views import (
    Caveats,
    DocumentClass,
    DocumentGraph,
    DocumentProperty,
    FailureNote,
    GeneratorOptions,
    Overview,
    ParentReference,
    ProfileDocument,
    RenderedDocument,
    SampledClass,
    SettingValue,
)
from fingerprint.service_layer.generators.generator import Generator, TemplateRenderer, graph_slug
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
        options: GeneratorOptions | None = None,
        diagrams: list[RenderedDocument] | None = None,
    ):
        """`diagrams`: the PlantUML source per graph slug, composed by the representations service."""
        super().__init__(analytics, renderer, template_location, options)
        self.diagrams = diagrams or []

    # --- hooks: every class and property is shown, written or not; unwritable IRIs are caveats (P-8) ---

    def visit_class(self, graph: GraphAnalytics, cls: ClassAnalytics) -> bool:
        self.accepts(cls.class_iri)
        return True

    def visit_property(self, graph: GraphAnalytics, cls: ClassAnalytics, prop: PropertyAnalytics) -> DocumentProperty:
        self.accepts(prop.property)
        for value_type in prop.value_types or []:
            self.accepts(value_type)
        return DocumentProperty(
            iri=prop.property,
            label=self.label(prop.property),
            types=[self.label(t) for t in prop.value_types or []],
            cardinality=multiplicity(prop.cardinality_label, prop.exact_count) if prop.cardinality_label else ABSENT,
            usage=ABSENT if prop.confidence is None else f"{round(prop.confidence * 100)} %",
            inheritance=prop.inheritance or ABSENT,
        )

    def end_class(self, graph: GraphAnalytics, cls: ClassAnalytics, properties: list[DocumentProperty]) -> DocumentClass:
        sampled = cls.precision_mode == PrecisionMode.first_n
        parents = sorted(cls.parents or [], key=lambda p: p.parent)
        return DocumentClass(
            iri=cls.class_iri,
            label=self.label(cls.class_iri),
            anchor=f"{graph_slug(graph.graph)}-{graph_slug(cls.class_iri)}",
            instances=cls.instances,
            precision=f"first {cls.observed_instances} of {cls.instances}" if sampled else "exact",
            sampled=sampled,
            parents=[ParentReference(label=self.label(p.parent), source=p.source) for p in parents],
            properties=properties,
        )

    def end_graph(self, graph: GraphAnalytics, classes: list[DocumentClass]) -> DocumentGraph:
        slug = graph_slug(graph.graph)
        diagram = next((d.text for d in self.diagrams if d.file_name == slug), "")
        return DocumentGraph(slug=slug, label=graph.graph or config.default_graph_label, diagram=diagram, classes=classes)

    def render_graphs(self) -> list[RenderedDocument]:
        """The whole document under one name: it covers every graph."""
        graphs = self.view()
        analytics = self.analytics
        sampled = [
            SampledClass(graph=g.label, class_label=c.label, precision=c.precision)
            for g in graphs
            for c in g.classes or []
            if c.sampled
        ]
        failures = [
            FailureNote(
                graph=f.graph or config.default_graph_label,
                class_label=self.label(f.class_iri) if f.class_iri else ABSENT,
                measurement=str(f.query_kind),
                message=f.message,
            )
            for f in analytics.failures or []
        ]
        overview = Overview(
            endpoint=analytics.endpoint,
            started_at=analytics.started_at,
            finished_at=analytics.finished_at,
            tool_version=analytics.tool_version,
            settings=[
                SettingValue(name=name, value=ABSENT if value is None else str(value))
                for name, value in sorted(analytics.settings.model_dump(mode="json").items())
            ],
        )
        document = ProfileDocument(
            overview=overview,
            namespaces=self.used_namespaces(),
            graphs=graphs,
            caveats=Caveats(sampled=sampled, failures=failures, skipped=list(self.skipped)),
            skipped=list(self.skipped),
        )
        return [RenderedDocument(file_name=self.file_name, text=self._render(document))]

    def serialize(self) -> list[RenderedDocument]:
        return self.render_graphs()
