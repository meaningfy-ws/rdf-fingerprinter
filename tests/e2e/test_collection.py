"""Collection and analysis of the loaded test store (`make oxigraph-load-test-data`)."""

from fingerprint.adapters.sparql import SparqlWrapperClient
from fingerprint.domain.analytics import analyse
from fingerprint.service_layer.collection import collect
from fingerprint.service_layer.settings import resolve_settings
from tests import LOCAL_ENDPOINT


def fingerprint(**cli):
    settings = resolve_settings(cli=cli, env={})
    return collect(LOCAL_ENDPOINT, settings, SparqlWrapperClient(LOCAL_ENDPOINT, settings.timeout_seconds))


def test_every_graph_is_profiled_without_failures():
    run = fingerprint(depth="links", graph_statistics=True, completeness_check=True)
    assert [g.graph for g in run.graphs][0] is None and len(run.graphs) == 3
    assert not run.failures
    assert all(g.class_partitions for g in run.graphs)
    assert analyse(run).graphs[1].class_count == len(run.graphs[1].class_partitions)


def test_first_n_reads_at_most_n_instances():
    run = fingerprint(precision_policy="first_n", first_n=2)
    assert all(c.observed_instances <= 2 for g in run.graphs for c in g.class_partitions)
