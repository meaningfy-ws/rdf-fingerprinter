import subprocess
import sys
from importlib.metadata import version
from importlib.resources import files

import fingerprint
import fingerprint_report_templates


def test_version_comes_from_the_installed_metadata():
    assert fingerprint.__version__ == version("rdf-fingerprinter")


def test_import_from_another_directory_has_no_logging_side_effects(tmp_path):
    code = (
        "import logging; before = list(logging.getLogger().handlers); "
        "import fingerprint.entrypoints.cli.main; "
        "assert logging.getLogger().handlers == before, logging.getLogger().handlers"
    )
    result = subprocess.run([sys.executable, "-c", code], cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_the_report_package_is_packaged():
    assert (files(fingerprint_report_templates) / "fingerprint_report" / "config.json").is_file()
