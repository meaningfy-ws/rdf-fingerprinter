"""Golden files per format from the fixed sample profile, and SHACL on its own source data (task 4.3).

Run with UPDATE_GOLDEN=1 to rewrite the golden files after an intended change, then review the diff.
"""

import os
from pathlib import Path

import pyshacl
import pytest
from rdflib import Graph, Namespace

from fingerprint.adapters.profile_file import load_profile
from fingerprint.adapters.template_renderer import JinjaTemplateRenderer
from fingerprint.domain.analytics import analyse
from fingerprint.service_layer.generators import GENERATORS
from fingerprint.service_layer.representations import make_generator, with_threshold
from tests.unit.fakes import files

DATA = Path(__file__).parents[1] / "test_data"
GOLDEN = DATA / "golden"
SH = Namespace("http://www.w3.org/ns/shacl#")
# make oxigraph-load-test-data puts continents in the default graph too; no union default graph.
SOURCE = {"default": "continents", "continents": "continents", "treaties": "treaties"}


def texts(name, threshold=None, profile="sample-profile.json"):
    run = load_profile(DATA / "profiles" / profile)
    if threshold is not None:
        run = with_threshold(run, threshold)
    return files(make_generator(name, analyse(run), JinjaTemplateRenderer()).serialize())


def check_golden(produced, folder):
    stem = next(iter(produced)).split("-")[0].split(".")[0]
    if os.environ.get("UPDATE_GOLDEN"):
        folder.mkdir(exist_ok=True)
        for file_name, text in produced.items():
            (folder / file_name).write_text(text, encoding="utf-8")
    assert set(produced) == {p.name for p in folder.iterdir() if p.is_file() and p.name.startswith(stem)}
    for file_name, text in produced.items():
        assert text == (folder / file_name).read_text(encoding="utf-8"), f"{file_name} differs from its golden file"


@pytest.mark.parametrize("name", sorted(set(GENERATORS) - {"pitfalls"}))  # the sample has no scan results
def test_golden_output(name):
    check_golden(texts(name), GOLDEN)


@pytest.mark.parametrize("name", ["doc", "pitfalls"])
def test_golden_output_of_a_scanned_profile(name):
    """The page's Pitfalls section and the TSV, for the test data scanned with continents as the schema graph."""
    check_golden(texts(name, profile="scanned-profile.json"), GOLDEN / "scanned")


@pytest.mark.parametrize("threshold", [None, 0.5, 0.1])  # None: the profile's own (0.95)
@pytest.mark.parametrize("graph", sorted(SOURCE))
def test_shapes_report_no_violation_on_their_own_data(graph, threshold):
    (file_name, text) = next((f, t) for f, t in texts("shacl", threshold).items() if f.startswith(f"shapes-{graph}"))
    source = next(f for key, f in SOURCE.items() if file_name.startswith(f"shapes-{key}"))
    data = Graph().parse(DATA / f"{source}-source-ap.rdf")
    _, results, _ = pyshacl.validate(data, shacl_graph=Graph().parse(data=text, format="turtle"), inference="none")
    violations = list(results.subjects(SH.resultSeverity, SH.Violation))
    assert not violations, results.serialize(format="turtle")[:2000]
