"""The per-layer coverage gate of `make test` (lean-test-suite P-7, developer-tooling "Coverage and mutation gate").

The report's arguments are read from the Makefile `test` recipe, so editing the recipe changes what is proven.
"""

import re
import subprocess
import sys

from tests.guards.makefile import command_args

GATE_FLAGS = ("--include", "--omit", "--fail-under")


def _domain_report_args() -> list[str]:
    args = [a for a in command_args("test", "coverage report") if a.startswith(GATE_FLAGS)]
    assert {a.split("=")[0] for a in args} == set(GATE_FLAGS), args
    return args


def _coverage(cwd, *args):
    return subprocess.run([sys.executable, "-m", "coverage", *args], cwd=cwd, capture_output=True, text=True)


def test_the_gate_demands_every_domain_line_and_branch():
    args = _domain_report_args()
    assert "--fail-under=100" in args
    assert any(a.startswith("--include=") and "fingerprint/domain/" in a for a in args)


def test_an_untested_domain_branch_fails_the_domain_coverage_report(tmp_path):
    domain = tmp_path / "fingerprint" / "domain"
    domain.mkdir(parents=True)
    (domain / "rule.py").write_text("def sign(x):\n    if x < 0:\n        return -1\n    return 1\n\n\nsign(1)\n")
    (tmp_path / "rc").write_text("[run]\nbranch = True\n")  # not the repository's .coveragerc

    assert _coverage(tmp_path, "run", "--rcfile=rc", "fingerprint/domain/rule.py").returncode == 0
    report = _coverage(tmp_path, "report", "--rcfile=rc", "--show-missing", *_domain_report_args())

    assert report.returncode != 0
    # the untaken `return -1`, line 3, is in the Missing column of the rule.py row
    assert re.search(r"^fingerprint/domain/rule\.py\s.*\s3(?:,|\s*$)", report.stdout, re.MULTILINE)
