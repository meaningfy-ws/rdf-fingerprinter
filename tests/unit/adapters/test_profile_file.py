"""The profile store: profile.json written and read back (profile-representations P-5, P-16)."""

import json
from pathlib import Path

import pytest

from fingerprint import config
from fingerprint.adapters.exceptions import ProfileFileError
from fingerprint.adapters.profile_file import load_profile, save_profile
from fingerprint.domain.profile import NamespacePrefix, PrefixSource
from tests.sample_data import SAMPLE_PROFILE as SAMPLE


def test_round_trip(tmp_path, sample_run):
    run = sample_run
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


def test_saved_profile_matches_the_published_schema(tmp_path, sample_run):
    jsonschema = pytest.importorskip("jsonschema")
    schema = Path(__file__).parents[3] / "fingerprint" / "domain" / "profile_run.schema.json"
    path = save_profile(sample_run, tmp_path)
    jsonschema.validate(json.loads(path.read_text()), json.loads(schema.read_text()))


def test_namespace_table_round_trips(tmp_path, sample_run):
    """namespace-prefixes: the namespace table is saved with the profile."""
    run = sample_run
    table = [NamespacePrefix(prefix="ex", namespace="http://ex.org/", source=PrefixSource.generated)]
    loaded = load_profile(save_profile(run.model_copy(update={"namespaces": table}), tmp_path))
    assert loaded.namespaces == table


def test_a_profile_without_a_namespace_table_still_loads():
    """namespace-prefixes: an old profile (saved before 3.0) loads; its table is resolved later."""
    assert "namespaces" not in json.loads(SAMPLE.read_text())
    assert load_profile(SAMPLE).namespaces is None


# --- term annotations (llm-schema-tools P-6, backward compatibility) ---

from fingerprint.domain.profile import LangText, TermAnnotation  # noqa: E402
from tests.sample_data import SCANNED_PROFILE  # noqa: E402


def test_term_annotations_round_trip(tmp_path, sample_run):
    annotation = TermAnnotation(term="http://ex.org/Person", labels=[LangText(text="Person", language="en")], descriptions=[])
    graph = sample_run.graphs[0].model_copy(update={"term_annotations": [annotation]})
    run = sample_run.model_copy(update={"graphs": [graph, *sample_run.graphs[1:]]})
    assert load_profile(save_profile(run, tmp_path)) == run


@pytest.mark.parametrize("path", [SAMPLE, SCANNED_PROFILE])
def test_a_profile_saved_before_term_annotations_loads_without_them(path):
    run = load_profile(path)
    assert all(graph.term_annotations is None for graph in run.graphs)
