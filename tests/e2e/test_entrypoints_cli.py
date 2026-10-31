#!/usr/bin/python3

# test_entrypoints_cli.py
# Date:  18/10/2020
# Author: Eugeniu Costetchi
# Email: costezki.eugen@gmail.com

""" """

from pathlib import Path

from click.testing import CliRunner

from fingerprint.entrypoints.cli.main import fingerprint_endpoint
from tests import LOCAL_ENDPOINT


def test_fingerprint_execution(tmpdir):
    runner = CliRunner()
    output_path = tmpdir.mkdir("/output")
    result = runner.invoke(fingerprint_endpoint, ["-e", LOCAL_ENDPOINT, "-o", output_path])

    assert result.exit_code == 0

    files_in_output_path = list(Path(str(output_path)).iterdir())
    main_file = files_in_output_path[0].name

    assert main_file == "main.html"


def test_unreachable_endpoint_exits_3(tmp_path):
    result = CliRunner().invoke(fingerprint_endpoint, ["-e", "http://localhost:1/query", "-o", str(tmp_path)])
    assert result.exit_code == 3
    assert not (tmp_path / "main.html").exists()


def test_missing_output_folder_is_a_usage_error(tmp_path):
    result = CliRunner().invoke(fingerprint_endpoint, ["-e", LOCAL_ENDPOINT, "-o", str(tmp_path / "missing")])
    assert result.exit_code == 2


def test_collection_options_are_recorded(tmp_path):
    result = CliRunner().invoke(
        fingerprint_endpoint, ["-e", LOCAL_ENDPOINT, "-o", str(tmp_path), "--precision", "first_n", "--first-n", "2"]
    )
    assert result.exit_code == 0
    assert "first 2 of" in (tmp_path / "main.html").read_text()
