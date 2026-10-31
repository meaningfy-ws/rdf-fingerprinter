"""The generator framework, modelled on LinkML's `Generator` (AD-8, P-1, P-2).

A generator walks the analytics and calls one visit hook per graph, class and property; each hook
returns the dict its template sees at that level, or None to drop the element. All mapping logic
lives in the hooks; the template package only lays the view out as text.
"""

import hashlib
import logging
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any, ClassVar, Protocol

from fingerprint import config
from fingerprint.domain.exceptions import IriRefError
from fingerprint.domain.iri import split_curie, to_iriref
from fingerprint.domain.profile import ClassAnalytics, GraphAnalytics, ProfileAnalytics, PropertyAnalytics

logger = logging.getLogger(__name__)

# Graph names reach PlantUML titles and Turtle comments, where the tools interpret text: keep it plain.
_NOT_PLAIN = re.compile(r"[^\w:/#.~ -]")


class TemplateRenderer(Protocol):
    """The port the generators render through; `fingerprint.adapters.template_renderer` implements it."""

    prefixes: dict[str, str]

    def render(
        self,
        package: str | Path,
        *,
        view: Any = None,
        config: Mapping[str, Any] | None = None,
        autoescape: bool | None = None,
    ) -> str: ...

    def write(self, folder: str | Path, texts: Mapping[str, str], check: str | None = None) -> list[Path]: ...


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

    def __init__(self, analytics: ProfileAnalytics, renderer: TemplateRenderer, template_location: str | Path | None = None):
        self.analytics = analytics
        self.renderer = renderer
        self.prefixes = renderer.prefixes
        self.template_location = template_location
        self.skipped: list[str] = []  # IRIs left out because they cannot be written (P-8)
        self.namespaces: dict[str, str] = {}  # prefixes the labels used, for a namespaces section

    # --- hooks, overridden per format ---

    def visit_graph(self, graph: GraphAnalytics) -> dict[str, Any] | None:
        return {"graph": graph.graph, "slug": graph_slug(graph.graph), "graph_label": plain_label(graph.graph)}

    def visit_class(self, graph: GraphAnalytics, cls: ClassAnalytics) -> dict[str, Any] | None:
        return {"iri": cls.class_iri}

    def visit_property(self, graph: GraphAnalytics, cls: ClassAnalytics, prop: PropertyAnalytics) -> dict[str, Any] | None:
        return {"iri": prop.property}

    def end_graph(self, graph: GraphAnalytics, view: dict[str, Any]) -> None:
        """Called once a graph's classes are visited, e.g. to declare the prefixes they used."""

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

    # --- the walk ---

    def view(self) -> list[dict[str, Any]]:
        """One dict per graph, each with "classes", each with "properties"; classes and properties by IRI."""
        graphs = []
        for graph in self.analytics.graphs or []:
            graph_view = self.visit_graph(graph)
            if graph_view is None:
                continue
            classes = []
            for cls in sorted(graph.class_partitions or [], key=lambda c: c.class_iri):
                class_view = self.visit_class(graph, cls)
                if class_view is None:
                    continue
                props = sorted(cls.property_partitions or [], key=lambda p: p.property)
                class_view["properties"] = [v for p in props if (v := self.visit_property(graph, cls, p)) is not None]
                classes.append(class_view)
            graph_view["classes"] = classes
            self.end_graph(graph, graph_view)
            graphs.append(graph_view)
        return graphs

    def render_graphs(self) -> dict[str, str]:
        """Slug → text, one per graph (per-graph formats)."""
        return {g["slug"]: self._render({"graph": g}) for g in self.view()}

    def serialize(self) -> dict[str, str]:
        """File name → text: one file per graph, or one file for all graphs."""
        if self.per_graph:
            return {self.file_name.format(slug=slug): text for slug, text in self.render_graphs().items()}
        return {self.file_name: self._render({"graphs": self.view()})}

    def write(self, folder: str | Path) -> list[Path]:
        return self.renderer.write(folder, self.serialize(), self.check)

    def _render(self, view: dict[str, Any]) -> str:
        return self.renderer.render(
            self.template_location or self.template_package,
            view=view | {"skipped": self.skipped},
            config={"conf": {"profile": self.analytics}},
            autoescape=self.autoescape,
        )
