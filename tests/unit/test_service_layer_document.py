"""The application-profile document (DEC-7): overview, namespaces, a chapter per graph, caveats."""

from bs4 import BeautifulSoup

from fingerprint.adapters.template_renderer import JinjaTemplateRenderer
from fingerprint.domain.analytics import analyse
from fingerprint.service_layer.representations import make_generator
from tests.unit.fakes import EX, XSD, files, klass, literals, profile_run, prop

PREFIXES = {"ex": EX, "xsd": XSD}


def document(run):
    (text,) = files(make_generator("doc", analyse(run), JinjaTemplateRenderer(prefixes=PREFIXES)).serialize()).values()
    return BeautifulSoup(text, "html.parser")


def people(**kwargs):
    return profile_run(klass(EX + "Person", 50, prop(EX + "name", {1: 10}, literals(10)), observed=10), **kwargs)


def test_sections_and_class_table():
    soup = document(people())
    assert [s["id"] for s in soup.select("section[id]")][:2] == ["overview", "namespaces"]
    assert soup.find(id="caveats") is not None
    chapter = soup.select_one("section.graph")
    assert "default graph" in chapter.get_text(" ") and "@startuml" in chapter.find("pre").text
    headers = [th.text.strip() for th in chapter.find("table").find_all("th")]
    assert headers == ["Property", "Value types", "Cardinality", "Usage", "Inheritance"]
    row = [td.text.strip() for td in chapter.find("table").find("tbody").find("tr").find_all("td")]
    assert row[:4] == ["ex:name", "xsd:string", "1", "100 %"]


def test_samples_and_failures_are_flagged():
    failure = {"query_kind": "co_types", "class_iri": EX + "Big", "message": "class Big: not profiled after 2 attempts"}
    soup = document(people(failures=[failure]))
    caveats = soup.find(id="caveats").get_text(" ")
    assert "ex:Person" in caveats and "first 10 of 50" in caveats
    assert "not profiled after 2 attempts" in caveats
    assert "first 10 of 50" in soup.select_one("section.class").get_text(" ")


def test_iris_are_shown_as_text_and_unwritable_ones_are_listed():
    bad = "http://ex.org/<script>alert(1)</script> x"
    run = profile_run(klass("http://ex.org/q?a=1&b='x'", 4), klass(bad, 1))
    soup = document(run)
    assert soup.find("script") is None
    assert "http://ex.org/q?a=1&b='x'" in soup.get_text(" ")
    assert bad in soup.find(id="caveats").get_text(" ")


def test_overview_has_the_provenance():
    text = document(people()).find(id="overview").get_text(" ")
    assert "http://e/sparql" in text and "acceptance_threshold" in text
