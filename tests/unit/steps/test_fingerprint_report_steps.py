"""Step definitions for fingerprint_report.feature: render_report, the CLI and the library call over FakeSparql."""

import io
import urllib.error
from pathlib import Path

import pytest
import SPARQLWrapper
from bs4 import BeautifulSoup
from click.testing import CliRunner
from pytest_bdd import given, parsers, scenarios, then, when
from rdflib import Literal

from fingerprint.adapters.sparql import QueryTimeout
from fingerprint.domain.analytics import analyse
from fingerprint.domain.generated.profile import ProfileRun
from fingerprint.entrypoints.cli import main as cli
from fingerprint.service_layer import handlers
from fingerprint.service_layer.report import render_report
from tests.unit.fakes import EX, FakeSparql

scenarios("fingerprint_report.feature")

CUSTOM_TEMPLATE = Path(__file__).parents[2] / "test_data" / "custom_template"


def raw_class(mode="exact", observed=3, instances=3, properties=None):
    return {
        "class_iri": EX + "Person",
        "instances": instances,
        "observed_instances": observed,
        "precision_mode": mode,
        "property_partitions": properties
        or [{"property": EX + "name", "cardinality_histogram": [{"values_per_subject": 1, "subjects": observed}]}],
    }


def profile(classes=None, failures=None):
    return analyse(
        ProfileRun.model_validate(
            {
                "endpoint": "http://127.0.0.1:9/sparql",
                "settings": {},
                "graphs": [{"class_partitions": classes or [raw_class()]}],
                "failures": failures or [],
            }
        )
    )


@pytest.fixture
def ctx(tmp_path):
    output = tmp_path / "output"
    output.mkdir()
    return {"output": output, "profile": profile()}


def soup(ctx):
    return BeautifulSoup((ctx["output"] / "main.html").read_text(), "html.parser")


# --- rendering ---


@given("an analytics profile")
def an_profile(ctx):
    ctx["profile"] = profile()


@given("an endpoint that fails on any query")
def failing_endpoint(ctx, monkeypatch):
    ctx["queried"] = []

    def refuse(self, *args, **kwargs):
        ctx["queried"].append(self)
        raise AssertionError("the report must not query")

    monkeypatch.setattr(SPARQLWrapper.SPARQLWrapper, "query", refuse)


@when("the report is rendered")
def rendered(ctx):
    render_report(ctx["profile"], ctx["output"])


@then("the report is written")
def written(ctx):
    assert (ctx["output"] / "main.html").is_file()


@then("no report is written")
def not_written(ctx):
    assert not (ctx["output"] / "main.html").exists()


@then("the endpoint was never queried")
def never_queried(ctx):
    assert ctx["queried"] == []


@given(parsers.parse("a class read in {mode} with {observed:d} of {instances:d} instances observed"))
def class_read(ctx, mode, observed, instances):
    ctx["profile"] = profile([raw_class("first_n" if mode == "first-N" else "exact", observed, instances)])


@then(parsers.parse('its section shows "{label}"'))
def section_shows(ctx, label):
    assert label in soup(ctx).get_text(" ")


@given("the report is generated for the test data")
def generated(ctx):
    render_report(ctx["profile"], ctx["output"])


@then(parsers.parse("every class table has the columns {columns}"))
def has_columns(ctx, columns):
    expected = [c.strip().lower() for c in columns.replace(" and ", ", ").split(",")]
    expected = ["avg" if c == "avg" else c for c in expected]
    tables = soup(ctx).find_all("table", class_="class-profile")
    assert tables
    for table in tables:
        headers = [th.text.strip().lower() for th in table.find_all("th")]
        assert all(any(h.startswith(c) for h in headers) for c in expected), (expected, headers)


@given("a property whose language coverage is absent")
def no_language(ctx):
    ctx["profile"] = profile()


@then('its language coverage cell shows "—"')
def dash(ctx):
    table = soup(ctx).find("table", class_="class-profile")
    column = [th.text.strip() for th in table.find_all("th")].index("Language coverage")
    assert table.find("tbody").find("tr").find_all("td")[column].text.strip() == "—"


@given(parsers.parse('the profile contains one failure for class "{cls}"'))
def one_failure(ctx, cls):
    failure = {"query_kind": "co_types", "class_iri": EX + "Big", "message": "class Big: not profiled after 2 attempts"}
    ctx["profile"] = profile(failures=[failure])


@then(parsers.parse('the collection section lists "{cls}" with the failed measurement and the error message'))
def lists_failure(ctx, cls):
    text = soup(ctx).find(id="collection").get_text(" ")
    assert (cls in text or EX + cls[3:] in text) and "co_types" in text and "not profiled after 2 attempts" in text


@then("the collection section lists the settings used")
def lists_settings(ctx):
    text = soup(ctx).find(id="collection").get_text(" ")
    assert "precision_policy" in text and "timeout_seconds" in text


# --- the command line ---


@pytest.fixture
def fake(monkeypatch):
    fake = FakeSparql()
    for i in range(2):
        fake.add(f"ex:p{i}", "a", "ex:Person")
        fake.add(f"ex:p{i}", "ex:name", Literal(f"n{i}"))
        fake.add(f"ex:c{i}", "a", "ex:City")
    monkeypatch.setattr(handlers, "SparqlWrapperClient", lambda endpoint, timeout: fake)
    return fake


def refused() -> urllib.error.URLError:
    return urllib.error.URLError(ConnectionRefusedError("refused"))


def unauthorized() -> urllib.error.HTTPError:
    return urllib.error.HTTPError("http://fake", 401, "unauthorized", {}, io.BytesIO(b""))  # type: ignore[arg-type]


SITUATIONS = {
    "every class is profiled": lambda fake, ctx: None,
    "one class fails and the others are profiled": lambda fake, ctx: fake.on(
        "Q8", QueryTimeout("timed out"), when=lambda q: "City" in q
    ),
    "the endpoint refuses connections": lambda fake, ctx: fake.on("Q0", refused()),
    "the endpoint requires authentication": lambda fake, ctx: fake.on("Q0", unauthorized()),
    "the output folder does not exist": lambda fake, ctx: ctx.update(output=ctx["output"] / "missing"),
    "a setting is invalid": lambda fake, ctx: ctx.update(args=["--threshold", "0"]),
    "an unexpected error occurs": lambda fake, ctx: fake.on("Q3", [{"c": EX + "Person", "instances": "many"}]),
}


@given(parsers.re(r"(?P<situation>" + "|".join(SITUATIONS) + ")$"))
def situation(ctx, fake, situation):
    SITUATIONS[situation](fake, ctx)


@when("the fingerprint command runs")
def command_runs(ctx):
    args = ["-e", "http://fake/sparql", "-o", str(ctx["output"]), *ctx.get("args", [])]
    ctx["result"] = CliRunner().invoke(cli.fingerprint_endpoint, args)


@then(parsers.parse("it exits with {code:d}"))
def exits_with(ctx, code):
    assert ctx["result"].exit_code == code, ctx["result"].output


# --- the library ---


@when("the library is called with only an endpoint and an output folder")
def library_call(ctx, fake):
    ctx["returned"] = handlers.generate_endpoint_fingerprint_report("http://fake/sparql", ctx["output"])


@then("it returns the path of the main report document")
def returns_path(ctx):
    assert ctx["returned"] == ctx["output"] / "main.html" and ctx["returned"].is_file()


@given("a custom template that reads a constant from the additional configuration")
def custom_template(ctx):
    ctx["template"] = CUSTOM_TEMPLATE


@when("the report is generated with that constant")
def with_constant(ctx, fake):
    handlers.generate_endpoint_fingerprint_report(
        "http://fake/sparql", ctx["output"], external_template_location=ctx["template"], additional_config={"title": "Ours"}
    )


@then("the constant appears in the report")
def constant_appears(ctx):
    assert soup(ctx).find("h1").text == "Ours"


# --- the saved profile ---


@given("the report template raises an error")
def report_raises(monkeypatch):
    def broken(*args, **kwargs):
        raise RuntimeError("template error")

    monkeypatch.setattr(handlers, "render_report", broken)


@then("the output folder holds the report and the profile file")
def report_and_profile(ctx):
    assert {"main.html", "profile.json"} <= {p.name for p in ctx["output"].iterdir()}


@then("the output folder holds the profile file")
def profile_only(ctx):
    assert (ctx["output"] / "profile.json").is_file()


@then("the profile file lists that failure")
def profile_lists_failure(ctx):
    run = ProfileRun.model_validate_json((ctx["output"] / "profile.json").read_text())
    assert [f.class_iri for f in run.failures or []] == [EX + "City"]
