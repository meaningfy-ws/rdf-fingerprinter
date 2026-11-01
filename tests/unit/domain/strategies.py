"""Hypothesis strategies for domain properties (lean-test-suite P-9); domain-only imports, per the domain-tests fence."""

from hypothesis import strategies as st

from fingerprint.domain.profile import (
    CardinalityBin,
    ClassProfile,
    NamespacePrefix,
    PrefixSource,
    PropertyProfile,
    ValuePartition,
)
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
    namespaces = draw(st.lists(_NAMESPACES, min_size=1, max_size=6, unique=True))
    return [NamespacePrefix(prefix=f"p{i}", namespace=ns, source=PrefixSource.packaged) for i, ns in enumerate(namespaces)]


@st.composite
def table_and_iri(draw):
    """A prefix table and an IRI built from one of its namespaces or from the IRI's own namespace."""
    table = draw(prefix_tables())
    base = draw(st.sampled_from([e.namespace for e in table]))
    return table, base + draw(_LABEL)


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
