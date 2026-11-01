#!/usr/bin/python3

# __init__.py
# Date:  15/08/2019
# Author: Eugeniu Costetchi
# Email: costezki.eugen@gmail.com

"""The package version and its configuration: every operational value, read from an `RDF_FINGERPRINTER_*`
variable with a default (domain-object-model DEC-6, P-7). Values resolve on access, never at import."""

from importlib.metadata import version
from pathlib import Path
from typing import Any, get_args

from pydantic import ValidationError

from fingerprint.adapters.config_resolver import ConfigResolverABC, EnvConfigResolver, env_property
from fingerprint.adapters.exceptions import ConfigError
from fingerprint.domain.iri import to_iriref
from fingerprint.domain.profile import SettingsOverride
from fingerprint_report_templates import packaged

__docformat__ = "restructuredtext en"

# The version lives in pyproject.toml only (DEC-2).
__version__ = version("rdf-fingerprinter")

ENV_PREFIX = "RDF_FINGERPRINTER_"
_TRUE = {"1", "true", "yes", "on"}
_FALSE = {"0", "false", "no", "off"}


def _texts(value: str | None) -> tuple[str, ...]:
    return tuple(part.strip() for part in (value or "").split(",") if part.strip())


class FingerprintConfig:
    def __init__(self, resolver: ConfigResolverABC):
        self.resolver = resolver

    @env_property(f"{ENV_PREFIX}PROFILE_FILE", "profile.json")
    def profile_file(self, value: str | None) -> str:
        """File name of the saved profile run, inside the output folder."""
        if not value or "/" in value:
            raise ValueError("a file name is required")
        return value

    @env_property(f"{ENV_PREFIX}RETRY_BACKOFF_SECONDS", "1,4")
    def retry_backoff_seconds(self, value: str | None) -> tuple[float, ...]:
        """Seconds to wait before each retry of a transient failure; one retry per number."""
        seconds = tuple(float(part) for part in _texts(value))
        if any(s < 0 for s in seconds):
            raise ValueError("seconds cannot be negative")
        return seconds

    @env_property(f"{ENV_PREFIX}TIMEOUT_MARKERS", "timeout,time limit,timed out,estimated execution time")
    def timeout_markers(self, value: str | None) -> tuple[str, ...]:
        """Texts that make an HTTP 500 answer a timeout (lower case)."""
        return tuple(marker.lower() for marker in _texts(value))

    @env_property(f"{ENV_PREFIX}ERROR_EXCERPT_LENGTH", "200")
    def error_excerpt_length(self, value: str | None) -> int:
        """How much of an endpoint's error body a failure message keeps."""
        length = int(value or "")
        if length < 1:
            raise ValueError("must be at least 1")
        return length

    @env_property(f"{ENV_PREFIX}SHAPES_NAMESPACE")
    def shapes_namespace(self, value: str | None) -> str | None:
        """One namespace for every SHACL shape IRI; unset: each class's own `<namespace>/shape/`."""
        if value:
            to_iriref(value)  # an IRI Turtle can hold, else IriRefError (a ValueError)
        return value or None

    @env_property(f"{ENV_PREFIX}DEFAULT_GRAPH_LABEL", "default graph")
    def default_graph_label(self, value: str | None) -> str:
        """How the representations name the default graph."""
        return value or ""

    @env_property(f"{ENV_PREFIX}PREFIXES_FILE")
    def prefixes_file(self, value: str | None) -> Path | None:
        """The user's prefix file (`{"skos:": "http://…#"}`), over the packaged prefixes; unset: none."""
        return Path(value) if value else None

    @env_property(f"{ENV_PREFIX}PREFIX_LOOKUP", "true")
    def prefix_lookup(self, value: str | None) -> bool:
        """Whether the `fingerprint` command reads prefix.cc's prefix list for unnamed namespaces."""
        return _flag(f"{ENV_PREFIX}PREFIX_LOOKUP", value or "")

    @property
    def packaged_prefixes_file(self) -> Path:
        """The prefixes packaged with the fingerprinter (source `packaged`)."""
        return packaged("fingerprint_report") / "templates" / "prefixes.json"

    def settings_override(self) -> SettingsOverride:
        """The collection settings set by `RDF_FINGERPRINTER_<SETTING>` variables."""
        raw = ((name, self.resolver.config_resolve(ENV_PREFIX + name.upper())) for name in SettingsOverride.model_fields)
        try:
            return SettingsOverride(**{name: _setting(name, value) for name, value in raw if value is not None})
        except ValidationError as error:
            names = sorted({ENV_PREFIX + str(e["loc"][0]).upper() for e in error.errors()})
            raise ConfigError(f"{', '.join(names)}: {error.errors()[0]['msg']}") from error

    def validate(self) -> None:
        """Read every value once; the first that does not coerce raises ConfigError naming its variable."""
        for name, member in vars(type(self)).items():
            if isinstance(member, property):
                getattr(self, name)
        self.settings_override()


def _setting(name: str, raw: str) -> Any:
    if name in ("selected_graphs", "schema_graphs"):
        return [graph.strip() for graph in raw.split(",")]
    if bool in get_args(SettingsOverride.model_fields[name].annotation):
        return _flag(f"{ENV_PREFIX}{name.upper()}", raw)
    return raw


def _flag(variable: str, raw: str) -> bool:
    value = raw.strip().lower()
    if value not in _TRUE | _FALSE:
        raise ConfigError(f"{variable} must be one of 1/true/yes/on or 0/false/no/off, not {raw!r}")
    return value in _TRUE


config = FingerprintConfig(EnvConfigResolver())
