"""The pattern schema generator: the pattern view laid out as text (profile-representations › Pattern schema output)."""

import pytest

from fingerprint.adapters.template_renderer import JinjaTemplateRenderer
from fingerprint.domain.analytics import analyse
from fingerprint.domain.views import GeneratorOptions, RepresentationFormat
from fingerprint.service_layer.generators import GENERATORS
from fingerprint.service_layer.generators.generator import plain_label
from fingerprint.service_layer.generators.pattern import PatternGenerator
from tests.builders import klass, literals, profile_run, prop
from tests.fakes import EX, files


def outputs(run, **options):
    generator = PatternGenerator(analyse(run), JinjaTemplateRenderer(), options=GeneratorOptions(**options))
    return files(generator.serialize()), generator


@pytest.fixture(scope="module")
def continents(sample_analytics):
    texts = files(PatternGenerator(sample_analytics, JinjaTemplateRenderer()).serialize())
    return next(t for name, t in texts.items() if name.startswith("pattern-continents"))


def test_the_pattern_format_is_registered():
    assert GENERATORS[RepresentationFormat.pattern] is PatternGenerator


def test_one_file_per_graph_named_by_its_slug(sample_analytics):
    texts = files(PatternGenerator(sample_analytics, JinjaTemplateRenderer()).serialize())
    assert sorted(texts) == ["pattern-continents-214e8f67.txt", "pattern-default.txt", "pattern-treaties-3b4301a8.txt"]


def test_the_file_holds_prefixes_then_the_legend_then_blocks_then_the_glossary(continents):
    lines = continents.splitlines()
    prefixes = [i for i, line in enumerate(lines) if line.startswith("PREFIX ")]
    names = [lines[i].split()[1] for i in prefixes]
    legend = next(i for i, line in enumerate(lines) if line.startswith("# (:A&B) n: classes"))
    first_block = next(i for i, line in enumerate(lines) if line.startswith("(:"))
    assert prefixes == list(range(len(prefixes))) and legend == len(prefixes) < first_block
    assert lines[-1] == "# glossary: none" and names == sorted(names)


def test_the_blocks_are_the_view_s_header_and_edge_texts_indented_by_depth(continents):
    assert "\n(:euvoc:Continent&skos:Concept) 6\n  -dcterms:created-> xsd:date =2014-10-10\n" in continents
    assert "\n    -lvont:script-> IRI 12/145 d2\n" in continents
    assert "\n  -skosxl:prefLabel-> (:skosxl:Label) bn ^\n" in continents  # the edge's ending is printed once


def test_the_hidden_line_is_written_only_when_classes_are_hidden():
    texts, _ = outputs(
        profile_run(klass(EX + "A", 5, prop(EX + "p", {1: 5}, literals(5))), klass(EX + "B", 1)), min_instances=2
    )
    (text,) = texts.values()
    assert "# hidden: 1 classes\n" in text
    plain, _ = outputs(profile_run(klass(EX + "A", 5, prop(EX + "p", {1: 5}, literals(5)))))
    assert "# hidden" not in next(iter(plain.values()))


def test_a_graph_with_no_shown_class_writes_no_file():
    texts, _ = outputs(profile_run())
    assert texts == {}


def test_a_named_graph_is_labelled_in_plain_characters():
    (view,) = PatternGenerator(analyse(profile_run(klass(EX + "A", 1), graph=EX + "g")), JinjaTemplateRenderer()).views()
    assert view.graph_label == plain_label(EX + "g")
