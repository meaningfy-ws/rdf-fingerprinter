"""Step definitions for namespace_prefixes.feature: resolution, generation and the saved table."""

import io
import json
import logging
import re
import ssl
import urllib.error
import urllib.request
from pathlib import Path

import pytest
from click.testing import CliRunner
from pytest_bdd import given, parsers, scenarios, then, when

from fingerprint.adapters.prefixes import PrefixCcList, PrefixLookupError
from fingerprint.adapters.profile_file import load_profile, save_profile
from fingerprint.adapters.template_renderer import JinjaTemplateRenderer
from fingerprint.domain.analytics import analyse
from fingerprint.domain.prefixes import PrefixTable, generate_prefixes
from fingerprint.domain.profile import NamespacePrefix, PrefixSource
from fingerprint.entrypoints.cli import generate
from fingerprint.entrypoints.cli import main as cli
from fingerprint.service_layer import handlers
from fingerprint.service_layer.generators.plantuml import PlantumlGenerator
from fingerprint.service_layer.prefixes import resolve_namespaces
from tests.builders import klass, profile_run, prop, resources
from tests.fakes import FakeSparql, files

scenarios("namespace_prefixes.feature")

FOAF = "http://xmlns.com/foaf/0.1/"
SAMPLE = Path(__file__).parents[1] / "test_data" / "profiles" / "sample-profile.json"
READABILITY = Path(__file__).parents[1] / "test_data" / "profiles" / "readability-profile.json"
BRAINFRAME = "https://ontology.brainframe.com/2016/04/brainframe#"


def entry(prefix, namespace, source):
    return NamespacePrefix(prefix=prefix, namespace=namespace, source=source)


class FakePrefixList:
    def __init__(self, entries=(), error=None):
        self.entries, self.error = list(entries), error

    def fetch(self):
        if self.error:
            raise PrefixLookupError(self.error)
        return self.entries


def using(*namespaces):
    """A run whose one class has a property in each namespace."""
    props = [prop(ns + "p", {1: 1}, resources(1)) for ns in namespaces]
    return profile_run(klass("http://ex.org/data/Thing", 1, *props))


@pytest.fixture
def ctx():
    return {"user": [], "packaged": [], "lookup": None}


# --- every namespace has a prefix ---


@given(parsers.parse('a profile uses "{iri}"'))
def profile_uses(ctx, iri):
    ctx["run"] = profile_run(klass(iri, 1))


@given("no prefix source names that namespace")
def no_source():
    """The default: the fixture holds no user file, packaged file or lookup."""


@then(parsers.parse('the namespace table holds the generated prefix "{prefix}" for "{namespace}"'))
def holds_generated(ctx, prefix, namespace):
    assert {e.namespace: (e.prefix, e.source) for e in ctx["table"]}[namespace] == (prefix, "generated")


@then(parsers.parse('its namespace is "{namespace}"'))
def namespace_is(ctx, namespace):
    assert namespace in {e.namespace for e in ctx["table"]}


@given(parsers.parse('a profile using the namespaces "{a}" and "{b}"'))
def profile_using(ctx, a, b):
    ctx["run"] = using(a, b)


@when("the same profile is resolved twice with the same prefix sources")
def resolved_twice(ctx):
    resolved(ctx)
    ctx["first"] = ctx["table"]
    resolved(ctx)


@then("both namespace tables are equal")
def tables_equal(ctx):
    assert ctx["first"] == ctx["table"]


# --- precedence ---


@given(parsers.parse('the namespace "{namespace}" is named by {sources}'))
def named_by(ctx, namespace, sources):
    ctx["run"] = using(namespace)
    if "user file" in sources:
        ctx["user"] = [entry("friend", namespace, PrefixSource.user)]
    if "packaged" in sources:
        ctx["packaged"] = [entry("foaf", namespace, PrefixSource.packaged)]
    if "prefix.cc" in sources:
        ctx["lookup"] = FakePrefixList([entry("foaf", namespace, PrefixSource.prefix_cc)])


@when("the namespace table is resolved")
def resolved(ctx):
    ctx["table"] = resolve_namespaces(ctx["run"], ctx["user"], ctx["packaged"], ctx["lookup"]).namespaces


@then(parsers.parse('its prefix is "{prefix}" with source "{source}"'))
def prefix_and_source(ctx, prefix, source):
    assert (prefix, source) in {(e.prefix, e.source) for e in ctx["table"] if e.namespace == FOAF}


@given(parsers.parse('the user file maps "{a}" to "{a_ns}" and "{b}" to "{b_ns}"'))
def user_maps(ctx, a, a_ns, b, b_ns):
    ctx["run"] = using(a_ns, b_ns)
    ctx["user"] = [entry(a, a_ns, PrefixSource.user), entry(b, b_ns, PrefixSource.user)]
    ctx["pairs"] = [(a, a_ns), (b, b_ns)]


@then("neither name is used for those namespaces")
def neither_used(ctx):
    names = {e.namespace: e.prefix for e in ctx["table"]}
    assert all(names[ns] != prefix for prefix, ns in ctx["pairs"])


@given(parsers.parse('a saved table names "{saved_ns}" as "{prefix}" and the user file maps "{same}" to "{user_ns}"'))
def saved_and_user(ctx, saved_ns, prefix, same, user_ns):
    ctx["run"] = using(saved_ns, user_ns).model_copy(update={"namespaces": [entry(prefix, saved_ns, PrefixSource.packaged)]})
    ctx["user"] = [entry(same, user_ns, PrefixSource.user)]


@then(parsers.parse('"{user_ns}" is "{prefix}" from the user file and "{saved_ns}" is not "{again}"'))
def displaced(ctx, user_ns, prefix, saved_ns, again):
    names = {e.namespace: (e.prefix, e.source) for e in ctx["table"]}
    assert names[user_ns] == (prefix, "user") and names[saved_ns][0] != again


@given("prefix.cc is unreachable")
def unreachable(ctx):
    ctx["run"] = using("https://ontology.brainframe.com/2016/04/brainframe#")
    ctx["lookup"] = FakePrefixList(error="unreachable")


@when("the namespace table is resolved with the lookup on")
def resolved_with_lookup(ctx, caplog):
    with caplog.at_level(logging.INFO):
        resolved(ctx)
    ctx["log"] = caplog.text
    ctx["warnings"] = [r for r in caplog.records if r.levelno >= logging.WARNING]


@then("one warning names prefix.cc and the unnamed namespaces have generated prefixes")
def warned_and_generated(ctx):
    assert len(ctx["warnings"]) == 1 and ctx["log"].count("prefix.cc lookup failed") == 1
    assert {e.prefix: e.source for e in ctx["table"]}["brainframe"] == "generated"


@given(parsers.re(r'the namespace "(?P<namespace>[^"]+)" with the table "(?P<known>[^"]*)"'))
def namespace_and_table(ctx, namespace, known):
    ctx["namespace"] = namespace
    ctx["known"] = [entry(*pair.split("=", 1), PrefixSource.packaged) for pair in known.split(",") if pair]


@when("its prefix is generated")
def generated(ctx):
    (ctx["generated"],) = generate_prefixes([ctx["namespace"]], ctx["known"])


@then(parsers.parse('it is "{prefix}"'))
def it_is(ctx, prefix):
    assert ctx["generated"].prefix == prefix


@given(parsers.parse('the table names "{a_ns}" as "{a}" and "{b_ns}" as "{b}"'))
def two_entries(ctx, a_ns, a, b_ns, b):
    ctx["prefix_table"] = PrefixTable([entry(a, a_ns, PrefixSource.user), entry(b, b_ns, PrefixSource.user)])


@then(parsers.parse('"{iri}" is shown as "{curie}"'))
def shown_as(ctx, iri, curie):
    assert ctx["prefix_table"].curie(iri) == curie


@given("a profile file without a namespace table")
def old_profile(ctx):
    ctx["run"] = load_profile(SAMPLE)
    assert ctx["run"].namespaces is None


@when("it is loaded and its diagram generated")
def diagram_of_old(ctx):
    generator = PlantumlGenerator(analyse(ctx["run"]), JinjaTemplateRenderer())
    ctx["texts"], ctx["table"] = files(generator.serialize()), generator.table.entries


@then("every namespace has a prefix and no long IRI is in a label")
def no_long_labels(ctx):
    assert ctx["table"]
    for text in ctx["texts"].values():
        assert not re.search(r'"[^"]*https?://[^"]*"', text), text


# --- commands: a bad user file, a user file over a saved table, the lookup switch, offline generators ---


@pytest.fixture
def store(monkeypatch):
    fake = FakeSparql()
    fake.add("ex:p1", "a", "ex:Person")
    monkeypatch.setattr(handlers, "SparqlHttpClient", lambda endpoint, timeout: fake)
    return fake


@pytest.fixture
def lookups(monkeypatch):
    built = []

    class Recording:
        def __init__(self):
            built.append(self)

        def fetch(self):
            return []

    monkeypatch.setattr(cli, "PrefixCcList", Recording)
    return built


def fingerprint(ctx, tmp_path, *args):
    ctx["result"] = CliRunner().invoke(cli.fingerprint_endpoint, ["-e", "http://fake/sparql", "-o", str(tmp_path), *args])


@given("the prefix option names a file that is not a JSON object of names to IRIs")
def bad_user_file(ctx, tmp_path):
    ctx["prefix_file"] = tmp_path / "bad-prefixes.json"
    ctx["prefix_file"].write_text("[]")


@when("the fingerprint command runs")
def command_runs(ctx, store, tmp_path):
    fingerprint(ctx, tmp_path, "--prefixes", str(ctx["prefix_file"]))


@then("it exits with 2 and a message naming the option and the file")
def usage_error(ctx):
    output = ctx["result"].output
    assert ctx["result"].exit_code == 2 and "--prefixes" in output and str(ctx["prefix_file"]) in output


@then("no query is sent")
def no_query(store):
    assert store.queries == []


@given("the prefix lookup is switched on by the environment")
def lookup_on(monkeypatch):
    monkeypatch.setenv("RDF_FINGERPRINTER_PREFIX_LOOKUP", "true")


@when(parsers.parse('the fingerprint command runs with "{option}"'))
def command_runs_with(ctx, store, lookups, tmp_path, option):
    ctx["lookups"] = lookups
    fingerprint(ctx, tmp_path, option)
    assert ctx["result"].exit_code == 0, ctx["result"].output


@then("prefix.cc is not contacted")
def not_contacted(ctx):
    assert ctx["lookups"] == []


def saved_profile(tmp_path, *table):
    run = profile_run(klass("http://ex.org/A", 1), klass("http://ex.org/core/B", 1)).model_copy(
        update={"namespaces": list(table)}
    )
    return save_profile(run, tmp_path)


@given(
    parsers.parse('a saved profile whose table names "{a_ns}" as "{a}" and "{b_ns}" as "{b}", both generated'),
    target_fixture="saved",
)
def saved_two(tmp_path, a_ns, a, b_ns, b):
    return saved_profile(tmp_path, entry(a, a_ns, PrefixSource.generated), entry(b, b_ns, PrefixSource.generated))


@given(parsers.parse('a saved profile whose table names "{namespace}" as "{prefix}", generated'), target_fixture="saved")
def saved_one(tmp_path, namespace, prefix):
    return saved_profile(tmp_path, entry(prefix, namespace, PrefixSource.generated))


@given(parsers.parse('a user file that names "{namespace}" as "{prefix}"'), target_fixture="user_file")
def user_file(tmp_path, namespace, prefix):
    path = tmp_path / "my.json"
    path.write_text(json.dumps({prefix + ":": namespace}))  # dict-ok: the JSON of a prefix file
    return path


def render_diagram(ctx, tmp_path, saved, *args):
    out = tmp_path / "out"
    out.mkdir()
    result = CliRunner().invoke(generate.gen_puml, [str(saved), "-o", str(out), *args])
    assert result.exit_code == 0, result.output
    ctx["diagram"] = "".join(p.read_text() for p in out.glob("*.puml"))


@when("the diagram generator renders the saved profile")
def render_with_user_file(ctx, tmp_path, saved, user_file):
    render_diagram(ctx, tmp_path, saved, "--prefixes", str(user_file))


@when("the diagram generator renders the saved profile with HTTP forbidden")
def render_offline(ctx, tmp_path, saved, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("an HTTP request was made")

    monkeypatch.setattr(urllib.request, "urlopen", forbidden)
    render_diagram(ctx, tmp_path, saved)


@then(parsers.parse('the diagram uses "{prefix}" for "{namespace}" and still "{other}" for "{other_ns}"'))
def diagram_uses_two(ctx, prefix, namespace, other, other_ns):
    assert f"{prefix}A" in ctx["diagram"] and f"{other}B" in ctx["diagram"], ctx["diagram"]


@then(parsers.parse('the diagram uses "{prefix}" for "{namespace}"'))
def diagram_uses(ctx, prefix, namespace):
    assert f"{prefix}A" in ctx["diagram"], ctx["diagram"]


# --- the lookup over an expired certificate ---


class Answer(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


@given("prefix.cc's HTTPS certificate fails verification and its HTTP list is reachable")
def expired_certificate(ctx):
    expired = urllib.error.URLError(ssl.SSLCertVerificationError("certificate has expired"))
    listing = json.dumps({"brainframe": BRAINFRAME}).encode()  # dict-ok: the JSON of prefix.cc's list
    calls = []

    def open_(url, timeout):
        calls.append(url)
        if url.startswith("https"):
            raise expired
        return Answer(listing)

    ctx["run"] = using(BRAINFRAME)
    ctx["calls"] = calls
    ctx["lookup"] = PrefixCcList(opener=open_)


@then("the list is read over HTTP, the INFO line is logged and no warning is logged")
def read_over_http(ctx):
    assert [u.split(":")[0] for u in ctx["calls"]] == ["https", "http"]
    assert "certificate not valid; fetched the prefix list over HTTP" in ctx["log"]
    assert not ctx["warnings"]
    assert {e.prefix: e.source for e in ctx["table"]}["brainframe"] == "prefix_cc"


# --- the diagram of the readability profile ---


@given("the readability test profile")
def readability_profile(ctx):
    ctx["run"] = load_profile(READABILITY)


@when("the PlantUML output is generated")
def diagram_of_readability(ctx):
    diagram_of_old(ctx)


@then("no class, attribute, association or package label holds a full IRI")
def no_full_iri_label(ctx):
    no_long_labels(ctx)
