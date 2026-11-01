"""One generator per representation, keyed by the format the commands and `--format` use (AD-8)."""

from fingerprint.domain.views import RepresentationFormat
from fingerprint.service_layer.generators.document import DocumentGenerator
from fingerprint.service_layer.generators.generator import Generator
from fingerprint.service_layer.generators.pattern import PatternGenerator
from fingerprint.service_layer.generators.pitfalls import PitfallsGenerator
from fingerprint.service_layer.generators.plantuml import PlantumlGenerator
from fingerprint.service_layer.generators.shacl import ShaclGenerator

SHACL, PUML, DOC = RepresentationFormat.shacl, RepresentationFormat.puml, RepresentationFormat.doc
PITFALLS, PATTERN = RepresentationFormat.pitfalls, RepresentationFormat.pattern
GENERATORS: dict[RepresentationFormat, type[Generator]] = {
    SHACL: ShaclGenerator,
    PUML: PlantumlGenerator,
    DOC: DocumentGenerator,
    PITFALLS: PitfallsGenerator,
    PATTERN: PatternGenerator,
}
