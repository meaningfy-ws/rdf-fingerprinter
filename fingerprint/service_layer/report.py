"""Render the analytics through eds4jinja2; the templates read `conf.profile` and issue no queries (DEC-6, P-7)."""

import json
import logging
from importlib.resources import files
from pathlib import Path
from typing import Any

from eds4jinja2.services.report_builder import ReportBuilder

import fingerprint_report_templates
from fingerprint.domain.generated.profile import ProfileAnalytics

logger = logging.getLogger(__name__)

# Templates ship inside the package as plain files (Poetry package data), so a real path exists.
DEFAULT_TEMPLATE_LOCATION = Path(str(files(fingerprint_report_templates) / "fingerprint_report"))


def generate_report_builder_config(
    sparql_endpoint_url: str, selected_graphs: list[str], external_template_location: str | Path | None
) -> dict:
    """
        Read the default config json from the fingerprint_report and set the endpoint and the graph uri if necessary
    :param sparql_endpoint_url: URL to fingerprint
    :param selected_graphs: a list of valid graph URIs or empty string for the default graph
    :param external_template_location: location of the custom template
    :return: the new configuration
    """
    template_location = external_template_location or DEFAULT_TEMPLATE_LOCATION
    config_dict = json.loads((Path(template_location) / "config.json").read_bytes())
    config_dict["conf"]["default_endpoint"] = sparql_endpoint_url
    config_dict["conf"]["selected_graphs"] = selected_graphs
    return config_dict


def render_report(
    analytics: ProfileAnalytics,
    output_location: str | Path,
    template_location: str | Path | None = None,
    extra_conf: dict[str, Any] | None = None,
) -> Path:
    """Write the report for `analytics`; `extra_conf` (constants for custom templates) is merged into `conf` as in 1.x."""
    location = Path(output_location)
    profiled = [graph.graph or "" for graph in analytics.graphs or []]
    config = generate_report_builder_config(analytics.endpoint or "", profiled, template_location)
    config["conf"].update(extra_conf or {})
    config["conf"]["default_endpoint"] = analytics.endpoint
    config["conf"]["selected_graphs"] = profiled
    config["conf"]["profile"] = analytics
    builder = ReportBuilder(
        target_path=template_location or DEFAULT_TEMPLATE_LOCATION, additional_config=config, output_path=location
    )
    if template_location is None:
        # Endpoint data is untrusted and eds4jinja2 disables autoescape; templates compile on first load,
        # so this applies to every template of the packaged report. Custom templates keep 1.x behaviour.
        builder.template_env.autoescape = True
    builder.make_document()
    return location / config["template"]
