"""The generator framework: visit hooks build a view, one file per graph or one in all (P-2, P-8, P-11)."""

import json
import logging
import re

import pytest

from fingerprint import config
from fingerprint.adapters.template_renderer import JinjaTemplateRenderer
from fingerprint.domain.analytics import analyse
from fingerprint.domain.namespace_filter import META_NAMESPACES
from fingerprint.domain.views import GeneratorOptions, NodeShape, OutputCheck, PropertyShape, ShapesGraph
from fingerprint.domain.vocabulary import RDFS
from fingerprint.service_layer.generators.generator import Generator, graph_slug, plain_label
from tests import builders
from tests.builders import profile_run
from tests.fakes import files

EX = "http://ex.org/"


def run(*classes, graph=None):
    return profile_run(*classes, graph=graph)


def klass(iri, *props):
    return builders.klass(iri, 2, *(builders.prop(p, {1: 2}) for p in props))


def package(tmp_path, body):
    (tmp_path / "templates").mkdir()
    (tmp_path / "templates" / "out.txt").write_text(body)
    (tmp_path / "config.json").write_text(json.dumps({"template": "out.txt", "conf": {"title": "T"}}))
    return tmp_path


class Listing(Generator):
    """Lists classes and properties as shapes; enough to exercise the framework."""

    file_name = "list-{slug}.txt"

    def visit_class(self, graph, cls):
        return self.accepts(cls.class_iri)

    def visit_property(self, graph, cls, prop):
        return (
            PropertyShape(shape=prop.property, path=prop.property, severity="violation")
            if self.accepts(prop.property)
            else None
        )

    def end_class(self, graph, cls, properties):
        return NodeShape(shape=cls.class_iri, target=cls.class_iri, property_shapes=properties)

    def end_graph(self, graph, classes):
        return ShapesGraph(graph_label="g", slug=graph_slug(graph.graph), node_shapes=classes)


BODY = "{% for c in view.node_shapes %}{{ c.target }}:{% for p in c.property_shapes %}{{ p.path }},{% endfor %};{% endfor %}"


def listing(tmp_path, profile, body=BODY, **kwargs):
    return Listing(analyse(profile), JinjaTemplateRenderer(), template_location=package(tmp_path, body), **kwargs)


def test_view_is_sorted_by_iri(tmp_path):
    texts = files(listing(tmp_path, run(klass(EX + "B", EX + "q", EX + "p"), klass(EX + "A"))).serialize())
    assert texts == {"list-default.txt": f"{EX}A:;{EX}B:{EX}p,{EX}q,;"}


def test_a_hook_returning_none_drops_the_element_and_records_it(tmp_path, caplog):
    bad = "http://ex.org/<script> x"
    with caplog.at_level(logging.WARNING):
        generator = listing(tmp_path, run(klass(bad), klass(EX + "A", "http://ex.org/a b")))
        texts = files(generator.serialize())
    assert texts == {"list-default.txt": f"{EX}A:;"}
    assert generator.skipped == [bad, "http://ex.org/a b"]
    assert caplog.messages == [
        f"skipping {bad!r}: it cannot be written as an IRI",
        "skipping 'http://ex.org/a b': it cannot be written as an IRI",
    ]


def test_custom_template_reads_its_configuration(tmp_path):
    texts = files(listing(tmp_path, run(klass(EX + "A")), body="{{ conf.title }}").serialize())
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


# --- what the framework hands the renderer and how it walks (lean-test-suite 7.5) ---


class Recorder:
    """A renderer port that records what the generator asked for."""

    def __init__(self):
        self.calls = []

    def render(self, package, outputs, **kwargs):
        self.calls.append(("render", package, list(outputs), kwargs))
        return []

    def make(self, package, outputs, **kwargs):
        self.calls.append(("make", package, list(outputs), kwargs))
        return []


class Escaping(Listing):
    autoescape = True
    check = OutputCheck.turtle


def graphs(*runs):
    """One run with the graphs of all `runs`, in order."""
    return runs[0].model_copy(update={"graphs": [g for r in runs for g in r.graphs]})


def test_the_renderer_gets_the_package_the_prefix_table_and_the_generators_settings(tmp_path):
    renderer, location = Recorder(), tmp_path / "pkg"
    generator = Escaping(analyse(run(klass(EX + "A"))), renderer, template_location=location)
    generator.serialize()
    generator.write(tmp_path / "out")
    (kind, package, outputs, kwargs), (make_kind, make_package, make_outputs, make_kwargs) = renderer.calls
    assert (kind, package, [name for name, _ in outputs]) == ("render", location, ["list-default.txt"])
    assert kwargs == {"conf": {}, "autoescape": True, "prefixes": generator.table}
    assert (make_kind, make_package, make_outputs) == ("make", location, outputs)
    assert make_kwargs == {
        "folder": tmp_path / "out",
        "conf": {},
        "check": OutputCheck.turtle,
        "autoescape": True,
        "prefixes": generator.table,
    }


class Walker(Listing):
    """Skips the graph g1 and records the graph each hook is given."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.seen = []

    def visit_graph(self, graph):
        return graph.graph != EX + "g1"

    def visit_class(self, graph, cls):
        self.seen.append(("class", graph.graph))
        return super().visit_class(graph, cls)

    def visit_property(self, graph, cls, prop):
        self.seen.append(("property", graph.graph))
        return super().visit_property(graph, cls, prop)


def test_the_walk_goes_on_past_a_skipped_graph_and_a_graph_without_shown_classes():
    owl = "http://www.w3.org/2002/07/owl#"
    g1 = run(klass(EX + "A"), graph=EX + "g1")
    g2 = run(klass(owl + "Class"), klass(owl + "Thing"), graph=EX + "g2")
    g3 = run(klass(EX + "B", EX + "p"), graph=EX + "g3")
    generator = Walker(analyse(graphs(g1, g2, g3)), Recorder())
    names = [name for name, _ in generator.outputs()]
    assert len(names) == 1 and names[0].startswith("list-g3-")
    assert generator.seen == [("class", EX + "g3"), ("property", EX + "g3")]
    assert generator.hidden == {owl: {owl + "Class", owl + "Thing"}}


@pytest.mark.parametrize(
    "iri, namespace",
    [
        (EX + "deep/Thing", EX),  # the table's own namespace wins over the IRI's own split
        ("http://other.org/a/B", "http://other.org/a/"),
        ("http://other.org/a#B", "http://other.org/a#"),
    ],
)
def test_namespace_is_the_tables_or_the_iris_own(iri, namespace):
    assert Listing(analyse(run(klass(EX + "A"))), Recorder()).namespace(iri) == namespace


def test_a_format_without_a_document_writes_nothing():
    class Whole(Generator):
        per_graph = False
        file_name = "all.txt"

    assert Whole(analyse(run(klass(EX + "A"))), Recorder()).outputs() == []


def test_every_file_lists_every_iri_skipped_in_any_graph():
    bad_a, bad_b = EX + "a b", EX + "c d"
    first = run(klass(bad_a), klass(EX + "A"), graph=EX + "g1")
    second = run(klass(bad_b), klass(EX + "B"), graph=EX + "g2")
    generator = Listing(analyse(graphs(first, second)), Recorder())
    outputs = generator.outputs()
    assert [view.skipped for _, view in outputs] == [[bad_a, bad_b]] * 2 and len(outputs) == 2


@pytest.mark.parametrize(
    "graph, pattern",
    [
        ("///", r"graph-[0-9a-f]{8}"),  # no name at all
        ("http://ex.org/" + "a" * 50, r"a{40}-[0-9a-f]{8}"),  # at most 40 readable characters
        ("http://ex.org/--Ünï--", r"n-[0-9a-f]{8}"),  # file-safe, no edge dashes
        ("urn:x:A_B c", r"a-b-c-[0-9a-f]{8}"),
    ],
)
def test_graph_slug_is_readable_and_file_safe(graph, pattern):
    assert re.fullmatch(pattern, graph_slug(graph))


def test_a_graph_label_keeps_only_plain_characters():
    assert plain_label('http://g/%getenv("HOME")\n!x') == "http://g/_getenv__HOME____x"
    assert plain_label(None) == config.default_graph_label


def test_a_hook_left_alone_keeps_every_class():
    class Bare(Generator):
        file_name = "bare-{slug}.txt"

        def end_class(self, graph, cls, properties):
            return NodeShape(shape=cls.class_iri, target=cls.class_iri)

        def end_graph(self, graph, classes):
            return ShapesGraph(graph_label="g", slug="s", node_shapes=classes)

    ((_, view),) = Bare(analyse(run(klass(EX + "A"), klass(EX + "B"))), Recorder()).outputs()
    assert [c.target for c in view.node_shapes] == [EX + "A", EX + "B"]


# --- namespace-filter: a Generator built directly hides what the filter names, class by class (TC-G1) ---


def test_a_generator_built_directly_hides_the_meta_and_the_excluded_namespaces():
    profile = builders.filter_profile()
    analytics = analyse(profile)
    plain = Listing(analytics, JinjaTemplateRenderer())
    excluded = Listing(analytics, JinjaTemplateRenderer(), options=GeneratorOptions(exclude_namespaces=["org"]))
    assert plain.excluded == set(META_NAMESPACES)
    assert excluded.excluded == set(META_NAMESPACES) | {builders.ORG}
    assert [(c.target) for c in excluded.view()[0].node_shapes] == [builders.EX + "Person"]


def test_a_meta_namespace_included_is_no_longer_hidden():
    generator = Listing(
        analyse(builders.filter_profile()), JinjaTemplateRenderer(), options=GeneratorOptions(include_namespaces=["rdfs"])
    )
    assert generator.excluded == set(META_NAMESPACES) - {RDFS}
