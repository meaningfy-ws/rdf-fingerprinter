"""Step definitions for fingerprint_report.feature: the report page, the CLI and the library call over FakeSparql."""

import io
import re
import urllib.error
from pathlib import Path

import pytest
from bs4 import BeautifulSoup
from click.testing import CliRunner
from pytest_bdd import given, parsers, scenarios, then, when
from rdflib import Literal

from fingerprint.adapters.profile_file import load_profile
from fingerprint.adapters.sparql import QueryTimeout, SparqlHttpClient
from fingerprint.adapters.template_renderer import JinjaTemplateRenderer
from fingerprint.domain.analytics import analyse
from fingerprint.domain.profile import ProfileRun, Settings
from fingerprint.entrypoints.cli import main as cli
from fingerprint.service_layer import handlers
from fingerprint.service_layer.generators import DocumentGenerator
from tests.fakes import EX, FakeSparql

scenarios("fingerprint_report.feature")

TEST_DATA = Path(__file__).parents[1] / "test_data"
CUSTOM_TEMPLATE = TEST_DATA / "custom_template"
READABILITY = TEST_DATA / "profiles" / "readability-profile.json"


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
    return ProfileRun.model_validate(
        {
            "endpoint": "http://127.0.0.1:9/sparql",
            "settings": {},
            "graphs": [{"class_partitions": classes or [raw_class()]}],
            "failures": failures or [],
        }
    )


@pytest.fixture
def ctx(tmp_path):
    output = tmp_path / "output"
    output.mkdir()
    return {"output": output, "profile": profile()}


def soup(ctx):
    return BeautifulSoup((ctx["output"] / "main.html").read_text(), "html.parser")


def render(ctx):
    DocumentGenerator(analyse(ctx["profile"]), JinjaTemplateRenderer()).write(ctx["output"])


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

    monkeypatch.setattr(SparqlHttpClient, "_once", refuse)


@when("the report is rendered")
def rendered(ctx):
    render(ctx)


@then("the report is written")
def written(ctx):
    assert (ctx["output"] / "main.html").is_file()


@then("no report is written")
def not_written(ctx):
    assert not (ctx["output"] / "main.html").exists()


@then("the endpoint was never queried")
def never_queried(ctx):
    assert (ctx["queried"] if "queried" in ctx else ctx["fake"].queries) == []


@given(parsers.parse("a class read in {mode} with {observed:d} of {instances:d} instances observed"))
def class_read(ctx, mode, observed, instances):
    ctx["profile"] = profile([raw_class("first_n" if mode == "first-N" else "exact", observed, instances)])


@then(parsers.parse('its section shows "{label}"'))
def section_shows(ctx, label):
    assert label in soup(ctx).get_text(" ")


@given("the report is generated for the test data")
def generated(ctx):
    render(ctx)


@then(parsers.parse("every class table has the columns {columns}"))
def has_columns(ctx, columns):
    expected = [c.strip().lower() for c in columns.replace(" and ", ", ").split(",")]
    expected = ["avg" if c == "avg" else c for c in expected]
    tables = soup(ctx).find_all("table", class_="props")
    assert tables
    for table in tables:
        headers = [th.text.strip().lower() for th in table.find_all("th")]
        assert all(any(h.startswith(c) for h in headers) for c in expected), (expected, headers)


@given("a property whose language coverage is absent")
def no_language(ctx):
    ctx["profile"] = profile()


@then('its language coverage cell shows "—"')
def dash(ctx):
    table = soup(ctx).find("table", class_="props")
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


# --- readability (readability-representations: short names, one self-contained page) ---


@given("the readability test profile")
def readability_profile(ctx):
    ctx["profile"] = load_profile(READABILITY)


@then("no visible text outside the namespace table, the endpoint, the settings, the failures and the caveats holds a full IRI")
def short_names_only(ctx):
    page = soup(ctx)
    # exactly the spec's exemptions: the namespace table, the endpoint, the settings, failure messages, unwritable IRIs
    exempt = [page.find(id="namespaces"), page.select_one("#collection details"), page.select_one(".bar small")]
    exempt += page.select("#overview dd")[:1] + page.select("#collection tbody td:last-child")
    exempt += [h3.find_next("ul") for h3 in page.select("#caveats h3") if "cannot be written" in h3.text]
    for element in [*exempt, *page.find_all(["script", "style"])]:
        if element is not None:
            element.decompose()
    text = page.get_text(" ")
    assert "http://" not in text and "https://" not in text, [t for t in text.split() if "://" in t]


@then(parsers.parse('the caveats list "{prefix}" as hidden with {count:d} class'))
def hidden_listed(ctx, prefix, count):
    text = " ".join(soup(ctx).find(id="caveats").get_text(" ").split())
    assert re.search(rf"{re.escape(prefix)}\s*:\s*{count} classes", text), text


@then(parsers.parse('no "{prefix}:" class section exists'))
def no_hidden_section(ctx, prefix):
    assert not soup(ctx).select(f'details.cls[data-ns="{prefix.rstrip(":")}"]')


@then("the page has no external stylesheet, script, image or CSS url")
def no_external_resources(ctx):
    page = soup(ctx)
    assert not page.find_all("link", rel="stylesheet")
    assert not page.find_all("script", src=True) and not page.find_all("img")
    assert "url(" not in " ".join(s.get_text() for s in page.find_all("style"))


@then("without its scripts the page still has the table of contents, every class section and every table")
def readable_without_script(ctx):
    page = soup(ctx)
    for script in page.find_all("script"):
        script.decompose()
    sections = page.select("details.cls")
    assert page.find("nav") and sections and len(page.select("li[data-anchor]")) == len(sections)
    assert all(s.find("table") for s in sections)


@then("each class section carries its prefix and a search text with its short name and full IRI")
def search_data(ctx):
    for section in soup(ctx).select("details.cls"):
        link = section.find("summary").find(class_="curie")
        assert section["data-ns"] and link["title"].lower() in section["data-q"]
        assert link.get_text().lower() in section["data-q"]


# --- the command line ---


@pytest.fixture
def fake(monkeypatch):
    fake = FakeSparql()
    for i in range(2):
        fake.add(f"ex:p{i}", "a", "ex:Person")
        fake.add(f"ex:p{i}", "ex:name", Literal(f"n{i}"))
        fake.add(f"ex:c{i}", "a", "ex:City")
    monkeypatch.setattr(handlers, "SparqlHttpClient", lambda endpoint, timeout: fake)
    return fake


def refused() -> urllib.error.URLError:
    return urllib.error.URLError(ConnectionRefusedError("refused"))


def unauthorized() -> urllib.error.HTTPError:
    return urllib.error.HTTPError("http://fake", 401, "unauthorized", {}, io.BytesIO(b""))  # type: ignore[arg-type]


def _bad_prefixes(ctx) -> Path:
    path = ctx["output"].parent / "bad-prefixes.json"
    path.write_text("[]")
    return path


SITUATIONS = {
    "every class is profiled": lambda fake, ctx: None,
    "one class fails and the others are profiled": lambda fake, ctx: fake.on(
        "Q8", QueryTimeout("timed out"), when=lambda q: "City" in q
    ),
    "the endpoint refuses connections": lambda fake, ctx: fake.on("Q0", refused()),
    "the endpoint requires authentication": lambda fake, ctx: fake.on("Q0", unauthorized()),
    "the output folder does not exist": lambda fake, ctx: ctx.update(output=ctx["output"] / "missing"),
    "a setting is invalid": lambda fake, ctx: ctx.update(args=["--threshold", "0"]),
    "the prefix file is malformed": lambda fake, ctx: ctx.update(args=["--prefixes", str(_bad_prefixes(ctx))]),
    "an unexpected error occurs": lambda fake, ctx: fake.on("Q3", [{"c": EX + "Person", "instances": "many"}]),
}


@given(parsers.re(r"(?P<situation>" + "|".join(SITUATIONS) + ")$"))
def situation(ctx, fake, situation):
    ctx["fake"] = fake
    SITUATIONS[situation](fake, ctx)


@when("the fingerprint command runs")
def command_runs(ctx):
    args = ["-e", "http://fake/sparql", "-o", str(ctx["output"]), *ctx.get("args", [])]
    ctx["result"] = CliRunner().invoke(cli.fingerprint_endpoint, args)


@then(parsers.parse("it exits with {code:d}"))
def exits_with(ctx, code):
    assert ctx["result"].exit_code == code, ctx["result"].output


# --- the library ---


@when("the library is called with an endpoint, an output folder and default settings")
def library_call(ctx, fake):
    ctx["returned"], _ = handlers.fingerprint_report("http://fake/sparql", ctx["output"], Settings())


@then("it returns the path of the main report document")
def returns_path(ctx):
    assert ctx["returned"] == ctx["output"] / "main.html" and ctx["returned"].is_file()


@given("a custom template package that prints the number of graphs")
def custom_template(ctx):
    ctx["template"] = CUSTOM_TEMPLATE


@when("the report is generated with that package")
def with_package(ctx, fake):
    _, ctx["run"] = handlers.fingerprint_report("http://fake/sparql", ctx["output"], Settings(), template=ctx["template"])


@then("the page shows that number")
def page_shows_number(ctx):
    page = soup(ctx)
    assert page.find("h1").text == "Ours" and page.find(id="graphs").text == str(len(ctx["run"].graphs))


# --- the saved profile ---


@given("the report template raises an error")
def report_raises(monkeypatch):
    from fingerprint.adapters.template_renderer import JinjaTemplateRenderer

    def broken(self, *args, **kwargs):
        raise RuntimeError("template error")

    monkeypatch.setattr(JinjaTemplateRenderer, "make", broken)


@then("the output folder holds the report and the profile file")
def report_and_profile(ctx):
    assert {"main.html", "profile.json"} <= {p.name for p in ctx["output"].iterdir()}


@then("the output folder holds the profile file")
def profile_only(ctx):
    assert (ctx["output"] / "profile.json").is_file()


@then("the profile file holds a namespace table")
def profile_has_namespaces(ctx):
    run = ProfileRun.model_validate_json((ctx["output"] / "profile.json").read_text())
    assert run.namespaces and {"ex", "rdf"} <= {e.prefix for e in run.namespaces}


@then("the profile file lists that failure")
def profile_lists_failure(ctx):
    run = ProfileRun.model_validate_json((ctx["output"] / "profile.json").read_text())
    assert [f.class_iri for f in run.failures or []] == [EX + "City"]


# --- representations in the same run (UC-B2.2) ---


@when(parsers.parse('the fingerprint command runs with the format "{name}"'))
def command_runs_with_format(ctx, name):
    args = ["-e", "http://fake/sparql", "-o", str(ctx["output"]), "--format", name]
    ctx["result"] = CliRunner().invoke(cli.fingerprint_endpoint, args)


@then("the output folder holds the report and no profile.html")
def report_not_profile_html(ctx):
    names = {p.name for p in ctx["output"].iterdir()}
    assert "main.html" in names and "profile.html" not in names


@then("the output folder holds the report, the profile file and one shapes file per non-empty profiled graph")
def report_profile_and_shapes(ctx):
    names = {p.name for p in ctx["output"].iterdir()}
    assert {"main.html", "profile.json"} <= names and [n for n in names if n.startswith("shapes-")] == ["shapes-default.ttl"]


@then("the message names the known formats")
def names_known_formats(ctx):
    assert all(name in ctx["result"].output for name in ("shacl", "puml", "doc"))


@given("the shapes fail to render")
def shapes_fail(monkeypatch):
    from fingerprint.adapters.exceptions import GeneratedOutputError
    from fingerprint.service_layer import representations

    class Failing:
        def __init__(self, *args, **kwargs):
            pass

        def write(self, folder):
            raise GeneratedOutputError("shapes-default.ttl is not valid turtle")

    monkeypatch.setitem(representations.GENERATORS, "shacl", Failing)
