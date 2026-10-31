"""Collection settings: CLI > environment > `selected_graphs` parameter > config file > default (P-6)."""

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from fingerprint.adapters import settings_sources
from fingerprint.adapters.exceptions import ConfigFileError
from fingerprint.domain.generated.profile import Settings
from fingerprint.service_layer.exceptions import UsageError  # noqa: F401 — also importable from here (2.0)

ENV_PREFIX = "RDF_FINGERPRINTER_"
NAMES = tuple(Settings.model_fields)
_TRUE = {"1", "true", "yes", "on"}
_FALSE = {"0", "false", "no", "off"}


def _from_env(name: str, raw: str) -> Any:
    annotation = str(Settings.model_fields[name].annotation)
    if name == "selected_graphs":
        return [graph.strip() for graph in raw.split(",")]
    if "bool" in annotation:
        value = raw.strip().lower()
        if value in _TRUE | _FALSE:
            return value in _TRUE
        raise UsageError(f"{ENV_PREFIX}{name.upper()} must be one of 1/true/yes/on or 0/false/no/off, not {raw!r}")
    return raw


def load_config_file(path: str | Path) -> dict[str, Any]:
    """The `--config FILE`: a JSON object with the setting names as keys."""
    try:
        return settings_sources.load_config_file(path)
    except ConfigFileError as error:
        raise UsageError(str(error)) from error


def resolve_settings(
    cli: Mapping[str, Any] | None = None,
    env: Mapping[str, str] | None = None,
    selected_graphs: list[str] | None = None,
    config: Mapping[str, Any] | None = None,
) -> Settings:
    """Merge the sources per setting; unknown config keys and invalid values are usage errors."""
    env = settings_sources.environment() if env is None else env
    unknown = set(config or {}) - set(NAMES)
    if unknown:
        raise UsageError(f"unknown collection settings: {', '.join(sorted(unknown))}")
    values: dict[str, Any] = dict(config or {})
    if selected_graphs:
        values["selected_graphs"] = list(selected_graphs)
    for name in NAMES:
        raw = env.get(ENV_PREFIX + name.upper())
        if raw is not None:
            values[name] = _from_env(name, raw)
    values.update({k: v for k, v in (cli or {}).items() if v is not None})
    try:
        settings = Settings.model_validate(values)
    except ValidationError as error:
        raise UsageError(str(error)) from error
    if settings.acceptance_threshold <= 0:  # the model allows [0, 1]; a label needs some support (P-6)
        raise UsageError("acceptance_threshold must be in (0, 1]")
    return settings
