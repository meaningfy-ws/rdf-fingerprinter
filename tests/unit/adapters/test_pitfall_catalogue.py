"""The pitfall catalogue: packaged and user checks, validation (pitfall-scans › Pitfall check contract)."""

import pytest

from fingerprint.adapters.pitfall_catalogue import load_catalogue, packaged_checks
from fingerprint.domain.pitfalls import PitfallCheckError

HEADER = "# id: {id}\n# title: T\n# importance: minor\n# scope: data\n# source: me\n"
SELECT = "SELECT ?entity ?property ?value WHERE { ?entity ?property ?value }\n"


def write(folder, name, text):
    folder.mkdir(exist_ok=True)
    (folder / name).write_text(text)
    return folder


def test_heuristic_checks_are_minor():
    """design D-1a: heuristic checks are always minor (the catalogue size is a Gherkin scenario)."""
    assert all(c.importance == "minor" for c in packaged_checks() if c.heuristic)


def test_a_user_check_with_a_new_id_is_added(tmp_path):
    folder = write(tmp_path / "u", "mine.rq", HEADER.format(id="mine") + SELECT)
    assert len(load_catalogue(folder)) == 30


def test_skip_and_an_empty_catalogue(tmp_path):
    ids = [c.check_id for c in packaged_checks()]
    assert "p13_missing_inverse" not in [c.check_id for c in load_catalogue(skip=["p13_missing_inverse"])]
    assert load_catalogue(skip=ids) == []
    with pytest.raises(PitfallCheckError, match="unknown check"):
        load_catalogue(skip=["nope"])


def test_a_duplicate_user_id_and_a_missing_folder(tmp_path):
    folder = write(tmp_path / "u", "a.rq", HEADER.format(id="dup") + SELECT)
    write(folder, "b.rq", HEADER.format(id="dup") + SELECT)
    with pytest.raises(PitfallCheckError, match="another user check"):
        load_catalogue(folder)
    with pytest.raises(PitfallCheckError, match="not a directory"):
        load_catalogue(tmp_path / "missing")


def test_select_distinct_is_accepted(tmp_path):
    folder = write(tmp_path / "u", "d.rq", HEADER.format(id="d") + SELECT.replace("SELECT", "SELECT DISTINCT"))
    assert "d" in [c.check_id for c in load_catalogue(folder)]
