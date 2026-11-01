"""The representations service: load, re-analyse at a threshold, run generators in order (P-6, UC-W2)."""

import logging
import re
from pathlib import Path

import pytest

from fingerprint.adapters.exceptions import GeneratedOutputError
from fingerprint.adapters.profile_file import save_profile
from fingerprint.adapters.template_renderer import JinjaTemplateRenderer
from fingerprint.domain.profile import Inheritance, NamespacePrefix
from fingerprint.domain.views import GeneratorOptions
from fingerprint.service_layer import representations
from fingerprint.service_layer.exceptions import UsageError
from fingerprint.service_layer.prefixes import resolve_namespaces
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


def test_with_threshold_changes_only_the_threshold(run):
    changed = with_threshold(run, 0.5)
    assert changed.settings.acceptance_threshold == 0.5 and changed.graphs == run.graphs
    assert run.settings.acceptance_threshold == 0.95


@pytest.mark.parametrize("threshold", [0, 1.5, -1])
def test_threshold_outside_the_range_is_a_usage_error(run, threshold):
    with pytest.raises(UsageError):
        with_threshold(run, threshold)


def test_generators_get_the_analytics_at_the_threshold(run, tmp_path, generators):
    options = GeneratorOptions(shapes_namespace="urn:x:")
    generate_representations(run, tmp_path, ["a"], threshold=0.6, options=options)
    assert Recording.seen == [(0.6, options)]


def test_formats_run_in_order_and_a_failure_keeps_earlier_ones(run, tmp_path, generators):
    with pytest.raises(GeneratedOutputError):
        generate_representations(run, tmp_path, ["a", "b", "c"])
    assert [p.name for p in tmp_path.iterdir()] == ["ok-1"]


def test_an_unknown_format_is_a_usage_error(run, tmp_path, generators):
    with pytest.raises(UsageError, match="void"):
        generate_representations(run, tmp_path, ["void"])


def test_from_a_profile_file(run, tmp_path, generators):
    path = save_profile(run, tmp_path)
    out = tmp_path / "out"
    out.mkdir()
    assert [p.name for p in generate_from_profile_file(path, out, ["a"])] == ["ok-1"]


def test_an_unusable_profile_file_is_a_usage_error(tmp_path, generators):
    with pytest.raises(UsageError, match="missing.json"):
        generate_from_profile_file(tmp_path / "missing.json", tmp_path, ["a"])


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


@pytest.fixture
def namespaced(monkeypatch):
    Namespaces.tables = []
    monkeypatch.setattr(representations, "GENERATORS", {"a": Namespaces})


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


def test_a_run_without_a_namespace_table_gets_one_and_a_user_table_is_applied(run, tmp_path, namespaced):
    assert run.namespaces is None
    generate_representations(run, tmp_path, ["a"])
    resolved = resolve_namespaces(run)
    assert Namespaces.tables[-1] == resolved.namespaces
    mine = [NamespacePrefix(prefix="mine", namespace=resolved.namespaces[0].namespace, source="user")]
    generate_representations(resolved, tmp_path, ["a"], user_prefixes=mine)
    assert "mine" in {e.prefix for e in Namespaces.tables[-1]}
    generate_representations(resolved, tmp_path, ["a"])
    assert Namespaces.tables[-1] == resolved.namespaces


@pytest.fixture
def filtering(filter_run, tmp_path, generators):
    """Runs `generate_representations` on the filter profile with a recording generator, returning what it saw."""

    def generate(exclude=(), include=(), **kwargs):
        options = GeneratorOptions(exclude_namespaces=list(exclude), include_namespaces=list(include))
        generate_representations(filter_run, tmp_path, ["a"], options=options, **kwargs)
        return Recording.analyses[-1]

    return generate


@pytest.fixture
def filter_run():
    return builders.filter_profile(
        builders.klass(builders.EX + "Agent", 5, builders.prop(builders.EX + "name", {1: 5}, builders.literals(5))),
        builders.klass(builders.REL + "Base", 5, builders.prop(builders.EX + "name", {1: 5}, builders.literals(5))),
        edges=[(builders.EX + "Agent", builders.REL + "Base")],
    )


@pytest.mark.parametrize(
    "option, message",
    [
        ("include_namespaces", "--include-namespace nope: no such namespace; ignored"),
        ("exclude_namespaces", "--exclude-namespace nope: no such namespace; ignored"),
    ],
)
def test_an_unknown_namespace_filter_is_warned_about_once_and_named_by_its_option(
    option, message, filter_run, tmp_path, generators, caplog
):
    options = GeneratorOptions(**{option: ["nope", "nope"]})
    with caplog.at_level(logging.WARNING):
        generate_representations(filter_run, tmp_path, ["a"], options=options)
    assert caplog.messages == [message]


def test_a_filter_naming_a_prefix_or_namespace_of_the_table_is_not_unknown(filtering, caplog):
    with caplog.at_level(logging.WARNING):
        filtering(include=["ex"], exclude=[builders.REL])
    assert caplog.messages == []


def test_an_exclude_value_that_hides_nothing_is_warned_about_once(filtering, caplog):
    with caplog.at_level(logging.WARNING):
        filtering(exclude=["foaf", "foaf", "rel"])
    assert caplog.messages == ["--exclude-namespace foaf: no term in this namespace; ignored"]


def test_an_exclude_value_fully_re_included_is_not_warned_about(filtering, caplog):
    with caplog.at_level(logging.WARNING):
        filtering(exclude=["foaf"], include=["foaf"])
    assert caplog.messages == []


def test_an_exclude_value_with_one_namespace_that_hides_something_is_not_warned_about(filtering, caplog):
    with caplog.at_level(logging.WARNING):
        filtering(exclude=["*o*"])  # foaf (no term) and org (a class)
    assert caplog.messages == []


def test_an_exclude_value_whose_terms_sit_under_an_excluded_class_is_not_warned_about(tmp_path, generators, caplog):
    # rel's two properties are on ex:Person, which ex removes: rel has uses but no counted term
    options = GeneratorOptions(exclude_namespaces=["ex", "rel"])
    with caplog.at_level(logging.WARNING):
        generate_representations(builders.filter_profile(), tmp_path, ["a"], options=options)
    assert caplog.messages == []


def test_no_warning_is_made_when_the_caller_asks_for_none(filtering, caplog):
    with caplog.at_level(logging.WARNING):
        filtering(exclude=["nope", "foaf"], check_filters=False)
    assert caplog.messages == []


def test_the_filters_are_warned_about_before_any_format_runs(filter_run, tmp_path, generators, caplog):
    with caplog.at_level(logging.WARNING), pytest.raises(GeneratedOutputError):
        generate_representations(filter_run, tmp_path, ["a", "b"], options=GeneratorOptions(exclude_namespaces=["nope"]))
    assert caplog.messages == ["--exclude-namespace nope: no such namespace; ignored"]


def test_a_run_without_a_namespace_table_is_filtered_by_the_resolved_one(run, tmp_path, generators):
    assert run.namespaces is None
    generate_representations(run, tmp_path, ["a"], options=GeneratorOptions(exclude_namespaces=["skos"]))
    graph = Recording.analyses[-1].graphs[0]
    assert [t.namespace for t in graph.excluded_terms] == [SKOS]


def test_the_excluded_terms_are_noted_on_each_graph_and_nothing_excluded_gives_none(filtering):
    graphs = filtering(exclude=["rel"]).graphs
    assert [(t.namespace, t.properties) for t in graphs[0].excluded_terms] == [(builders.REL, 2)]
    assert filtering().graphs[0].excluded_terms == []


def test_an_excluded_term_s_ontology_label_does_not_reach_the_generators(run, tmp_path, generators):
    options = GeneratorOptions(ontology=str(LABELS), exclude_namespaces=["skos"])
    generate_representations(run, tmp_path, ["a"], options=options)
    assert all(a.term != CONCEPT for g in Recording.analyses[-1].graphs for a in g.term_annotations)
    generate_representations(run, tmp_path, ["a"], options=GeneratorOptions(ontology=str(LABELS)))
    assert any(a.term == CONCEPT for g in Recording.analyses[-1].graphs for a in g.term_annotations)


def test_a_property_inherited_from_an_excluded_parent_stays_inherited(filtering):
    agent = next(c for c in filtering(exclude=["rel"]).graphs[0].class_partitions if c.class_iri.endswith("Agent"))
    assert [(p.property, p.inheritance) for p in agent.property_partitions] == [(builders.EX + "name", Inheritance.inherited)]


def test_the_inherited_property_is_left_out_of_the_diagram_box_with_or_without_the_exclusion(filter_run, tmp_path):
    for exclude in ([], ["rel"]):
        out = tmp_path / f"out{len(exclude)}"
        out.mkdir()
        generate_representations(filter_run, out, ["puml"], options=GeneratorOptions(exclude_namespaces=exclude))
        text = "\n".join(p.read_text() for p in out.iterdir())
        agent = re.search(r'class "ex:Agent" as \w+ \{(.*?)\n\}', text, re.S)
        assert agent is not None and "ex:name" not in agent.group(1)


# --- llm-schema-tools: the ontology and the size filters (TC-G1) ---

LABELS = Path(__file__).parents[2] / "test_data" / "ontology" / "labels.ttl"
SKOS = "http://www.w3.org/2004/02/skos/core#"
CONCEPT = SKOS + "Concept"


@pytest.mark.parametrize("name", ["min_instances", "max_classes"])
def test_a_size_filter_below_one_is_a_usage_error_even_when_built_around_the_model(name):
    with pytest.raises(UsageError) as error:
        validate_options(GeneratorOptions.model_construct(**{name: 0}))
    assert str(error.value) == f"--{name.replace('_', '-')} must be at least 1"


def test_without_an_ontology_the_run_is_unchanged(run):
    assert representations.with_ontology(run, None) is run


def test_an_ontology_label_is_added_to_every_graph_s_annotations(run):
    labelled = representations.with_ontology(run, LABELS)
    for graph in labelled.graphs:
        concept = next(a for a in graph.term_annotations if a.term == CONCEPT)
        assert [t.text for t in concept.labels] == ["Concept"]


def test_an_unreadable_ontology_is_a_usage_error_naming_the_file(run, tmp_path, generators):
    bad = tmp_path / "bad.ttl"
    bad.write_text("this is not turtle")
    with pytest.raises(UsageError, match="bad.ttl"):
        generate_representations(run, tmp_path, ["a"], options=GeneratorOptions(ontology=str(bad)))
    assert not Recording.seen
