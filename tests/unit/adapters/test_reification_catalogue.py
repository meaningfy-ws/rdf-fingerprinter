"""The reification catalogue: packaged templates and their validation (singleton-property-pattern P-1, P-2, P-16)."""

import re

import pytest

from fingerprint.adapters.queries import reification_query
from fingerprint.adapters.reification_catalogue import ReificationTemplateError, packaged_templates, validate
from fingerprint.domain.profile import ReificationKind

PROBE = "ASK { $graph_open ?s ?sp ?o . ?sp rdf:singletonPropertyOf ?g . $graph_close }"
PREFIX = "PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\n"
HEADER = "# id: singleton_property\n# title: T\n# family: statement_identity\n"
HIDDEN = "SELECT DISTINCT ?term WHERE { $graph_open ?term rdf:singletonPropertyOf ?g . $graph_close }"


def section(kind, name, query):
    return f"# REIFY {kind} {name}\n{PREFIX}{query}\n"


def template(**sections):
    """A template file: the probe and any other section given as {name: query} (dashes as underscores)."""
    body = "".join(section("singleton_property", name.replace("_", "-"), query) for name, query in sections.items())
    return HEADER + body


def test_packaged_catalogue_holds_the_stage_one_kinds():
    templates = {t.id: t for t in packaged_templates()}
    assert set(templates) == set(ReificationKind)
    assert templates["triple_term"].relations is None
    assert templates["singleton_property"].reifier_properties


def test_a_valid_file_is_split_into_its_sections():
    found = validate(template(probe=PROBE, hidden=HIDDEN), "test")
    assert (found.id, found.title, found.family) == ("singleton_property", "T", "statement_identity")
    assert found.probe.startswith("# REIFY singleton_property probe\n")
    assert found.hidden.startswith("# REIFY singleton_property hidden\n")
    assert found.relations is None


@pytest.mark.parametrize(
    ("text", "message"),
    [
        (HEADER + section("singleton_property", "hidden", HIDDEN), "no probe"),
        (template(probe="SELECT ?s WHERE { ?s ?p ?o }"), "must be an ASK"),
        (template(probe=PROBE, relations="SELECT ?a WHERE { ?a ?b ?c }"), "?subjectClass ?predicate ?objectClass ?statements"),
        (template(probe=PROBE, reifier_properties="SELECT ?a WHERE { ?a ?b ?c }"), "?reifierProperty"),
        (template(probe=PROBE, hidden="SELECT ?x WHERE { ?x ?b ?c }"), "?term"),
        (template(probe=PROBE, count="SELECT ?n WHERE { ?n ?b ?c }"), "?count"),
        (template(probe=PROBE, hidden="SELECT ?term FROM <http://x/g> WHERE { ?term ?b ?c }"), "FROM"),
        (template(probe="ASK FROM <http://x/g> { ?s ?p ?o }"), "FROM"),
        (template(probe="ASK { ?s ?p"), "not a SPARQL query"),
        (template(probe="ASK { ?s ?p $other }"), "placeholder"),
        (HEADER + "# REIFY singleton_property bogus\nASK { ?s ?p ?o }\n", "unknown section"),
        (template(probe=PROBE).replace("# REIFY singleton_property probe", "# REIFY owl_axiom probe"), "must equal the id"),
        (template(probe=PROBE) + section("singleton_property", "probe", PROBE), "twice"),
        (template(probe=PROBE).replace("# id: singleton_property", "# id: made_up"), "not a reification kind"),
        (template(probe=PROBE).replace("# title: T\n", ""), "missing header key"),
        (template(probe=PROBE).replace("# id: singleton_property\n", ""), "missing header key"),
    ],
)
def test_a_template_that_breaks_the_contract_is_rejected(text, message):
    with pytest.raises(ReificationTemplateError, match=re.escape(message)):
        validate(text, "bad.rq")


def test_a_rejection_names_the_origin():
    with pytest.raises(ReificationTemplateError, match=r"^bad\.rq:"):
        validate(template(probe="ASK { ?s ?p"), "bad.rq")


def test_reification_query_fills_the_graph_for_a_named_graph():
    found = validate(template(probe=PROBE), "test")
    query = reification_query(found, "probe", "http://example.org/g")
    assert "GRAPH <http://example.org/g> {" in query
    assert "$" not in query


def test_reification_query_fills_the_default_graph_and_distinct():
    sub = "SELECT $distinct ?term WHERE { $graph_open ?term rdf:singletonPropertyOf ?g . $graph_close }"
    found = validate(template(probe=PROBE, hidden=sub), "test")
    assert "GRAPH" not in reification_query(found, "probe", None)
    assert re.search(r"SELECT DISTINCT\s+\?term", reification_query(found, "hidden", None))
    assert not re.search("DISTINCT", reification_query(found, "hidden", "http://example.org/g"))


def test_reification_query_refuses_a_section_the_template_lacks():
    found = validate(template(probe=PROBE), "test")
    with pytest.raises(ValueError, match="relations"):
        reification_query(found, "relations", None)
