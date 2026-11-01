"""The pitfall findings as ROBOT-style TSV, one file per scanned graph (pitfall-scans DEC-9)."""

import re

from pydantic import BaseModel

from fingerprint.domain.pitfalls import rank, robot_level
from fingerprint.domain.profile import NodeKind, PitfallTerm
from fingerprint.domain.views import PitfallLine, PitfallsTable
from fingerprint.service_layer.generators.generator import Generator, graph_slug, plain_label
from fingerprint_report_templates import packaged

_BREAKS = re.compile(r"[\t\r\n]+")


def cell(term: PitfallTerm | None) -> str:
    """Full IRI, `_:id` for a blank node, a literal's lexical form; empty when unbound; no tab or line break."""
    if term is None:
        return ""
    text = f"_:{term.text}" if term.kind == NodeKind.blank_node else term.text
    return _BREAKS.sub(" ", text)


class PitfallsGenerator(Generator):
    template_package = packaged("pitfalls_tsv")
    file_name = "pitfalls-{slug}.tsv"

    def outputs(self) -> list[tuple[str, BaseModel]]:
        """One file per graph with scan results (a graph whose checks all counted 0 gets the header only)."""
        files: list[tuple[str, BaseModel]] = []
        for graph in self.analytics.graphs or []:
            if graph.pitfalls is None:
                continue
            ordered = sorted(graph.pitfalls, key=lambda r: (rank(r.importance), r.check_id))
            lines = [
                PitfallLine(
                    level=robot_level(r.importance),
                    rule=r.check_id,
                    subject=cell(e.entity),
                    property=cell(e.property),
                    value=cell(e.value),
                )
                for r in ordered
                for e in r.examples or []
            ]
            view = PitfallsTable(graph_label=plain_label(graph.graph), slug=graph_slug(graph.graph), lines=lines)
            files.append((self.file_name.format(slug=view.slug), view))
        return files
