"""The pitfalls TSV format (pitfall-scans › Pitfalls TSV format)."""

from fingerprint.adapters.template_renderer import JinjaTemplateRenderer
from fingerprint.domain.analytics import analyse
from fingerprint.domain.profile import GraphProfile, PitfallExample, PitfallResult, PitfallTerm, ProfileRun
from fingerprint.service_layer.generators import GENERATORS
from tests.unit.fakes import files


def term(text, kind="iri"):
    return PitfallTerm(text=text, kind=kind)


def result(check_id, importance, examples, count=None):
    return PitfallResult(
        check_id=check_id,
        title="t",
        importance=importance,
        scope="schema",
        source="s",
        count=len(examples) if count is None else count,
        examples=examples,
    )


def tsv(graphs):
    run = ProfileRun(endpoint="http://e", settings={}, graphs=graphs)
    return files(GENERATORS["pitfalls"](analyse(run), JinjaTemplateRenderer()).serialize())


def test_robot_style_lines():
    example = PitfallExample(
        entity=term("http://ex.org/p"), property=term("http://www.w3.org/2000/01/rdf-schema#range"), value=term("2", "literal")
    )
    (text,) = tsv([GraphProfile(pitfalls=[result("p19_multiple_domains_or_ranges", "critical", [example])])]).values()
    lines = text.strip().split("\n")
    assert lines[0] == "Level\tRule Name\tSubject\tProperty\tValue"
    assert lines[1] == "ERROR\tp19_multiple_domains_or_ranges\thttp://ex.org/p\thttp://www.w3.org/2000/01/rdf-schema#range\t2"


def test_cells_blank_nodes_unbound_and_breaks():
    example = PitfallExample(entity=term("b1", "blank_node"), value=term("a\tb\nc", "literal"))
    (text,) = tsv([GraphProfile(graph="http://ex.org/g", pitfalls=[result("x", "minor", [example])])]).values()
    assert text.strip().split("\n")[1] == "INFO\tx\t_:b1\t\ta b c"


def test_files_per_scanned_graph_only():
    names = tsv([GraphProfile(pitfalls=[result("x", "minor", [], count=0)]), GraphProfile(graph="http://ex.org/g")])
    assert (
        list(names) == ["pitfalls-default.tsv"]
        and names["pitfalls-default.tsv"].strip() == "Level\tRule Name\tSubject\tProperty\tValue"
    )
    assert tsv([GraphProfile()]) == {}
