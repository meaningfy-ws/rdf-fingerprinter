"""The generator framework, modelled on LinkML's `Generator` (AD-8, P-1, P-2; domain-object-model P-4).

A generator walks the analytics. Pre-order hooks keep state and filter (`visit_graph`, `visit_class`
return False to skip); `visit_property` returns a property's view; post-order hooks build the frozen
view of a class from its properties (`end_class`) and of a graph from its classes (`end_graph`). The
views are LinkML-generated objects (`fingerprint.domain.views`); the template package only lays them
out as text.
"""

import hashlib
import logging
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, ClassVar, Protocol

from pydantic import BaseModel

from fingerprint import config
from fingerprint.domain.exceptions import IriRefError
from fingerprint.domain.iri import to_iriref
from fingerprint.domain.namespace_filter import namespace_filter
from fingerprint.domain.prefixes import PrefixTable, namespace_of
from fingerprint.domain.profile import ClassAnalytics, GraphAnalytics, ProfileAnalytics, PropertyAnalytics
from fingerprint.domain.views import GeneratorOptions, GraphView, OutputCheck, RenderedDocument
from fingerprint.service_layer.prefixes import resolve_namespaces

logger = logging.getLogger(__name__)

# Graph names reach PlantUML titles and Turtle comments, where the tools interpret text: keep it plain.
_NOT_PLAIN = re.compile(r"[^\w:/#.~ -]")


class TemplateRenderer(Protocol):
    """The port the generators render through; `fingerprint.adapters.template_renderer` implements it.
    `outputs` are (file name, view) pairs rendered with one template package; `conf` is what the template sees
    as `conf`, over the package's own `config.json` (domain-object-model P-6); `prefixes` binds the `curie` and
    `turtle_term` filters to the profile's table."""

    def render(
        self,
        package: str | Path,
        outputs: Sequence[tuple[str, BaseModel | None]],
        *,
        conf: Mapping[str, Any] | None = None,  # dict-ok: eds4jinja2 configuration
        autoescape: bool | None = None,
        prefixes: PrefixTable | None = None,
    ) -> list[RenderedDocument]:
        """The texts, in memory, in the order of `outputs`."""
        ...

    def make(
        self,
        package: str | Path,
        outputs: Sequence[tuple[str, BaseModel | None]],
        *,
        folder: str | Path,
        conf: Mapping[str, Any] | None = None,  # dict-ok: eds4jinja2 configuration
        check: OutputCheck | None = None,
        autoescape: bool | None = None,
        prefixes: PrefixTable | None = None,
    ) -> list[Path]:
        """Render, check every text, then write them all under `folder`; one failed check writes nothing."""
        ...


def graph_slug(graph: str | None) -> str:
    """`default`, or the graph IRI's last name made file-safe plus a short hash, so slugs never collide (P-11)."""
    if not graph:
        return "default"
    name = next((part for part in reversed(re.split(r"[/#:]", graph)) if part), "")
    readable = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:40] or "graph"
    return f"{readable}-{hashlib.sha1(graph.encode()).hexdigest()[:8]}"


def plain_label(graph: str | None) -> str:
    """The graph's name for titles and comments: letters, digits and `:/#.~ -` only, anything else `_`."""
    return _NOT_PLAIN.sub("_", graph or config.default_graph_label)


class Generator:
    """Walks the analytics it is given into views. Built directly, it hides the classes of the hidden and excluded
    namespaces only; the terms of an excluded namespace are removed by `exclude_terms`, which
    `generate_representations` applies first (namespace-filter P-3)."""

    template_package: ClassVar[Path]
    file_name: ClassVar[str]  # "{slug}" is replaced per graph when per_graph
    per_graph: ClassVar[bool] = True
    autoescape: ClassVar[bool | None] = None
    check: ClassVar[OutputCheck | None] = None  # what every text must pass before any file is written

    def __init__(
        self,
        analytics: ProfileAnalytics,
        renderer: TemplateRenderer,
        template_location: str | Path | None = None,
        options: GeneratorOptions | None = None,
    ):
        if analytics.namespaces is None:  # a profile saved before 3.0, or a library caller's own run
            analytics = resolve_namespaces(analytics)
        self.analytics = analytics
        self.renderer = renderer
        self.table = PrefixTable(analytics.namespaces)
        self.template_location = template_location
        self.options = options or GeneratorOptions()
        filters = namespace_filter(self.options, self.table)
        self.excluded = set(filters.hidden or []) | set(filters.excluded or [])  # class-level hiding only (DEC-7, P-3)
        self.skipped: list[str] = []  # IRIs left out because they cannot be written (P-8)
        self.hidden: dict[str, set[str]] = {}  # dict-ok: lookup index namespace → hidden class IRIs

    # --- hooks, overridden per format ---

    def visit_graph(self, graph: GraphAnalytics) -> bool:
        """Before a graph's classes: reset per-graph state; False skips the graph."""
        return True

    def visit_class(self, graph: GraphAnalytics, cls: ClassAnalytics) -> bool:
        """Before a class's properties; False skips the class and its properties."""
        return True

    def visit_property(self, graph: GraphAnalytics, cls: ClassAnalytics, prop: PropertyAnalytics) -> Any:
        """The view of one property, or None to leave it out."""
        return None

    def end_class(self, graph: GraphAnalytics, cls: ClassAnalytics, properties: list[Any]) -> Any:
        """The view of one class from its properties' views, or None to leave it out."""
        return None

    def end_graph(self, graph: GraphAnalytics, classes: list[Any]) -> Any:
        """The view of one graph from its classes' views (a `GraphView` for per-graph formats), or None."""
        return None

    def end_profile(self, graphs: list[Any]) -> BaseModel | None:
        """The one view of a format that covers every graph (`per_graph` False), or None to write nothing."""
        return None

    # --- shared rules ---

    def accepts(self, iri: str) -> bool:
        """Whether `iri` can be written as an IRI; if not, it is logged and recorded as skipped (P-8)."""
        try:
            to_iriref(iri)
        except IriRefError:
            logger.warning("skipping %r: it cannot be written as an IRI", iri)
            if iri not in self.skipped:
                self.skipped.append(iri)
            return False
        return True

    def namespace(self, iri: str) -> str:
        entry = self.table.entry_for(iri)
        return entry.namespace if entry else namespace_of(iri)

    def shown(self, iri: str) -> bool:
        """Whether a class is shown: its namespace is not excluded (DEC-5, DEC-8)."""
        return self.namespace(iri) not in self.excluded

    def label(self, iri: str) -> str:
        """A CURIE for display; the IRI itself when no prefix covers it."""
        entry = self.table.entry_for(iri)
        if entry is None:
            return iri
        return f"{entry.prefix}:{iri[len(entry.namespace) :]}"

    # --- the walk ---

    def view(self) -> list[Any]:
        """One view per graph; classes and properties visited in IRI order."""
        graphs = []
        for graph in self.analytics.graphs or []:
            if not self.visit_graph(graph):
                continue
            classes = []
            for cls in sorted(graph.class_partitions or [], key=lambda c: c.class_iri):
                if not self.shown(cls.class_iri):
                    self.hidden.setdefault(self.namespace(cls.class_iri), set()).add(cls.class_iri)
                    continue
                if not self.visit_class(graph, cls):
                    continue
                props = sorted(cls.property_partitions or [], key=lambda p: p.property)
                properties = [v for p in props if (v := self.visit_property(graph, cls, p)) is not None]
                if (class_view := self.end_class(graph, cls, properties)) is not None:
                    classes.append(class_view)
            if self.per_graph and not classes:  # no shown class: no file (profile-representations)
                continue
            if (graph_view := self.end_graph(graph, classes)) is not None:
                graphs.append(graph_view)
        return graphs

    def outputs(self) -> list[tuple[str, BaseModel]]:
        """(file name, view) pairs: one per graph, each listing every IRI skipped, or one for all graphs."""
        graphs = self.view()
        if not self.per_graph:
            document = self.end_profile(graphs)
            return [] if document is None else [(self.file_name, document)]
        skipped = list(self.skipped)
        views: list[GraphView] = graphs
        return [(self.file_name.format(slug=g.slug), g.model_copy(update={"skipped": skipped})) for g in views]

    def serialize(self) -> list[RenderedDocument]:
        """The files, in memory."""
        outputs = self.outputs()
        return self.renderer.render(
            self._package(), outputs, conf=self._conf(), autoescape=self.autoescape, prefixes=self.table
        )

    def write(self, folder: str | Path) -> list[Path]:
        outputs = self.outputs()
        return self.renderer.make(
            self._package(),
            outputs,
            folder=folder,
            conf=self._conf(),
            check=self.check,
            autoescape=self.autoescape,
            prefixes=self.table,
        )

    def _package(self) -> str | Path:
        return self.template_location or self.template_package

    def _conf(self) -> Mapping[str, Any]:  # dict-ok: eds4jinja2 configuration
        """Nothing beyond the package's own `config.json`: templates read their `view` (DEC-9)."""
        return {}  # dict-ok: eds4jinja2 configuration
