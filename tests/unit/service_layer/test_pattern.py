"""The pattern schema generator: the pattern view laid out as five files per graph (profile-representations)."""

import csv
import io

import pytest

from fingerprint.adapters.template_renderer import JinjaTemplateRenderer
from fingerprint.domain.views import RepresentationFormat
from fingerprint.service_layer.generators import GENERATORS
from fingerprint.service_layer.generators.pattern import PatternGenerator
from tests.fakes import files
from tests.sample_data import PATTERNS_COLUMNS

CONTINENTS_GRAPH = "http://publications.europa.eu/resources/authority/continents"
PATTERNS_HEADER = ",".join(PATTERNS_COLUMNS)


@pytest.fixture(scope="module")
def sample_files(sample_analytics):
    return files(PatternGenerator(sample_analytics, JinjaTemplateRenderer()).serialize())


@pytest.fixture(scope="module")
def continents(sample_files):
    return sample_files["patterns-continents-214e8f67.md"]


def test_the_pattern_format_is_registered():
    assert GENERATORS[RepresentationFormat.pattern] is PatternGenerator


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


# --- the prefix, CSV and glossary files ---


def rows(text):
    return list(csv.DictReader(io.StringIO(text, newline="")))


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
