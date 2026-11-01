"""The import contracts fence the test tiers (lean-test-suite P-4, TC-5)."""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]
LINT_IMPORTS = Path(sys.executable).parent / "lint-imports"
DOMAIN_CONTRACT = "domain tests import no higher layer or test double"

pytestmark = pytest.mark.skipif(not LINT_IMPORTS.exists(), reason="lint-imports is not installed (poetry install --with lint)")


@pytest.fixture
def tree(tmp_path):
    """A copy of the packages and the contracts, small enough to lint in a second or two."""
    shutil.copy(ROOT / ".importlinter", tmp_path)
    ignore = shutil.ignore_patterns("__pycache__", "test_data", "features")
    for package in ("fingerprint", "tests"):
        shutil.copytree(ROOT / package, tmp_path / package, ignore=ignore)
    return tmp_path


def lint(tree):
    return subprocess.run(
        [str(LINT_IMPORTS), "--config", str(tree / ".importlinter")], cwd=tree, capture_output=True, text=True
    )


def test_the_real_tree_keeps_every_contract(tree):
    assert lint(tree).returncode == 0


@pytest.mark.parametrize("imported", ["fingerprint.service_layer.handlers", "fingerprint.adapters.sparql", "tests.fakes"])
def test_a_domain_test_importing_a_higher_layer_or_a_double_fails(tree, imported):
    (tree / "tests" / "unit" / "domain" / "test_violation.py").write_text(f"import {imported}\n")
    result = lint(tree)
    assert result.returncode != 0
    assert DOMAIN_CONTRACT in result.stdout
