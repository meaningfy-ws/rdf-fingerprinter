"""The generator commands `fingerprint-gen-shacl`, `-puml`, `-doc`, `-pitfalls`, `-pattern`, `-shex`: a profile in, one output.

Shaped after LinkML's `gen-*` commands and their shared arguments (P-3, P-4); they only parse and map
the outcome to an exit code (0 written, 2 usage error, 4 unexpected error, P-13).
"""

import logging
import sys
from collections.abc import Callable
from typing import Any

import click

from fingerprint.domain.views import GeneratorOptions, RepresentationFormat
from fingerprint.entrypoints.cli import EXIT_UNEXPECTED, configure_logging
from fingerprint.service_layer.exceptions import UsageError
from fingerprint.service_layer.generators import DOC, PATTERN, PITFALLS, PUML, SHACL, SHEX
from fingerprint.service_layer.representations import generate_from_profile_file
from fingerprint.service_layer.settings import load_user_prefixes

logger = logging.getLogger(__name__)


def shared_arguments(command: Callable[..., Any]) -> Callable[..., Any]:
    """The arguments every generator command takes (LinkML's `shared_arguments`)."""
    for decorator in reversed(
        [
            click.argument("profile", type=click.Path(dir_okay=False)),
            click.option("-o", "--output", default="./output", type=str, help="output folder (must exist)"),
            click.option("--threshold", type=float, help="acceptance threshold, (0, 1]; default: the profile's"),
            click.option("--template", type=click.Path(file_okay=False), help="a template package of your own"),
            click.option(
                "--prefixes", "prefixes_file", type=click.Path(dir_okay=False), help="your prefix file, over the saved table"
            ),
            click.option(
                "--exclude-namespace",
                multiple=True,
                help=(
                    "leave out every term of the matching namespaces: "
                    "a prefix, a prefix glob ('rel*') or an IRI stem (repeatable)"
                ),
            ),
            click.option(
                "--include-namespace",
                multiple=True,
                help=(
                    "keep the matching namespaces, over --exclude-namespace "
                    "and the default hiding of rdf, rdfs, owl, sh classes (repeatable)"
                ),
            ),
        ]
    ):
        command = decorator(command)
    return command


def generate_one(
    name: RepresentationFormat,
    profile: str,
    output: str,
    threshold: float | None,
    template: str | None,
    shared: dict[str, Any],  # dict-ok: click's parsed options
    **options: Any,
) -> None:
    configure_logging()
    try:
        generator_options = GeneratorOptions(
            exclude_namespaces=list(shared["exclude_namespace"]),
            include_namespaces=list(shared["include_namespace"]),
            **options,
        )
        paths = generate_from_profile_file(
            profile,
            output,
            [name],
            threshold=threshold,
            template_location=template,
            options=generator_options,
            user_prefixes=load_user_prefixes(shared["prefixes_file"]),
        )
    except UsageError as error:
        raise click.UsageError(str(error)) from error
    except Exception as error:
        logger.exception("could not generate %s from %s", name.value, profile)
        click.echo(f"error: could not generate {name.value}: {error}", err=True)
        sys.exit(EXIT_UNEXPECTED)
    for path in paths:
        logger.info("wrote %s", path)


@click.command()
@shared_arguments
@click.option("--shapes-namespace", help="one namespace for every shape IRI (default: each class's <ns>/shape/)")
def gen_shacl(
    profile: str, output: str, threshold: float | None, template: str | None, shapes_namespace: str | None, **shared
):
    """SHACL shapes, one Turtle file per graph with a shown class, from a saved profile.json."""
    generate_one(SHACL, profile, output, threshold, template, shared, shapes_namespace=shapes_namespace)


@click.command()
@shared_arguments
@click.option("--module-size", type=click.IntRange(min=1), help="most classes per module (default 15)")
def gen_puml(profile: str, output: str, threshold: float | None, template: str | None, module_size: int | None, **shared):
    """PlantUML diagrams per graph, an overview and one file per module, from a saved profile.json."""
    generate_one(PUML, profile, output, threshold, template, shared, module_size=module_size)


@click.command()
@shared_arguments
def gen_doc(profile: str, output: str, threshold: float | None, template: str | None, **shared):
    """The report page main.html from a saved profile.json."""
    generate_one(DOC, profile, output, threshold, template, shared)


@click.command()
@shared_arguments
def gen_pitfalls(profile: str, output: str, threshold: float | None, template: str | None, **shared):
    """The pitfall findings as ROBOT-style TSV, one file per scanned graph, from a saved profile.json."""
    generate_one(PITFALLS, profile, output, threshold, template, shared)


def size_and_label_options(command: Callable[..., Any]) -> Callable[..., Any]:
    """The options of the two LLM outputs, the pattern schema and the ShExC."""
    for decorator in reversed(
        [
            click.option(
                "--ontology", type=click.Path(dir_okay=False), help="an ontology file whose labels and descriptions win"
            ),
            click.option("--min-instances", type=click.IntRange(min=1), help="leave out classes with fewer instances"),
            click.option("--max-classes", type=click.IntRange(min=1), help="show only this many classes, the largest first"),
        ]
    ):
        command = decorator(command)
    return command


@click.command()
@shared_arguments
@size_and_label_options
def gen_pattern(
    profile: str,
    output: str,
    threshold: float | None,
    template: str | None,
    ontology: str | None,
    min_instances: int | None,
    max_classes: int | None,
    **shared,
):
    """The pattern schema, one text file per graph with a block, from a saved profile.json."""
    generate_one(
        PATTERN, profile, output, threshold, template, shared,
        ontology=ontology, min_instances=min_instances, max_classes=max_classes,
    )  # fmt: skip


@click.command()
@shared_arguments
@size_and_label_options
def gen_shex(
    profile: str,
    output: str,
    threshold: float | None,
    template: str | None,
    ontology: str | None,
    min_instances: int | None,
    max_classes: int | None,
    **shared,
):
    """The enriched ShExC, one .shex file per graph with a block, from a saved profile.json."""
    generate_one(
        SHEX, profile, output, threshold, template, shared,
        ontology=ontology, min_instances=min_instances, max_classes=max_classes,
    )  # fmt: skip
