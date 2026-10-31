"""The profile store: profile.json written and read back (profile-representations P-5, P-16)."""

import json
from pathlib import Path

import pytest

from fingerprint import config
from fingerprint.adapters.exceptions import ProfileFileError
from fingerprint.adapters.profile_file import load_profile, save_profile
from fingerprint.domain.profile import ProfileRun

SAMPLE = Path(__file__).parents[1] / "test_data" / "profiles" / "sample-profile.json"


def test_round_trip(tmp_path):
    run = ProfileRun.model_validate_json(SAMPLE.read_text())
    path = save_profile(run, tmp_path)
    assert path == tmp_path / config.profile_file and load_profile(path) == run


@pytest.mark.parametrize(
    "content, reason",
    [(None, "does not exist"), ("{not json", "not a profile"), ('{"graphs": "x"}', "not a profile")],
)
def test_unusable_file_names_the_file(tmp_path, content, reason):
    path = tmp_path / "p.json"
    if content is not None:
        path.write_text(content)
    with pytest.raises(ProfileFileError, match=reason) as raised:
        load_profile(path)
    assert str(path) in str(raised.value)


def test_a_newer_file_names_its_tool_version(tmp_path):
    raw = json.loads(SAMPLE.read_text()) | {"tool_version": "2.9.0", "added_in_2_9": 1}
    path = tmp_path / "p.json"
    path.write_text(json.dumps(raw))
    with pytest.raises(ProfileFileError, match="2.9.0"):
        load_profile(path)


def test_saved_profile_matches_the_published_schema(tmp_path):
    jsonschema = pytest.importorskip("jsonschema")
    schema = Path(__file__).parents[2] / "fingerprint" / "domain" / "profile_run.schema.json"
    path = save_profile(ProfileRun.model_validate_json(SAMPLE.read_text()), tmp_path)
    jsonschema.validate(json.loads(path.read_text()), json.loads(schema.read_text()))
