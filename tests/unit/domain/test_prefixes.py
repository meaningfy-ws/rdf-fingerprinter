"""Namespaces and generated prefixes (readable-representations, namespace-prefixes)."""

import pytest

from fingerprint.domain.prefixes import PrefixTable, generate_prefixes, is_reserved, namespace_of, path_segments
from fingerprint.domain.profile import NamespacePrefix, PrefixSource

BF = "https://ontology.brainframe.com/2016/04/brainframe#"


def entry(prefix: str, namespace: str, source: PrefixSource = PrefixSource.packaged) -> NamespacePrefix:
    return NamespacePrefix(prefix=prefix, namespace=namespace, source=source)


@pytest.mark.parametrize(
    ("iri", "namespace"),
    [
        ("http://ex.org/a/b", "http://ex.org/a/"),
        ("urn:x:thing:A", "urn:x:thing:"),
        ("http://ex.org/core#", "http://ex.org/core#"),
        ("http://ex.org/a/#x", "http://ex.org/a/#"),
        ("http://ex.org/a#/b", "http://ex.org/a#/"),
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


def test_table_lookups():
    table = PrefixTable([entry("ex", "http://ex.org/")])
    assert table.by_prefix("ex").namespace == "http://ex.org/"
    assert table.by_namespace("http://ex.org/").prefix == "ex"
    assert table.by_prefix("nope") is None and PrefixTable(None).curie("http://ex.org/a") == "http://ex.org/a"


EX = "http://example.org/"
FILTER_TABLE = PrefixTable(
    [entry("ex", EX), entry("rel", EX + "rel/"), entry("relx", EX + "relx/"), entry("org", "http://org.example/")]
)


@pytest.mark.parametrize(
    ("value", "prefixes"),
    [
        ("rel", ["rel"]),  # exact prefix
        ("rel*", ["rel", "relx"]),  # glob
        ("*lx", ["relx"]),
        ("*x", ["ex", "relx"]),  # `ex` ends with `x` too: the table of the design's §A and the scenario say `relx` only
        ("*", ["ex", "rel", "relx", "org"]),  # in namespace order
        ("**", ["ex", "rel", "relx", "org"]),  # repeated stars
        ("r*l*", ["rel", "relx"]),
        ("Rel*", []),  # a glob is case-sensitive
        ("REL", []),
        ("", []),
        ("nope", []),
        (EX + "rel/", ["rel"]),  # stem: `…/relx/` does not start with `…/rel/`
        (EX, ["ex", "rel", "relx"]),  # a full namespace IRI is a stem: it takes the namespaces under it
        ("http://org.example/", ["org"]),
        ("HTTP://example.org/", []),  # a stem is case-sensitive
        (EX + "*", []),  # `*` is literal in a stem
        ("http:", ["ex", "rel", "relx", "org"]),
    ],
)
def test_match_applies_the_first_rule_that_fits(value, prefixes):
    assert [e.prefix for e in FILTER_TABLE.match(value)] == prefixes


def test_a_glob_takes_dot_question_mark_and_brackets_literally():
    table = PrefixTable(
        [entry("a.bc", "http://a/"), entry("axbc", "http://b/"), entry("a-b", "http://c/"), entry("a[b]", "http://d/")]
    )
    assert [e.prefix for e in table.match("a.b*")] == ["a.bc"]
    assert [e.prefix for e in table.match("a?b*")] == []
    assert [e.prefix for e in table.match("a[b]*")] == ["a[b]"]


def test_match_lists_the_namespaces_in_iri_order():
    table = PrefixTable([entry("z", "http://a.org/"), entry("a", "http://z.org/")])
    assert [e.namespace for e in table.match("*")] == ["http://a.org/", "http://z.org/"]


def test_the_namespace_of_the_iri_wins_over_a_longer_entry_that_only_starts_the_local_name():
    table = PrefixTable([entry("p1", "http://ex.org/a/"), entry("p2", "http://ex.org/a/b")])
    assert table.shorten("http://ex.org/a/bc") == ("p1", "bc")


def test_an_iri_deeper_than_any_namespace_takes_the_longest_one_that_starts_it():
    table = PrefixTable([entry("ex", "http://ex.org/"), entry("exa", "http://ex.org/a/")])
    assert table.shorten("http://ex.org/a/b/c") == ("exa", "b/c")


def test_is_reserved():
    assert is_reserved("shape") and is_reserved("x-shape") and is_reserved("rdf")
    assert not is_reserved("rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#") and not is_reserved("foo")


@pytest.mark.parametrize(
    ("namespace", "prefix"),
    [
        ("http://ex.org/shape/", "shape2"),  # `shape` is reserved for the shapes
        ("http://ex.org/_core_/", "core"),
        ("http://ex.org/a--b/", "a-b"),
        ("http://ex.org/3d/", "n3d"),
        ("http://www.ex.org/", "ex"),
        ("http://ex.co.uk/", "ex"),
        ("http://a.name.org/", "name"),
    ],
)
def test_the_own_name_of_a_namespace(namespace, prefix):
    assert [e.prefix for e in generate_prefixes([namespace], [])] == [prefix]


@pytest.mark.parametrize("order", [1, -1])
@pytest.mark.parametrize(
    ("known", "namespace", "prefix"),
    [
        # a table entry of another scheme or namespace does not end the search
        ([("u", "urn:x:"), ("other", "http://other.org/"), ("ex", "http://ex.org/")], "http://ex.org/core/", "ex-core"),
        # the deepest named parent wins whatever its prefix sorts like
        ([("zz", "http://ex.org/"), ("aa", "http://ex.org/core/")], "http://ex.org/core/x/", "aa-x"),
        # a parent by host and a parent by path of the same depth: the later prefix wins
        ([("aa", "http://a.b.org/"), ("zz", "http://b.org/x/")], "http://a.b.org/x/", "zz-a"),
        # an entry with the same host and path is no parent, only a clash
        ([("exns", "http://ex.org/a")], "http://ex.org/a/", "a"),
        ([("other", "http://other.org/")], "http://ex.org/", "ex"),
    ],
)
def test_the_parent_of_a_namespace(known, namespace, prefix, order):
    table = [entry(p, ns) for p, ns in known][::order]
    assert [e.prefix for e in generate_prefixes([namespace], table)] == [prefix]


def test_a_host_parent_is_named_before_its_child_though_it_sorts_after_it():
    names = {e.namespace: e.prefix for e in generate_prefixes(["http://a.b.org/x/", "http://b.org/x/"], [])}
    assert names == {"http://b.org/x/": "x", "http://a.b.org/x/": "x-a"}
