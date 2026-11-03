"""Resolving a run's namespace table (namespace-prefixes › Prefix source precedence, › prefix.cc lookup is best effort)."""

import logging

from fingerprint.adapters.prefixes import PrefixLookupError
from fingerprint.domain.profile import NamespacePrefix, PrefixSource, ValueCount
from fingerprint.service_layer.prefixes import resolve_namespaces, used_namespaces
from tests.builders import klass, profile_run, prop, resources

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
    assert message == "prefix.cc lookup failed: unreachable; generating prefixes"


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


def test_an_invalid_prefix_does_not_end_its_sources_list():
    user = [e("../../x", OTHER, PrefixSource.user), e("good", USED, PrefixSource.user)]
    assert prefix_of(resolve_namespaces(run(OTHER + "A", USED + "B"), user, packaged=[]))[USED] == "good"


def test_a_reserved_or_taken_prefix_does_not_end_its_sources_list():
    user = [e("rdf", OTHER, PrefixSource.user), e("good", USED, PrefixSource.user)]  # rdf belongs to the rdf namespace
    resolved = resolve_namespaces(run(OTHER + "A", USED + "B"), user, packaged=[])
    assert prefix_of(resolved)[USED] == "good" and prefix_of(resolved)[OTHER] != "rdf"
    taken = [e("same", OTHER, PrefixSource.user), e("SAME", USED, PrefixSource.user), e("fine", FOAF, PrefixSource.user)]
    assert prefix_of(resolve_namespaces(run(OTHER + "A", USED + "B"), taken, packaged=[]))[FOAF] == "fine"


def single_value_run(value, kind="iri", distinct=1):
    one = prop("http://ex.org/p", {1: 1}, resources(1, None, kind)).model_copy(
        update={"distinct_objects": distinct, "top_values": [ValueCount(value=value, triples=1)]}
    )
    return profile_run(klass("http://ex.org/A", 1, one))


def test_top_values_of_other_properties_name_no_namespace():
    for run_ in (
        single_value_run("http://ex.org/status/a", distinct=2),
        single_value_run("http://ex.org/status/a", "literal"),
    ):
        assert "http://ex.org/status/" not in {x.namespace for x in resolve_namespaces(run_, packaged=[]).namespaces}


def test_a_skipped_prefix_is_logged_with_its_reason(caplog):
    user = [e("../../x", OTHER, PrefixSource.user), e("rdf", USED, PrefixSource.user)]
    with caplog.at_level(logging.DEBUG, logger="fingerprint.service_layer.prefixes"):
        resolve_namespaces(run(OTHER + "A", USED + "B"), user, packaged=[])
    assert caplog.messages == [
        f"prefix '../../x' for {OTHER} skipped: not a prefix with a writable IRI",
        f"prefix 'rdf' for {USED} skipped: reserved or taken",
    ]
