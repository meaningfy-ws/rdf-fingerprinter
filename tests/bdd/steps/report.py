"""Steps of fingerprint_report.feature: the report page, the CLI and the library call over FakeSparql."""

import io
import logging
import re
import urllib.error

from bs4 import BeautifulSoup
from click.testing import CliRunner
from pytest_bdd import given, parsers, then, when

from fingerprint.adapters.exceptions import GeneratedOutputError
from fingerprint.adapters.profile_file import load_profile
from fingerprint.adapters.sparql import QueryTimeout, SparqlHttpClient
from fingerprint.adapters.template_renderer import JinjaTemplateRenderer
from fingerprint.domain.analytics import analyse
from fingerprint.domain.profile import ProfileRun, Settings
from fingerprint.entrypoints.cli import generate
from fingerprint.service_layer import handlers, representations
from fingerprint.service_layer.generators import DocumentGenerator
from tests.bdd.steps.common import ENDPOINT, READABILITY, big_failure, person_run, run_fingerprint
from tests.fakes import EX
from tests.sample_data import TEST_DATA

CUSTOM_TEMPLATE = TEST_DATA / "custom_template"


def soup(ctx):
    return BeautifulSoup((ctx["output"] / "main.html").read_text(), "html.parser")


def render(ctx):
    run = ctx.get("run") or person_run()
    DocumentGenerator(analyse(run), JinjaTemplateRenderer()).write(ctx["output"])


# --- rendering ---


@given("an analytics profile")
def an_profile(ctx):
    ctx["run"] = person_run()


@given("an endpoint that fails on any query")
def failing_endpoint(ctx, monkeypatch):
    ctx["queried"] = []

    def refuse(self, *args, **kwargs):
        ctx["queried"].append(self)
        raise AssertionError("the endpoint must not be queried")

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
@then("no query is sent")
def never_queried(ctx):
    assert (ctx["queried"] if "queried" in ctx else ctx["fake"].queries) == []


@given(parsers.parse("a class read in {mode} with {observed:d} of {instances:d} instances observed"))
def class_read(ctx, mode, observed, instances):
    ctx["run"] = person_run(instances, observed)


@then(parsers.parse('its section shows "{label}"'))
def section_shows(ctx, label):
    assert label in soup(ctx).get_text(" ")


@given("the report is generated for the test data")
def generated(ctx):
    render(ctx)


@then(parsers.parse("every class table has the columns {columns}"))
def has_columns(ctx, columns):
    expected = [c.strip().lower() for c in columns.replace(" and ", ", ").split(",")]
    tables = soup(ctx).find_all("table", class_="props")
    assert tables
    for table in tables:
        headers = [th.text.strip().lower() for th in table.find_all("th")]
        assert all(any(h.startswith(c) for h in headers) for c in expected), (expected, headers)


@given("a property whose language coverage is absent")
def no_language(ctx):
    ctx["run"] = person_run()


@then('its language coverage cell shows "—"')
def dash(ctx):
    table = soup(ctx).find("table", class_="props")
    column = [th.text.strip() for th in table.find_all("th")].index("Language coverage")
    assert table.find("tbody").find("tr").find_all("td")[column].text.strip() == "—"


@given(parsers.parse('the profile contains one failure for class "{cls}"'))
def one_failure(ctx, cls):
    ctx["run"] = person_run(failures=[big_failure()])


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
    ctx["run"] = load_profile(READABILITY)


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


def refused() -> urllib.error.URLError:
    return urllib.error.URLError(ConnectionRefusedError("refused"))


def unauthorized() -> urllib.error.HTTPError:
    return urllib.error.HTTPError(ENDPOINT, 401, "unauthorized", {}, io.BytesIO(b""))  # type: ignore[arg-type]


def bad_prefix_file(ctx):
    path = ctx["tmp"] / "bad-prefixes.json"
    path.write_text("[]")
    ctx["args"] = ["--prefixes", str(path)]


SITUATIONS = {
    "every class is profiled": lambda fake, ctx: None,
    "one class fails and the others are profiled": lambda fake, ctx: fake.on(
        "Q8", QueryTimeout("timed out"), when=lambda q: "City" in q
    ),
    "the endpoint refuses connections": lambda fake, ctx: fake.on("Q0", refused()),
    "the endpoint requires authentication": lambda fake, ctx: fake.on("Q0", unauthorized()),
    "the output folder does not exist": lambda fake, ctx: ctx.update(output=ctx["output"] / "missing"),
    "a setting is invalid": lambda fake, ctx: ctx.update(args=["--threshold", "0"]),
    "the prefix file is malformed": lambda fake, ctx: bad_prefix_file(ctx),
    "an unexpected error occurs": lambda fake, ctx: fake.on("Q3", [{"c": EX + "Person", "instances": "many"}]),
}


@given(parsers.re(r"(?P<situation>" + "|".join(SITUATIONS) + ")$"))
def situation(ctx, store, situation):
    ctx["fake"] = store
    SITUATIONS[situation](store, ctx)


@given(parsers.parse('the endpoint address "{url}"'))
def endpoint_address(ctx, store, url):
    ctx["fake"], ctx["url"] = store, url


@when("the fingerprint command runs")
def command_runs(ctx, caplog):
    caplog.set_level(logging.INFO)
    run_fingerprint(ctx)


@when(parsers.parse('the fingerprint command runs with the format "{name}"'))
def command_runs_with_format(ctx, name):
    run_fingerprint(ctx, "--format", name)


@when("the document is rendered again from the saved profile file")
def document_again(ctx):
    again = ctx["tmp"] / "again"
    again.mkdir()
    ctx["again"] = again
    CliRunner().invoke(generate.gen_doc, [str(ctx["output"] / "profile.json"), "-o", str(again)])


@then("the two pages are equal")
def pages_equal(ctx):
    assert (ctx["again"] / "main.html").read_text() == (ctx["output"] / "main.html").read_text()


@then("it logs the number of failures")
def logs_failures(caplog):
    assert "with 1 failures" in caplog.text


@then("it logs that the endpoint cannot be reached")
def logs_unreachable(caplog):
    assert "cannot reach endpoint" in caplog.text


@then(parsers.parse('no output file and no log line holds the user info "{userinfo}" or the query string "{query}"'))
def no_secrets(ctx, caplog, userinfo, query):
    texts = [p.read_text() for p in ctx["output"].iterdir()] + [caplog.text, ctx["result"].output]
    assert not any(token in text for text in texts for token in (userinfo, query))


@then(parsers.parse('the outputs and logs show "{shown}"'))
def shows_redacted(ctx, shown):
    assert shown in (ctx["output"] / "profile.json").read_text() and shown in (ctx["output"] / "main.html").read_text()


@then(parsers.parse("it exits with {code:d}"))
@then(parsers.parse("the command exits with {code:d}"))
def exits_with(ctx, code):
    assert ctx["result"].exit_code == code, ctx["result"].output


# --- the library ---


@when("the library is called with an endpoint, an output folder and default settings")
def library_call(ctx, store):
    ctx["returned"], _ = handlers.fingerprint_report(ENDPOINT, ctx["output"], Settings())


@then("it returns the path of the main report document")
def returns_path(ctx):
    assert ctx["returned"] == ctx["output"] / "main.html" and ctx["returned"].is_file()


@given("a custom template package that prints the number of graphs")
def custom_template(ctx):
    ctx["template"] = CUSTOM_TEMPLATE


@when("the report is generated with that package")
def with_package(ctx, store):
    _, ctx["collected"] = handlers.fingerprint_report(ENDPOINT, ctx["output"], Settings(), template=ctx["template"])


@then("the page shows that number")
def page_shows_number(ctx):
    page = soup(ctx)
    assert page.find("h1").text == "Ours" and page.find(id="graphs").text == str(len(ctx["collected"].graphs))


# --- the saved profile ---


@given("the report template raises an error")
def report_raises(monkeypatch):
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
    class Failing:
        def __init__(self, *args, **kwargs):
            pass

        def write(self, folder):
            raise GeneratedOutputError("shapes-default.ttl is not valid turtle")

    monkeypatch.setitem(representations.GENERATORS, "shacl", Failing)
