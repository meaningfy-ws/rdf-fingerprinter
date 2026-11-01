"""The ShExC command (UC-B2.1): the same size and ontology options as the pattern command (TC-E1)."""

import tomllib
from pathlib import Path

import pytest
from click.testing import CliRunner

from fingerprint.entrypoints.cli import generate
from tests.sample_data import SAMPLE_PROFILE as SAMPLE
from tests.sample_data import TEST_DATA

LABELS = TEST_DATA / "ontology" / "labels.ttl"
CONTINENTS = "shex-continents-214e8f67.shex"


def invoke(*args):
    return CliRunner().invoke(generate.gen_shex, [str(a) for a in args])


def test_the_shex_command_writes_one_file_per_graph(tmp_path):
    result = invoke(SAMPLE, "-o", tmp_path)
    assert result.exit_code == 0, result.output
    assert (tmp_path / CONTINENTS).is_file()


@pytest.mark.parametrize("option", ["--min-instances", "--max-classes"])
def test_a_size_filter_below_one_exits_2(tmp_path, option):
    result = invoke(SAMPLE, "-o", tmp_path, option, "0")
    assert result.exit_code == 2 and not list(tmp_path.iterdir())


def test_the_size_options_are_passed_through(tmp_path):
    invoke(SAMPLE, "-o", tmp_path, "--max-classes", "1")
    shapes = [ln for ln in (tmp_path / CONTINENTS).read_text().splitlines() if ln.endswith(" {") and not ln.startswith(" ")]
    assert shapes == ["euvoc:Continent {"]  # the other block is gone, and Label, reached once, is inline


def test_the_ontology_option_is_passed_through(tmp_path):
    result = invoke(SAMPLE, "-o", tmp_path, "--ontology", LABELS)
    assert result.exit_code == 0, result.output
    assert '# skos:Concept "Concept"@en' in (tmp_path / CONTINENTS).read_text()


def test_an_unreadable_ontology_exits_2_naming_it(tmp_path):
    bad = tmp_path / "bad.ttl"
    bad.write_text("not turtle")
    out = tmp_path / "out"
    out.mkdir()
    result = invoke(SAMPLE, "-o", out, "--ontology", bad)
    assert result.exit_code == 2 and "bad.ttl" in result.output and not list(out.iterdir())


def test_the_script_is_declared_and_pyshexc_is_a_test_dependency_only():
    project = tomllib.loads((Path(__file__).parents[3] / "pyproject.toml").read_text())
    assert project["project"]["scripts"]["fingerprint-gen-shex"] == "fingerprint.entrypoints.cli.generate:gen_shex"
    assert not any("pyshexc" in d for d in project["project"].get("dependencies", []))
    assert "pyshexc==0.10.3.post1" in project["dependency-groups"]["test"]
