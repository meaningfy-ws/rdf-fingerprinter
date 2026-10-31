"""PlantUML class diagrams from the analytics: one diagram per graph, own and refined properties (DEC-6)."""

from pathlib import Path

from fingerprint.domain.analytics import multiplicity
from fingerprint.domain.profile import (
    ClassAnalytics,
    GraphAnalytics,
    Inheritance,
    ParentSource,
    ProfileAnalytics,
    PropertyAnalytics,
    PropertyKind,
)
from fingerprint.domain.views import DiagramBox, DiagramClass, DiagramGraph, DiagramMember, DiagramMemberKind, GeneratorOptions
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
        self._aliases: dict[str, str] = {}  # dict-ok: lookup index class IRI → alias, built per graph
        self._parents: dict[str, str] = {}  # dict-ok: lookup index parent IRI → box alias, built per graph

    def visit_graph(self, graph: GraphAnalytics) -> bool:
        # Aliases make every name safe to quote: the labels are CURIEs of IRIs the hooks accepted.
        accepted = sorted(c.class_iri for c in graph.class_partitions or [] if self.accepts(c.class_iri))
        self._aliases = {iri: f"C{n}" for n, iri in enumerate(accepted, 1)}  # dict-ok: lookup index
        self._parents = {}  # dict-ok: lookup index
        return True

    def visit_class(self, graph: GraphAnalytics, cls: ClassAnalytics) -> bool:
        return cls.class_iri in self._aliases

    def visit_property(self, graph: GraphAnalytics, cls: ClassAnalytics, prop: PropertyAnalytics) -> DiagramMember | None:
        if prop.inheritance not in DIAGRAMMED_INHERITANCE or not self.accepts(prop.property):
            return None
        uml = multiplicity(prop.cardinality_label, prop.exact_count)
        classes = {p.object_class for p in prop.value_partitions or [] if p.object_class}
        target = next(iter(classes)) if len(classes) == 1 else None
        if target in self._aliases and not prop.untyped_object_ratio and prop.property_kind == PropertyKind.object_property:
            text = f'"{uml}" {self._aliases[target]} : {self.label(prop.property)}'
            return DiagramMember(kind=DiagramMemberKind.association, text=text)
        return DiagramMember(
            kind=DiagramMemberKind.attribute, text=f"{self.label(prop.property)} : {self.types(prop)} [{uml}]"
        )

    def end_class(self, graph: GraphAnalytics, cls: ClassAnalytics, properties: list[DiagramMember]) -> DiagramClass:
        alias = self._aliases[cls.class_iri]
        generalisations = []
        for parent in sorted(cls.parents or [], key=lambda p: p.parent):
            if self.accepts(parent.parent):
                arrow = "--|>" if parent.source == ParentSource.declared else "..|>"
                generalisations.append(f"{alias} {arrow} {self.alias(parent.parent)}")
        return DiagramClass(alias=alias, label=self.label(cls.class_iri), members=properties, generalisations=generalisations)

    def end_graph(self, graph: GraphAnalytics, classes: list[DiagramClass]) -> DiagramGraph:
        return DiagramGraph(
            graph_label=plain_label(graph.graph),
            slug=graph_slug(graph.graph),
            classes=classes,
            parent_boxes=[DiagramBox(alias=a, label=self.label(iri)) for iri, a in self._parents.items()],
        )

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
