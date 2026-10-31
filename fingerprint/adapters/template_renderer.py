"""Render eds4jinja2 template packages, check the texts and write them (profile-representations P-1).

Rendering goes through eds4jinja2's own document building (2.1, domain-object-model P-6):
`render_documents` for texts in memory, `make_documents` to check every text before any file is written.
"""

from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

import rdflib
from eds4jinja2.services.report_builder import ReportBuilder
from pydantic import BaseModel

from fingerprint.adapters.exceptions import GeneratedOutputError, TemplatePackageError
from fingerprint.domain.iri import curie, to_iriref, turtle_number, turtle_string, turtle_term
from fingerprint.domain.prefixes import PrefixTable
from fingerprint.domain.views import OutputCheck, RenderedDocument


def _parse_turtle(text: str) -> None:
    rdflib.Graph().parse(data=text, format="turtle")


CHECKS: dict[OutputCheck, Callable[[str], None]] = {OutputCheck.turtle: _parse_turtle}


def filters(prefixes: PrefixTable) -> dict[str, Callable[..., Any]]:  # dict-ok: eds4jinja2 filters
    """The IRI and literal filters every template gets, bound to the profile's prefix table, so custom templates
    escape and shorten like the packaged ones."""
    return {  # dict-ok: eds4jinja2 filters
        "turtle_iri": to_iriref,
        "turtle_term": lambda iri: turtle_term(iri, prefixes)[0],
        "turtle_string": turtle_string,
        "turtle_number": turtle_number,
        "curie": lambda iri: curie(iri, prefixes),
    }


class JinjaTemplateRenderer:
    """Renders eds4jinja2 template packages; the prefix table comes with each call (the profile's own)."""

    def render(
        self,
        package: str | Path,
        outputs: Sequence[tuple[str, BaseModel | None]],
        *,
        conf: Mapping[str, Any] | None = None,  # dict-ok: eds4jinja2 configuration
        autoescape: bool | None = None,
        prefixes: PrefixTable | None = None,
    ) -> list[RenderedDocument]:
        """Each output's text, in memory: the package's template rendered with `view` = the output's view."""
        texts = self._builder(package, conf, prefixes).render_documents(_variables(outputs), autoescape=autoescape)
        return [RenderedDocument(file_name=name, text=text) for name, text in texts.items()]

    def make(
        self,
        package: str | Path,
        outputs: Sequence[tuple[str, BaseModel | None]],
        *,
        folder: str | Path,
        conf: Mapping[str, Any] | None = None,  # dict-ok: eds4jinja2 configuration
        check: OutputCheck | None = None,
        autoescape: bool | None = None,
        prefixes: PrefixTable | None = None,
    ) -> list[Path]:
        """Render, check every text, then write them all; a text that fails its check leaves the folder untouched."""

        def checked(name: str, text: str) -> None:
            if check:
                try:
                    CHECKS[check](text)
                except Exception as error:  # the parser's own error types vary; the message is kept
                    raise GeneratedOutputError(f"{name} is not valid {check.value}: {error}") from error

        builder = self._builder(package, conf, prefixes, folder)
        return builder.make_documents(_variables(outputs), check=checked, autoescape=autoescape)

    def _builder(
        self,
        package: str | Path,
        conf: Mapping[str, Any] | None,  # dict-ok: eds4jinja2 configuration
        prefixes: PrefixTable | None,
        folder: str | Path | None = None,
    ) -> ReportBuilder:
        """The package's builder, `conf` deep-merged over its `config.json` `conf`, writing into `folder`."""
        try:
            additional = {"conf": dict(conf)} if conf else None  # dict-ok: eds4jinja2 configuration
            return ReportBuilder(
                target_path=package,
                output_path=None if folder is None else str(folder),
                additional_config=additional,
                external_filters=filters(prefixes or PrefixTable(None)),
            )
        except FileNotFoundError as error:
            raise TemplatePackageError(f"{package} is not a template package: {error}") from error
        except KeyError as error:
            raise TemplatePackageError(f"{package}/config.json must have `template` and `conf`: {error}") from error


def _variables(outputs: Sequence[tuple[str, BaseModel | None]]) -> dict[str, dict[str, Any]]:  # dict-ok: eds4jinja2 outputs
    """eds4jinja2's output name → template variables; every template receives its view as `view`."""
    return {name: {"view": view} for name, view in outputs}  # dict-ok: eds4jinja2 outputs
