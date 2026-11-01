"""The pitfall scan against the loaded test store (`make oxigraph-load-test-data`), which it leaves unchanged.

Treaties is scanned as data with continents as the schema graph: this exercises the FROM merge on a real store.
"""

import pytest
from bs4 import BeautifulSoup
from click.testing import CliRunner

from fingerprint.domain.profile import ProfileRun
from fingerprint.entrypoints.cli.main import fingerprint_endpoint
from tests import LOCAL_ENDPOINT

BASE = "http://publications.europa.eu/resources/authority/"
ARGS = ["--graph", BASE + "treaties", "--pitfalls", "--schema-graph", BASE + "continents", "--format", "pitfalls"]


@pytest.fixture(scope="module")
def scanned(tmp_path_factory):
    output = tmp_path_factory.mktemp("output")
    result = CliRunner().invoke(fingerprint_endpoint, ["-e", LOCAL_ENDPOINT, "-o", str(output), *ARGS])
    assert result.exit_code == 0, result.output
    return output


def test_both_graphs_are_scanned_with_their_checks(scanned):
    run = ProfileRun.model_validate_json((scanned / "profile.json").read_text())
    by_graph = {g.graph: g for g in run.graphs}
    assert set(by_graph) == {BASE + "treaties", BASE + "continents"}
    assert {r.scope for r in by_graph[BASE + "treaties"].pitfalls} == {"data"}
    assert {r.scope for r in by_graph[BASE + "continents"].pitfalls} == {"schema"}
    assert not run.failures and any(r.count for g in run.graphs for r in g.pitfalls)


def test_the_page_and_the_tsv(scanned):
    page = BeautifulSoup((scanned / "main.html").read_text(), "html.parser")
    assert page.find(id="pitfalls").select("details.pitfall")
    tsv = sorted(scanned.glob("pitfalls-*.tsv"))
    assert len(tsv) == 2 and all(p.read_text().startswith("Level\tRule Name\tSubject\tProperty\tValue") for p in tsv)


def test_fail_on_minor_exits_5(tmp_path):
    result = CliRunner().invoke(fingerprint_endpoint, ["-e", LOCAL_ENDPOINT, "-o", str(tmp_path), *ARGS, "--fail-on", "minor"])
    assert result.exit_code == 5, result.output
