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
    PrefixSource,
    PropertyAnalytics,
    PropertyKind,
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
    DocumentPropertyGroup,
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
    TaxonomyNode,
    UntypedSubjects,
)
from fingerprint.service_layer.generators.generator import Generator, graph_slug
from fingerprint_report_templates import packaged

ABSENT = "—"
# Property groups of a class table, in display order (pitfall-scans DEC-14); no hierarchy reads as own.
# Property kinds a class indicator counts as data and as object; mixed counts in both (DEC-19).
DATA_KINDS = (PropertyKind.datatype_property, PropertyKind.mixed)
OBJECT_KINDS = (PropertyKind.object_property, PropertyKind.mixed)
PROPERTY_GROUPS = (("Own", ("own", None)), ("Refined", ("refined",)), ("Inherited", ("inherited",)))


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
        groups = self.property_groups(cls, properties)
        kinds = {p.property: p.property_kind for p in cls.property_partitions or []}  # dict-ok: lookup index
        shown = [kinds[p.iri] for p in properties]
        return DocumentClass(
            iri=cls.class_iri,
            label=self.label(cls.class_iri),
            prefix=entry.prefix if entry else "",
            anchor=f"{graph_slug(graph.graph)}-{graph_slug(cls.class_iri)}",
            q=self.search_text(cls.class_iri),
            instances=cls.instances,
            data_properties=sum(k in DATA_KINDS for k in shown),
            object_properties=sum(k in OBJECT_KINDS for k in shown),
            precision=f"first {cls.observed_instances} of {cls.instances}" if sampled else "exact",
            sample_note="(sample may differ between queries)" if sampled and cls.sample_shared is False else None,
            sampled=sampled,
            parents=[ParentReference(iri=p.parent, label=self.label(p.parent), source=p.source) for p in parents],
            properties=[p for g in groups for p in g.properties or []],
            property_groups=groups,
            badges=self.badges(graph, cls.class_iri),
        )

    @staticmethod
    def property_groups(cls: ClassAnalytics, properties: list[DocumentProperty]) -> list[DocumentPropertyGroup]:
        """Own, refined, inherited; within each by subjects, confidence (both descending), short name (DEC-14)."""
        raw = {p.property: p for p in cls.property_partitions or []}  # dict-ok: lookup index IRI → analytics

        def key(row: DocumentProperty) -> tuple[int, float, str]:
            p = raw[row.iri]
            return -(p.subjects_with_property or 0), -(p.confidence or 0.0), row.label

        groups = []
        for name, kinds in PROPERTY_GROUPS:
            members = sorted((r for r in properties if raw[r.iri].inheritance in kinds), key=key)
            if members:
                groups.append(DocumentPropertyGroup(name=name, properties=members))
        return groups

    def end_graph(self, graph: GraphAnalytics, classes: list[DocumentClass]) -> DocumentGraph:
        ordered = sorted(classes, key=lambda c: (c.prefix, -c.instances, c.label))  # DEC-13
        return DocumentGraph(
            slug=graph_slug(graph.graph),
            label=self.graph_label(graph.graph),
            iri=graph.graph,
            empty=not graph.class_partitions,
            classes=ordered,
            taxonomy=self.taxonomy(ordered),
        )

    def taxonomy(self, classes: list[DocumentClass]) -> list[TaxonomyNode]:
        """The class tree from declared and implied parents, with popularity bars (DEC-15, design D-14)."""
        by_iri = {c.iri: c for c in classes}  # dict-ok: lookup index IRI → class
        largest = max((c.instances for c in classes), default=0)
        parents = {  # dict-ok: lookup index class → its shown parents, by short name
            c.iri: sorted({p.iri: p.label for p in c.parents or [] if self.shown(p.iri)}.items(), key=lambda kv: kv[1])
            for c in classes
        }
        children: dict[str, list[str]] = {}  # dict-ok: lookup index parent → child IRIs
        for iri, shown in parents.items():
            for parent, _ in shown:
                children.setdefault(parent, []).append(iri)
        first = {iri: shown[0][0] for iri, shown in parents.items() if shown}  # dict-ok: lookup index

        def order(iris: list[str]) -> list[str]:
            return sorted(iris, key=lambda i: (i not in by_iri, -(by_iri[i].instances if i in by_iri else 0), self.label(i)))

        placed: set[str] = set()

        def node(iri: str, path: tuple[str, ...]) -> TaxonomyNode:
            placed.add(iri)
            kids = []
            for child in order(children.get(iri, [])):
                if child in path or child == iri:
                    continue  # a cycle ends where it closes
                if first.get(child) == iri:
                    kids.append(node(child, (*path, iri)))
                else:
                    kids.append(self.taxonomy_node(by_iri[child], largest, see=True))
            cls = by_iri.get(iri)
            if cls is None:  # a parent not profiled in this graph
                return TaxonomyNode(label=self.label(iri), iri=iri, bar=0, children=kids)
            return self.taxonomy_node(cls, largest, children=kids)

        roots = [iri for iri in by_iri if not parents[iri]] + [p for p in children if p not in by_iri]
        tree = [node(iri, ()) for iri in order(roots)]
        for iri in order(list(by_iri)):  # classes reachable only through a cycle
            if iri not in placed:
                tree.append(node(iri, ()))
        return tree

    @staticmethod
    def taxonomy_node(
        cls: DocumentClass, largest: int, children: list[TaxonomyNode] | None = None, see: bool = False
    ) -> TaxonomyNode:
        bar = max(1, cls.instances * 100 // largest) if cls.instances and largest else 0
        return TaxonomyNode(
            label=cls.label,
            iri=cls.iri,
            anchor=None if see else cls.anchor,
            see=cls.anchor if see else None,
            instances=cls.instances,
            bar=bar,
            children=children or [],
        )

    def namespace_table(self) -> list[PrefixDeclaration]:
        """By prefix source, then uses descending, then prefix (DEC-18)."""
        uses = dict.fromkeys((e.namespace for e in self.table.entries), 0)  # dict-ok: lookup index namespace → uses

        def count(iri: str, n: int | None) -> None:
            entry = self.table.entry_for(iri)
            if entry:
                uses[entry.namespace] += n or 0

        for g in self.analytics.graphs or []:
            for c in g.class_partitions or []:
                count(c.class_iri, c.instances)
                for p in c.property_partitions or []:
                    count(p.property, p.subjects_with_property)
        order = list(PrefixSource)
        entries = sorted(self.table.entries, key=lambda e: (order.index(e.source), -uses[e.namespace], e.prefix))
        return [
            PrefixDeclaration(prefix=e.prefix, namespace=e.namespace, source=str(e.source), uses=uses[e.namespace])
            for e in entries
        ]

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
        namespaces = self.namespace_table()
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
