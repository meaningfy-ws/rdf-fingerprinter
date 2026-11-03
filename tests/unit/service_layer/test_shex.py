"""The ShExC generator: the ShExC view laid out as text (profile-representations › Enriched ShExC output)."""

import logging

import pytest

from fingerprint.adapters.template_renderer import JinjaTemplateRenderer
from fingerprint.domain.analytics import analyse
from fingerprint.domain.views import GeneratorOptions, RepresentationFormat
from fingerprint.service_layer.generators import GENERATORS
from fingerprint.service_layer.generators.shex import ShexGenerator
from tests.builders import klass, literals, profile_run, prop
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


def test_a_constraint_ends_in_a_semicolon_then_its_comment_and_a_group_closes_with_its_cardinality(continents):
    assert "bn\n    dcterms:created xsd:date ;  # =2014-10-10\n" in continents
    assert "\n  } ;\n" in continents
    assert "\n# (:skosxl:Label) 145\nskosxl:Label BNODE {\n" in continents


def only(texts):
    (text,) = texts.values()
    return text


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
