"""The representations service: load, re-analyse at a threshold, run generators in order (P-6, UC-W2)."""

import logging
import re
from pathlib import Path

import pytest

from fingerprint.adapters.exceptions import GeneratedOutputError
from fingerprint.adapters.profile_file import save_profile
from fingerprint.adapters.template_renderer import JinjaTemplateRenderer
from fingerprint.domain.profile import ValueCount
from fingerprint.domain.views import GeneratorOptions
from fingerprint.service_layer import representations
from fingerprint.service_layer.exceptions import UsageError
from fingerprint.service_layer.representations import (
    generate_from_profile_file,
    generate_representations,
    make_generator,
    validate_options,
    with_threshold,
)
from tests import builders


@pytest.fixture
def run(sample_run):
    return sample_run


class Recording:
    """A stand-in generator: records the analytics it was given, writes one file, or fails."""

    seen: list = []

    analyses: list = []

    def __init__(self, analytics, renderer, template_location=None, options=None):
        self.analytics, self.options = analytics, options

    def write(self, folder):
        Recording.analyses.append(self.analytics)
        Recording.seen.append((self.analytics.settings.acceptance_threshold, self.options))
        path = Path(folder) / f"ok-{len(Recording.seen)}"
        path.write_text("x")
        return [path]


class Failing(Recording):
    def write(self, folder):
        raise GeneratedOutputError("bad.ttl is not valid turtle")


@pytest.fixture
def generators(monkeypatch):
    Recording.seen, Recording.analyses = [], []
    monkeypatch.setattr(representations, "GENERATORS", {"a": Recording, "b": Failing, "c": Recording})


@pytest.mark.parametrize("threshold", [0, 1.5, -1])
def test_threshold_outside_the_range_is_a_usage_error(run, threshold):
    with pytest.raises(UsageError):
        with_threshold(run, threshold)


def test_generators_get_the_analytics_at_the_threshold(run, tmp_path, generators):
    options = GeneratorOptions(shapes_namespace="urn:x:")
    generate_representations(run, tmp_path, ["a"], threshold=0.6, options=options)
    assert Recording.seen == [(0.6, options)]


def test_an_unknown_format_is_a_usage_error(run, tmp_path, generators):
    with pytest.raises(UsageError, match="void"):
        generate_representations(run, tmp_path, ["void"])


def test_a_missing_output_folder_is_a_usage_error(run, tmp_path, generators):
    path = save_profile(run, tmp_path)
    with pytest.raises(UsageError, match="not an existing folder"):
        generate_from_profile_file(path, tmp_path / "nowhere", ["a"])


# --- usage errors and the namespace table (lean-test-suite 7.5) ---


class Namespaces(Recording):
    """Remembers the namespace table of the analytics it was given."""

    tables: list = []

    def write(self, folder):
        Namespaces.tables.append(self.analytics.namespaces)
        return []


@pytest.mark.parametrize("size", [1, 5, None])
def test_a_module_size_of_one_or_more_is_accepted(size):
    validate_options(GeneratorOptions(module_size=size))


def test_a_module_size_below_one_is_a_usage_error_even_when_built_around_the_model():
    with pytest.raises(UsageError) as error:
        validate_options(GeneratorOptions.model_construct(module_size=0))
    assert str(error.value) == "--module-size must be at least 1"


def test_bad_options_stop_before_any_generator_runs(run, tmp_path, generators):
    with pytest.raises(UsageError, match="--shapes-namespace 'urn:x y<' cannot be written as an IRI"):
        generate_representations(run, tmp_path, ["a"], options=GeneratorOptions(shapes_namespace="urn:x y<"))
    assert Recording.seen == []


def test_a_generator_refusing_its_namespace_is_a_usage_error(sample_analytics):
    with pytest.raises(UsageError) as error:
        make_generator("shacl", sample_analytics, JinjaTemplateRenderer(), None, GeneratorOptions(shapes_namespace="urn:x y<"))
    assert str(error.value) == "'urn:x y<' cannot be written as an IRI"


def test_unknown_formats_are_all_named_with_the_known_ones(run, tmp_path, generators):
    with pytest.raises(UsageError) as error:
        generate_representations(run, tmp_path, ["a", "void", "nope"])
    assert str(error.value) == "unknown formats: void, nope (known: a, b, c)"


@pytest.fixture
def filter_run():
    return builders.filter_profile(
        builders.klass(builders.EX + "Agent", 5, builders.prop(builders.EX + "name", {1: 5}, builders.literals(5))),
        builders.klass(builders.REL + "Base", 5, builders.prop(builders.EX + "name", {1: 5}, builders.literals(5))),
        edges=[(builders.EX + "Agent", builders.REL + "Base")],
    )


def test_an_exclude_value_whose_only_term_is_the_one_value_of_a_property_is_not_warned_about(tmp_path, generators, caplog):
    hub = builders.prop(builders.EX + "hub", {1: 2}, builders.resources(2)).model_copy(
        update={"distinct_objects": 1, "top_values": [ValueCount(value=builders.FOAF + "x", triples=2)]}
    )
    run = builders.filter_profile(builders.klass(builders.EX + "Thing", 2, hub))
    with caplog.at_level(logging.WARNING):
        generate_representations(run, tmp_path, ["a"], options=GeneratorOptions(exclude_namespaces=["foaf"]))
    assert caplog.messages == []
    assert [(t.namespace, t.values) for t in Recording.analyses[-1].graphs[0].excluded_terms] == [(builders.FOAF, 1)]


def test_the_inherited_property_is_left_out_of_the_diagram_box_with_or_without_the_exclusion(filter_run, tmp_path):
    for exclude in ([], ["rel"]):
        out = tmp_path / f"out{len(exclude)}"
        out.mkdir()
        generate_representations(filter_run, out, ["puml"], options=GeneratorOptions(exclude_namespaces=exclude))
        text = "\n".join(p.read_text() for p in out.iterdir())
        agent = re.search(r'class "ex:Agent" as \w+ \{(.*?)\n\}', text, re.S)
        assert agent is not None and "ex:name" not in agent.group(1)


# --- llm-schema-tools: the ontology and the size filters (TC-G1) ---

SKOS = "http://www.w3.org/2004/02/skos/core#"


@pytest.mark.parametrize("name", ["min_instances", "max_classes"])
def test_a_size_filter_below_one_is_a_usage_error_even_when_built_around_the_model(name):
    with pytest.raises(UsageError) as error:
        validate_options(GeneratorOptions.model_construct(**{name: 0}))
    assert str(error.value) == f"--{name.replace('_', '-')} must be at least 1"


def test_diagram_descriptions_match_the_files_written_in_order_and_write_nothing(tmp_path):
    from tests.builders import klass, profile_run
    from tests.fakes import EX

    run = profile_run(klass(EX + "A", 1), klass("http://xmlns.com/foaf/0.1/Agent", 1), graph="http://example.org/g/one")
    described = representations.describe_diagrams(run, tmp_path)
    assert list(tmp_path.iterdir()) == []
    written = generate_representations(run, tmp_path, ["puml"])
    assert [Path(d.path) for d in described] == written
    assert {d.graph for d in described} == {"http://example.org/g/one"}
    assert [(d.kind, d.module) for d in described] == [("overview", None), ("module", "ex"), ("module", "foaf")]


def test_a_default_graph_diagram_is_described_with_no_graph(tmp_path):
    from tests.builders import klass, profile_run
    from tests.fakes import EX

    described = representations.describe_diagrams(profile_run(klass(EX + "A", 1)), tmp_path)
    assert [d.graph for d in described] == [None, None]


def test_describing_diagrams_checks_the_threshold_and_the_options_like_generating_them(tmp_path):
    from tests.builders import klass, profile_run
    from tests.fakes import EX

    run = profile_run(klass(EX + "A", 1))
    with pytest.raises(UsageError):
        representations.describe_diagrams(run, tmp_path, threshold=2)
    with pytest.raises(UsageError, match="--module-size must be at least 1"):
        representations.describe_diagrams(run, tmp_path, options=GeneratorOptions.model_construct(module_size=0))
