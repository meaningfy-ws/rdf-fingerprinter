"""The report page `main.html`: one static, self-contained HTML document (readable-representations DEC-3, DEC-4).

Every value is written as display text here; the template only lays it out (domain-object-model DEC-2).
"""

from fingerprint import config
from fingerprint.domain.pitfalls import IMPORTANCE_ORDER, rank
from fingerprint.domain.profile import (
    ClassAnalytics,
    GraphAnalytics,
    NodeKind,
    PitfallResult,
    PitfallTerm,
    PrecisionMode,
    PropertyAnalytics,
)
from fingerprint.domain.views import (
    Caveats,
    CollectionSection,
    DocumentBadge,
    DocumentClass,
    DocumentGraph,
    DocumentPitfallCheck,
    DocumentPitfallExample,
    DocumentPitfallGraph,
    DocumentPitfalls,
    DocumentProperty,
    DocumentTerm,
    DocumentValue,
    FailureNote,
    HiddenNamespace,
    Overview,
    ParentReference,
    PitfallLevelCount,
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

    def value(self, term: PitfallTerm | None) -> DocumentValue:
        """A pitfall term as the page shows it: an IRI as a short name (full IRI kept), anything else as text."""
        if term is None:
            return DocumentValue(label="")
        if term.kind == NodeKind.iri:
            return DocumentValue(label=self.label(term.text), iri=term.text)
        return DocumentValue(label=f"_:{term.text}" if term.kind == NodeKind.blank_node else term.text)

    @staticmethod
    def check_anchor(graph: GraphAnalytics, check_id: str) -> str:
        return f"pitfall-{graph_slug(graph.graph)}-{check_id}"

    def badges(self, graph: GraphAnalytics, class_iri: str) -> list[DocumentBadge]:
        """The checks of this graph whose examples name the class (fingerprint-report › Pitfalls in the report)."""
        found = [
            r
            for r in graph.pitfalls or []
            if any(e.entity and e.entity.kind == NodeKind.iri and e.entity.text == class_iri for e in r.examples or [])
        ]
        return [
            DocumentBadge(check_id=r.check_id, anchor=self.check_anchor(graph, r.check_id), importance=str(r.importance))
            for r in sorted(found, key=lambda r: (rank(r.importance), r.check_id))
        ]

    def pitfall_check(self, graph: GraphAnalytics, result: PitfallResult) -> DocumentPitfallCheck:
        return DocumentPitfallCheck(
            check_id=result.check_id,
            anchor=self.check_anchor(graph, result.check_id),
            title=result.title,
            description=result.description,
            importance=str(result.importance),
            source=result.source,
            count=result.count,
            heuristic=bool(result.heuristic),
            q=f"{result.check_id} {result.title}".lower(),
            examples=[
                DocumentPitfallExample(entity=self.value(e.entity), property=self.value(e.property), value=self.value(e.value))
                for e in result.examples or []
            ],
        )

    def pitfalls(self) -> DocumentPitfalls | None:
        """The Pitfalls section, or None when the profile has no scan results (DEC-5)."""
        scanned = [g for g in self.analytics.graphs or [] if g.pitfalls is not None]
        if not scanned:
            return None
        graphs = []
        for g in scanned:
            found = sorted((r for r in g.pitfalls or [] if r.count), key=lambda r: (rank(r.importance), -r.count, r.check_id))
            graphs.append(
                DocumentPitfallGraph(
                    label=self.graph_label(g.graph),
                    slug=graph_slug(g.graph),
                    checks=[self.pitfall_check(g, r) for r in found],
                    clean=sorted(r.check_id for r in g.pitfalls or [] if not r.count),
                )
            )
        summary = [
            PitfallLevelCount(
                importance=level.value,
                checks=len({r.check_id for g in scanned for r in g.pitfalls or [] if r.count and rank(r.importance) == i}),
            )
            for i, level in enumerate(IMPORTANCE_ORDER)
        ]
        return DocumentPitfalls(summary=summary, graphs=graphs)

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
            badges=self.badges(graph, cls.class_iri),
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
                measurement=str(f.query_kind) + (f" {f.check_id}" if f.check_id else ""),
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
            pitfalls=self.pitfalls(),
            graphs=graphs,
            caveats=Caveats(sampled=sampled, untyped=untyped, hidden=hidden, skipped=list(self.skipped)),
            skipped=list(self.skipped),
        )
