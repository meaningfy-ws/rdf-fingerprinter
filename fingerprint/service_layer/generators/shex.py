"""The enriched ShExC: per graph one `.shex` file, the pattern view's statistics in `#` comments (llm-schema-tools P-2).

The pattern view is the same as the pattern schema's; `fingerprint.domain.shex` maps it to shapes, the template lays them out.
"""

import logging

from pydantic import BaseModel

from fingerprint.domain.shex import shex_view
from fingerprint.service_layer.generators.pattern import PatternGenerator
from fingerprint_report_templates import packaged

logger = logging.getLogger(__name__)


class ShexGenerator(PatternGenerator):
    template_package = packaged("shex_schema")
    file_name = "shex-{slug}.shex"

    def outputs(self) -> list[tuple[str, BaseModel]]:
        files: list[tuple[str, BaseModel]] = []
        for view in self.views():
            schema = shex_view(view)
            for iri in schema.skipped_terms or []:
                logger.warning("skipping %r in ShExC: PyShExC rejects '=' in an IRI", iri)
            files.append((self.file_name.format(slug=view.slug), schema))
        return files
