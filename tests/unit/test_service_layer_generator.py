"""The generator framework: visit hooks build a view, one file per graph or one in all (P-2, P-8, P-11)."""

import json
import logging

import pytest

from fingerprint.adapters.template_renderer import JinjaTemplateRenderer
from fingerprint.domain.analytics import analyse
from fingerprint.domain.generated.profile import ProfileRun
from fingerprint.service_layer.generators.generator import Generator, graph_slug

EX = "http://ex.org/"


def run(*classes, graph=None):
    graph_profile = {"class_partitions": list(classes)} | ({"graph": graph} if graph else {})
    return ProfileRun.model_validate({"endpoint": "http://e", "settings": {}, "graphs": [graph_profile]})


def klass(iri, *props):
    partitions = [{"property": p, "cardinality_histogram": [{"values_per_subject": 1, "subjects": 2}]} for p in props]
    return {
        "class_iri": iri,
        "instances": 2,
        "observed_instances": 2,
        "precision_mode": "exact",
        "property_partitions": partitions,
    }


def package(tmp_path, body):
    (tmp_path / "templates").mkdir()
    (tmp_path / "templates" / "out.txt").write_text(body)
    (tmp_path / "config.json").write_text(json.dumps({"template": "out.txt", "conf": {"title": "T"}}))
    return tmp_path


class Listing(Generator):
    """Lists classes and properties; enough to exercise the framework."""

    file_name = "list-{slug}.txt"

    def visit_class(self, graph, cls):
        return self.writable(cls.class_iri, {"iri": cls.class_iri})

    def visit_property(self, graph, cls, prop):
        return self.writable(prop.property, {"iri": prop.property})


BODY = "{% for c in view.graph.classes %}{{ c.iri }}:{% for p in c.properties %}{{ p.iri }},{% endfor %};{% endfor %}"


def listing(tmp_path, profile, body=BODY, **kwargs):
    return Listing(analyse(profile), JinjaTemplateRenderer(prefixes={}), template_location=package(tmp_path, body), **kwargs)


def test_view_is_sorted_by_iri(tmp_path):
    texts = listing(tmp_path, run(klass(EX + "B", EX + "q", EX + "p"), klass(EX + "A"))).serialize()
    assert texts == {"list-default.txt": f"{EX}A:;{EX}B:{EX}p,{EX}q,;"}


def test_a_hook_returning_none_drops_the_element_and_records_it(tmp_path, caplog):
    bad = "http://ex.org/<script> x"
    with caplog.at_level(logging.WARNING):
        generator = listing(tmp_path, run(klass(bad), klass(EX + "A", "http://ex.org/a b")))
        texts = generator.serialize()
    assert texts == {"list-default.txt": f"{EX}A:;"}
    assert generator.skipped == [bad, "http://ex.org/a b"] and bad in caplog.text


def test_custom_template_reads_its_configuration(tmp_path):
    texts = listing(tmp_path, run(klass(EX + "A")), body="{{ conf.title }}").serialize()
    assert texts == {"list-default.txt": "T"}


def test_write_puts_the_files_in_the_folder(tmp_path):
    out = tmp_path / "out"
    paths = listing(tmp_path, run(klass(EX + "A"))).write(out)
    assert [p.name for p in paths] == ["list-default.txt"]


@pytest.mark.parametrize(
    "graph, slug",
    [
        (None, "default"),
        ("http://publications.europa.eu/resources/authority/continents", "continents-"),
        ("http://ex.org/data/", "data-"),
        ("urn:x:Ünïcode Graph!", "n-code-graph-"),
        ("http://ex.org/#", "ex-org-"),
    ],
)
def test_graph_slug(graph, slug):
    result = graph_slug(graph)
    assert result.startswith(slug) and (graph is None or len(result) == len(slug) + 8)
