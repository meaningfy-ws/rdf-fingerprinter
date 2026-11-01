"""Resolving a run's namespace table (namespace-prefixes › Prefix source precedence, › prefix.cc lookup is best effort)."""

import logging

from fingerprint.adapters.prefixes import PrefixLookupError
from fingerprint.domain.profile import NamespacePrefix, PrefixSource
from fingerprint.service_layer.prefixes import resolve_namespaces, used_namespaces
from tests.builders import klass, literals, profile_run, prop, resources

FOAF = "http://xmlns.com/foaf/0.1/"
BF = "https://ontology.brainframe.com/2016/04/brainframe#"


def e(prefix, namespace, source=PrefixSource.packaged):
    return NamespacePrefix(prefix=prefix, namespace=namespace, source=source)


class FakePrefixList:
    def __init__(self, entries=(), error=None):
        self.entries, self.error, self.calls = list(entries), error, 0

    def fetch(self):
        self.calls += 1
        if self.error:
            raise PrefixLookupError(self.error)
        return self.entries


def run(*iris, graph=None):
    """A run whose classes are `iris`, each with a property in its own namespace and a FOAF object type."""
    return profile_run(*(klass(i, 1, prop(i + "_p", {1: 1}, resources(1, FOAF + "Person"))) for i in iris), graph=graph)


def table(resolved):
    return {(x.prefix, x.namespace, x.source) for x in resolved.namespaces}


def test_every_namespace_in_use_is_named_and_only_those():
    resolved = resolve_namespaces(
        run(BF + "Person", graph="https://my.brainframe.com/graph/workspace"),
        packaged=[e("foaf", FOAF), e("dc", "http://purl.org/dc/elements/1.1/")],
    )
    assert table(resolved) == {
        ("foaf", FOAF, "packaged"),
        ("brainframe", BF, "generated"),
        ("graph", "https://my.brainframe.com/graph/", "generated"),
        ("rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#", "packaged"),
    }
    assert used_namespaces(resolved) == {x.namespace for x in resolved.namespaces}


def test_a_named_parent_names_its_sub_namespace():
    resolved = resolve_namespaces(run("http://ex.org/core/A"), [e("ex", "http://ex.org/", PrefixSource.user)], packaged=[])
    assert {x.prefix for x in resolved.namespaces} >= {"ex-core"}
    assert "http://ex.org/" not in {x.namespace for x in resolved.namespaces}  # a parent only, not saved


def test_the_prefix_cc_warning_carries_the_failure_reason_and_is_logged_once(caplog):
    lookup = FakePrefixList(error="unreachable")
    with caplog.at_level(logging.WARNING):
        resolve_namespaces(run(BF + "A"), packaged=[], prefix_list=lookup)
    assert lookup.calls == 1
    assert caplog.text.count("prefix.cc lookup failed: unreachable; generating prefixes") == 1


def test_no_fetch_when_the_files_name_everything():
    lookup = FakePrefixList()
    resolve_namespaces(
        profile_run(klass(FOAF + "Person", 1, prop(FOAF + "name", {1: 1}, literals(1, datatype=None)))),
        packaged=[e("foaf", FOAF)],
        prefix_list=lookup,
    )
    assert lookup.calls == 0


def test_resolving_is_idempotent_and_deterministic():
    first = resolve_namespaces(run(BF + "A", "http://ex.org/core/B"), packaged=[])
    assert resolve_namespaces(first, packaged=[]).namespaces == first.namespaces
    assert resolve_namespaces(run("http://ex.org/core/B", BF + "A"), packaged=[]).namespaces == first.namespaces


def test_a_skipped_first_prefix_falls_to_the_next_source_not_the_next_alias():
    ns = "http://ex.org/sh#"
    user = [e("sh", ns, PrefixSource.user), e("exsh", ns, PrefixSource.user)]
    resolved = resolve_namespaces(run(ns + "A"), user, packaged=[e("pk", ns), e("pk2", ns)])
    assert {x.namespace: x.prefix for x in resolved.namespaces}[ns] == "pk"
    looked_up = resolve_namespaces(
        run(ns + "A"),
        packaged=[],
        prefix_list=FakePrefixList([e("sh", ns, PrefixSource.prefix_cc), e("alias", ns, PrefixSource.prefix_cc)]),
    )
    assert {x.namespace: x.source for x in looked_up.namespaces}[ns] == "generated"


def test_invalid_saved_prefixes_are_skipped():
    saved = run("http://ex.org/core/A").model_copy(
        update={"namespaces": [e("../../escaped", "http://ex.org/core/", PrefixSource.user)]}
    )
    resolved = resolve_namespaces(saved, packaged=[])
    assert {x.namespace: x.prefix for x in resolved.namespaces}["http://ex.org/core/"] == "core"
