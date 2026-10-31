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
from collections.abc import Mapping
from pathlib import Path
from typing import Any, ClassVar, Protocol

from pydantic import BaseModel

from fingerprint import config
from fingerprint.domain.exceptions import IriRefError
from fingerprint.domain.iri import split_curie, to_iriref
from fingerprint.domain.profile import ClassAnalytics, GraphAnalytics, ProfileAnalytics, PropertyAnalytics
from fingerprint.domain.views import GeneratorOptions, PrefixDeclaration, RenderedDocument

logger = logging.getLogger(__name__)

# Graph names reach PlantUML titles and Turtle comments, where the tools interpret text: keep it plain.
_NOT_PLAIN = re.compile(r"[^\w:/#.~ -]")


class TemplateRenderer(Protocol):
    """The port the generators render through; `fingerprint.adapters.template_renderer` implements it."""

    prefixes: dict[str, str]  # dict-ok: prefix table

    def render(
        self,
        package: str | Path,
        *,
        view: BaseModel | None = None,
        config: Mapping[str, Any] | None = None,  # dict-ok: eds4jinja2 configuration
        autoescape: bool | None = None,
    ) -> str: ...

    def write(self, folder: str | Path, documents: list[RenderedDocument], check: str | None = None) -> list[Path]: ...


def graph_slug(graph: str | None) -> str:
    """`default`, or the graph IRI's last name made file-safe plus a short hash, so slugs never collide (P-11)."""
    if not graph:
        return "default"
    name = next((part for part in reversed(re.split(r"[/#:]", graph)) if part), "")
    readable = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:40] or "graph"
    return f"{readable}-{hashlib.sha1(graph.encode()).hexdigest()[:8]}"


def plain_label(graph: str | None) -> str:
    """The graph's name for titles and comments: letters, digits and `:/#.~ -` only, anything else `_`."""
    return _NOT_PLAIN.sub("_", graph) if graph else config.default_graph_label


class Generator:
    template_package: ClassVar[Path]
    file_name: ClassVar[str]  # "{slug}" is replaced per graph when per_graph
    per_graph: ClassVar[bool] = True
    autoescape: ClassVar[bool | None] = None
    check: ClassVar[str | None] = None  # a check of the template renderer, e.g. "turtle"

    def __init__(
        self,
        analytics: ProfileAnalytics,
        renderer: TemplateRenderer,
        template_location: str | Path | None = None,
        options: GeneratorOptions | None = None,
    ):
        self.analytics = analytics
        self.renderer = renderer
        self.prefixes = renderer.prefixes
        self.template_location = template_location
        self.options = options or GeneratorOptions()
        self.skipped: list[str] = []  # IRIs left out because they cannot be written (P-8)
        self.namespaces: dict[str, str] = {}  # dict-ok: lookup index of the prefixes the labels used

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
        """The view of one graph from its classes' views, or None to leave it out."""
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

    def label(self, iri: str) -> str:
        """A CURIE for display, remembering the namespace it used."""
        found = split_curie(iri, self.prefixes)
        if not found:
            return iri
        self.namespaces[found[0]] = self.prefixes[found[0]]
        return f"{found[0]}:{found[1]}"

    def used_namespaces(self) -> list[PrefixDeclaration]:
        return [PrefixDeclaration(prefix=p, namespace=ns) for p, ns in sorted(self.namespaces.items())]

    # --- the walk ---

    def view(self) -> list[Any]:
        """One view per graph; classes and properties visited in IRI order."""
        graphs = []
        for graph in self.analytics.graphs or []:
            if not self.visit_graph(graph):
                continue
            classes = []
            for cls in sorted(graph.class_partitions or [], key=lambda c: c.class_iri):
                if not self.visit_class(graph, cls):
                    continue
                props = sorted(cls.property_partitions or [], key=lambda p: p.property)
                properties = [v for p in props if (v := self.visit_property(graph, cls, p)) is not None]
                if (class_view := self.end_class(graph, cls, properties)) is not None:
                    classes.append(class_view)
            if (graph_view := self.end_graph(graph, classes)) is not None:
                graphs.append(graph_view)
        return graphs

    def render_graphs(self) -> list[RenderedDocument]:
        """One text per graph, under the graph's slug (per-graph formats); each view lists every IRI skipped."""
        views = self.view()
        return [
            RenderedDocument(file_name=g.slug, text=self._render(g.model_copy(update={"skipped": list(self.skipped)})))
            for g in views
        ]

    def serialize(self) -> list[RenderedDocument]:
        """The files: one per graph, or one for all graphs."""
        return [RenderedDocument(file_name=self.file_name.format(slug=d.file_name), text=d.text) for d in self.render_graphs()]

    def write(self, folder: str | Path) -> list[Path]:
        return self.renderer.write(folder, self.serialize(), self.check)

    def _render(self, view: BaseModel) -> str:
        return self.renderer.render(
            self.template_location or self.template_package,
            view=view,
            config={"conf": {"profile": self.analytics}},  # dict-ok: eds4jinja2 configuration
            autoescape=self.autoescape,
        )
