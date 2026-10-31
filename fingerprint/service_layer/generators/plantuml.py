"""PlantUML class diagrams: per graph an overview of its namespaces and one diagram per module (DEC-7).

A module is a namespace's shown classes, or one cluster of them when there are more than the module size; a class
outside the module, or not profiled, is a reference box. Own and refined properties only (2.0 DEC-6).
"""

from collections import Counter
from pathlib import Path

from pydantic import BaseModel

from fingerprint.domain.analytics import multiplicity
from fingerprint.domain.modules import cluster
from fingerprint.domain.profile import (
    ClassAnalytics,
    GraphAnalytics,
    Inheritance,
    ParentSource,
    ProfileAnalytics,
    PropertyAnalytics,
    PropertyKind,
)
from fingerprint.domain.views import (
    DiagramBox,
    DiagramClass,
    DiagramKind,
    DiagramLink,
    DiagramMember,
    DiagramMemberKind,
    DiagramModule,
    DiagramOverview,
    DiagramPackage,
    GeneratorOptions,
)
from fingerprint.service_layer.generators.generator import Generator, TemplateRenderer, graph_slug, plain_label
from fingerprint_report_templates import packaged

DIAGRAMMED_INHERITANCE = {Inheritance.own.value, Inheritance.refined.value}


class PlantumlGenerator(Generator):
    template_package = packaged("plantuml_diagram")
    file_name = "diagram-{slug}.puml"

    def __init__(
        self,
        analytics: ProfileAnalytics,
        renderer: TemplateRenderer,
        template_location: str | Path | None = None,
        options: GeneratorOptions | None = None,
    ):
        super().__init__(analytics, renderer, template_location, options)
        self.module_size = self.options.module_size or 15
        self._aliases: dict[str, str] = {}  # dict-ok: lookup index class IRI → alias, built per graph
        self._iri_of: dict[str, str] = {}  # dict-ok: lookup index alias → class IRI
        self._references = 0
        self._links: list[tuple[str, str]] = []  # (class IRI, target IRI): associations and generalisations
        self._files: list[tuple[str, DiagramModule | DiagramOverview]] = []

    # --- hooks ---

    def visit_graph(self, graph: GraphAnalytics) -> bool:
        # Aliases make every name safe to quote: the labels are CURIEs of IRIs the hooks accepted.
        accepted = sorted(
            c.class_iri for c in graph.class_partitions or [] if self.shown(c.class_iri) and self.accepts(c.class_iri)
        )
        self._aliases = {iri: f"C{n}" for n, iri in enumerate(accepted, 1)}  # dict-ok: lookup index
        self._iri_of = {alias: iri for iri, alias in self._aliases.items()}  # dict-ok: lookup index
        self._references = 0
        self._links = []
        return True

    def visit_class(self, graph: GraphAnalytics, cls: ClassAnalytics) -> bool:
        return cls.class_iri in self._aliases

    def visit_property(self, graph: GraphAnalytics, cls: ClassAnalytics, prop: PropertyAnalytics) -> DiagramMember | None:
        if prop.inheritance not in DIAGRAMMED_INHERITANCE or not self.accepts(prop.property):
            return None
        uml = multiplicity(prop.cardinality_label, prop.exact_count)
        classes = {p.object_class for p in prop.value_partitions or [] if p.object_class}
        target = next(iter(classes)) if len(classes) == 1 else None
        if (
            target
            and self.accepts(target)
            and not prop.untyped_object_ratio
            and prop.property_kind == PropertyKind.object_property
        ):
            self._links.append((cls.class_iri, target))
            text = f'"{uml}" {self.alias(target)} : {self.label(prop.property)}'
            return DiagramMember(kind=DiagramMemberKind.association, text=text)
        return DiagramMember(
            kind=DiagramMemberKind.attribute, text=f"{self.label(prop.property)} : {self.types(prop)} [{uml}]"
        )

    def end_class(self, graph: GraphAnalytics, cls: ClassAnalytics, properties: list[DiagramMember]) -> DiagramClass:
        alias = self._aliases[cls.class_iri]
        generalisations = []
        for parent in sorted(cls.parents or [], key=lambda p: p.parent):
            if self.accepts(parent.parent) and self.shown(parent.parent):  # a hidden parent is left out
                arrow = "--|>" if parent.source == ParentSource.declared else "..|>"
                generalisations.append(f"{alias} {arrow} {self.alias(parent.parent)}")
                self._links.append((cls.class_iri, parent.parent))
        return DiagramClass(alias=alias, label=self.label(cls.class_iri), members=properties, generalisations=generalisations)

    def end_graph(self, graph: GraphAnalytics, classes: list[DiagramClass]) -> None:
        """Queue the graph's overview and module files (see `outputs`)."""
        slug = graph_slug(graph.graph)
        title = plain_label(self.label(graph.graph) if graph.graph else None)
        by_namespace: dict[str, list[DiagramClass]] = {}  # dict-ok: lookup index namespace → its class boxes
        for box in classes:
            by_namespace.setdefault(self.namespace(self._iri_of[box.alias]), []).append(box)
        modules: list[tuple[str, DiagramModule]] = []
        modules_of: dict[str, list[str]] = {}  # dict-ok: lookup index namespace → module names
        for namespace in sorted(by_namespace, key=self.prefix):
            boxes = by_namespace[namespace]
            prefix = self.prefix(namespace)
            label_of = {self._iri_of[b.alias]: b.label for b in boxes}  # dict-ok: lookup index
            inner = [(label_of[a], label_of[b]) for a, b in self._links if a in label_of and b in label_of]
            groups = cluster(label_of.values(), inner, self.module_size)
            names = [prefix] if len(groups) == 1 else [f"{prefix}~{n}" for n in range(1, len(groups) + 1)]
            modules_of[namespace] = names
            for name, group in zip(names, groups, strict=True):
                members = [b for b in boxes if b.label in group]
                view = DiagramModule(
                    kind=DiagramKind.module,
                    graph_label=title,
                    slug=slug,
                    name=name,
                    classes=members,
                    reference_boxes=self.references(members),
                )
                modules.append((f"diagram-{slug}--{name}.puml", view))
        self._files.append((f"diagram-{slug}.puml", self.overview(title, slug, by_namespace, modules_of)))
        self._files += modules

    # --- diagram parts ---

    def prefix(self, namespace: str) -> str:
        entry = self.table.by_namespace(namespace)
        return entry.prefix if entry else namespace

    def alias(self, iri: str) -> str:
        """A profiled class's alias, or a reference alias for any other class."""
        if iri not in self._aliases:
            self._references += 1
            self._aliases[iri] = f"P{self._references}"
            self._iri_of[self._aliases[iri]] = iri
        return self._aliases[iri]

    def references(self, members: list[DiagramClass]) -> list[DiagramBox]:
        """Boxes for the classes the module's arrows point to that are not in the module, in alias order."""
        inside = {m.alias for m in members}
        sources = {self._iri_of[m.alias] for m in members}
        targets = {self._aliases[t] for s, t in self._links if s in sources} - inside
        return [DiagramBox(alias=a, label=self.label(self._iri_of[a])) for a in sorted(targets, key=_alias_order)]

    def overview(
        self,
        title: str,
        slug: str,
        by_namespace: dict[str, list[DiagramClass]],  # dict-ok: lookup index
        modules_of: dict[str, list[str]],  # dict-ok: lookup index
    ) -> DiagramOverview:
        """Namespaces as packages, with counted links; links to hidden classes are neither drawn nor counted."""
        counts: Counter[tuple[str, str]] = Counter()  # dict-ok: lookup index namespace pair → link count
        referenced = set()
        for source, target in self._links:
            if not self.shown(target):
                continue
            pair = (self.namespace(source), self.namespace(target))
            if pair[0] != pair[1]:
                counts[pair] += 1
            if pair[1] not in by_namespace:
                referenced.add(pair[1])
        namespaces = sorted(set(by_namespace) | referenced, key=self.prefix)
        alias = {ns: f"N{n}" for n, ns in enumerate(namespaces, 1)}  # dict-ok: lookup index
        packages = [
            DiagramPackage(
                alias=alias[ns],
                prefix=self.prefix(ns),
                classes=len(by_namespace.get(ns, [])),
                referenced=ns not in by_namespace,
                modules=modules_of.get(ns, []),
            )
            for ns in namespaces
        ]
        ordered = sorted(counts.items(), key=lambda item: (self.prefix(item[0][0]), self.prefix(item[0][1])))
        links = [DiagramLink(source=alias[s], target=alias[t], count=n) for (s, t), n in ordered]
        return DiagramOverview(kind=DiagramKind.overview, graph_label=title, slug=slug, packages=packages, links=links)

    def outputs(self) -> list[tuple[str, BaseModel]]:
        """Per graph with a shown class: the overview, then one file per module, each listing every IRI skipped."""
        self._files = []
        self.view()
        skipped = list(self.skipped)
        return [(name, view.model_copy(update={"skipped": skipped})) for name, view in self._files]

    def types(self, prop: PropertyAnalytics) -> str:
        """The value types as labels; an IRI that cannot be written is left out and recorded (P-8)."""
        names = [self.label(t) for t in prop.value_types or [] if self.accepts(t)]
        if (prop.untyped_object_ratio or 0) > 0 or (not names and prop.property_kind == PropertyKind.object_property):
            names.append("resource")
        return " | ".join(names) or "value"


def _alias_order(alias: str) -> tuple[str, int]:
    return alias[0], int(alias[1:])
