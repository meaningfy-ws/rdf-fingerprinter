"""Every section of every packaged reification template is accepted by the real engine (singleton-property-pattern P-15)."""

import pytest

from fingerprint.adapters.queries import reification_query
from fingerprint.adapters.reification_catalogue import packaged_templates
from fingerprint.adapters.sparql import SparqlHttpClient
from tests import LOCAL_ENDPOINT

SECTIONS = ("probe", "relations", "reifier-properties", "hidden", "count")
GRAPHS = [None, "http://example.org/reifications"]
CASES = [(t, s) for t in packaged_templates() for s in SECTIONS if getattr(t, s.replace("-", "_"))]


@pytest.mark.parametrize("graph", GRAPHS, ids=["default-graph", "named-graph"])
@pytest.mark.parametrize("template,section", CASES, ids=lambda v: getattr(v, "id", v))
def test_the_engine_accepts_the_rendered_section(template, section, graph):
    sparql = SparqlHttpClient(LOCAL_ENDPOINT, timeout_seconds=30)
    query = reification_query(template, section, graph)
    (sparql.ask if section == "probe" else sparql.select)(query)  # an engine error raises
