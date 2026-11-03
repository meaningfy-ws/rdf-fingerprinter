"""The report page main.html (fingerprint-report › Report content, › One self-contained page)."""

import pytest
from bs4 import BeautifulSoup

from fingerprint.adapters.template_renderer import JinjaTemplateRenderer
from fingerprint.domain.analytics import analyse
from fingerprint.domain.profile import Failure, QueryKind
from fingerprint.domain.views import GeneratorOptions
from fingerprint.service_layer.representations import make_generator
from tests.builders import filtered_analytics, klass, literals, profile_run, prop
from tests.fakes import EX, files


def document(run):
    (text,) = files(make_generator("doc", analyse(run), JinjaTemplateRenderer()).serialize()).values()
    return BeautifulSoup(text, "html.parser")


def people(**kwargs):
    return profile_run(klass(EX + "Person", 50, prop(EX + "name", {1: 10}, literals(10)), observed=10), **kwargs)


def test_iris_are_escaped_and_unwritable_ones_are_listed():
    bad = "http://ex.org/<script>alert(1)</script> x"
    run = profile_run(klass("http://ex.org/q?a=1&b='x'", 4), klass(bad, 1), klass("javascript:alert(1)", 1))
    soup = document(run)
    assert all("alert(1)" not in s.get_text() for s in soup.find_all("script"))
    assert not soup.select('a[href^="javascript:"]')
    assert bad in soup.find(id="caveats").get_text(" ")


# --- values the first tests left open (lean-test-suite 7.5) ---

OWL = "http://www.w3.org/2002/07/owl#"


def with_class(run, **update):
    """`run` with its first class updated."""
    graph = run.graphs[0]
    changed = graph.class_partitions[0].model_copy(update=update)
    return run.model_copy(update={"graphs": [graph.model_copy(update={"class_partitions": [changed]})]})


def generator_of(run):
    return make_generator("doc", analyse(run), JinjaTemplateRenderer())


def test_cardinality_is_the_label_present_or_a_dash():
    run = profile_run(
        klass(
            EX + "Person",
            4,
            prop(EX + "full", {1: 4}, literals(4)),
            prop(EX + "seen", presence_only=True),
            prop(EX + "none", {1: 2}, literals(2)),
        )
    )
    cells = {}
    for tr in document(run).select("details.cls tbody tr"):
        cells[tr.find("td").text.strip()] = tr.find_all("td")[9].text.strip()
    assert cells["ex:full"] == "exactly_one" and cells["ex:seen"] == "present"
    empty = document(profile_run(klass(EX + "Empty", 0, prop(EX + "p", {1: 2}, literals(2)))))
    assert empty.select_one("details.cls tbody tr").find_all("td")[9].text.strip() == "—"


@pytest.mark.parametrize(
    "shared, sampled, note",
    [(False, True, True), (True, True, False), (None, True, False), (False, False, False)],
)
def test_a_sample_is_flagged_when_its_queries_saw_different_instances(shared, sampled, note):
    run = people() if sampled else profile_run(klass(EX + "Person", 50))
    summary = document(with_class(run, sample_shared=shared)).select_one("details.cls summary .meta").text
    flag = " (sample may differ between queries)" if note else ""
    assert summary.strip() == f"{'50 instances, first 10 of 50' if sampled else '50 instances, exact'}{flag}"


def test_a_failure_row_names_graph_class_property_measurement_attempts_and_message():
    full = Failure(
        graph=EX + "g", class_iri=EX + "Big", property=EX + "p", query_kind=QueryKind.co_types, attempts=3, message="m1"
    )
    bare = Failure(query_kind=QueryKind.co_types, message="m2")
    soup = document(people(failures=[full, bare]))
    rows = [[td.text.strip() for td in tr.find_all("td")] for tr in soup.select("#collection tbody tr")][:2]
    assert rows[0] == ["ex:g", "ex:Big", "ex:p", "co_types", "3", "m1"]
    assert rows[1] == ["default graph", "—", "—", "co_types", "—", "m2"]


def test_subjects_without_a_type_are_a_caveat_per_graph():
    run = people()
    graph = run.graphs[0].model_copy(update={"untyped_subjects": 7, "graph": EX + "g"})
    other = run.graphs[0].model_copy(update={"untyped_subjects": 0, "graph": EX + "h"})
    items = [li.text for li in document(run.model_copy(update={"graphs": [graph, other]})).select("#caveats li")]
    assert [i for i in items if "rdf:type" in i] == ["ex:g: 7 subjects have no rdf:type, so no class section covers them."]


def test_hidden_namespaces_count_their_classes_and_fall_back_to_the_iri():
    run = profile_run(klass(EX + "A", 1), klass(OWL + "Class", 1), klass(OWL + "Thing", 1))
    soup = document(run.model_copy(update={"namespaces": []}))
    assert [li.text.strip() for li in soup.select("#caveats li")] == [f"{OWL}: 2 classes"]


def test_the_page_view_lists_the_skipped_iris_in_the_page_and_in_the_view():
    bad = EX + "a b"
    generator = generator_of(profile_run(klass(bad, 1), klass(EX + "A", 1)))
    ((_, view),) = generator.outputs()
    assert view.skipped == [bad] and view.caveats.skipped == [bad]


# --- namespace-filter: the report under the term filter (TC-D1) ---


def filtered_page(*exclude, run=None):
    """The document view and the page of the filter profile (or `run`) with `exclude`d namespaces."""
    generator = make_generator(
        "doc",
        filtered_analytics(*exclude, run=run),
        JinjaTemplateRenderer(),
        options=GeneratorOptions(exclude_namespaces=list(exclude)),
    )
    ((name, view),) = generator.outputs()
    (text,) = files(generator.serialize()).values()
    return view, BeautifulSoup(text, "html.parser")


def test_a_property_no_prefix_covers_has_no_prefix_and_no_switch():
    run = profile_run(klass(EX + "A", 1, prop("urn:x:p", {1: 1}, literals(1))))
    view, soup = filtered_page(run=run.model_copy(update={"namespaces": []}))
    assert [p.prefix for p in view.graphs[0].classes[0].properties] == [""]
    assert view.switches == [] and not soup.select("input[data-switch]")
