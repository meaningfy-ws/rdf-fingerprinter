"""The pattern schema: per graph one text file of class blocks and their edges with statistics (llm-schema-tools P-2).

Every rule that decides what a line says is in `fingerprint.domain.patterns`; the template only lays the view out.
"""

from pydantic import BaseModel

from fingerprint.domain.patterns import pattern_view
from fingerprint.service_layer.generators.generator import Generator, graph_slug, plain_label
from fingerprint_report_templates import packaged


class PatternGenerator(Generator):
    template_package = packaged("pattern_schema")
    file_name = "pattern-{slug}.txt"

    def outputs(self) -> list[tuple[str, BaseModel]]:
        """One file per graph that has a block (a graph with no shown class, or all hidden by a size filter, has none)."""
        files: list[tuple[str, BaseModel]] = []
        for graph in self.analytics.graphs or []:
            view = pattern_view(
                graph,
                self.table,
                self.options,
                excluded=frozenset(self.excluded),
                graph_label=plain_label(graph.graph),
                slug=graph_slug(graph.graph),
            )
            self.skipped.extend(iri for iri in view.skipped or [] if iri not in self.skipped)
            if view.blocks:
                files.append((self.file_name.format(slug=view.slug), view))
        return files
