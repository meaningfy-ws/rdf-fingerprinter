"""Where configuration values come from (the Meaningfy settings pattern, domain-object-model P-7).

A config class declares each value with `env_property`; the property asks the instance's resolver for
the raw text and its body coerces it. Swap the resolver to read another source (tests use defaults).
"""

import json
import os
from abc import ABC, abstractmethod
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from fingerprint.adapters.exceptions import ConfigError, ConfigFileError


class ConfigResolverABC(ABC):
    @abstractmethod
    def config_resolve(self, name: str, default_value: str | None = None) -> str | None: ...


class EnvConfigResolver(ConfigResolverABC):
    """The process environment."""

    def config_resolve(self, name: str, default_value: str | None = None) -> str | None:
        return os.environ.get(name, default_value)


class DefaultConfigResolver(ConfigResolverABC):
    """Every value at its default; for tests."""

    def config_resolve(self, name: str, default_value: str | None = None) -> str | None:
        return default_value


class MappingConfigResolver(ConfigResolverABC):
    """A given name → text mapping, e.g. an environment passed explicitly."""

    def __init__(self, values: Mapping[str, str]):  # dict-ok: an environment given as a mapping
        self.values = values

    def config_resolve(self, name: str, default_value: str | None = None) -> str | None:
        return self.values.get(name, default_value)


def env_property(name: str, default_value: str | None = None) -> Callable[[Callable[[Any, str | None], Any]], property]:
    """A property resolved through `self.resolver` on every access; a value the body rejects is a ConfigError."""

    def decorator(coerce: Callable[[Any, str | None], Any]) -> property:
        def resolve(self: Any) -> Any:
            value = self.resolver.config_resolve(name, default_value)
            try:
                return coerce(self, value)
            except (TypeError, ValueError) as error:
                raise ConfigError(f"{name}={value!r} is not valid: {error}") from error

        resolve.__doc__ = coerce.__doc__
        return property(resolve)

    return decorator


def load_config_file(path: str | Path) -> dict[str, Any]:  # dict-ok: JSON being parsed into SettingsOverride
    """The `--config FILE`: a JSON object with the setting names as keys."""
    try:
        config = json.loads(Path(path).read_text())
    except (OSError, ValueError) as error:
        raise ConfigFileError(f"cannot read config file {path}: {error}") from error
    if not isinstance(config, dict):
        raise ConfigFileError(f"config file {path} must hold a JSON object")
    return config
