"""The pitfall catalogue: packaged checks, user checks, validation (pitfall-scans › Pitfall check contract, › The packaged catalogue)."""

import pytest

from fingerprint.adapters.pitfall_catalogue import load_catalogue, packaged_checks
from fingerprint.domain.pitfalls import PitfallCheckError

HEADER = "# id: {id}\n# title: T\n# importance: minor\n# scope: data\n# source: me\n"
SELECT = "SELECT ?entity ?property ?value WHERE { ?entity ?property ?value }\n"


def write(folder, name, text):
    folder.mkdir(exist_ok=True)
    (folder / name).write_text(text)
    return folder


def test_the_packaged_catalogue():
    checks = packaged_checks()
    ids = [c.check_id for c in checks]
    assert len(checks) == 29 and len(set(ids)) == 29
    assert all(c.source.startswith("OOPS! P") for c in checks if not c.check_id.startswith("x_"))
    assert all(c.importance == "minor" for c in checks if c.heuristic)


def test_a_user_check_is_added_and_one_with_a_packaged_id_replaces_it(tmp_path):
    folder = write(tmp_path / "u", "mine.rq", HEADER.format(id="mine") + SELECT)
    write(folder, "p22.rq", HEADER.format(id="p22_class_naming") + SELECT)
    checks = {c.check_id: c for c in load_catalogue(folder)}
    assert len(checks) == 30 and checks["p22_class_naming"].origin.endswith("p22.rq")


def test_skip_and_an_empty_catalogue(tmp_path):
    ids = [c.check_id for c in packaged_checks()]
    assert "p13_missing_inverse" not in [c.check_id for c in load_catalogue(skip=["p13_missing_inverse"])]
    assert load_catalogue(skip=ids) == []
    with pytest.raises(PitfallCheckError, match="unknown check"):
        load_catalogue(skip=["nope"])


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("# title: T\n# importance: minor\n# scope: data\n# source: me\n" + SELECT, "missing"),
        (HEADER.replace("minor", "severe").format(id="a") + SELECT, "importance"),
        (HEADER.format(id="a") + "INSERT DATA { <urn:a> <urn:b> <urn:c> }\n", "SPARQL|SELECT"),
        (HEADER.format(id="a") + "DELETE WHERE { ?s ?p ?o }\n", "SPARQL|SELECT"),
        (HEADER.format(id="a") + "SELECT ?s ?p ?o WHERE { ?s ?p ?o }\n", "select \\?entity"),
        (HEADER.format(id="a") + "SELECT ?entity ?property ?value WHERE { ?entity\n", "SPARQL"),
        (HEADER.format(id="a") + "# severity: high\n" + SELECT, "unknown header key"),
        (HEADER.format(id="a") + "SELECT ?entity ?property ?value FROM <http://ex.org/g> WHERE { ?entity ?property ?value }\n", "FROM"),
    ],
    ids=["no-id", "bad-importance", "insert", "delete", "wrong-variables", "unparsable", "unknown-key", "from-clause"],
)
def test_invalid_user_checks_are_refused_naming_the_file(tmp_path, text, message):
    folder = write(tmp_path / "u", "bad.rq", text)
    with pytest.raises(PitfallCheckError, match=message) as raised:
        load_catalogue(folder)
    assert "bad.rq" in str(raised.value)


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
