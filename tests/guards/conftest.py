"""A lintable copy of the packages and the import contracts, shared by the guards that break a contract."""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]
LINT_IMPORTS = Path(sys.executable).parent / "lint-imports"


@pytest.fixture
def tree(tmp_path):
    """A copy of the packages and the contracts, small enough to lint in a second or two."""
    if not LINT_IMPORTS.exists():
        pytest.skip("lint-imports is not installed (poetry install --with lint)")
    shutil.copy(ROOT / ".importlinter", tmp_path)
    ignore = shutil.ignore_patterns("__pycache__", "test_data", "features")
    for package in ("fingerprint", "tests"):
        shutil.copytree(ROOT / package, tmp_path / package, ignore=ignore)
    return tmp_path


@pytest.fixture
def lint():
    """Run import-linter on a tree; the result carries the exit code and the report."""

    def run(tree):
        return subprocess.run(
            [str(LINT_IMPORTS), "--config", str(tree / ".importlinter")], cwd=tree, capture_output=True, text=True
        )

    return run
