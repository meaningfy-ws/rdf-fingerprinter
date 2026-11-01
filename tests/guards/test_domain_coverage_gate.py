"""The per-layer coverage gate of `make test` (lean-test-suite P-7, developer-tooling "Coverage and mutation gate")."""

import subprocess
import sys

DOMAIN_REPORT = [
    "--include=fingerprint/domain/*",
    "--omit=fingerprint/domain/profile.py,fingerprint/domain/views.py",
    "--fail-under=100",
]


def _coverage(cwd, *args):
    return subprocess.run([sys.executable, "-m", "coverage", *args], cwd=cwd, capture_output=True, text=True)


def test_an_untested_domain_branch_fails_the_domain_coverage_report(tmp_path):
    domain = tmp_path / "fingerprint" / "domain"
    domain.mkdir(parents=True)
    (domain / "rule.py").write_text("def sign(x):\n    if x < 0:\n        return -1\n    return 1\n\n\nsign(1)\n")
    (tmp_path / "rc").write_text("[run]\nbranch = True\n")  # not the repository's .coveragerc

    assert _coverage(tmp_path, "run", "--rcfile=rc", "fingerprint/domain/rule.py").returncode == 0
    report = _coverage(tmp_path, "report", "--rcfile=rc", "--show-missing", *DOMAIN_REPORT)

    assert report.returncode != 0
    assert "fingerprint/domain/rule.py" in report.stdout
    assert report.stdout.rstrip().splitlines()[2].endswith("71%   3")  # the untaken `return -1`, line 3, is listed
