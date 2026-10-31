import logging

from bs4 import BeautifulSoup
from rdflib import Literal

from fingerprint.adapters.sparql import QueryTimeout
from fingerprint.domain.analytics import analyse
from fingerprint.domain.profile import ProfileRun
from fingerprint.service_layer import handlers
from fingerprint.service_layer.report import render_report
from fingerprint.service_layer.settings import resolve_settings
from tests.unit.fakes import FakeSparql

EX = "http://example.org/"
SKOS = "http://www.w3.org/2004/02/skos/core#"


def analytics(**overrides):
    raw = {
        "endpoint": "http://localhost:1/unreachable",
        "settings": {"first_n": 10000},
        "graphs": [
            {
                "class_partitions": [
                    {
                        "class_iri": SKOS + "Concept",
                        "instances": 120,
                        "observed_instances": 120,
                        "precision_mode": "exact",
                        "property_partitions": [
                            {
                                "property": SKOS + "prefLabel",
                                "cardinality_histogram": [{"values_per_subject": 1, "subjects": 120}],
                            }
                        ],
                    },
                    {
                        "class_iri": EX + "Big",
                        "instances": 50000,
                        "observed_instances": 10000,
                        "precision_mode": "first_n",
                        "sample_shared": False,
                    },
                ]
            },
            {"graph": EX + "g"},
        ],
        **overrides,
    }
    return analyse(ProfileRun.model_validate(raw))


def rendered(tmp_path, profile, **kwargs):
    path = render_report(profile, tmp_path, **kwargs)
    return path, BeautifulSoup(path.read_text(), "html.parser")


def test_renders_without_querying_an_endpoint(tmp_path):
    path, soup = rendered(tmp_path, analytics())
    assert path == tmp_path / "main.html"
    assert soup.find("h1", attrs={"id": "skip-toc"}).text == "Structural fingerprint"


def test_precision_per_class_and_prefixed_iris(tmp_path):
    text = rendered(tmp_path, analytics())[1].get_text(" ")
    assert "skos:Concept" in text and "skos:prefLabel" in text
    assert "exact" in text
    assert "first 10000 of 50000" in text
    assert "sample may differ between queries" in text


def test_class_table_columns(tmp_path):
    soup = rendered(tmp_path, analytics())[1]
    headers = [th.text.strip() for th in soup.find("table", class_="class-profile").find_all("th")]
    assert headers == [
        "Property",
        "Subjects",
        "Min",
        "Max",
        "Avg",
        "Kind",
        "Distinct values",
        "Value types",
        "Confidence",
        "Cardinality",
        "Inheritance",
        "Language coverage",
    ]


def test_absent_values_are_a_dash(tmp_path):
    soup = rendered(tmp_path, analytics())[1]
    row = [td.text.strip() for td in soup.find("table", class_="class-profile").find("tbody").find("tr").find_all("td")]
    assert row[5] == "—" and row[6] == "—"


def test_failures_and_settings_are_reported(tmp_path):
    failure = {"query_kind": "co_types", "class_iri": EX + "Lost", "message": "class Lost: not profiled", "attempts": 2}
    text = rendered(tmp_path, analytics(failures=[failure]))[1].find(id="collection").get_text(" ")
    assert "ex:Lost" in text or EX + "Lost" in text
    assert "co_types" in text and "class Lost: not profiled" in text
    assert "first_n" in text and "10000" in text


def test_profiled_graphs_and_extra_constants_reach_the_template(tmp_path):
    profile = analytics()
    soup = rendered(tmp_path, profile, extra_conf={"title": "Custom title"})[1]
    assert soup.find("h1", attrs={"id": "skip-toc"}).text == "Custom title"
    assert "default graph" in soup.get_text(" ") and EX + "g" in soup.get_text(" ")


def test_endpoint_values_are_escaped(tmp_path):
    evil = "http://x/<script>alert(1)</script>"
    failure = {"query_kind": "class_partitions", "graph": evil, "class_iri": evil, "message": "skipping"}
    raw = {"endpoint": "http://e", "settings": {}, "graphs": [{"graph": evil}], "failures": [failure]}
    html = render_report(analyse(ProfileRun.model_validate(raw)), tmp_path).read_text()
    assert "<script>alert" not in html and "&lt;script&gt;alert(1)" in html


def test_pipeline_logs_the_number_of_failures(tmp_path, monkeypatch, caplog):
    fake = FakeSparql()
    fake.add("ex:p", "a", "ex:Person")
    fake.add("ex:p", "ex:name", Literal("n"))
    fake.on("Q4", QueryTimeout("timed out"))
    monkeypatch.setattr(handlers, "SparqlWrapperClient", lambda endpoint, timeout: fake)
    with caplog.at_level(logging.WARNING):
        _, run = handlers.fingerprint_report("http://fake", tmp_path, resolve_settings(env={}))
    assert len(run.failures) == 1 and "with 1 failures" in caplog.text
