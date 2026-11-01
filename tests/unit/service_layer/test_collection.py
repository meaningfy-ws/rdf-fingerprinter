"""Error-matrix rows and query selection of `collect` (design.md "Error matrix", "Which queries run")."""

import logging
import re
import urllib.error

import pytest
from pydantic import ValidationError
from rdflib import Literal

from fingerprint import __version__
from fingerprint.adapters.sparql import EndpointUnreachable, PermanentError, QueryTimeout, query_name, redact
from fingerprint.service_layer.collection import collect
from fingerprint.service_layer.settings import UsageError, resolve_settings
from tests.fakes import EX, FakeSparql

TIMEOUT, REJECTED = QueryTimeout("timed out"), PermanentError("400 unsupported", 400)


@pytest.fixture
def fake():
    fake = FakeSparql()
    for i in range(2):
        fake.add(f"ex:p{i}", "a", "ex:Person")
        fake.add(f"ex:p{i}", "ex:name", Literal(f"n{i}"))
    return fake


def run(fake, **cli):
    return collect("http://user:secret@fake/sparql?key=k", resolve_settings(cli=cli, env={}), fake)


def kinds(result):
    return [(f.query_kind, f.message) for f in result.failures]


@pytest.mark.parametrize(
    "query, error, cli, kind, message",
    [
        ("Q4", TIMEOUT, {}, "declared_hierarchy", "declared hierarchy not read"),
    ],
)
def test_discovery_failures_are_recorded(fake, query, error, cli, kind, message):
    fake.on("Q2", TIMEOUT)  # so Q2a runs
    fake.on(query, error)
    (failure,) = [f for f in run(fake, **cli).failures]
    assert failure.query_kind == kind and message in failure.message


def test_q2_timeout_falls_back_to_q2a(fake):
    fake.on("Q2", TIMEOUT)
    graph = run(fake, graph_statistics=True).graphs[0]
    assert {p.property for p in graph.predicate_partitions} == {EX + "name", "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"}
    assert all(p.triples is None for p in graph.predicate_partitions)


@pytest.mark.parametrize("error", [TIMEOUT, REJECTED])
def test_class_counts_fall_back_per_class_without_a_failure(fake, error):
    fake.on("Q3", error)
    result = run(fake)
    assert not result.failures and result.graphs[0].class_partitions[0].instances == 2


def test_classes_not_listed(fake):
    fake.on("Q3", TIMEOUT)
    fake.on("Q3a", TIMEOUT)
    result = run(fake)
    assert kinds(result) == [("class_partitions", "graph default: classes not listed: timed out")]
    assert not result.graphs[0].class_partitions


def test_a_class_whose_own_count_times_out_is_left_out_and_recorded(fake):
    fake.add("ex:c", "a", "ex:City")
    fake.on("Q3", TIMEOUT)
    fake.on("Q3b", TIMEOUT, when=lambda q: "City" in q)
    result = run(fake)
    assert [c.class_iri for c in result.graphs[0].class_partitions] == [EX + "Person"]
    assert [f.class_iri for f in result.failures] == [EX + "City"]


def test_blank_node_class_is_skipped(fake):
    fake.add("ex:x", "a", "_:anonymous")
    result = run(fake)
    assert [f.query_kind for f in result.failures] == ["class_partitions"]
    assert "not usable in a SPARQL query" in result.failures[0].message


def test_unreachable_endpoint_is_named_without_credentials(fake):
    fake.on("Q0", urllib.error.URLError(ConnectionRefusedError("refused")))
    with pytest.raises(EndpointUnreachable) as raised:
        run(fake)
    assert "cannot reach endpoint http://fake/sparql" in str(raised.value) and "secret" not in str(raised.value)


def test_default_depth_sends_only_its_queries(fake):
    run(fake)
    sent = {q.lstrip("# ").split()[0] for q in fake.queries}
    assert sent == {"Q0", "Q4", "Q3", "Q5", "Q6", "Q7", "Q8", "Q12"}


def test_failures_are_logged(fake, caplog):
    fake.on("Q4", TIMEOUT)
    with caplog.at_level(logging.WARNING):
        run(fake)
    assert "declared hierarchy not read" in caplog.text


@pytest.mark.parametrize(
    "kwargs",
    [
        {"env": {"RDF_FINGERPRINTER_ACCEPTANCE_THRESHOLD": "0"}},
        {"env": {"RDF_FINGERPRINTER_ACCEPTANCE_THRESHOLD": "0.0"}},
        {"env": {}, "config": {"acceptance_threshold": 0}},
    ],
)
def test_zero_threshold_is_refused_from_every_source(kwargs):
    with pytest.raises(UsageError):
        resolve_settings(**kwargs)


def test_profile_objects_are_read_only(fake):
    result = run(fake)
    with pytest.raises(ValidationError):
        result.endpoint = "http://other"


@pytest.mark.parametrize(
    "url, shown",
    [
        ("https://user:pw@host:8890/sparql?key=abc", "https://host:8890/sparql"),
        ("http://localhost:7878/query", "http://localhost:7878/query"),
    ],
)
def test_redact(url, shown):
    assert redact(url) == shown


# --- decisions no Gherkin scenario reaches (mutation triage, lean-test-suite 7.5) ---

G = EX + "g"
RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
RDF_TYPE = RDF + "type"
BAD = "http://example.org/a b"  # a space cannot appear in a SPARQL IRI reference
DENIED = PermanentError("400 unsupported", 400)


def people(graph=None):
    fake = FakeSparql()
    for i in range(2):
        fake.add(f"ex:p{i}", "a", "ex:Person", graph)
        fake.add(f"ex:p{i}", "ex:name", Literal(f"n{i}"), graph)
    return fake


def collected(fake, graph=None, **cli):
    settings = resolve_settings(cli=cli, env={}, selected_graphs=[graph] if graph else None)
    return collect("http://fake/sparql", settings, fake)


def rich(graph=G):
    """Two Persons (one also an Agent) with literals, typed and untyped links and a property only p1 has."""
    fake = FakeSparql()
    triples = [
        ("ex:p0", "a", "ex:Person"), ("ex:p1", "a", "ex:Person"), ("ex:p0", "a", "ex:Agent"),
        ("ex:p0", "ex:name", Literal("Ann", lang="en")), ("ex:p1", "ex:name", Literal("Bo", lang="en")),
        ("ex:p0", "ex:age", Literal(30)), ("ex:p1", "ex:age", Literal(5)),
        ("ex:p0", "ex:knows", "ex:p1"), ("ex:p0", "ex:knows", "ex:x"),
        ("ex:p0", "ex:mix", Literal("t")), ("ex:p0", "ex:mix", "ex:x"),
        ("ex:p1", "ex:rare", "ex:x"),
    ]  # fmt: skip
    for triple in triples:
        fake.add(*triple, graph)
    return fake


def klass(result, name="Person"):
    return next(c for c in result.graphs[0].class_partitions if c.class_iri == EX + name)


def prop(cls, name):
    return next(p for p in cls.property_partitions if p.property == EX + name)


def test_a_named_graph_is_read_value_by_value():
    result = collected(rich(), G, depth="links", graph_statistics=True, top_k=5)
    graph, person, agent = result.graphs[0], klass(result), klass(result, "Agent")
    assert not result.failures and graph.graph == G
    assert (graph.triples, graph.distinct_subjects, graph.distinct_objects, graph.untyped_subjects) == (12, 2, 9, 0)
    assert {(p.property, p.triples) for p in graph.predicate_partitions} == {
        (EX + "name", 2), (EX + "age", 2), (EX + "knows", 2), (EX + "mix", 2), (EX + "rare", 1), (RDF_TYPE, 3),
    }  # fmt: skip
    assert [(c.class_iri, c.subjects) for c in person.co_types] == [(EX + "Agent", 1)]
    name = prop(person, "name")
    (words,) = name.value_partitions
    assert (name.distinct_objects, [(b.values_per_subject, b.subjects) for b in name.cardinality_histogram]) == (2, [(1, 2)])
    assert (words.datatype, words.language, words.triples, words.distinct_objects) == (RDF + "langString", "en", 2, 2)
    assert (words.min_length, words.max_length, words.total_length, words.min_value, words.max_value) == (2, 3, 5, "Ann", "Bo")
    assert sorted((v.value, v.triples) for v in name.top_values) == [("Ann", 1), ("Bo", 1)] and name.top_values_exact
    assert sorted((v.value, v.triples) for v in prop(agent, "name").top_values) == [("Ann", 1)]
    assert prop(person, "mix").distinct_objects == 2  # one literal and one resource, summed over the groups
    links = prop(person, "knows").value_partitions
    assert sorted((v.object_class or "", v.triples, v.distinct_objects) for v in links) == [("", 1, 1), (EX + "Person", 1, 1)]
    assert {(i.subject_class, i.property, i.triples) for i in person.incoming_links} == {
        (EX + "Person", EX + "knows", 1), (EX + "Agent", EX + "knows", 1),
    }  # fmt: skip


def test_a_first_n_sample_is_shared_and_asks_about_rare_properties_only():
    fake = rich()
    fake.on("QS", [{"s": EX + "p0"}])
    result = collected(fake, G, depth="links", precision_policy="first_n", first_n=1, completeness_check=True)
    person = klass(result)
    assert (person.precision_mode, person.observed_instances, person.sample_shared) == ("first_n", 1, True)
    assert prop(person, "name").top_values_exact is False
    assert [(p.property, p.presence_only) for p in person.property_partitions if p.presence_only] == [(EX + "rare", True)]
    assert RDF_TYPE not in [p.property for p in person.property_partitions]
    assert len(fake.sent("Q10")) == 2 and all(EX + "rare" in q for q in fake.sent("Q10"))  # once per class
    for name in ("Q5", "Q6", "Q7", "Q8", "Q9", "Q11"):
        assert fake.sent(name) and all("VALUES ?s" in q and f"GRAPH <{G}>" in q for q in fake.sent(name))


@pytest.mark.parametrize("policy, completeness", [("exact", True), ("first_n", False)])
def test_presence_is_asked_only_of_a_sample_with_the_check_on(policy, completeness):
    fake = rich()
    fake.on("QS", [{"s": EX + "p0"}])
    collected(fake, G, precision_policy=policy, first_n=1, completeness_check=completeness)
    assert not fake.sent("Q10")


def test_the_graph_list_is_read_and_a_listing_failure_says_why():
    fake = FakeSparql()
    fake.add("ex:a", "a", "ex:A", G)
    assert [g.graph for g in collected(fake).graphs] == [None, G]
    for error, reason in ((TIMEOUT, "timeout"), (DENIED, "400 unsupported")):
        fake = FakeSparql()
        fake.on("Q0", error)
        (failure,) = collected(fake).failures
        assert failure.message == f"named graphs not listed ({reason}); profiling the default graph only"


def test_a_run_records_when_it_ran_and_with_which_version():
    result = collected(people())
    assert result.started_at.tzinfo is not None and result.started_at <= result.finished_at
    assert result.finished_at.tzinfo is not None and result.tool_version == __version__


def test_depth_graphs_reads_no_hierarchy():
    fake = people()
    collected(fake, depth="graphs")
    assert [query_name(q).split()[0] for q in fake.queries] == ["Q0"]


def test_the_hierarchy_keeps_only_complete_rows():
    fake = people()
    fake.on("Q4", [{"sub": EX + "A", "sup": EX + "B"}, {"sub": EX + "A"}, {"sup": EX + "B"}])
    edges = collected(fake).graphs[0].declared_subclass_edges
    assert [(e.sub_class, e.super_class) for e in edges] == [(EX + "A", EX + "B")]


def test_classes_are_profiled_largest_first_then_by_iri():
    fake = FakeSparql()
    rows = [("B", 2), ("A", 2), ("C", 5), ("D", 1)]
    fake.on("Q3", [{"c": EX + c, "instances": str(n)} for c, n in rows])
    classes = collected(fake).graphs[0].class_partitions
    assert [(c.class_iri, c.instances) for c in classes] == [(EX + "C", 5), (EX + "A", 2), (EX + "B", 2), (EX + "D", 1)]


def test_counts_that_arrive_empty_are_none_or_zero():
    fake = people()
    fake.on("Q2", [{"p": EX + "a", "triples": ""}, {"p": EX + "b"}])
    fake.on("Q3", [{"c": EX + "Person", "instances": None}])
    result = collected(fake, graph_statistics=True)
    assert [p.triples for p in result.graphs[0].predicate_partitions] == [None, None]
    assert klass(result).instances == 0


def test_a_class_count_that_arrives_empty_is_zero_when_counted_on_its_own():
    fake = people()
    fake.on("Q3", TIMEOUT)
    fake.on("Q3b", [{"instances": None}])
    assert klass(collected(fake)).instances == 0


def test_the_fallback_queries_stay_in_their_graph():
    fake = people(G)
    fake.on("Q2", TIMEOUT)
    fake.on("Q3", TIMEOUT)
    result = collected(fake, G, graph_statistics=True)
    assert not result.failures
    assert {p.property for p in result.graphs[0].predicate_partitions} == {NAME, RDF_TYPE}
    assert klass(result).instances == 2


def test_a_blank_node_sample_is_taken_inside_its_graph():
    fake = people(G)
    fake.add("_:b", "a", "ex:Person", G)
    result = collected(fake, G, precision_policy="first_n", first_n=3)
    person = klass(result)
    assert not result.failures and person.sample_shared is False and person.observed_instances == 3
    assert [(b.values_per_subject, b.subjects) for b in prop(person, "name").cardinality_histogram] == [(1, 2)]


@pytest.mark.parametrize("graph", [None, G])
def test_a_failed_presence_check_names_its_class_and_property(graph):
    fake = people(graph)
    fake.add("ex:p1", "ex:rare", "ex:x", graph)
    fake.on("QS", [{"s": EX + "p0"}])
    fake.on("Q10", DENIED)
    result = collected(fake, graph, precision_policy="first_n", first_n=1, completeness_check=True)
    expected = ("property_presence", f"class {PERSON}, property {EX}rare: Q10 failed: 400 unsupported")
    assert failure_of(result) == (*expected, graph, PERSON, EX + "rare", None)


def test_value_rows_are_grouped_by_property_and_typed_by_what_they_carry():
    fake = people()
    columns = dict.fromkeys(
        (
            "p",
            "kind",
            "distinct",
            "dt",
            "lang",
            "triples",
            "min_length",
            "max_length",
            "total_length",
            "min_value",
            "max_value",
        )
    )
    fake.on(
        "Q6",
        [
            columns | {"kind": "literal", "triples": "1"},  # no property: skipped, the rows after it are still read
            columns | {"p": EX + "tag", "kind": "literal", "lang": "en", "triples": "2", "distinct": "3"},
            columns | {"p": EX + "plain", "kind": "literal", "triples": "1"},
        ],
    )
    cls = klass(collected(fake, depth="values"))
    tag, plain = prop(cls, "tag"), prop(cls, "plain")
    assert (tag.distinct_objects, tag.value_partitions[0].datatype, tag.value_partitions[0].language) == (
        3,
        RDF + "langString",
        "en",
    )
    assert (plain.distinct_objects, plain.value_partitions[0].datatype, plain.value_partitions[0].distinct_objects) == (
        0,
        None,
        None,
    )


def failure_of(result):
    (failure,) = result.failures
    return (failure.query_kind, failure.message, failure.graph, failure.class_iri, failure.property, failure.attempts)


PERSON, NAME = EX + "Person", EX + "name"
OF_PERSON = f"class {PERSON}: not profiled after "
REJECTED_BY = "{} rejected by endpoint: {}"


@pytest.mark.parametrize("graph", [None, G])
@pytest.mark.parametrize(
    "rules, cli, kind, message, cls, property, attempts",
    [
        ([("Q2", TIMEOUT), ("Q2a", DENIED)], {"graph_statistics": True}, "predicate_partitions",
         "graph {g}: predicates not listed; completeness check skipped", None, None, None),
        ([("Q1", TIMEOUT)], {"graph_statistics": True}, "triples", "graph {g}: Q1 timed out after 60 s", None, None, None),
        ([("QU", DENIED)], {"graph_statistics": True}, "untyped_subjects",
         "graph {g}: QU failed: 400 unsupported", None, None, None),
        ([("Q3", TIMEOUT), ("Q3a", DENIED)], {}, "class_partitions",
         "graph {g}: classes not listed: 400 unsupported", None, None, None),
        ([("Q3", TIMEOUT), ("Q3b", DENIED)], {}, "class_partitions",
         "graph {g}: class " + PERSON + " not counted: 400 unsupported", PERSON, None, None),
        ([("Q3", TIMEOUT), ("Q3a", [{"c": BAD}])], {}, "class_partitions",
         f"skipping {BAD!r}: not usable in a SPARQL query", BAD, None, None),
        ([("Q9", DENIED)], {"depth": "rich_values"}, "top_values",
         f"class {PERSON}, property {NAME}: Q9 failed: 400 unsupported", PERSON, NAME, None),
        ([("Q11", DENIED)], {"depth": "links"}, "incoming_links",
         f"class {PERSON}: Q11 failed: 400 unsupported", PERSON, None, None),
        ([("Q5", DENIED)], {}, "cardinality_votes", "Q5 rejected by endpoint: 400 unsupported", PERSON, None, 1),
        ([("Q6", DENIED)], {}, "value_partitions", "Q6 rejected by endpoint: 400 unsupported", PERSON, None, 1),
        ([("Q7", DENIED)], {}, "object_classes", "Q7 rejected by endpoint: 400 unsupported", PERSON, None, 1),
        ([("Q8", DENIED)], {}, "co_types", "Q8 rejected by endpoint: 400 unsupported", PERSON, None, 1),
        ([("Q5", EndpointUnreachable("forbidden", 403))], {}, "cardinality_votes",
         "Q5 rejected by endpoint: forbidden", PERSON, None, 1),
        ([("Q8", TIMEOUT)], {}, "co_types", OF_PERSON + "2 attempts", PERSON, None, 2),
        ([("Q5", TIMEOUT)], {}, "cardinality_votes", OF_PERSON + "2 attempts", PERSON, None, 2),
        ([("QS", TIMEOUT)], {"precision_policy": "first_n"}, "subject_stream", OF_PERSON + "1 attempts", PERSON, None, 1),
        ([("Q8", TIMEOUT)], {"precision_policy": "exact"}, "co_types", OF_PERSON + "1 attempts", PERSON, None, 1),
        ([("QS", [{"s": BAD}])], {"precision_policy": "first_n"}, "subject_stream",
         f"skipping {BAD!r}: not usable in a SPARQL query", PERSON, None, None),
        ([("Q8", PermanentError("413 too large", 413))], {"precision_policy": "first_n", "first_n": 7}, "co_types",
         f"class {PERSON}: endpoint rejected 7-IRI query; lower --first-n", PERSON, None, 1),
        ([("Q8", PermanentError("500 boom", 500))], {"precision_policy": "first_n"}, "co_types",
         "Q8 rejected by endpoint: 500 boom", PERSON, None, 1),
        ([("Q8", PermanentError("413 too large", 413))], {"precision_policy": "exact"}, "co_types",
         "Q8 rejected by endpoint: 413 too large", PERSON, None, 1),
        ([("QS", PermanentError("413 too large", 413))], {"precision_policy": "first_n"}, "subject_stream",
         "QS rejected by endpoint: 413 too large", PERSON, None, 1),
    ],
)  # fmt: skip
def test_failures_name_their_query_graph_class_property_and_attempts(
    graph, rules, cli, kind, message, cls, property, attempts
):
    fake = people(graph)
    for query, outcome in rules:
        fake.on(query, outcome)
    expected = (kind, message.format(g=graph or "default"), graph, cls, property, attempts)
    assert failure_of(collected(fake, graph, **cli)) == expected


def test_a_graph_iri_unusable_in_a_query_is_skipped_by_name():
    result = collected(FakeSparql(), BAD)
    assert failure_of(result) == ("class_partitions", f"skipping {BAD!r}: not usable in a SPARQL query", BAD, None, None, None)


def test_a_blank_node_class_is_skipped_with_its_graph_and_text():
    fake = people(G)
    fake.add("ex:x", "a", "_:anonymous", G)
    kind, message, graph, cls, *_ = failure_of(collected(fake, G))
    assert (kind, graph, cls) == ("class_partitions", G, "_:anonymous") and message.startswith("skipping '_:anonymous'")


# --- term annotations (llm-schema-tools TC-C1) ---


def annotated_terms(query):
    """The IRIs in a Q12 query's VALUES block."""
    return sorted(re.findall(r"<([^>]+)>", query.split("VALUES ?t {")[1].split("}")[0]))


def test_term_annotations_are_asked_once_per_graph_after_the_classes_for_the_classes_and_their_properties():
    fake = people()
    fake.add("ex:p0", "http://www.w3.org/2004/02/skos/core#prefLabel", Literal("Pip", lang="en"))
    result = collected(fake, depth="properties")
    (query,) = fake.sent("Q12")
    assert annotated_terms(query) == [EX + "Person", EX + "name", "http://www.w3.org/2004/02/skos/core#prefLabel"]
    assert fake.queries.index(query) > max(i for i, q in enumerate(fake.queries) if q.startswith("# Q8"))
    assert result.graphs[0].term_annotations == []


def test_the_classes_alone_are_annotated_at_depth_classes_and_no_term_is_asked_at_depth_graphs():
    fake = people()
    collected(fake, depth="classes")
    assert [annotated_terms(q) for q in fake.sent("Q12")] == [[EX + "Person"]]
    none = people()
    collected(none, depth="graphs")
    assert not none.sent("Q12")


def test_a_graph_with_no_class_stores_an_empty_list_and_sends_no_annotation_query():
    fake = FakeSparql()
    fake.add("ex:s", "ex:p", "ex:o")
    result = collected(fake)
    assert not fake.sent("Q12") and result.graphs[0].term_annotations == []


def test_a_property_that_cannot_be_written_is_left_out_of_the_annotation_query_without_a_failure():
    fake = people()
    fake.on("Q5", [{"p": BAD, "n": "1", "subjects": "2"}, {"p": EX + "name", "n": "1", "subjects": "2"}])
    result = collected(fake, depth="properties")
    assert annotated_terms(fake.sent("Q12")[0]) == [EX + "Person", EX + "name"]
    assert not [f for f in result.failures if f.query_kind == "term_annotations"]


def test_rows_are_selected_per_term_and_a_failure_leaves_none():
    fake = people()
    fake.add("ex:Person", "http://www.w3.org/2000/01/rdf-schema#label", Literal("Person", lang="en"))
    (annotation,) = collected(fake).graphs[0].term_annotations
    assert (annotation.term, [(t.text, t.language) for t in annotation.labels]) == (EX + "Person", [("Person", "en")])
    failing = people()
    failing.on("Q12", DENIED)
    result = collected(failing)
    assert result.graphs[0].term_annotations is None
    assert failure_of(result)[:2] == ("term_annotations", "graph default: term annotations not read: 400 unsupported")


def test_language_tags_of_annotations_are_lower_cased():
    fake = people()
    fake.add("ex:Person", "http://www.w3.org/2000/01/rdf-schema#label", Literal("Person", lang="EN"))
    (annotation,) = collected(fake).graphs[0].term_annotations
    assert [t.language for t in annotation.labels] == ["en"]


def test_two_graphs_send_one_annotation_query_each():
    fake = people()
    for i in range(2):
        fake.add(f"ex:q{i}", "a", "ex:Person", G)
    result = collected(fake)
    assert [g.graph for g in result.graphs] == [None, G]
    assert len(fake.sent("Q12")) == 2


@pytest.mark.parametrize("code", [429, 502])
def test_a_transient_failure_of_the_annotation_query_is_retried(code):
    fake = people()
    fake.on("Q12", urllib.error.HTTPError("http://fake", code, "status", {}, None), times=1)  # type: ignore[arg-type]
    result = collected(fake)
    assert len(fake.sent("Q12")) == 2
    assert result.graphs[0].term_annotations == [] and not result.failures


def test_a_failure_of_the_annotation_query_names_its_graph():
    failing = people(G)
    failing.on("Q12", DENIED)
    kind, message, graph, *_ = failure_of(collected(failing, G))
    assert (kind, message, graph) == ("term_annotations", f"graph {G}: term annotations not read: 400 unsupported", G)


def test_an_annotation_whose_value_is_an_iri_has_no_language():
    fake = people()
    fake.on("Q12", [{"t": PERSON, "p": "http://www.w3.org/2000/01/rdf-schema#label", "v": EX + "Thing"}])
    (annotation,) = collected(fake).graphs[0].term_annotations
    assert [(t.text, t.language) for t in annotation.labels] == [(EX + "Thing", None)]


# --- what the collection logs (lean-test-suite: the operator's messages are pinned) ---

LOGGER = "fingerprint.service_layer.collection"


@pytest.mark.parametrize("graph, label", [(None, "default"), (G, G)])
def test_a_failed_predicate_listing_is_logged_with_its_graph_and_reason(caplog, graph, label):
    for error, reason in ((TIMEOUT, "timed out after 60 s"), (DENIED, "rejected by endpoint: 400 unsupported")):
        caplog.clear()
        fake = people(graph)
        fake.on("Q2", error)
        with caplog.at_level(logging.WARNING, logger=LOGGER):
            collected(fake, graph, graph_statistics=True)
        assert f"graph {label}: Q2 {reason}" in caplog.messages


@pytest.mark.parametrize("graph, label", [(None, "default"), (G, G)])
def test_each_graph_and_each_class_is_logged_as_profiled(caplog, graph, label):
    with caplog.at_level(logging.INFO, logger=LOGGER):
        collected(people(graph), graph, depth="classes")
    assert f"graph {label}: profiling" in caplog.messages
    assert f"class {PERSON}: exact, 2 of 2 instances, 1 queries" in caplog.messages


def test_a_class_that_times_out_is_logged_with_the_precision_it_tries_next(caplog):
    fake = people()
    fake.on("Q8", TIMEOUT, times=1)
    with caplog.at_level(logging.INFO, logger=LOGGER):
        collected(fake)
    assert f"class {PERSON}: exact timed out after 60 s; trying first_n" in caplog.messages
    assert f"class {PERSON}: first_n, 2 of 2 instances, 5 queries" in caplog.messages
    last = people()
    last.on("Q8", TIMEOUT)
    with caplog.at_level(logging.WARNING, logger=LOGGER):
        collected(last)
    assert f"class {PERSON}: first_n timed out after 60 s; trying nothing" in caplog.messages
