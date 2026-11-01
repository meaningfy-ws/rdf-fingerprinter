"""The ShExC generator: the ShExC view laid out as text (profile-representations › Enriched ShExC output)."""

import logging

import pytest

from fingerprint.adapters.template_renderer import JinjaTemplateRenderer
from fingerprint.domain.analytics import analyse
from fingerprint.domain.views import GeneratorOptions, RepresentationFormat
from fingerprint.service_layer.generators import GENERATORS
from fingerprint.service_layer.generators.shex import ShexGenerator
from tests import builders
from tests.builders import klass, literals, profile_run, prop, resources
from tests.fakes import EX, files


def outputs(run, **options):
    generator = ShexGenerator(analyse(run), JinjaTemplateRenderer(), options=GeneratorOptions(**options))
    return files(generator.serialize()), generator


@pytest.fixture(scope="module")
def continents(sample_analytics):
    texts = files(ShexGenerator(sample_analytics, JinjaTemplateRenderer()).serialize())
    return next(t for name, t in texts.items() if name.startswith("shex-continents"))


def test_the_shex_format_is_registered():
    assert GENERATORS[RepresentationFormat.shex] is ShexGenerator


def test_the_file_holds_prefixes_then_the_legend_then_the_shapes_then_the_glossary(continents):
    lines = continents.splitlines()
    prefixes = [i for i, line in enumerate(lines) if line.startswith("PREFIX ")]
    assert prefixes == list(range(len(prefixes)))
    assert lines[len(prefixes)].startswith("# comments use the pattern schema's legend: k/n instances")
    assert lines[len(prefixes) + 1] == "# (:euvoc:Continent&skos:Concept) 6"
    assert lines[-1] == "# glossary: none"


def test_a_constraint_ends_in_a_semicolon_then_its_comment_and_a_group_closes_with_its_cardinality(continents):
    assert "bn\n    dcterms:created xsd:date ;  # =2014-10-10\n" in continents
    assert "\n  } ;\n" in continents
    assert "\n# (:skosxl:Label) 145\nskosxl:Label BNODE {\n" in continents


def test_a_constraint_without_comment_parts_has_no_hash():
    texts, _ = outputs(profile_run(klass(EX + "A", 5, prop(EX + "p", {1: 5}, resources(5)))))
    assert "  ex:p IRI ;\n" in only(texts)


def only(texts):
    (text,) = texts.values()
    return text


def test_the_hidden_line_follows_the_legend_when_classes_are_hidden():
    texts, _ = outputs(profile_run(klass(EX + "A", 5), klass(EX + "B", 1)), min_instances=2)
    lines = only(texts).splitlines()
    assert lines[lines.index("# hidden: 1 classes") - 1].startswith("# comments use")


def test_a_graph_whose_every_shape_is_dropped_still_gets_a_file_with_the_header_and_the_glossary():
    bad = "http://ex.org/q?a=1&b='x'"
    texts, _ = outputs(profile_run(klass(bad, 2)))
    lines = only(texts).splitlines()
    assert lines[-2:] == [f"# skipped: {bad}", "# glossary: none"] and not any(ln.endswith("{") for ln in lines)


def test_a_graph_with_no_shown_class_writes_no_file():
    texts, _ = outputs(profile_run())
    assert texts == {}


def test_a_class_iri_with_an_equals_sign_is_listed_after_the_hidden_line_and_warned_about(caplog):
    bad = "http://ex.org/q?a=1&b='x'"
    with caplog.at_level(logging.WARNING):
        texts, generator = outputs(profile_run(klass(bad, 2), klass(EX + "B", 1)), min_instances=2)
    lines = only(texts).splitlines()
    assert lines[lines.index("# hidden: 1 classes") + 1] == f"# skipped: {bad}"
    assert caplog.messages == [f"skipping {bad!r} in ShExC: PyShExC rejects '=' in an IRI"]
    assert generator.skipped == []


def test_the_iris_the_pattern_view_cannot_write_are_skipped_for_the_report():
    _, generator = outputs(profile_run(klass(EX + "bad iri", 2, prop(EX + "p", {1: 2}, literals(2))), klass(EX + "B", 2)))
    assert generator.skipped == [EX + "bad iri"]


def test_the_note_of_the_excluded_namespaces_follows_the_legend_and_is_absent_without_a_filter():
    def lines(analytics):
        texts = files(ShexGenerator(analytics, JinjaTemplateRenderer()).serialize())
        return next(iter(texts.values())).splitlines()

    noted = lines(builders.filtered_analytics("rel"))
    assert noted[noted.index(f"# excluded namespaces: {builders.REL_NOTE}") - 1].startswith("# comments use")
    assert not any("excluded namespaces" in line for line in lines(builders.filtered_analytics("foaf")))
