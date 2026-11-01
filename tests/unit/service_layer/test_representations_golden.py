"""Golden files per format from the fixed sample profile, and SHACL on its own source data (task 4.3).

After an intended change run `make refresh-golden`, then review the diff.
"""

import pyshacl
import pytest
from rdflib import Graph, Namespace

from fingerprint.service_layer.generators import GENERATORS
from fingerprint.service_layer.representations import with_threshold
from tests.refresh_golden import render
from tests.sample_data import GOLDEN, TEST_DATA

SH = Namespace("http://www.w3.org/ns/shacl#")
# make oxigraph-load-test-data puts continents in the default graph too; no union default graph.
SOURCE = {"default": "continents", "continents": "continents", "treaties": "treaties"}


@pytest.mark.parametrize("name", sorted(GENERATORS))
def test_golden_output(name, sample_outputs):
    produced = sample_outputs[name]
    stem = next(iter(produced)).split("-")[0].split(".")[0]
    assert set(produced) == {p.name for p in GOLDEN.iterdir() if p.name.startswith(stem)}
    for file_name, text in produced.items():
        assert text == (GOLDEN / file_name).read_text(encoding="utf-8"), f"{file_name} differs from its golden file"


def shacl_files(run, threshold):
    return render(with_threshold(run, threshold) if threshold is not None else run, "shacl")


@pytest.mark.parametrize("threshold", [None, 0.5, 0.1])  # None: the profile's own (0.95)
@pytest.mark.parametrize("graph", sorted(SOURCE))
def test_shapes_report_no_violation_on_their_own_data(graph, threshold, sample_run):
    (file_name, text) = next((f, t) for f, t in shacl_files(sample_run, threshold).items() if f.startswith(f"shapes-{graph}"))
    source = next(f for key, f in SOURCE.items() if file_name.startswith(f"shapes-{key}"))
    data = Graph().parse(TEST_DATA / f"{source}-source-ap.rdf")
    _, results, _ = pyshacl.validate(data, shacl_graph=Graph().parse(data=text, format="turtle"), inference="none")
    violations = list(results.subjects(SH.resultSeverity, SH.Violation))
    assert not violations, results.serialize(format="turtle")[:2000]
