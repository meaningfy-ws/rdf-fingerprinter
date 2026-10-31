"""One generator per representation, by the name the commands and `--format` use (AD-8)."""

from fingerprint.service_layer.generators.generator import Generator
from fingerprint.service_layer.generators.shacl import ShaclGenerator

GENERATORS: dict[str, type[Generator]] = {"shacl": ShaclGenerator}
