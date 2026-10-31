#!/usr/bin/python3

# main.py
# Date:  18/10/2020
# Author: Eugeniu Costetchi
# Email: costezki.eugen@gmail.com

"""The `fingerprint` command: settings → collect → analyse → render, with exit codes 0/1/2/3/4 (P-7)."""

import logging
import pathlib
import sys

import click

from fingerprint.adapters.sparql import EndpointUnreachable, SparqlWrapperClient
from fingerprint.domain.analytics import analyse
from fingerprint.service_layer.collection import collect
from fingerprint.service_layer.report import render_report
from fingerprint.service_layer.settings import UsageError, load_config_file, resolve_settings

logger = logging.getLogger(__name__)

EXIT_FAILURES, EXIT_UNREACHABLE, EXIT_UNEXPECTED = 1, 3, 4


def _choice(*values: str) -> click.Choice:
    return click.Choice(values, case_sensitive=False)


@click.command()
@click.option("-e", "--sparql_endpoint_url", required=True, type=str, help="SPARQL endpoint")
@click.option("-o", "--output", default="./output", required=False, type=str, help="output folder (must exist)")
@click.option("--depth", type=_choice("graphs", "classes", "properties", "values", "rich_values", "links"))
@click.option("--precision", "precision_policy", type=_choice("auto", "exact", "first_n"), help="precision policy")
@click.option("--first-n", "first_n", type=int, help="instances read per class in first-N mode")
@click.option("--top-k", "top_k", type=int, help="top values kept per class and property")
@click.option("--threshold", "acceptance_threshold", type=float, help="cardinality label acceptance threshold, (0, 1]")
@click.option("--object-types", "object_type_scope", type=_choice("same_graph", "any_graph"))
@click.option("--completeness/--no-completeness", "completeness_check", default=None, help="property presence check")
@click.option("--graph-stats/--no-graph-stats", "graph_statistics", default=None, help="graph totals (full scans)")
@click.option("--timeout", "timeout_seconds", type=int, help="per-query timeout in seconds")
@click.option("--concurrency", type=int, help="classes profiled at once")
@click.option("--graph", "graphs", multiple=True, help="graph to profile (repeatable; empty string = default graph)")
@click.option("--config", "config_file", type=click.Path(dir_okay=False), help="JSON file with collection settings")
def fingerprint_endpoint(sparql_endpoint_url: str, output: str, graphs: tuple[str, ...], config_file: str | None, **options):
    """
    Generate a fingerprint report on a given SPARQL endpoint.
    Exit status: 0 profiled, 1 report written with failures, 2 usage error, 3 endpoint unreachable, 4 unexpected error.
    """
    # the application, not the library, configures logging (DEC-9)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)5s %(name)s: %(message)s")
    output_location = pathlib.Path(output)
    if not output_location.is_dir():
        raise click.BadParameter(f"{output} is not an existing folder", param_hint="--output")
    try:
        settings = resolve_settings(
            cli={**options, "selected_graphs": list(graphs) or None},
            config=load_config_file(config_file) if config_file else None,
        )
    except UsageError as error:
        raise click.UsageError(str(error)) from error

    try:
        sparql = SparqlWrapperClient(sparql_endpoint_url, settings.timeout_seconds or 60)
        run = collect(sparql_endpoint_url, settings, sparql)
        report = render_report(analyse(run), output_location)
    except EndpointUnreachable as error:
        logger.error("%s", error)
        sys.exit(EXIT_UNREACHABLE)
    except Exception:
        logger.exception("unexpected error while fingerprinting %s", sparql_endpoint_url)
        sys.exit(EXIT_UNEXPECTED)

    if run.failures:
        logger.warning("report written to %s with %d failures", report, len(run.failures))
        sys.exit(EXIT_FAILURES)
    logger.info("fingerprint report written to %s", report)


if __name__ == "__main__":
    fingerprint_endpoint()
