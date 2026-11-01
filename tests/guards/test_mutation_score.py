"""The mutation-score ratchet and its wiring (lean-test-suite P-7, TC-6)."""

import json
import re
from pathlib import Path

import pytest
import yaml

from tests.guards.mutation_score import EXIT_DROPPED, EXIT_ERROR, EXIT_OK, Stats, main, score

ROOT = Path(__file__).parents[2]


def _run(tmp_path: Path, stored: str | None, **counts: int) -> tuple[int, Path]:
    stats = {"killed": 0, "timeout": 0, "survived": 0, "no_tests": 0, "check_was_interrupted_by_user": 0}
    stats.update(counts)  # dict-ok: the JSON mutmut writes
    stats_path = tmp_path / "stats.json"
    stats_path.write_text(json.dumps(stats))
    stored_path = tmp_path / "mutation_score.txt"
    if stored is not None:
        stored_path.write_text(stored)
    return main(stats_path, stored_path), stored_path


def test_the_score_counts_a_mutant_no_test_covers_as_not_caught():
    assert score(Stats(killed=80, timeout=4, survived=10, no_tests=6)) == 0.84


def test_the_mutation_score_drops(tmp_path, capsys):
    code, stored = _run(tmp_path, "0.850\n", killed=84, survived=16)
    assert code == EXIT_DROPPED
    assert "mutmut results" in capsys.readouterr().out
    assert stored.read_text() == "0.850\n"


def test_an_equal_score_leaves_the_file_unchanged(tmp_path):
    code, stored = _run(tmp_path, "0.850", killed=85, survived=15)
    assert code == EXIT_OK
    assert stored.read_text() == "0.850"


def test_a_higher_score_rewrites_the_file_with_three_decimals(tmp_path):
    code, stored = _run(tmp_path, "0.500\n", killed=2, survived=1)
    assert code == EXIT_OK
    assert stored.read_text() == "0.667\n"


def test_an_interrupted_run_is_an_error(tmp_path, capsys):
    code, _ = _run(tmp_path, "0.500\n", killed=9, check_was_interrupted_by_user=1)
    assert code == EXIT_ERROR
    assert "interrupted" in capsys.readouterr().err


def test_zero_mutants_is_an_error_not_a_division_by_zero(tmp_path, capsys):
    code, _ = _run(tmp_path, "0.500\n")
    assert code == EXIT_ERROR
    assert "no mutants" in capsys.readouterr().err


def test_a_missing_stored_file_is_an_error_naming_it(tmp_path, capsys):
    code, stored = _run(tmp_path, None, killed=1)
    assert code == EXIT_ERROR
    assert str(stored) in capsys.readouterr().err
    assert not stored.exists()


@pytest.mark.parametrize("text", ["", "high\n", "1.5\n"])
def test_a_malformed_stored_score_is_an_error(tmp_path, capsys, text):
    code, _ = _run(tmp_path, text, killed=1)
    assert code == EXIT_ERROR
    assert "mutation_score.txt" in capsys.readouterr().err


def test_check_mutation_runs_mutmut_then_the_ratchet_and_is_not_part_of_check_all():
    makefile = (ROOT / "Makefile").read_text()
    recipe = re.search(r"^check-mutation:[^\n]*\n((?:\t[^\n]*\n)*)", makefile, re.MULTILINE)
    assert recipe, "Makefile has no target check-mutation"
    text = recipe.group(1)
    assert text.index("mutmut run") < text.index("export-cicd-stats") < text.index("mutation_score.py")
    assert "mutmut results" in text
    check_all = re.search(r"^check-all:([^\n#]*)", makefile, re.MULTILINE)
    assert check_all
    assert "check-mutation" not in check_all.group(1)


def test_the_mutation_workflow_runs_weekly_and_on_demand():
    workflow = yaml.safe_load((ROOT / ".github" / "workflows" / "mutation.yml").read_text())
    triggers = workflow.get("on") or workflow[True]  # YAML reads a bare `on` as True
    assert "workflow_dispatch" in triggers
    assert triggers["schedule"][0]["cron"]
    job = next(iter(workflow["jobs"].values()))
    assert job["timeout-minutes"] >= 120
    assert any(step.get("run") == "make check-mutation" for step in job["steps"])
