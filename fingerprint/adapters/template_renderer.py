"""Render eds4jinja2 template packages, check the texts and write them (profile-representations P-1).

Rendering goes through `ReportBuilder.template_env`, not `make_document()`, so one package can yield
several files and every text is checked before any file is written.
"""

import json
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

import rdflib
from eds4jinja2.services.report_builder import ReportBuilder

from fingerprint.adapters.exceptions import GeneratedOutputError, TemplatePackageError
from fingerprint.domain.iri import curie, to_iriref, turtle_number, turtle_string, turtle_term
from fingerprint_report_templates import packaged

# The one prefix list of the package, shared with the report (P-7).
PREFIXES_FILE = packaged("fingerprint_report") / "templates" / "prefixes.json"


def load_prefixes(path: Path = PREFIXES_FILE) -> dict[str, str]:
    """`{"skos": "http://www.w3.org/2004/02/skos/core#", …}` from the report's `{"skos:": …}` file."""
    return {prefix.rstrip(":"): namespace for prefix, namespace in json.loads(path.read_text()).items()}


def _parse_turtle(text: str) -> None:
    rdflib.Graph().parse(data=text, format="turtle")


CHECKS: dict[str, Callable[[str], None]] = {"turtle": _parse_turtle}


class JinjaTemplateRenderer:
    """Every template gets the IRI and literal filters, so custom templates can escape like the packaged ones."""

    def __init__(self, prefixes: Mapping[str, str] | None = None):
        self.prefixes = dict(load_prefixes() if prefixes is None else prefixes)
        self.filters: dict[str, Callable[..., Any]] = {
            "turtle_iri": to_iriref,
            "turtle_term": lambda iri: turtle_term(iri, self.prefixes)[0],
            "turtle_string": turtle_string,
            "turtle_number": turtle_number,
            "curie": lambda iri: curie(iri, self.prefixes),
        }

    def render(
        self,
        package: str | Path,
        *,
        view: Any = None,
        config: Mapping[str, Any] | None = None,
        autoescape: bool | None = None,
    ) -> str:
        """The text of the package's template; `config` is deep-merged over its `config.json`."""
        try:
            builder = ReportBuilder(target_path=package, additional_config=dict(config or {}), external_filters=self.filters)
        except FileNotFoundError as error:
            raise TemplatePackageError(f"{package} is not a template package: {error}") from error
        except KeyError as error:
            raise TemplatePackageError(f"{package}/config.json must have `template` and `conf`: {error}") from error
        if autoescape is not None:
            # templates compile on first load, so this applies to every template of the package
            builder.template_env.autoescape = autoescape
        return builder.template_env.get_template(builder.template).render(view=view)

    def write(self, folder: str | Path, texts: Mapping[str, str], check: str | None = None) -> list[Path]:
        """Check every text, then write them all; a text that fails its check leaves the folder untouched."""
        for name, text in texts.items():
            if check:
                try:
                    CHECKS[check](text)
                except Exception as error:  # the parser's own error types vary; the message is kept
                    raise GeneratedOutputError(f"{name} is not valid {check}: {error}") from error
        location = Path(folder)
        location.mkdir(parents=True, exist_ok=True)
        paths = []
        for name, text in texts.items():
            path = location / name
            path.write_text(text, encoding="utf-8")
            paths.append(path)
        return paths
