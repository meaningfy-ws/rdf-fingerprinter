"""Collection and analysis of the loaded test store (`make oxigraph-load-test-data`)."""

import json
from pathlib import Path

from fingerprint.adapters.profile_file import load_profile
from fingerprint.adapters.sparql import SparqlHttpClient
from fingerprint.domain.analytics import analyse
from fingerprint.service_layer.collection import collect
from fingerprint.service_layer.settings import resolve_settings
from tests import LOCAL_ENDPOINT


def fingerprint(**cli):
    settings = resolve_settings(cli=cli, env={})
    return collect(LOCAL_ENDPOINT, settings, SparqlHttpClient(LOCAL_ENDPOINT, settings.timeout_seconds))


def test_every_graph_is_profiled_without_failures():
    run = fingerprint(depth="links", graph_statistics=True, completeness_check=True)
    assert [g.graph for g in run.graphs][0] is None and len(run.graphs) == 3
    assert not run.failures
    assert all(g.class_partitions for g in run.graphs)
    assert analyse(run).graphs[1].class_count == len(run.graphs[1].class_partitions)


def test_first_n_reads_at_most_n_instances():
    run = fingerprint(precision_policy="first_n", first_n=2)
    assert all(c.observed_instances <= 2 for g in run.graphs for c in g.class_partitions)


def test_a_live_collection_equals_the_sample_profile():
    """Typed rdflib rows build the same profile the 2.1 sample holds (domain-object-model P-8)."""
    sample = load_profile(Path(__file__).parents[1] / "test_data" / "profiles" / "sample-profile.json")
    run = collect(LOCAL_ENDPOINT, sample.settings, SparqlHttpClient(LOCAL_ENDPOINT, sample.settings.timeout_seconds))
    varying = {"started_at", "finished_at", "tool_version"}
    assert ordered(run.model_dump(exclude_none=True, exclude=varying)) == ordered(
        sample.model_dump(exclude_none=True, exclude=varying)
    )


def ordered(value):
    """Lists sorted by their JSON text: stores may return rows (e.g. property partitions) in any order."""
    if isinstance(value, dict):
        return {key: ordered(item) for key, item in value.items()}  # dict-ok: comparing JSON dumps
    if isinstance(value, list):
        return sorted((ordered(item) for item in value), key=lambda item: json.dumps(item, sort_keys=True, default=str))
    return value
