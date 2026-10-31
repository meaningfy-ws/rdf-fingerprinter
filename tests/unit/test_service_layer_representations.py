"""The representations service: load, re-analyse at a threshold, run generators in order (P-6, UC-W2)."""

from pathlib import Path

import pytest

from fingerprint.adapters.exceptions import GeneratedOutputError
from fingerprint.adapters.profile_file import save_profile
from fingerprint.domain.profile import ProfileRun
from fingerprint.domain.views import GeneratorOptions
from fingerprint.service_layer import representations
from fingerprint.service_layer.exceptions import UsageError
from fingerprint.service_layer.representations import (
    generate_from_profile_file,
    generate_representations,
    with_threshold,
)

SAMPLE = Path(__file__).parents[1] / "test_data" / "profiles" / "sample-profile.json"


@pytest.fixture
def run():
    return ProfileRun.model_validate_json(SAMPLE.read_text())


class Recording:
    """A stand-in generator: records the analytics it was given, writes one file, or fails."""

    seen: list = []

    def __init__(self, analytics, renderer, template_location=None, options=None):
        self.analytics, self.options = analytics, options

    def write(self, folder):
        Recording.seen.append((self.analytics.settings.acceptance_threshold, self.options))
        path = Path(folder) / f"ok-{len(Recording.seen)}"
        path.write_text("x")
        return [path]


class Failing(Recording):
    def write(self, folder):
        raise GeneratedOutputError("bad.ttl is not valid turtle")


@pytest.fixture
def generators(monkeypatch):
    Recording.seen = []
    monkeypatch.setattr(representations, "GENERATORS", {"a": Recording, "b": Failing, "c": Recording})


def test_with_threshold_changes_only_the_threshold(run):
    changed = with_threshold(run, 0.5)
    assert changed.settings.acceptance_threshold == 0.5 and changed.graphs == run.graphs
    assert run.settings.acceptance_threshold == 0.95


@pytest.mark.parametrize("threshold", [0, 1.5, -1])
def test_threshold_outside_the_range_is_a_usage_error(run, threshold):
    with pytest.raises(UsageError):
        with_threshold(run, threshold)


def test_generators_get_the_analytics_at_the_threshold(run, tmp_path, generators):
    options = GeneratorOptions(shapes_namespace="urn:x:")
    generate_representations(run, tmp_path, ["a"], threshold=0.6, options=options)
    assert Recording.seen == [(0.6, options)]


def test_formats_run_in_order_and_a_failure_keeps_earlier_ones(run, tmp_path, generators):
    with pytest.raises(GeneratedOutputError):
        generate_representations(run, tmp_path, ["a", "b", "c"])
    assert [p.name for p in tmp_path.iterdir()] == ["ok-1"]


def test_an_unknown_format_is_a_usage_error(run, tmp_path, generators):
    with pytest.raises(UsageError, match="void"):
        generate_representations(run, tmp_path, ["void"])


def test_from_a_profile_file(run, tmp_path, generators):
    path = save_profile(run, tmp_path)
    out = tmp_path / "out"
    out.mkdir()
    assert [p.name for p in generate_from_profile_file(path, out, ["a"])] == ["ok-1"]


def test_an_unusable_profile_file_is_a_usage_error(tmp_path, generators):
    with pytest.raises(UsageError, match="missing.json"):
        generate_from_profile_file(tmp_path / "missing.json", tmp_path, ["a"])


def test_a_missing_output_folder_is_a_usage_error(run, tmp_path, generators):
    path = save_profile(run, tmp_path)
    with pytest.raises(UsageError, match="not an existing folder"):
        generate_from_profile_file(path, tmp_path / "nowhere", ["a"])
