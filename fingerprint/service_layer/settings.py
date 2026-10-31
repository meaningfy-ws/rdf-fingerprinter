"""Collection settings: CLI > environment > `selected_graphs` parameter > config file > default (P-6).

Each source is read as a `SettingsOverride`; per setting, the first source that sets it wins
(domain-object-model P-7).
"""

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from fingerprint import FingerprintConfig
from fingerprint import config as fingerprint_config
from fingerprint.adapters import config_resolver
from fingerprint.adapters.config_resolver import MappingConfigResolver
from fingerprint.adapters.exceptions import ConfigError, ConfigFileError
from fingerprint.domain.profile import Settings, SettingsOverride
from fingerprint.service_layer.exceptions import UsageError

NAMES = tuple(Settings.model_fields)


def load_config_file(path: str | Path) -> dict[str, Any]:  # dict-ok: documented 2.0 API, JSON being parsed
    """The `--config FILE`: a JSON object with the setting names as keys."""
    try:
        return config_resolver.load_config_file(path)
    except ConfigFileError as error:
        raise UsageError(str(error)) from error


def validate_config() -> None:
    """Every `RDF_FINGERPRINTER_*` value read once, before any query or write; a bad one is a usage error."""
    try:
        fingerprint_config.validate()
    except ConfigError as error:
        raise UsageError(str(error)) from error


def _override(source: Mapping[str, Any] | SettingsOverride | None) -> SettingsOverride:  # dict-ok: resolve_settings API
    if isinstance(source, SettingsOverride):
        return source
    try:
        return SettingsOverride.model_validate(source) if source else SettingsOverride()
    except ValidationError as error:
        raise UsageError(str(error)) from error


def _environment(env: Mapping[str, str] | None) -> SettingsOverride:  # dict-ok: resolve_settings API
    source = fingerprint_config if env is None else FingerprintConfig(MappingConfigResolver(env))
    try:
        return source.settings_override()
    except ConfigError as error:
        raise UsageError(str(error)) from error


def _is_set(value: Any) -> bool:
    return value is not None and value != []


def resolve_settings(
    cli: Mapping[str, Any] | SettingsOverride | None = None,  # dict-ok: resolve_settings API
    env: Mapping[str, str] | None = None,  # dict-ok: resolve_settings API
    selected_graphs: list[str] | None = None,
    config: Mapping[str, Any] | None = None,  # dict-ok: resolve_settings API
) -> Settings:
    """Merge the sources per setting; unknown config keys and invalid values are usage errors."""
    unknown = set(config or ()) - set(NAMES)
    if unknown:
        raise UsageError(f"unknown collection settings: {', '.join(sorted(unknown))}")
    sources = (
        _override(cli),
        _environment(env),
        SettingsOverride(selected_graphs=selected_graphs or None),
        _override(config),
    )
    chosen = ((name, next((v for s in sources if _is_set(v := getattr(s, name))), None)) for name in NAMES)
    try:
        settings = Settings(**{name: value for name, value in chosen if value is not None})
    except ValidationError as error:
        raise UsageError(str(error)) from error
    if settings.acceptance_threshold <= 0:  # the model allows [0, 1]; a label needs some support (P-6)
        raise UsageError("acceptance_threshold must be in (0, 1]")
    return settings
