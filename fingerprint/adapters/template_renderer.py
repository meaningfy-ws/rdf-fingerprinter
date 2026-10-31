"""Render eds4jinja2 template packages, check the texts and write them (profile-representations P-1).

Rendering goes through `ReportBuilder.template_env`, not `make_document()`, so one package can yield
several files and every text is checked before any file is written.
"""

import json
import re
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

import jinja2
import rdflib
from eds4jinja2.services.report_builder import ReportBuilder
from pydantic import BaseModel

from fingerprint import config
from fingerprint.adapters.exceptions import ConfigError, GeneratedOutputError, TemplatePackageError
from fingerprint.domain.exceptions import IriRefError
from fingerprint.domain.iri import curie, to_iriref, turtle_number, turtle_string, turtle_term
from fingerprint.domain.views import OutputCheck, RenderedDocument

_PREFIX_KEY = re.compile(r"[A-Za-z][A-Za-z0-9_.-]*:")


def load_prefixes(path: Path | None = None) -> dict[str, str]:  # dict-ok: prefix table
    """`{"skos": "http://www.w3.org/2004/02/skos/core#", …}` from a `{"skos:": …}` file; default: `config.prefixes_file`.

    The names reach PlantUML and Turtle text, so each must be a plain prefix and each namespace a writable IRI."""
    location = path or config.prefixes_file
    try:
        table = json.loads(location.read_text())
    except (OSError, ValueError) as error:
        raise ConfigError(f"RDF_FINGERPRINTER_PREFIXES_FILE: cannot read {location}: {error}") from error
    if not isinstance(table, dict):
        raise ConfigError(f"RDF_FINGERPRINTER_PREFIXES_FILE: {location} must hold a JSON object")
    for prefix, namespace in table.items():
        if not (_PREFIX_KEY.fullmatch(prefix) and isinstance(namespace, str)):
            raise ConfigError(f"RDF_FINGERPRINTER_PREFIXES_FILE: {location}: {prefix!r} is not a prefix (`name:`) with an IRI")
        try:
            to_iriref(namespace)
        except IriRefError as error:
            raise ConfigError(f"RDF_FINGERPRINTER_PREFIXES_FILE: {location}: {namespace!r} is not a writable IRI") from error
    return {prefix.rstrip(":"): namespace for prefix, namespace in table.items()}  # dict-ok: prefix table


def _parse_turtle(text: str) -> None:
    rdflib.Graph().parse(data=text, format="turtle")


CHECKS: dict[OutputCheck, Callable[[str], None]] = {OutputCheck.turtle: _parse_turtle}


class JinjaTemplateRenderer:
    """Every template gets the IRI and literal filters, so custom templates can escape like the packaged ones."""

    def __init__(self, prefixes: Mapping[str, str] | None = None):  # dict-ok: prefix table
        self.prefixes = dict(load_prefixes() if prefixes is None else prefixes)  # dict-ok: prefix table
        self.filters: dict[str, Callable[..., Any]] = {  # dict-ok: eds4jinja2 filters
            "turtle_iri": to_iriref,
            "turtle_term": lambda iri: turtle_term(iri, self.prefixes)[0],
            "turtle_string": turtle_string,
            "turtle_number": turtle_number,
            "curie": lambda iri: curie(iri, self.prefixes),
        }

    def render(
        self,
        package: str | Path,
        outputs: Sequence[tuple[str, BaseModel | None]],
        *,
        conf: Mapping[str, Any] | None = None,  # dict-ok: eds4jinja2 configuration
        autoescape: bool | None = None,
    ) -> list[RenderedDocument]:
        """Each output's text, in memory: the package's template rendered with `view` = the output's view."""
        template = self._template(package, conf, autoescape)
        return [RenderedDocument(file_name=name, text=template.render(view=view)) for name, view in outputs]

    def make(
        self,
        package: str | Path,
        outputs: Sequence[tuple[str, BaseModel | None]],
        *,
        folder: str | Path,
        conf: Mapping[str, Any] | None = None,  # dict-ok: eds4jinja2 configuration
        check: OutputCheck | None = None,
        autoescape: bool | None = None,
    ) -> list[Path]:
        """Render, check every text, then write them all; a text that fails its check leaves the folder untouched."""
        documents = self.render(package, outputs, conf=conf, autoescape=autoescape)
        for document in documents:
            if check:
                try:
                    CHECKS[check](document.text)
                except Exception as error:  # the parser's own error types vary; the message is kept
                    raise GeneratedOutputError(f"{document.file_name} is not valid {check.value}: {error}") from error
        location = Path(folder)
        location.mkdir(parents=True, exist_ok=True)
        paths = []
        for document in documents:
            path = location / document.file_name
            path.write_text(document.text, encoding="utf-8")
            paths.append(path)
        return paths

    def _template(
        self,
        package: str | Path,
        conf: Mapping[str, Any] | None,
        autoescape: bool | None,  # dict-ok: eds4jinja2 configuration
    ) -> jinja2.Template:
        """The package's template, `conf` deep-merged over its `config.json` `conf`.

        shortcut: renders through `ReportBuilder.template_env`; with eds4jinja2 2.1 this becomes
        `render_documents` / `make_documents` (domain-object-model task 6.1)."""
        try:
            additional = {"conf": dict(conf or {})}  # dict-ok: eds4jinja2 configuration
            builder = ReportBuilder(target_path=package, additional_config=additional, external_filters=self.filters)
        except FileNotFoundError as error:
            raise TemplatePackageError(f"{package} is not a template package: {error}") from error
        except KeyError as error:
            raise TemplatePackageError(f"{package}/config.json must have `template` and `conf`: {error}") from error
        if autoescape is not None:
            # templates compile on first load, so this applies to every template of the package
            builder.template_env.autoescape = autoescape
        return builder.template_env.get_template(builder.template)
