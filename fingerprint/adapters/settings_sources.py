"""Where collection settings come from outside the code: the process environment and a config file."""

import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from fingerprint.adapters.exceptions import ConfigFileError


def environment() -> Mapping[str, str]:
    return os.environ


def load_config_file(path: str | Path) -> dict[str, Any]:
    """The `--config FILE`: a JSON object with the setting names as keys."""
    try:
        config = json.loads(Path(path).read_text())
    except (OSError, ValueError) as error:
        raise ConfigFileError(f"cannot read config file {path}: {error}") from error
    if not isinstance(config, dict):
        raise ConfigFileError(f"config file {path} must hold a JSON object")
    return config
