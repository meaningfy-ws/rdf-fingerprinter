#!/usr/bin/python3

# test_entrypoints_cli.py
# Date:  18/10/2020
# Author: Eugeniu Costetchi
# Email: costezki.eugen@gmail.com 

""" """
from pathlib import Path

from click.testing import CliRunner

from fingerprint.entrypoints.cli.main import fingerprint_endpoint

TEST_ENDPOINT = "http://localhost:3030/dev/query"

def test_fingerprint_endpoint():
    runner = CliRunner()
    Path("./output").mkdir(parents=True,exist_ok=True)
    result = runner.invoke(fingerprint_endpoint, ['-e', TEST_ENDPOINT])
    assert result.exit_code == 0
    assert Path("./output").exists()
    assert sorted(Path("./output").glob("*"))
