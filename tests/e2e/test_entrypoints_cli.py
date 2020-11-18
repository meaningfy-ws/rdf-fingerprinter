#!/usr/bin/python3

# test_entrypoints_cli.py
# Date:  18/10/2020
# Author: Eugeniu Costetchi
# Email: costezki.eugen@gmail.com 

""" """
from pathlib import Path

from click.testing import CliRunner

from fingerprint.entrypoints.cli.main import fingerprint_endpoint


def test_fingerprint_execution(tmpdir):
    runner = CliRunner()
    output_path = tmpdir.mkdir("/output")
    result = runner.invoke(fingerprint_endpoint, ['-e', 'http://localhost:3030/dev/query', '-o', output_path])

    assert result.exit_code == 0

    files_in_output_path = list((Path(str(output_path)).iterdir()))
    main_file = files_in_output_path[0].name

    assert main_file == 'main.html'
