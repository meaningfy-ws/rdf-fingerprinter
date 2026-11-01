"""Invariants of the domain that must hold for any input, not only the examples (lean-test-suite P-9, DEC-7)."""

from hypothesis import given

from fingerprint.domain.analytics import analyse, cardinality_statistics
from fingerprint.domain.exceptions import IriRefError
from fingerprint.domain.iri import to_iriref
from fingerprint.domain.prefixes import PrefixTable
from tests.builders import profile_run
from tests.unit.domain.strategies import class_with, histograms, profiled_properties, raw_iris, table_and_iri

RATIOS = (
    "confidence",
    "label_support",
    "type_purity",
    "untyped_object_ratio",
    "language_coverage",
    "distinct_ratio",
    "top_k_share",
)


@given(table_and_iri())
def test_expanding_the_compacted_form_of_an_iri_gives_the_iri_back(case):
    table, iri = case
    prefix, local = PrefixTable(table).shorten(iri)
    assert PrefixTable(table).by_prefix(prefix).namespace + local == iri


@given(table_and_iri())
def test_when_several_namespaces_match_the_longest_is_chosen(case):
    table, iri = case
    chosen = PrefixTable(table).entry_for(iri)
    assert chosen.namespace == max((e.namespace for e in table if iri.startswith(e.namespace)), key=len)


@given(histograms())
def test_cardinality_statistics_are_ordered_min_mean_max(case):
    observed, histogram = case
    stats = cardinality_statistics(histogram, observed)
    assert 0 <= stats.min <= stats.mean_when_present <= stats.max
    assert stats.min <= stats.mean <= stats.max


@given(profiled_properties())
def test_every_ratio_in_the_analytics_lies_between_zero_and_one(case):
    observed, prop = case
    analysed = analyse(profile_run(class_with(observed, prop))).graphs[0].class_partitions[0].property_partitions[0]
    for name in RATIOS:
        value = getattr(analysed, name)
        assert value is None or 0 <= value <= 1, name


@given(raw_iris)
def test_to_iriref_gives_a_valid_iriref_or_raises(iri):
    try:
        result = to_iriref(iri)
    except IriRefError:
        return
    assert result == f"<{iri}>"
    assert not any(c in '<>"{}|^`\\' or c <= " " for c in iri)
