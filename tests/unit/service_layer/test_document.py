"""The report page main.html (fingerprint-report › Report content, › One self-contained page)."""

from bs4 import BeautifulSoup

from fingerprint.adapters.template_renderer import JinjaTemplateRenderer
from fingerprint.domain.analytics import analyse
from fingerprint.domain.profile import Failure, QueryKind
from fingerprint.service_layer.representations import make_generator
from tests.builders import klass, literals, profile_run, prop
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
    assert ["ex", EX, "packaged"] in rows
    assert "acceptance_threshold" in soup.find(id="collection").get_text(" ")


def test_an_empty_graph_is_listed():
    soup = document(profile_run())
    assert "no typed instances" in soup.get_text(" ")
