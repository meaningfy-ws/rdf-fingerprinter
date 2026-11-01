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
    (message,) = caplog.messages
    assert "prefix.cc" in message and "unreachable" in message


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


# --- decisions the first tests left open (lean-test-suite 7.5) ---

RDF_NS = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
USED, OTHER = "http://used.example/", "http://other.example/"


def prefix_of(resolved):
    return {x.namespace: x.prefix for x in resolved.namespaces}


def test_a_namespace_that_cannot_be_written_is_not_in_use():
    assert used_namespaces(profile_run(klass("http://ex.org/a b/Thing", 1))) == {RDF_NS}


def test_a_prefix_for_a_namespace_not_in_use_does_not_hold_the_name():
    """The user's `u` for an unused namespace must not block the saved `u` of a used one."""
    saved = run(USED + "A").model_copy(update={"namespaces": [e("u", USED, PrefixSource.user)]})
    resolved = resolve_namespaces(saved, [e("u", "http://unused.example/", PrefixSource.user)], packaged=[])
    assert prefix_of(resolved)[USED] == "u" and "http://unused.example/" not in prefix_of(resolved)


def test_an_invalid_prefix_does_not_end_its_sources_list():
    user = [e("../../x", OTHER, PrefixSource.user), e("good", USED, PrefixSource.user)]
    assert prefix_of(resolve_namespaces(run(OTHER + "A", USED + "B"), user, packaged=[]))[USED] == "good"


def test_a_reserved_or_taken_prefix_does_not_end_its_sources_list():
    user = [e("rdf", OTHER, PrefixSource.user), e("good", USED, PrefixSource.user)]  # rdf belongs to the rdf namespace
    resolved = resolve_namespaces(run(OTHER + "A", USED + "B"), user, packaged=[])
    assert prefix_of(resolved)[USED] == "good" and prefix_of(resolved)[OTHER] != "rdf"
    taken = [e("same", OTHER, PrefixSource.user), e("SAME", USED, PrefixSource.user), e("fine", FOAF, PrefixSource.user)]
    assert prefix_of(resolve_namespaces(run(OTHER + "A", USED + "B"), taken, packaged=[]))[FOAF] == "fine"


def test_pitfall_example_iris_are_named():
    from fingerprint.domain.profile import GraphProfile, PitfallExample, PitfallResult, PitfallTerm

    example = PitfallExample(
        entity=PitfallTerm(text="http://other.org/vocab#thing", kind="iri"),
        value=PitfallTerm(text="http://not.an.iri.org/x", kind="literal"),
    )
    result = PitfallResult(check_id="c", title="t", importance="minor", scope="data", source="s", count=1, examples=[example])
    scanned = run(BF + "A").model_copy(update={"graphs": [GraphProfile(pitfalls=[result])]})
    namespaces = {x.namespace for x in resolve_namespaces(scanned, packaged=[]).namespaces}
    assert "http://other.org/vocab#" in namespaces and "http://not.an.iri.org/" not in namespaces
