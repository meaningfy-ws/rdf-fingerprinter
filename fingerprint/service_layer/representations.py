"""Representations of a profile run: re-analyse at a threshold and run the chosen generators (UC-W2, P-6)."""

from collections.abc import Sequence
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from fingerprint.adapters.exceptions import ProfileFileError, TemplatePackageError
from fingerprint.adapters.profile_file import load_profile
from fingerprint.adapters.template_renderer import JinjaTemplateRenderer
from fingerprint.domain.analytics import analyse
from fingerprint.domain.exceptions import IriRefError
from fingerprint.domain.profile import ProfileAnalytics, ProfileRun, SettingsOverride
from fingerprint.domain.views import GeneratorOptions, RepresentationFormat
from fingerprint.service_layer.exceptions import UsageError
from fingerprint.service_layer.generators import DOC, GENERATORS, PUML
from fingerprint.service_layer.generators.generator import Generator, TemplateRenderer
from fingerprint.service_layer.settings import resolve_settings, validate_config


def with_threshold(run: ProfileRun, threshold: float) -> ProfileRun:
    """The same run read at another acceptance threshold; checked by the collection rule, (0, 1]."""
    try:
        override = SettingsOverride(acceptance_threshold=threshold)
    except ValidationError as error:
        raise UsageError(str(error)) from error
    checked = resolve_settings(cli=override, env={}).acceptance_threshold  # dict-ok: no environment
    return run.model_copy(update={"settings": run.settings.model_copy(update={"acceptance_threshold": checked})})


def make_generator(
    name: str | RepresentationFormat,
    analytics: ProfileAnalytics,
    renderer: TemplateRenderer,
    template_location: str | Path | None = None,
    options: GeneratorOptions | None = None,
) -> Generator:
    """The generator of one format; the document receives the diagrams it embeds (composition, not import)."""
    try:
        if name == DOC:
            diagrams = GENERATORS[PUML](analytics, renderer).render_graphs()
            return GENERATORS[DOC](analytics, renderer, template_location, options, diagrams=diagrams)  # type: ignore[call-arg]
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
) -> list[Path]:
    """Write each format in the order given; a failing format writes none of its files and stops the rest."""
    validate_config()
    unknown = [f for f in formats if f not in GENERATORS]
    if unknown:
        raise UsageError(f"unknown formats: {', '.join(unknown)} (known: {', '.join(GENERATORS)})")
    if threshold is not None:
        run = with_threshold(run, threshold)
    analytics = analyse(run)
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
