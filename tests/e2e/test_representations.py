"""UC-B2.2 then UC-B2.1 end to end: fingerprint the loaded store with every format, then regenerate each
format from the saved profile.json with any query refused (profile-representations task 7.4)."""

import pytest
from click.testing import CliRunner
from rdflib import Graph

from fingerprint.adapters.sparql import SparqlHttpClient
from fingerprint.entrypoints.cli import generate
from fingerprint.entrypoints.cli.main import fingerprint_endpoint
from tests import LOCAL_ENDPOINT

FORMATS = ["--format", "shacl", "--format", "puml", "--format", "doc"]


@pytest.fixture(scope="module")
def fingerprinted(tmp_path_factory):
    output = tmp_path_factory.mktemp("output")
    result = CliRunner().invoke(fingerprint_endpoint, ["-e", LOCAL_ENDPOINT, "-o", str(output), *FORMATS])
    assert result.exit_code == 0, result.output
    return output


def test_one_run_writes_the_report_the_profile_and_every_representation(fingerprinted):
    names = {p.name for p in fingerprinted.iterdir()}
    assert {"main.html", "profile.json", "profile.html", "shapes-default.ttl", "diagram-default.puml"} <= names
    assert len([n for n in names if n.startswith("shapes-")]) == 3  # default + continents + treaties
    for shapes in fingerprinted.glob("shapes-*.ttl"):
        Graph().parse(shapes, format="turtle")


@pytest.mark.parametrize("command", [generate.gen_shacl, generate.gen_puml, generate.gen_doc])
def test_regenerating_from_the_saved_profile_queries_nothing(fingerprinted, tmp_path, monkeypatch, command):
    def refuse(self, *args, **kwargs):
        raise AssertionError("a generator queried the endpoint")

    monkeypatch.setattr(SparqlHttpClient, "_once", refuse)
    result = CliRunner().invoke(command, [str(fingerprinted / "profile.json"), "-o", str(tmp_path)])
    assert result.exit_code == 0, result.output
    regenerated = {p.name: p.read_text() for p in tmp_path.iterdir()}
    assert regenerated and all(text == (fingerprinted / name).read_text() for name, text in regenerated.items())
