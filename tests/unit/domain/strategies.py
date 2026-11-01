"""Hypothesis strategies for domain properties (lean-test-suite P-9); domain-only imports, per the domain-tests fence."""

from hypothesis import strategies as st

from fingerprint.domain.profile import (
    AnnotationValue,
    CardinalityBin,
    ClassProfile,
    NamespacePrefix,
    PrefixSource,
    ProfileRun,
    PropertyProfile,
    TermAnnotation,
    ValueCount,
    ValuePartition,
)
from fingerprint.domain.vocabulary import ALT_LABEL, RDFS, TERM_DESCRIPTION_PREDICATES, TERM_LABEL_PREDICATES
from tests import builders

_LABEL = st.text("abcdefghijklmnopqrstuvwxyz0123456789", min_size=1, max_size=6)
_NAMESPACES = st.builds(
    lambda host, path, sep: (
        f"http://{host}.org/{'/'.join(path)}{'/' if path else ''}" if sep == "/" else f"http://{host}.org/{'/'.join(path)}#"
    ),
    _LABEL,
    st.lists(_LABEL, max_size=3),
    st.sampled_from("/#"),
)
iris = st.builds(lambda ns, local: ns + local, _NAMESPACES, _LABEL)
# Any text, including the characters an IRIREF forbids.
raw_iris = st.text(max_size=30)


@st.composite
def prefix_tables(draw):
    """Entries with distinct prefixes and distinct namespaces, some nested inside others."""
    roots = draw(st.lists(_NAMESPACES, min_size=1, max_size=4, unique=True))
    slashed = [ns for ns in roots if ns.endswith("/")]
    nested = (
        draw(st.lists(st.builds(lambda ns, label: f"{ns}{label}/", st.sampled_from(slashed), _LABEL), max_size=3))
        if slashed
        else []
    )
    namespaces = list(dict.fromkeys([*roots, *nested]))
    return [NamespacePrefix(prefix=f"p{i}", namespace=ns, source=PrefixSource.packaged) for i, ns in enumerate(namespaces)]


@st.composite
def table_and_iri(draw):
    """A prefix table and an IRI under one of its namespaces, its local part holding any number of `/`."""
    table = draw(prefix_tables())
    base = draw(st.sampled_from([e.namespace for e in table]))
    return table, base + "/".join(draw(st.lists(_LABEL, min_size=1, max_size=3)))


@st.composite
def histograms(draw, min_bins=1):
    """(observed instances, histogram): bins of n >= 0 with distinct n, their subjects adding up to at most `observed`."""
    ns = draw(st.lists(st.integers(0, 6), min_size=min_bins, max_size=4, unique=True))
    subjects = [draw(st.integers(0 if min_bins == 0 else 1, 20)) for _ in ns]
    observed = draw(st.integers(sum(subjects), sum(subjects) + 20))
    return observed, [CardinalityBin(values_per_subject=n, subjects=s) for n, s in zip(ns, subjects, strict=True)]


@st.composite
def profiled_properties(draw):
    """(observed, property): a histogram plus value partitions whose triples add up to the histogram's total."""
    observed, histogram = draw(histograms())
    total = sum(b.values_per_subject * b.subjects for b in histogram)
    literal = draw(st.integers(0, total))
    partitions: list[ValuePartition] = []
    if literal:
        partitions.append(builders.literals(literal, language=draw(st.sampled_from([None, "en"]))))
    if total - literal:
        partitions.append(builders.resources(total - literal, draw(st.sampled_from([None, "http://ex.org/C"]))))
    return observed, PropertyProfile(
        property="http://ex.org/p",
        cardinality_histogram=histogram,
        value_partitions=partitions,
        distinct_objects=draw(st.integers(0, total)),
    )


def class_with(observed: int, prop: PropertyProfile) -> ClassProfile:
    return builders.klass("http://ex.org/C", observed, prop)


_TERMS = st.sampled_from(["http://ex.org/A", "http://ex.org/B", "http://ex.org/p"])
_ANNOTATION_PREDICATES = st.sampled_from([*TERM_LABEL_PREDICATES, ALT_LABEL, *TERM_DESCRIPTION_PREDICATES, RDFS + "seeAlso"])


def annotation_values():
    """A list of raw annotation rows over few terms, predicates, languages and texts, so rows collide."""
    return st.lists(
        st.builds(
            AnnotationValue,
            term=_TERMS,
            predicate=_ANNOTATION_PREDICATES,
            text=st.sampled_from(["A", "B", "Zed"]),
            language=st.sampled_from([None, "en", "fr"]),
        ),
        max_size=12,
    )


_CLASSES = [f"http://ex.org/C{i}" for i in range(4)]
_OBJECT_CLASSES = st.sampled_from([*_CLASSES, "http://other.org/X", None])


def _partitions():
    """A literal, or IRIs or blank nodes of one of the classes, each with as many distinct objects as triples."""
    return st.one_of(
        st.builds(builders.literals, st.integers(1, 6)),
        st.builds(
            lambda n, cls, kind: builders.resources(n, cls, kind).model_copy(update={"distinct_objects": n}),
            st.integers(1, 6),
            _OBJECT_CLASSES,
            st.sampled_from(["iri", "blank_node"]),
        ),
    )


@st.composite
def pattern_graphs(draw):
    """The classes of a small graph: properties p0-p2 reach classes C0-C3 by IRIs, blank nodes or literals."""
    classes = []
    for index in draw(st.lists(st.integers(0, 3), unique=True, max_size=4)):
        instances = draw(st.integers(1, 6))
        properties = [
            builders.prop(f"http://ex.org/p{j}", {1: instances}, *draw(st.lists(_partitions(), max_size=3)))
            for j in draw(st.lists(st.integers(0, 2), unique=True, max_size=3))
        ]
        classes.append(builders.klass(_CLASSES[index], instances, *properties))
    return classes


# Three namespaces, one of them under another's IRI: the world of the namespace filter's properties.
FILTER_NAMESPACES = ["http://ex.org/", "http://ex.org/rel/", "http://org.org/"]
FILTER_TABLE = [
    NamespacePrefix(prefix=p, namespace=ns, source=PrefixSource.packaged)
    for p, ns in zip(["ex", "rel", "org"], FILTER_NAMESPACES, strict=True)
]
_FILTER_TERMS = st.builds(lambda ns, name: ns + name, st.sampled_from(FILTER_NAMESPACES), st.sampled_from("abcd"))


@st.composite
def _filter_property(draw, iri):
    """A property whose objects are literals and resources of the namespaces, with top values that are sometimes one IRI."""
    parts = draw(
        st.lists(
            st.one_of(_partitions(), st.builds(builders.resources, st.integers(1, 6), _FILTER_TERMS)), min_size=1, max_size=3
        )
    )
    total = sum(p.triples for p in parts)
    distinct = draw(st.integers(1, 2))
    values = st.lists(_FILTER_TERMS, unique=True, max_size=distinct)  # no more top values than distinct objects
    top = [ValueCount(value=v, triples=draw(st.integers(1, 6))) for v in draw(values)]
    return builders.prop(iri, {1: total}, *parts).model_copy(update={"distinct_objects": distinct, "top_values": top or None})


@st.composite
def filter_runs(draw):
    """A run of up to two graphs: classes, properties, co-types, declared parents and annotations drawn from three
    namespaces, so that every position `exclude_terms` filters occurs."""
    graphs = []
    for _ in range(draw(st.integers(0, 2))):
        iris = draw(st.lists(_FILTER_TERMS, unique=True, max_size=4))
        classes = []
        for iri in iris:
            properties = [draw(_filter_property(p)) for p in draw(st.lists(_FILTER_TERMS, unique=True, max_size=3))]
            classes.append(
                builders.klass(
                    iri,
                    draw(st.integers(1, 6)),
                    *properties,
                    co_types=[(c, 1) for c in draw(st.lists(_FILTER_TERMS, max_size=2, unique=True))],
                )
            )
        edges = draw(st.lists(st.tuples(_FILTER_TERMS, _FILTER_TERMS), max_size=2))
        base = builders.profile_run(*classes, graph=draw(st.sampled_from([None, "http://g.org/g"])), edges=edges).graphs[0]
        notes = draw(st.one_of(st.none(), st.lists(st.builds(TermAnnotation, term=_FILTER_TERMS), max_size=3)))
        graphs.append(base.model_copy(update={"term_annotations": notes}))
    run = builders.profile_run()
    return ProfileRun(settings=run.settings, graphs=graphs, namespaces=FILTER_TABLE)
