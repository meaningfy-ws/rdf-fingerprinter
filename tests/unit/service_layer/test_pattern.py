"""The pattern schema generator: the pattern view laid out as five files per graph (profile-representations)."""

import csv
import io

import pytest

from fingerprint.adapters.template_renderer import JinjaTemplateRenderer
from fingerprint.domain.analytics import analyse
from fingerprint.domain.profile import LangText, TermAnnotation
from fingerprint.domain.views import GeneratorOptions, RepresentationFormat
from fingerprint.service_layer.generators import GENERATORS
from fingerprint.service_layer.generators.generator import plain_label
from fingerprint.service_layer.generators.pattern import PatternGenerator
from tests import builders
from tests.builders import klass, literals, profile_run, prop
from tests.fakes import EX, files
from tests.sample_data import GLOSSARY_COLUMNS, PATTERNS_COLUMNS

CONTINENTS_GRAPH = "http://publications.europa.eu/resources/authority/continents"
PATTERNS_HEADER = ",".join(PATTERNS_COLUMNS)
GLOSSARY_HEADER = ",".join(GLOSSARY_COLUMNS)


def outputs(run, **options):
    generator = PatternGenerator(analyse(run), JinjaTemplateRenderer(), options=GeneratorOptions(**options))
    return files(generator.serialize()), generator


SLUGS = ("continents-214e8f67", "default", "treaties-3b4301a8")
NAMES = sorted(
    f"{kind}-{slug}.{extension}"
    for slug in SLUGS
    for kind, extension in (
        ("prefixes", "md"),
        ("patterns", "md"),
        ("patterns", "csv"),
        ("glossary", "md"),
        ("glossary", "csv"),
    )
)


@pytest.fixture(scope="module")
def sample_files(sample_analytics):
    return files(PatternGenerator(sample_analytics, JinjaTemplateRenderer()).serialize())


@pytest.fixture(scope="module")
def continents(sample_files):
    return sample_files["patterns-continents-214e8f67.md"]


def test_the_pattern_format_is_registered():
    assert GENERATORS[RepresentationFormat.pattern] is PatternGenerator


def test_five_files_per_graph_named_by_their_slug_and_none_a_txt(sample_files):
    assert sorted(sample_files) == NAMES and not any(name.endswith(".txt") for name in sample_files)


def test_every_file_of_a_graph_is_rendered_from_the_same_view_by_its_own_template():
    generator = PatternGenerator(analyse(profile_run(klass(EX + "A", 1))), JinjaTemplateRenderer())
    (graph,) = generator.views()
    outputs = generator.outputs()
    assert [(name, view.template) for name, view in outputs] == [
        ("prefixes-default.md", "prefixes.md"),
        ("patterns-default.md", "patterns.md"),
        ("patterns-default.csv", "patterns.csv"),
        ("glossary-default.md", "glossary.md"),
        ("glossary-default.csv", "glossary.csv"),
    ]
    assert all(view.graph == graph for _, view in outputs)


def test_the_patterns_markdown_holds_the_title_the_sibling_files_the_legend_then_a_fenced_block_per_class(continents):
    lines = continents.splitlines()
    assert lines[0] == f"# Patterns of {CONTINENTS_GRAPH}"
    assert "Prefixes: `prefixes-continents-214e8f67.md` · glossary: `glossary-continents-214e8f67.md`" in lines
    assert any(line.startswith("Legend: (:A&B) n: classes with the same n instances") for line in lines)
    at = lines.index("## euvoc:Continent&skos:Concept")
    assert lines[at + 1 : at + 4] == ["", "```text", "(:euvoc:Continent&skos:Concept) 6"]
    assert "```" in lines[at + 4 :]


def test_the_patterns_markdown_holds_no_prefix_declaration_and_no_glossary(continents):
    assert "PREFIX" not in continents and "glossary:" not in continents.split("Legend:")[1]


def test_the_blocks_are_the_view_s_header_and_edge_texts_indented_by_depth(continents):
    assert "\n(:euvoc:Continent&skos:Concept) 6\n  -dcterms:created-> xsd:date =2014-10-10\n" in continents
    assert "\n    -lvont:script-> IRI 12/145 d2\n" in continents
    assert "\n  -skosxl:prefLabel-> (:skosxl:Label) bn ^\n" in continents  # the edge's ending is printed once


def test_the_hidden_line_is_written_only_when_classes_are_hidden():
    texts, _ = outputs(
        profile_run(klass(EX + "A", 5, prop(EX + "p", {1: 5}, literals(5))), klass(EX + "B", 1)), min_instances=2
    )
    assert "\nHidden: 1 classes.\n" in texts["patterns-default.md"]
    plain, _ = outputs(profile_run(klass(EX + "A", 5, prop(EX + "p", {1: 5}, literals(5)))))
    assert "Hidden" not in plain["patterns-default.md"]


def test_a_graph_with_no_shown_class_writes_no_file():
    texts, _ = outputs(profile_run())
    assert texts == {}


def test_a_named_graph_is_labelled_in_plain_characters():
    (view,) = PatternGenerator(analyse(profile_run(klass(EX + "A", 1), graph=EX + "g")), JinjaTemplateRenderer()).views()
    assert view.graph_label == plain_label(EX + "g")


def test_the_note_of_the_excluded_namespaces_follows_the_legend():
    noted = patterns_lines(builders.filtered_analytics("rel"))
    assert noted[noted.index(f"Excluded namespaces: {builders.REL_NOTE}.") - 2].startswith("Legend: (:A&B) n: classes")


def test_the_note_of_the_excluded_namespaces_follows_the_hidden_line():
    hidden = builders.filter_profile(klass("http://www.w3.org/2002/07/owl#Thing", 1))
    noted = patterns_lines(builders.filtered_analytics("rel", run=hidden))
    assert noted[noted.index("Hidden: 1 classes.") + 2] == f"Excluded namespaces: {builders.REL_NOTE}."


def test_a_name_with_an_ampersand_is_not_escaped_in_any_file(sample_files):
    assert all("&amp;" not in text for text in sample_files.values())


def patterns_lines(analytics):
    texts = files(PatternGenerator(analytics, JinjaTemplateRenderer()).serialize())
    return next(t for name, t in texts.items() if name.startswith("patterns-") and name.endswith(".md")).splitlines()


# --- the prefix, CSV and glossary files ---


def rows(text):
    return list(csv.DictReader(io.StringIO(text, newline="")))


def with_notes(*notes: TermAnnotation):
    run = profile_run(klass(EX + "A", 3, prop(EX + "p", {1: 3}, literals(3))))
    return run.model_copy(update={"graphs": [g.model_copy(update={"term_annotations": list(notes)}) for g in run.graphs]})


def test_the_prefix_table_has_a_row_per_prefix_with_its_counts(sample_files):
    lines = sample_files["prefixes-continents-214e8f67.md"].splitlines()
    assert lines[0] == f"# Prefixes of {CONTINENTS_GRAPH}"
    assert "| prefix | namespace | classes | properties | instances | triples |" in lines
    assert "| xsd | <http://www.w3.org/2001/XMLSchema#> | 0 | 0 | 0 | 0 |" in lines
    assert next(line for line in lines if line.startswith("| euvoc |")).split("|")[3].strip() == "2"


def test_the_patterns_csv_has_the_header_a_block_row_and_the_edge_rows_in_line_order(sample_files):
    text = sample_files["patterns-continents-214e8f67.csv"]
    assert text.splitlines()[0] == PATTERNS_HEADER and text.endswith("\n")
    found = rows(text)
    block_row = found[0]
    assert (block_row["block"], block_row["owner"], block_row["depth"], block_row["instances"], block_row["property"]) == (
        "euvoc:Continent&skos:Concept",
        "euvoc:Continent&skos:Concept",
        "0",
        "6",
        "",
    )
    assert block_row["graph"] == CONTINENTS_GRAPH


def test_an_edge_row_holds_the_typed_facts_of_its_edge(sample_files):
    found = rows(sample_files["patterns-continents-214e8f67.csv"])
    script = next(r for r in found if r["property"] == "lvont:script")
    assert (script["owner"], script["path"], script["depth"], script["targets"], script["target_kinds"]) == (
        "skosxl:Label",
        "skosxl:prefLabel",
        "2",
        "IRI",
        "iri",
    )
    assert (script["subjects"], script["instances"], script["distinct"], script["blank_nodes"], script["ending"]) == (
        "12",
        "145",
        "2",
        "false",
        "",
    )
    ended = next(r for r in rows(sample_files["patterns-continents-214e8f67.csv"]) if r["ending"])
    assert ended["ending"] in ("^", "…")


def test_a_value_with_a_comma_or_a_quote_is_quoted_in_the_patterns_csv():
    value = literals(10).model_copy(update={"min_value": 'a, "b"', "max_value": 'a, "b"'})
    text = files(
        PatternGenerator(
            analyse(profile_run(klass(EX + "A", 10, prop(EX + "p", {1: 10}, value)))), JinjaTemplateRenderer()
        ).serialize()
    )["patterns-default.csv"]
    assert '"a, ""b"""' in text and rows(text)[1]["single_value"] == 'a, "b"'


def test_the_glossary_markdown_lists_the_lines_or_says_there_is_none(sample_files):
    assert sample_files["glossary-continents-214e8f67.md"].splitlines() == [
        f"# Glossary of {CONTINENTS_GRAPH}",
        "",
        "No term of this graph has a label or a description.",
    ]
    noted = TermAnnotation(term=EX + "A", labels=[LangText(text="Thing", language="en")])
    texts = files(PatternGenerator(analyse(with_notes(noted)), JinjaTemplateRenderer()).serialize())
    assert texts["glossary-default.md"].splitlines() == ["# Glossary of default graph", "", '- ex:A C "Thing"@en']


def test_the_glossary_csv_has_a_row_per_term_and_language_and_a_header_only_without_terms(sample_files):
    assert sample_files["glossary-continents-214e8f67.csv"] == GLOSSARY_HEADER + "\n"
    noted = TermAnnotation(
        term=EX + "A",
        labels=[LangText(text="Thing", language="en")],
        alt_labels=[LangText(text="Begriff", language="de"), LangText(text="Item", language="en")],
        notes=[LangText(text="Internal, really", language="en")],
    )
    texts = files(PatternGenerator(analyse(with_notes(noted)), JinjaTemplateRenderer()).serialize())
    assert [dict(r) for r in rows(texts["glossary-default.csv"])] == [
        {
            "term": "ex:A",
            "iri": EX + "A",
            "kind": "C",
            "language": "de",
            "pref_label": "",
            "alt_labels": "Begriff",
            "definition": "",
            "notes": "",
        },
        {
            "term": "ex:A",
            "iri": EX + "A",
            "kind": "C",
            "language": "en",
            "pref_label": "Thing",
            "alt_labels": "Item",
            "definition": "",
            "notes": "Internal, really",
        },
    ]


def test_a_term_with_notes_only_is_in_the_csv_but_not_in_the_markdown():
    noted = TermAnnotation(term=EX + "A", notes=[LangText(text="Internal", language="en")])
    texts = files(PatternGenerator(analyse(with_notes(noted)), JinjaTemplateRenderer()).serialize())
    assert rows(texts["glossary-default.csv"])[0]["notes"] == "Internal"
    assert texts["glossary-default.md"].splitlines()[-1] == "No term of this graph has a label or a description."
