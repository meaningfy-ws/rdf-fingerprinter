"""Step definitions for namespace_prefixes.feature: resolution, generation and the saved table."""

import logging
import re
from pathlib import Path

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from fingerprint.adapters.prefixes import PrefixLookupError
from fingerprint.adapters.profile_file import load_profile
from fingerprint.adapters.template_renderer import JinjaTemplateRenderer
from fingerprint.domain.analytics import analyse
from fingerprint.domain.prefixes import PrefixTable, generate_prefixes
from fingerprint.domain.profile import NamespacePrefix, PrefixSource
from fingerprint.service_layer.generators.plantuml import PlantumlGenerator
from fingerprint.service_layer.prefixes import resolve_namespaces
from tests.unit.fakes import files, klass, profile_run, prop, resources

scenarios("namespace_prefixes.feature")

FOAF = "http://xmlns.com/foaf/0.1/"
SAMPLE = Path(__file__).parents[2] / "test_data" / "profiles" / "sample-profile.json"


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
    with caplog.at_level(logging.WARNING):
        resolved(ctx)
    ctx["log"] = caplog.text


@then("one warning names prefix.cc and the unnamed namespaces have generated prefixes")
def warned_and_generated(ctx):
    assert ctx["log"].count("prefix.cc lookup failed") == 1
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
