#!/usr/bin/python3

# handlers.py
# Date:  15/10/2020
# Author: Eugeniu Costetchi
# Email: costezki.eugen@gmail.com

"""The public library function: collect → analyse → render, with the 1.x signature (P-7)."""

import logging
from pathlib import Path
from typing import Any

from fingerprint.adapters.sparql import SparqlWrapperClient
from fingerprint.domain.analytics import analyse
from fingerprint.domain.generated.profile import ProfileRun, Settings
from fingerprint.service_layer.collection import collect
from fingerprint.service_layer.report import (  # noqa: F401 — kept importable from here (1.x)
    DEFAULT_TEMPLATE_LOCATION,
    generate_report_builder_config,
    render_report,
)
from fingerprint.service_layer.settings import resolve_settings

logger = logging.getLogger(__name__)


def fingerprint_report(
    sparql_endpoint_url: str,
    output_location: Path,
    settings: Settings,
    template_location: str | Path | None = None,
    extra_conf: dict[str, Any] | None = None,
) -> tuple[Path, ProfileRun]:
    """Collect, analyse and render; returns the report path and the raw run (its failures decide the exit code)."""
    run = collect(sparql_endpoint_url, settings, SparqlWrapperClient(sparql_endpoint_url, settings.timeout_seconds))
    report = render_report(analyse(run), output_location, template_location, extra_conf)
    if run.failures:
        logger.warning("report written to %s with %d failures", report, len(run.failures))
    else:
        logger.info("fingerprint report written to %s", report)
    return report, run


def generate_endpoint_fingerprint_report(
    sparql_endpoint_url: str,
    output_location: str | Path,
    selected_graphs: list[str] | None = None,
    external_template_location: str | Path | None = None,
    additional_config: dict | None = None,
) -> Path:
    """
        Calculate the fingerprint of a given endpoint and write the report in the output location.
        Without selected graphs, the default graph and every named graph are profiled.
    :param sparql_endpoint_url: URL to fingerprint
    :param output_location: location of where to generate the report
    :param selected_graphs: a list of valid graph URIs or empty string for the default graph
    :param external_template_location: location of custom template (if None -> use the default template)
    :param additional_config: constants for the template; its "collection" key holds collection settings
    :return: path to the main report document
    """
    location = Path(output_location)
    if not location.exists() or not location.is_dir():
        raise NotADirectoryError("The output location must be a folder")

    extra_conf = dict(additional_config or {})
    settings = resolve_settings(selected_graphs=selected_graphs, config=extra_conf.pop("collection", None))
    return fingerprint_report(sparql_endpoint_url, location, settings, external_template_location, extra_conf)[0]
