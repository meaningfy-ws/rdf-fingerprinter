"""The report page main.html (fingerprint-report › Report content, › One self-contained page)."""

import pytest
from bs4 import BeautifulSoup

from fingerprint.adapters.template_renderer import JinjaTemplateRenderer
from fingerprint.domain.analytics import analyse
from fingerprint.domain.profile import Failure, QueryKind
from fingerprint.domain.views import GeneratorOptions
from fingerprint.service_layer.representations import make_generator
from tests.builders import ORG, REL, REL_NOTE, filtered_analytics, klass, literals, profile_run, prop, with_namespaces
from tests.fakes import EX, files


def document(run):
    (text,) = files(make_generator("doc", analyse(run), JinjaTemplateRenderer()).serialize()).values()
    return BeautifulSoup(text, "html.parser")


def people(**kwargs):
    return profile_run(klass(EX + "Person", 50, prop(EX + "name", {1: 10}, literals(10)), observed=10), **kwargs)


def test_sections_and_class_table():
    soup = document(people())
    assert [s["id"] for s in soup.select("main > section[id]")][:2] == ["overview", "namespaces"]
    assert soup.find(id="collection") and soup.find(id="caveats")
    section = soup.select_one("details.cls")
    assert section["data-ns"] == "ex" and "ex:person" in section["data-q"]
    headers = [th.text.strip() for th in section.find("table").find_all("th")]
    assert headers[:3] == ["Property", "Subjects", "Min"] and headers[-1] == "Language coverage"
    row = [td.text.strip() for td in section.find("tbody").find("tr").find_all("td")]
    assert row[0] == "ex:name" and row[7] == "xsd:string"


def test_samples_and_failures_are_flagged():
    failure = Failure(query_kind=QueryKind.co_types, class_iri=EX + "Big", message="class Big: not profiled after 2 attempts")
    soup = document(people(failures=[failure]))
    assert "not profiled after 2 attempts" in soup.find(id="collection").get_text(" ")
    caveats = soup.find(id="caveats").get_text(" ")
    assert "ex:Person" in caveats and "first 10 of 50" in caveats
    assert "first 10 of 50" in soup.select_one("details.cls").get_text(" ")


def test_iris_are_escaped_and_unwritable_ones_are_listed():
    bad = "http://ex.org/<script>alert(1)</script> x"
    run = profile_run(klass("http://ex.org/q?a=1&b='x'", 4), klass(bad, 1), klass("javascript:alert(1)", 1))
    soup = document(run)
    assert all("alert(1)" not in s.get_text() for s in soup.find_all("script"))
    assert not soup.select('a[href^="javascript:"]')
    assert bad in soup.find(id="caveats").get_text(" ")


def test_overview_and_namespace_table():
    soup = document(people())
    assert "http://e/sparql" in soup.find(id="overview").get_text(" ")
    rows = [[td.text.strip() for td in tr.find_all("td")] for tr in soup.find(id="namespaces").select("tbody tr")]
    assert ["ex", EX, "packaged", "60"] in rows
    assert "acceptance_threshold" in soup.find(id="collection").get_text(" ")


def test_an_empty_graph_is_listed():
    soup = document(profile_run())
    assert "no typed instances" in soup.get_text(" ")


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


def test_parents_are_listed_in_iri_order_whatever_their_source():
    run = profile_run(
        klass(EX + "Person", 4, co_types=[(EX + "Agent", 4)]), klass(EX + "Zoo", 1), edges=[(EX + "Person", EX + "Zoo")]
    )
    (person,) = [c for c in document(run).select("details.cls") if "ex:person" in c["data-q"]]
    (parents,) = [m for m in person.select("span.meta") if m.text.strip().startswith("parents:")]
    assert parents.text.strip() == "parents: ex:Agent (implied), ex:Zoo (declared)"


@pytest.mark.parametrize(
    "shared, sampled, note",
    [(False, True, True), (True, True, False), (None, True, False), (False, False, False)],
)
def test_a_sample_is_flagged_when_its_queries_saw_different_instances(shared, sampled, note):
    run = people() if sampled else profile_run(klass(EX + "Person", 50))
    summary = document(with_class(run, sample_shared=shared)).select_one("details.cls summary .meta").text
    flag = " (sample may differ between queries)" if note else ""
    assert summary.strip() == f"{'50 instances, first 10 of 50' if sampled else '50 instances, exact'}{flag}"


def test_a_class_outside_the_prefix_table_has_no_prefix():
    run = people().model_copy(update={"namespaces": []})
    assert document(run).select_one("details.cls")["data-ns"] == ""


def test_a_failure_row_names_graph_class_property_measurement_attempts_and_message():
    full = Failure(
        graph=EX + "g", class_iri=EX + "Big", property=EX + "p", query_kind=QueryKind.co_types, attempts=3, message="m1"
    )
    bare = Failure(query_kind=QueryKind.co_types, message="m2")
    soup = document(people(failures=[full, bare]))
    rows = [[td.text.strip() for td in tr.find_all("td")] for tr in soup.select("#collection tbody tr")][:2]
    assert rows[0] == ["ex:g", "ex:Big", "ex:p", "co_types", "3", "m1"]
    assert rows[1] == ["default graph", "—", "—", "co_types", "—", "m2"]


def test_settings_are_listed_as_plain_text():
    soup = document(people(object_type_scope="any_graph"))
    settings = {tr.find_all("td")[0].text: tr.find_all("td")[1].text for tr in soup.select("#collection details tbody tr")}
    assert settings["object_type_scope"] == "any_graph"


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


def test_property_rows_carry_their_prefix_and_the_switches_list_the_prefixes_in_use():
    view, soup = filtered_page()
    rows = {p.iri: p.prefix for c in view.graphs[0].classes for p in c.properties}
    assert rows[EX + "name"] == "ex" and rows[REL + "r1"] == "rel"
    assert view.switches == ["ex", "org", "rdfs", "rel"]
    assert {tr["data-ns"] for tr in soup.select("details.cls tbody tr:not(.group)")} == {"ex", "rdfs", "rel"}
    assert [i["value"] for i in soup.select("input[data-switch]")] == view.switches


def test_a_property_no_prefix_covers_has_no_prefix_and_no_switch():
    run = profile_run(klass(EX + "A", 1, prop("urn:x:p", {1: 1}, literals(1))))
    view, soup = filtered_page(run=run.model_copy(update={"namespaces": []}))
    assert [p.prefix for p in view.graphs[0].classes[0].properties] == [""]
    assert view.switches == [] and not soup.select("input[data-switch]")


def test_the_excluded_namespace_keeps_its_uses_and_its_place_and_is_marked_in_the_table():
    view, soup = filtered_page("rel")
    plain, _ = filtered_page()
    assert [(p.prefix, p.uses) for p in view.namespaces] == [(p.prefix, p.uses) for p in plain.namespaces]
    assert {p.prefix: p.uses for p in view.namespaces}["rel"] == 2
    assert [p.prefix for p in view.namespaces if p.excluded] == ["rel"]
    assert [tr["data-prefix"] for tr in soup.select("#namespaces tr.excluded")] == ["rel"]
    assert "rel" not in view.switches and view.switches == ["ex", "org", "rdfs"]


def test_an_excluded_namespace_that_hides_nothing_is_not_marked():
    view, soup = filtered_page("foaf")
    assert not any(p.excluded for p in view.namespaces) and not soup.select("#namespaces tr.excluded")


def test_the_caveats_note_the_excluded_namespaces_of_each_graph():
    view, soup = filtered_page("rel")
    ((note,),) = [[(n.graph, n.note)] for n in view.caveats.excluded]
    assert note == (view.graphs[0].label, REL_NOTE)
    assert REL_NOTE in soup.find(id="caveats").get_text(" ")
    assert filtered_page()[0].caveats.excluded == []


def test_a_graph_whose_classes_are_all_excluded_is_not_empty():
    only_org = profile_run(klass(ORG + "Unit", 2, prop(ORG + "name", {1: 2}, literals(2))))
    view, soup = filtered_page("org", run=with_namespaces(only_org, ("org", ORG)))
    assert view.graphs[0].empty is False and view.graphs[0].classes == []
    assert "Every class of this graph is in a hidden or excluded namespace (see caveats)." in soup.get_text(" ")
    assert document(profile_run()).get_text(" ").count("no typed instances") == 1
