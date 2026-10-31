"""Render the analytics through the template renderer; the templates read `conf.profile` and issue no queries (DEC-6, P-7)."""

import json
import logging
from pathlib import Path
from typing import Any

from fingerprint.adapters.template_renderer import JinjaTemplateRenderer
from fingerprint.domain.profile import ProfileAnalytics
from fingerprint.service_layer.generators.generator import TemplateRenderer
from fingerprint_report_templates import packaged

logger = logging.getLogger(__name__)

DEFAULT_TEMPLATE_LOCATION = packaged("fingerprint_report")


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
    *,
    renderer: TemplateRenderer | None = None,
) -> Path:
    """Write the report for `analytics`; `extra_conf` (constants for custom templates) is merged into `conf` as in 1.x."""
    location = Path(output_location)
    profiled = [graph.graph or "" for graph in analytics.graphs or []]
    config = generate_report_builder_config(analytics.endpoint or "", profiled, template_location)
    config["conf"].update(extra_conf or {})  # after the 1.x keys, so callers may override them, as in 1.x
    config["conf"]["profile"] = analytics
    # Endpoint data is untrusted and eds4jinja2 disables autoescape: escape the packaged report;
    # custom templates keep 1.x behaviour.
    autoescape = True if template_location is None else None
    renderer = renderer or JinjaTemplateRenderer()
    text = renderer.render(template_location or DEFAULT_TEMPLATE_LOCATION, config=config, autoescape=autoescape)
    return renderer.write(location, {config["template"]: text})[0]
