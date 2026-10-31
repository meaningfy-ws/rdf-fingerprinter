"""Resolving a run's namespace table (namespace-prefixes › Prefix source precedence, › prefix.cc lookup is best effort)."""

import logging

from fingerprint.adapters.prefixes import PrefixLookupError
from fingerprint.domain.profile import NamespacePrefix, PrefixSource
from fingerprint.service_layer.prefixes import resolve_namespaces, used_namespaces
from tests.unit.fakes import klass, literals, profile_run, prop, resources

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


def test_the_first_source_wins():
    user = [e("friend", FOAF, PrefixSource.user)]
    assert ("friend", FOAF, "user") in table(resolve_namespaces(run(BF + "A"), user, [e("foaf", FOAF)]))
    looked_up = resolve_namespaces(
        run(BF + "A"), packaged=[], prefix_list=FakePrefixList([e("foaf", FOAF, PrefixSource.prefix_cc)])
    )
    assert ("foaf", FOAF, "prefix_cc") in table(looked_up)
    assert ("foaf", FOAF, "generated") in table(resolve_namespaces(run(BF + "A"), packaged=[]))


def test_reserved_and_taken_names_fall_through_to_the_next_source():
    user = [e("sh", "http://ex.org/sh#", PrefixSource.user), e("bf-shape", "http://ex.org/bf/", PrefixSource.user)]
    resolved = resolve_namespaces(run("http://ex.org/sh#A", "http://ex.org/bf/B"), user, packaged=[])
    names = {x.namespace: x.prefix for x in resolved.namespaces}
    assert names["http://ex.org/sh#"] not in ("sh", "bf-shape") and names["http://ex.org/bf/"] != "bf-shape"


def test_a_user_file_over_a_saved_table():
    saved = run("http://ex.org/A", "http://ex.org/core/B").model_copy(
        update={
            "namespaces": [
                e("ex", "http://ex.org/", PrefixSource.generated),
                e("ex-core", "http://ex.org/core/", PrefixSource.generated),
            ]
        }
    )
    resolved = resolve_namespaces(saved, [e("exo", "http://ex.org/", PrefixSource.user)], packaged=[])
    names = {x.namespace: x.prefix for x in resolved.namespaces}
    assert names["http://ex.org/"] == "exo" and names["http://ex.org/core/"] == "ex-core"


def test_a_user_prefix_displaces_a_saved_one():
    saved = run("http://ex.org/foaf/A").model_copy(update={"namespaces": [e("foaf", FOAF)]})
    resolved = resolve_namespaces(saved, [e("foaf", "http://ex.org/foaf/", PrefixSource.user)], packaged=[e("foaf", FOAF)])
    names = {x.namespace: (x.prefix, x.source) for x in resolved.namespaces}
    assert names["http://ex.org/foaf/"] == ("foaf", "user")
    assert names[FOAF][0] != "foaf"


def test_a_named_parent_names_its_sub_namespace():
    resolved = resolve_namespaces(run("http://ex.org/core/A"), [e("ex", "http://ex.org/", PrefixSource.user)], packaged=[])
    assert {x.prefix for x in resolved.namespaces} >= {"ex-core"}
    assert "http://ex.org/" not in {x.namespace for x in resolved.namespaces}  # a parent only, not saved


def test_prefix_cc_offline_warns_once_and_generates(caplog):
    lookup = FakePrefixList(error="unreachable")
    with caplog.at_level(logging.WARNING):
        resolved = resolve_namespaces(run(BF + "A"), packaged=[], prefix_list=lookup)
    assert lookup.calls == 1
    assert caplog.text.count("prefix.cc lookup failed: unreachable; generating prefixes") == 1
    assert {x.prefix: x.source for x in resolved.namespaces}["brainframe"] == "generated"


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
