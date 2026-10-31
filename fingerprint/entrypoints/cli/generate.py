"""The generator commands `fingerprint-gen-shacl`, `-puml`, `-doc`: a saved profile in, one representation out.

Shaped after LinkML's `gen-*` commands and their shared arguments (P-3, P-4); they only parse and map
the outcome to an exit code (0 written, 2 usage error, 4 unexpected error, P-13).
"""

import logging
import sys
from collections.abc import Callable
from typing import Any

import click

from fingerprint.entrypoints.cli import EXIT_UNEXPECTED, configure_logging
from fingerprint.service_layer.exceptions import UsageError
from fingerprint.service_layer.generators import DOC, PUML, SHACL
from fingerprint.service_layer.representations import generate_from_profile_file

logger = logging.getLogger(__name__)


def shared_arguments(command: Callable[..., Any]) -> Callable[..., Any]:
    """The arguments every generator command takes (LinkML's `shared_arguments`)."""
    for decorator in reversed(
        [
            click.argument("profile", type=click.Path(dir_okay=False)),
            click.option("-o", "--output", default="./output", type=str, help="output folder (must exist)"),
            click.option("--threshold", type=float, help="acceptance threshold, (0, 1]; default: the profile's"),
            click.option("--template", type=click.Path(file_okay=False), help="a template package of your own"),
        ]
    ):
        command = decorator(command)
    return command


def generate_one(name: str, profile: str, output: str, threshold: float | None, template: str | None, **options: Any) -> None:
    configure_logging()
    try:
        paths = generate_from_profile_file(
            profile,
            output,
            [name],
            threshold=threshold,
            template_location=template,
            options={name: {k: v for k, v in options.items() if v is not None}},
        )
    except UsageError as error:
        raise click.UsageError(str(error)) from error
    except Exception as error:
        logger.exception("could not generate %s from %s", name, profile)
        click.echo(f"error: could not generate {name}: {error}", err=True)
        sys.exit(EXIT_UNEXPECTED)
    for path in paths:
        logger.info("wrote %s", path)


@click.command()
@shared_arguments
@click.option("--shapes-namespace", help="namespace of the node shape IRIs (default urn:fingerprint:shape:)")
def gen_shacl(profile: str, output: str, threshold: float | None, template: str | None, shapes_namespace: str | None):
    """SHACL shapes, one Turtle file per graph, from a saved profile.json."""
    generate_one(SHACL, profile, output, threshold, template, shapes_namespace=shapes_namespace)


@click.command()
@shared_arguments
def gen_puml(profile: str, output: str, threshold: float | None, template: str | None):
    """A PlantUML class diagram, one source file per graph, from a saved profile.json."""
    generate_one(PUML, profile, output, threshold, template)


@click.command()
@shared_arguments
def gen_doc(profile: str, output: str, threshold: float | None, template: str | None):
    """The application-profile document (HTML) from a saved profile.json."""
    generate_one(DOC, profile, output, threshold, template)
