"""Namespaces and generated prefixes (readable-representations, namespace-prefixes)."""

import pytest

from fingerprint.domain.prefixes import PrefixTable, generate_prefixes, namespace_of, path_segments
from fingerprint.domain.profile import NamespacePrefix, PrefixSource

BF = "https://ontology.brainframe.com/2016/04/brainframe#"


def entry(prefix: str, namespace: str, source: PrefixSource = PrefixSource.packaged) -> NamespacePrefix:
    return NamespacePrefix(prefix=prefix, namespace=namespace, source=source)


@pytest.mark.parametrize(
    ("iri", "namespace"),
    [
        (BF + "Person", BF),
        ("https://my.brainframe.com/#/knowledge/Person/7a08", "https://my.brainframe.com/#/knowledge/Person/"),
        ("http://ex.org/a/b", "http://ex.org/a/"),
        ("urn:x:thing:A", "urn:x:thing:"),
        ("http://ex.org/core#", "http://ex.org/core#"),
    ],
)
def test_namespace_of(iri, namespace):
    assert namespace_of(iri) == namespace


def test_fragment_segments_count_as_path_segments():
    assert path_segments("https://my.brainframe.com/#/knowledge/RelationId/") == ["knowledge", "RelationId"]
    assert path_segments(BF + "blueprint/") == ["2016", "04", "brainframe", "blueprint"]
    assert path_segments("urn:x:thing:") == ["x", "thing"]


@pytest.mark.parametrize("known_order", [1, -1])
def test_the_most_specific_named_parent_gives_the_name_whatever_the_table_order(known_order):
    known = [entry("ex", "http://ex.org/"), entry("ex-core", "http://ex.org/core/")][::known_order]
    assert [e.prefix for e in generate_prefixes(["http://ex.org/core/x/"], known)] == ["ex-core-x"]


def test_parents_are_named_before_children_and_clashes_count_up():
    graphs = ["https://ontology.brainframe.com/graph/", "https://my.brainframe.com/graph/"]
    names = {e.namespace: e.prefix for e in generate_prefixes(graphs, [])}
    assert names == {"https://my.brainframe.com/graph/": "graph", "https://ontology.brainframe.com/graph/": "graph2"}
    chain = generate_prefixes(["http://ex.org/core/x/", "http://ex.org/core/", "http://ex.org/"], [])
    assert [(e.namespace, e.prefix) for e in chain] == [
        ("http://ex.org/", "ex"),
        ("http://ex.org/core/", "ex-core"),
        ("http://ex.org/core/x/", "ex-core-x"),
    ]


def test_generation_is_deterministic():
    namespaces = [BF, "http://ex.org/a/", "http://ex.org/", "https://my.brainframe.com/#/knowledge/X/"]
    assert generate_prefixes(namespaces, []) == generate_prefixes(list(reversed(namespaces)), [])


def test_the_longest_namespace_wins():
    table = PrefixTable([entry("ex", "http://ex.org/"), entry("ex-core", "http://ex.org/core/")])
    assert table.shorten("http://ex.org/core/Thing") == ("ex-core", "Thing")
    assert table.curie("http://ex.org/Thing") == "ex:Thing"
    assert table.curie("http://ex.org/core/") == "ex-core:"
    assert table.curie("http://other.org/X") == "http://other.org/X"


def test_table_lookups():
    table = PrefixTable([entry("ex", "http://ex.org/")])
    assert table.by_prefix("ex").namespace == "http://ex.org/"
    assert table.by_namespace("http://ex.org/").prefix == "ex"
    assert table.by_prefix("nope") is None and PrefixTable(None).curie("http://ex.org/a") == "http://ex.org/a"
