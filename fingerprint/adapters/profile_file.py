"""The profile store: the raw profile run saved as `profile.json` and read back (profile-representations P-5)."""

import json
from pathlib import Path

from pydantic import ValidationError

from fingerprint.adapters.exceptions import ProfileFileError
from fingerprint.domain.generated.profile import ProfileRun

PROFILE_FILE = "profile.json"


def save_profile(run: ProfileRun, folder: str | Path) -> Path:
    path = Path(folder) / PROFILE_FILE
    path.write_text(run.model_dump_json(indent=2, exclude_none=True) + "\n", encoding="utf-8")
    return path


def load_profile(path: str | Path) -> ProfileRun:
    """The run saved in `path`; a missing, unreadable or non-matching file raises ProfileFileError naming it."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as error:
        raise ProfileFileError(f"profile file {path} does not exist or cannot be read: {error}") from error
    try:
        return ProfileRun.model_validate_json(text)
    except ValidationError as error:
        raise ProfileFileError(f"{path} is not a profile{_written_by(text)}: {error.errors()[0]['msg']}") from error


def _written_by(text: str) -> str:
    """Name the version that wrote a file, so an older reader can say a newer one is needed (AD-7)."""
    try:
        version = json.loads(text).get("tool_version")
    except (ValueError, AttributeError):
        return ""
    return f" readable by this version (written by rdf-fingerprinter {version})" if version else ""
