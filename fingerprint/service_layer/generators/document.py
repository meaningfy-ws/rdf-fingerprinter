"""The report page `main.html`: one static, self-contained HTML document (readable-representations DEC-3, DEC-4).

Every value is written as display text here; the template only lays it out (domain-object-model DEC-2).
"""

from fingerprint import config
from fingerprint.domain.profile import ClassAnalytics, GraphAnalytics, PrecisionMode, PropertyAnalytics
from fingerprint.domain.views import (
    Caveats,
    CollectionSection,
    DocumentClass,
    DocumentGraph,
    DocumentProperty,
    DocumentTerm,
    FailureNote,
    HiddenNamespace,
    Overview,
    ParentReference,
    PrefixDeclaration,
    ProfileDocument,
    SampledClass,
    SettingValue,
    UntypedSubjects,
)
from fingerprint.service_layer.generators.generator import Generator, graph_slug
from fingerprint_report_templates import packaged

ABSENT = "—"


def number(value: float | int | None) -> str:
    """A number rounded to 2 decimals; an absent value is a dash (the 1.x report's rule)."""
    if value is None:
        return ABSENT
    if isinstance(value, float):
        return f"{round(value, 2):g}"
    return str(value)


class DocumentGenerator(Generator):
    template_package = packaged("fingerprint_report")
    file_name = "main.html"
    per_graph = False
    autoescape = True  # endpoint data is untrusted (DEC-4)

    # --- hooks: every shown class and property is listed, written or not; unwritable IRIs are caveats (P-8) ---

    def visit_class(self, graph: GraphAnalytics, cls: ClassAnalytics) -> bool:
        self.accepts(cls.class_iri)
        return True

    def search_text(self, iri: str) -> str:
        return f"{self.label(iri)} {iri}".lower()

    def graph_label(self, graph: str | None) -> str:
        return self.label(graph) if graph else config.default_graph_label

    def visit_property(self, graph: GraphAnalytics, cls: ClassAnalytics, prop: PropertyAnalytics) -> DocumentProperty:
        self.accepts(prop.property)
        for value_type in prop.value_types or []:
            self.accepts(value_type)
        cardinality = prop.cardinality_label or ("present" if prop.presence_only else ABSENT)
        return DocumentProperty(
            iri=prop.property,
            label=self.label(prop.property),
            subjects=number(prop.subjects_with_property),
            min=number(prop.min),
            max=number(prop.max),
            avg=number(prop.mean),
            kind=prop.property_kind or ABSENT,
            distinct=number(prop.distinct_objects),
            types=[DocumentTerm(iri=t, label=self.label(t)) for t in prop.value_types or []],
            confidence=number(prop.confidence),
            cardinality=str(cardinality),
            inheritance=prop.inheritance or ABSENT,
            language_coverage=number(prop.language_coverage),
        )

    def end_class(self, graph: GraphAnalytics, cls: ClassAnalytics, properties: list[DocumentProperty]) -> DocumentClass:
        sampled = cls.precision_mode == PrecisionMode.first_n
        parents = sorted(cls.parents or [], key=lambda p: p.parent)
        entry = self.table.entry_for(cls.class_iri)
        return DocumentClass(
            iri=cls.class_iri,
            label=self.label(cls.class_iri),
            prefix=entry.prefix if entry else "",
            anchor=f"{graph_slug(graph.graph)}-{graph_slug(cls.class_iri)}",
            q=self.search_text(cls.class_iri),
            instances=cls.instances,
            precision=f"first {cls.observed_instances} of {cls.instances}" if sampled else "exact",
            sample_note="(sample may differ between queries)" if sampled and cls.sample_shared is False else None,
            sampled=sampled,
            parents=[ParentReference(iri=p.parent, label=self.label(p.parent), source=p.source) for p in parents],
            properties=properties,
        )

    def end_graph(self, graph: GraphAnalytics, classes: list[DocumentClass]) -> DocumentGraph:
        return DocumentGraph(
            slug=graph_slug(graph.graph),
            label=self.graph_label(graph.graph),
            iri=graph.graph,
            empty=not graph.class_partitions,
            classes=classes,
        )

    def end_profile(self, graphs: list[DocumentGraph]) -> ProfileDocument:
        """The whole page: it covers every graph."""
        analytics = self.analytics
        sampled = [
            SampledClass(graph=g.label, class_label=c.label, precision=c.precision)
            for g in graphs
            for c in g.classes or []
            if c.sampled
        ]
        failures = [
            FailureNote(
                graph=self.graph_label(f.graph),
                class_label=self.label(f.class_iri) if f.class_iri else ABSENT,
                property_label=self.label(f.property) if f.property else ABSENT,
                measurement=str(f.query_kind),
                attempts=number(f.attempts),
                message=f.message,
            )
            for f in analytics.failures or []
        ]
        untyped = [
            UntypedSubjects(graph=self.graph_label(g.graph), count=g.untyped_subjects)
            for g in analytics.graphs or []
            if g.untyped_subjects
        ]
        hidden = []
        for namespace, classes in sorted(self.hidden.items()):
            entry = self.table.by_namespace(namespace)
            prefix = entry.prefix if entry else namespace
            hidden.append(HiddenNamespace(prefix=prefix, namespace=namespace, classes=len(classes)))
        settings = [
            SettingValue(name=name, value=ABSENT if value is None else str(value))
            for name, value in sorted(analytics.settings.model_dump(mode="json").items())
        ]
        namespaces = [
            PrefixDeclaration(prefix=e.prefix, namespace=e.namespace, source=str(e.source)) for e in self.table.entries
        ]
        return ProfileDocument(
            overview=Overview(
                endpoint=analytics.endpoint,
                started_at=analytics.started_at,
                finished_at=analytics.finished_at,
                tool_version=analytics.tool_version,
            ),
            namespaces=namespaces,
            collection=CollectionSection(settings=settings, failures=failures),
            graphs=graphs,
            caveats=Caveats(sampled=sampled, untyped=untyped, hidden=hidden, skipped=list(self.skipped)),
            skipped=list(self.skipped),
        )
