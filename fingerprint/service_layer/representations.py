"""Representations of a profile run: re-analyse at a threshold and run the chosen generators (UC-W2, P-6)."""

import logging
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from fingerprint.adapters.exceptions import OntologyFileError, ProfileFileError, TemplatePackageError
from fingerprint.adapters.ontology_file import load_ontology
from fingerprint.adapters.profile_file import load_profile
from fingerprint.adapters.template_renderer import JinjaTemplateRenderer
from fingerprint.domain.analytics import analyse
from fingerprint.domain.annotations import merge_annotations, select_annotations
from fingerprint.domain.exceptions import IriRefError
from fingerprint.domain.iri import to_iriref
from fingerprint.domain.prefixes import PrefixTable
from fingerprint.domain.profile import NamespacePrefix, ProfileAnalytics, ProfileRun
from fingerprint.domain.views import GeneratorOptions, RepresentationFormat
from fingerprint.service_layer.exceptions import UsageError
from fingerprint.service_layer.generators import GENERATORS
from fingerprint.service_layer.generators.generator import Generator, TemplateRenderer, excluded_namespaces
from fingerprint.service_layer.prefixes import resolve_namespaces
from fingerprint.service_layer.settings import check_acceptance_threshold, validate_config

logger = logging.getLogger(__name__)


def with_threshold(run: ProfileRun, threshold: float) -> ProfileRun:
    """The same run read at another acceptance threshold; checked by the collection rule, (0, 1]."""
    checked = check_acceptance_threshold(threshold)
    return run.model_copy(update={"settings": run.settings.model_copy(update={"acceptance_threshold": checked})})


def with_ontology(run: ProfileRun, path: str | Path | None) -> ProfileRun:
    """The run with the ontology file's labels and descriptions over each graph's own, term by term (DEC-20).

    No path: the same run. An unreadable file is a usage error naming it."""
    if path is None:
        return run
    try:
        ontology = select_annotations(load_ontology(path))
    except OntologyFileError as error:
        raise UsageError(str(error)) from error
    graphs = [
        g.model_copy(update={"term_annotations": merge_annotations(ontology, g.term_annotations or [])})
        for g in run.graphs or []
    ]
    return run.model_copy(update={"graphs": graphs})


def validate_options(options: GeneratorOptions | None) -> None:
    """The generator options a caller gives, checked before any query or write (usage errors)."""
    if options is None:
        return
    if options.shapes_namespace:
        try:
            to_iriref(options.shapes_namespace)
        except IriRefError as error:
            raise UsageError(f"--shapes-namespace {error.iri!r} cannot be written as an IRI") from error
    if options.module_size is not None and options.module_size < 1:
        raise UsageError("--module-size must be at least 1")
    for name in ("min_instances", "max_classes"):
        if getattr(options, name) is not None and getattr(options, name) < 1:
            raise UsageError(f"--{name.replace('_', '-')} must be at least 1")


def warn_unknown_filters(run: ProfileRun, options: GeneratorOptions | None) -> None:
    """A filter name matching no namespace is warned about once per run and ignored (DEC-5)."""
    if options is None:
        return
    table = PrefixTable(run.namespaces)
    _, unknown = excluded_namespaces(options, table)
    for name in dict.fromkeys(unknown):  # dict-ok: ordered de-duplication
        option = "--include-namespace" if name in (options.include_namespaces or []) else "--exclude-namespace"
        logger.warning("%s %s: no such namespace; ignored", option, name)


def make_generator(
    name: str | RepresentationFormat,
    analytics: ProfileAnalytics,
    renderer: TemplateRenderer,
    template_location: str | Path | None = None,
    options: GeneratorOptions | None = None,
) -> Generator:
    """The generator of one format."""
    try:
        return GENERATORS[name](analytics, renderer, template_location, options)  # type: ignore[index]
    except IriRefError as error:  # e.g. an unwritable --shapes-namespace
        raise UsageError(f"{error.iri!r} cannot be written as an IRI") from error


def generate_representations(
    run: ProfileRun,
    output_location: str | Path,
    formats: Sequence[str],
    *,
    threshold: float | None = None,
    template_location: str | Path | None = None,
    options: GeneratorOptions | None = None,
    renderer: TemplateRenderer | None = None,
    user_prefixes: Sequence[NamespacePrefix] | None = None,
    check_filters: bool = True,
) -> list[Path]:
    """Write each format in the order given; a failing format writes none of its files and stops the rest.

    A run without a namespace table, or with a user prefix list to apply, is resolved first, never fetching."""
    validate_config()
    validate_options(options)
    unknown = [f for f in formats if f not in GENERATORS]
    if unknown:
        raise UsageError(f"unknown formats: {', '.join(unknown)} (known: {', '.join(GENERATORS)})")
    if run.namespaces is None or user_prefixes:
        run = resolve_namespaces(run, user_prefixes or ())
    if check_filters:
        warn_unknown_filters(run, options)
    if threshold is not None:
        run = with_threshold(run, threshold)
    analytics = analyse(with_ontology(run, options.ontology if options else None))
    renderer = renderer or JinjaTemplateRenderer()
    paths: list[Path] = []
    for name in formats:
        try:
            generator = make_generator(name, analytics, renderer, template_location, options)
            paths += generator.write(output_location)
        except TemplatePackageError as error:
            raise UsageError(str(error)) from error
    return paths


def generate_from_profile_file(
    profile_location: str | Path, output_location: str | Path, formats: Sequence[str], **kwargs: Any
) -> list[Path]:
    """The generator commands' service: the saved profile, never the endpoint (DEC-1)."""
    validate_config()
    if not Path(output_location).is_dir():
        raise UsageError(f"{output_location} is not an existing folder")
    try:
        run = load_profile(profile_location)
    except ProfileFileError as error:
        raise UsageError(str(error)) from error
    return generate_representations(run, output_location, formats, **kwargs)
