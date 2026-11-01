"""Golden files per format from the fixed sample profile, and SHACL on its own source data (task 4.3).

After an intended change run `make refresh-golden`, then review the diff.
"""

import pyshacl
import pytest
from rdflib import Graph, Namespace
from rdflib.compare import graph_diff, isomorphic, to_isomorphic

from fingerprint.adapters.profile_file import load_profile
from fingerprint.service_layer.generators import GENERATORS
from fingerprint.service_layer.representations import with_threshold
from tests.refresh_golden import render
from tests.sample_data import GOLDEN, SCANNED_FORMATS, SCANNED_GOLDEN, SCANNED_PROFILE, TEST_DATA

SH = Namespace("http://www.w3.org/ns/shacl#")
# make oxigraph-load-test-data puts continents in the default graph too; no union default graph.
SOURCE = {"default": "continents", "continents": "continents", "treaties": "treaties"}


def turtle_difference(golden: str, output: str) -> str | None:
    """None when the two Turtle texts are the same graph, else the triples found in only one of them."""
    expected, produced = Graph().parse(data=golden, format="turtle"), Graph().parse(data=output, format="turtle")
    if isomorphic(expected, produced):
        return None
    _, only_golden, only_output = graph_diff(to_isomorphic(expected), to_isomorphic(produced))

    def lines(graph):
        return "\n".join(sorted(f"  {s.n3()} {p.n3()} {o.n3()}" for s, p, o in graph))

    return f"only in the golden file:\n{lines(only_golden)}\nonly in the output:\n{lines(only_output)}"


def assert_golden(produced, folder):
    stem = next(iter(produced)).split("-")[0].split(".")[0]
    assert set(produced) == {p.name for p in folder.iterdir() if p.is_file() and p.name.startswith(stem)}
    for file_name, text in produced.items():
        golden = (folder / file_name).read_text(encoding="utf-8")
        if file_name.endswith(".ttl"):
            assert (difference := turtle_difference(golden, text)) is None, f"{file_name} differs:\n{difference}"
        else:
            assert text == golden, f"{file_name} differs from its golden file"


@pytest.mark.parametrize("name", sorted(set(GENERATORS) - {"pitfalls"}))  # the sample profile holds no scan results
def test_golden_output(name, sample_outputs):
    assert_golden(sample_outputs[name], GOLDEN)


@pytest.mark.parametrize("name", SCANNED_FORMATS)
def test_golden_output_of_the_scanned_profile(name):
    """The page's Pitfalls section and the TSV, from the test data scanned for pitfalls (pitfall-scans)."""
    assert_golden(render(load_profile(SCANNED_PROFILE), name), SCANNED_GOLDEN)


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


# --- the comparison itself (developer-tooling: Generated outputs compared by meaning) ---

GOLDEN_TTL = """@prefix ex: <http://ex.org/> .
ex:a ex:p "one" ; ex:q ex:b .
ex:b ex:p "two" .
"""


def test_a_reordered_turtle_output():
    """Scenario: A reordered Turtle output."""
    reordered = """@prefix e: <http://ex.org/> .
e:b e:p "two" .
e:a e:q e:b ; e:p "one" .
"""
    assert turtle_difference(GOLDEN_TTL, reordered) is None


def test_a_changed_triple():
    """Scenario: A changed triple."""
    changed = GOLDEN_TTL.replace('"two"', '"2"')
    difference = turtle_difference(GOLDEN_TTL, changed)
    golden_side, output_side = difference.split("only in the output:\n")
    assert golden_side.splitlines()[1:] == ['  <http://ex.org/b> <http://ex.org/p> "two"']
    assert output_side.splitlines() == ['  <http://ex.org/b> <http://ex.org/p> "2"']


def test_blank_nodes_match_by_structure_not_by_label():
    golden = '@prefix ex: <http://ex.org/> . ex:a ex:p [ ex:q "x" ] .'
    relabelled = '@prefix ex: <http://ex.org/> . ex:a ex:p _:other . _:other ex:q "x" .'
    assert turtle_difference(golden, relabelled) is None
    assert turtle_difference(golden, relabelled.replace('"x"', '"y"')) is not None
