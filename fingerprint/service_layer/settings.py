"""Collection settings: CLI > environment > `selected_graphs` parameter > config file > default (P-6).

Each source is read as a `SettingsOverride`; per setting, the first source that sets it wins
(domain-object-model P-7).
"""

import urllib.parse
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from fingerprint import FingerprintConfig
from fingerprint import config as fingerprint_config
from fingerprint.adapters import config_resolver
from fingerprint.adapters.config_resolver import MappingConfigResolver
from fingerprint.adapters.exceptions import ConfigError, ConfigFileError
from fingerprint.adapters.prefixes import load_packaged_prefixes, load_prefixes
from fingerprint.adapters.sparql import redact
from fingerprint.domain.profile import NamespacePrefix, PrefixSource, Settings, SettingsOverride
from fingerprint.service_layer.exceptions import UsageError

NAMES = tuple(Settings.model_fields)


def load_config_file(path: str | Path) -> dict[str, Any]:  # dict-ok: documented 2.0 API, JSON being parsed
    """The `--config FILE`: a JSON object with the setting names as keys."""
    try:
        return config_resolver.load_config_file(path)
    except ConfigFileError as error:
        raise UsageError(str(error)) from error


def describe(error: ValidationError) -> str:
    """A validation error in one line per field, without Pydantic's links."""
    return "; ".join(f"{'.'.join(map(str, e['loc'])) or 'value'}: {e['msg']}" for e in error.errors())


def check_acceptance_threshold(threshold: float) -> float:
    """The model allows [0, 1]; a cardinality label needs some support, so 0 is refused (P-6)."""
    if not 0 < threshold <= 1:
        raise UsageError("acceptance_threshold must be in (0, 1]")
    return threshold


def validate_endpoint(url: str) -> None:
    """Only HTTP(S) endpoints: urllib would also open file:, ftp: and data: URLs."""
    if urllib.parse.urlsplit(url).scheme.lower() not in ("http", "https"):
        raise UsageError(f"the endpoint must be an http or https URL, not {redact(url)!r}")


def validate_config() -> None:
    """Every `RDF_FINGERPRINTER_*` value read once, before any query or write; a bad one is a usage error."""
    try:
        fingerprint_config.validate()
        load_packaged_prefixes(fingerprint_config.packaged_prefixes_file)
    except ConfigError as error:
        raise UsageError(str(error)) from error
    load_user_prefixes()  # RDF_FINGERPRINTER_PREFIXES_FILE: a bad file is a usage error before any query


def load_user_prefixes(path: str | Path | None = None) -> list[NamespacePrefix]:
    """The user's prefix file: `--prefixes` when given, else `RDF_FINGERPRINTER_PREFIXES_FILE`, else none.

    Loaded before any query, so a bad file is a usage error naming the option or variable (namespace-prefixes)."""
    try:
        if path:
            return load_prefixes(Path(path), PrefixSource.user, "--prefixes")
        env_path = fingerprint_config.prefixes_file
        if env_path:
            return load_prefixes(env_path, PrefixSource.user, "RDF_FINGERPRINTER_PREFIXES_FILE")
    except ConfigError as error:
        raise UsageError(str(error)) from error
    return []


def _override(source: Mapping[str, Any] | SettingsOverride | None) -> SettingsOverride:  # dict-ok: resolve_settings API
    if isinstance(source, SettingsOverride):
        return source
    try:
        return SettingsOverride.model_validate(source) if source else SettingsOverride()
    except ValidationError as error:
        raise UsageError(describe(error)) from error


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
        raise UsageError(describe(error)) from error
    check_acceptance_threshold(settings.acceptance_threshold)
    return settings
