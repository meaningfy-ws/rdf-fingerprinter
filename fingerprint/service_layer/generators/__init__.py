"""One generator per representation, by the name the commands and `--format` use (AD-8)."""

from fingerprint.service_layer.generators.document import DocumentGenerator
from fingerprint.service_layer.generators.generator import Generator
from fingerprint.service_layer.generators.plantuml import PlantumlGenerator
from fingerprint.service_layer.generators.shacl import ShaclGenerator

SHACL, PUML, DOC = "shacl", "puml", "doc"
GENERATORS: dict[str, type[Generator]] = {SHACL: ShaclGenerator, PUML: PlantumlGenerator, DOC: DocumentGenerator}
