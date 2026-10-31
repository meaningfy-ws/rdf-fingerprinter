"""One generator per representation, by the name the commands and `--format` use (AD-8)."""

from fingerprint.service_layer.generators.generator import Generator

GENERATORS: dict[str, type[Generator]] = {}
