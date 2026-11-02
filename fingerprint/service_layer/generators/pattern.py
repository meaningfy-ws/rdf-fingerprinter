"""The pattern schema: per graph five files, all laid out from the one pattern view (llm-schema-split P-1).

Every rule that decides what a line says is in `fingerprint.domain.patterns`; the templates only lay the view out.
"""

from pydantic import BaseModel

from fingerprint.domain.patterns import pattern_view
from fingerprint.domain.views import PatternFile, PatternGraph
from fingerprint.service_layer.generators.generator import Generator, graph_slug, plain_label
from fingerprint_report_templates import packaged

# (file name, the sub-template of `files.j2` that writes it): the five files of a graph, in this order
FILES = (
    ("prefixes-{slug}.md", "prefixes.md"),
    ("patterns-{slug}.md", "patterns.md"),
    ("patterns-{slug}.csv", "patterns.csv"),
    ("glossary-{slug}.md", "glossary.md"),
    ("glossary-{slug}.csv", "glossary.csv"),
)


class PatternGenerator(Generator):
    template_package = packaged("pattern_schema")

    def views(self) -> list[PatternGraph]:
        """One view per graph that has a block (a graph with no shown class, or all hidden by a size filter, has none)."""
        found: list[PatternGraph] = []
        for graph in self.analytics.graphs or []:
            view = pattern_view(
                graph,
                self.table,
                self.options,
                excluded=frozenset(self.excluded),
                graph_label=plain_label(graph.graph),
                slug=graph_slug(graph.graph),
            ).model_copy(update={"excluded_note": self.excluded_note(graph)})
            self.skipped.extend(iri for iri in view.skipped or [] if iri not in self.skipped)
            if view.blocks:
                found.append(view)
        return found

    def outputs(self) -> list[tuple[str, BaseModel]]:
        return [
            (name.format(slug=view.slug), PatternFile(template=template, graph=view))
            for view in self.views()
            for name, template in FILES
        ]
