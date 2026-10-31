"""Render eds4jinja2 template packages, check the texts and write them (profile-representations P-1).

Rendering goes through `ReportBuilder.template_env`, not `make_document()`, so one package can yield
several files and every text is checked before any file is written.
"""

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

import rdflib
from eds4jinja2.services.report_builder import ReportBuilder

from fingerprint.adapters.exceptions import GeneratedOutputError, TemplatePackageError


def _parse_turtle(text: str) -> None:
    rdflib.Graph().parse(data=text, format="turtle")


CHECKS: dict[str, Callable[[str], None]] = {"turtle": _parse_turtle}


class JinjaTemplateRenderer:
    def __init__(self, filters: Mapping[str, Callable[..., Any]] | None = None):
        self.filters = dict(filters or {})

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
