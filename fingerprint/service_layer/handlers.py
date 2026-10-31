#!/usr/bin/python3

# handlers.py
# Date:  15/10/2020
# Author: Eugeniu Costetchi
# Email: costezki.eugen@gmail.com

"""The library entry: collect → resolve prefixes → save → render the report page and the chosen formats (3.0).

One render path: the report is the document generator's page (readable-representations DEC-3, DEC-9).
"""

import logging
from collections.abc import Sequence
from pathlib import Path

from fingerprint.adapters.prefixes import PrefixListSource
from fingerprint.adapters.profile_file import save_profile
from fingerprint.adapters.sparql import SparqlHttpClient, SparqlPort
from fingerprint.adapters.template_renderer import JinjaTemplateRenderer
from fingerprint.domain.profile import NamespacePrefix, ProfileRun, Settings
from fingerprint.domain.views import GeneratorOptions
from fingerprint.service_layer.collection import collect
from fingerprint.service_layer.generators import DOC
from fingerprint.service_layer.generators.generator import TemplateRenderer
from fingerprint.service_layer.prefixes import resolve_namespaces
from fingerprint.service_layer.representations import generate_representations, validate_options
from fingerprint.service_layer.settings import validate_config, validate_endpoint

logger = logging.getLogger(__name__)


def fingerprint_report(
    sparql_endpoint_url: str,
    output_location: str | Path,
    settings: Settings,
    *,
    formats: Sequence[str] = (),
    options: GeneratorOptions | None = None,
    template: str | Path | None = None,
    user_prefixes: Sequence[NamespacePrefix] | None = None,
    prefix_list: PrefixListSource | None = None,
    sparql: SparqlPort | None = None,
    renderer: TemplateRenderer | None = None,
) -> tuple[Path, ProfileRun]:
    """Collect, resolve the namespace table, save the profile, then write `main.html` and the chosen `formats`.

    Returns the report path and the run (its failures decide the exit code). Every usage error is raised before
    any query; the profile is saved before rendering, so a rendering failure loses nothing collected.
    `prefix_list` None means no prefix.cc lookup; `template` is a template package over the document view model.
    """
    location = Path(output_location)
    if not location.is_dir():
        raise NotADirectoryError(f"{output_location} is not an existing folder")
    validate_config()
    validate_endpoint(sparql_endpoint_url)
    validate_options(options)
    sparql = sparql or SparqlHttpClient(sparql_endpoint_url, settings.timeout_seconds)
    run = collect(sparql_endpoint_url, settings, sparql)
    run = resolve_namespaces(run, user_prefixes or (), prefix_list=prefix_list)
    save_profile(run, location)
    renderer = renderer or JinjaTemplateRenderer()
    if DOC in formats:
        logger.info("main.html is the document; no second page is written")
    (report,) = generate_representations(run, location, [DOC], template_location=template, options=options, renderer=renderer)
    others = [f for f in formats if f != DOC]
    if others:
        generate_representations(run, location, others, options=options, renderer=renderer, check_filters=False)
    if run.failures:
        logger.warning("report written to %s with %d failures", report, len(run.failures))
    else:
        logger.info("fingerprint report written to %s", report)
    return report, run
