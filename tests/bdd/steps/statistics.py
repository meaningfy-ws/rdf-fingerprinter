"""Steps of statistics_collection.feature: `collect` over FakeSparql."""

import io
import json
import re
import urllib.error

from pytest_bdd import given, parsers, then, when
from rdflib import Literal, URIRef

from fingerprint.adapters.sparql import PermanentError, QueryTimeout, query_name
from fingerprint.service_layer.collection import collect
from fingerprint.service_layer.settings import UsageError, load_config_file, resolve_settings
from tests.builders import XSD
from tests.fakes import EX, FakeSparql

RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
RDF_TYPE = RDF + "type"
GRAPH_A = "http://example.org/graph/a"
GRAPH_B = "http://example.org/graph/b"


def expand(curie: str) -> str:
    curie = curie.strip('"')
    for prefix, ns in (("ex:", EX), ("rdf:", RDF), ("xsd:", XSD)):
        if curie.startswith(prefix):
            return ns + curie.removeprefix(prefix)
    return curie


def http_error(code: int) -> urllib.error.HTTPError:
    return urllib.error.HTTPError("http://fake", code, "status", {}, io.BytesIO(b""))  # type: ignore[arg-type]


def exact(query: str) -> bool:
    """Exact-mode queries list no instances."""
    return "VALUES ?s" not in query and "LIMIT" not in query


def fingerprint(ctx, **cli):
    settings = resolve_settings(
        cli={**ctx["cli"], **cli}, env=ctx["env"], selected_graphs=ctx["selected"], config=ctx["config"]
    )
    return collect("http://fake/sparql", settings, ctx["fake"])


def graph(run, iri=None):
    return next(g for g in run.graphs if g.graph == iri)


def klass(run, curie, graph_iri=None):
    return next(c for c in graph(run, graph_iri).class_partitions or [] if c.class_iri == expand(curie))


def prop(cls, curie):
    return next(p for p in cls.property_partitions or [] if p.property == expand(curie))


def people(fake, n=3, cls="ex:Person", g=None):
    for i in range(n):
        fake.add(f"ex:{cls[3:]}{i}", "a", cls, g)
        fake.add(f"ex:{cls[3:]}{i}", "ex:name", Literal(f"name {i}"), g)


# --- background and shared steps ---


@given("a SPARQL endpoint holding a knowledge graph")
def endpoint(ctx):
    ctx["fake"] = FakeSparql()


@given("the default collection settings")
def default_settings(ctx):
    ctx["cli"] = {}


@when("the knowledge graph is fingerprinted")
def fingerprinted(ctx):
    try:
        ctx["run"] = fingerprint(ctx)
    except UsageError as error:
        ctx["error"] = error


@given("no graph is selected")
def none_selected(ctx):
    ctx["selected"] = None


# --- graphs and discovery ---


@given("the endpoint holds data in the default graph and in two named graphs")
def three_graphs(ctx):
    for g in (None, GRAPH_A, GRAPH_B):
        people(ctx["fake"], 1, g=g)


@given(parsers.parse('only the named graph "{iri}" is selected'))
@given(parsers.parse('the named graph "{iri}" is selected'))
def one_selected(ctx, iri):
    ctx["selected"] = [iri]
    people(ctx["fake"], 1, g=iri)


@then("the profile contains three graphs")
def contains_three(ctx):
    assert len(ctx["run"].graphs) == 3


@then("the default graph comes first")
def default_first(ctx):
    assert ctx["run"].graphs[0].graph is None


@then("the profile contains exactly that graph")
def exactly_that(ctx):
    assert [g.graph for g in ctx["run"].graphs] == ctx["selected"]


@given("counting all classes of a graph at once times out")
def class_count_timeout(ctx):
    people(ctx["fake"], 3)
    people(ctx["fake"], 2, cls="ex:Place")
    ctx["expected_counts"] = {c.class_iri: c.instances for c in graph(fingerprint(ctx)).class_partitions}
    ctx["fake"].on("Q3", QueryTimeout("timed out"))


@then("each class is counted on its own")
def counted_per_class(ctx):
    assert len(ctx["fake"].sent("Q3b")) == len(ctx["expected_counts"])


@then("the instance counts equal those of a single count")
def same_counts(ctx):
    assert {c.class_iri: c.instances for c in graph(ctx["run"]).class_partitions} == ctx["expected_counts"]


@given(parsers.parse("the endpoint answers the named-graph listing with {problem}"))
def q0_problem(ctx, problem):
    people(ctx["fake"], 1, g=GRAPH_A)
    error = QueryTimeout("timed out") if problem == "a timeout" else PermanentError("400 GRAPH ?g {} not supported")
    ctx["fake"].on("Q0", error)


@then("only the default graph is profiled")
def only_default(ctx):
    assert [g.graph for g in ctx["run"].graphs] == [None]


@then("only that graph is profiled")
def only_that(ctx):
    assert [g.graph for g in ctx["run"].graphs] == ctx["selected"]


@then("a failure about listing graphs is recorded")
def graphs_failure(ctx):
    assert [f.query_kind for f in ctx["run"].failures] == ["graphs"]


@then("no failure is recorded")
def no_failure(ctx):
    assert not ctx["run"].failures


# --- class scope and type statements ---


@when(parsers.parse('the statistics of class "{iri}" are measured'))
def measure_class(ctx, iri):
    people(ctx["fake"], 3)
    ctx["class"] = iri
    ctx["run"] = fingerprint(ctx, depth="links")


@then(parsers.parse('every measurement for that class reads only instances of "{iri}"'))
def class_bound(ctx, iri):
    for name in ("Q5", "Q6", "Q7", "Q8", "Q11"):
        for query in ctx["fake"].sent(name):
            assert f"?s a <{iri}> ." in query, name


@given(parsers.parse('every instance of "{sub}" is also typed "{sup}"'))
def also_typed(ctx, sub, sup):
    people(ctx["fake"], 2, cls=sub)
    for i in range(2):
        ctx["fake"].add(f"ex:{sub[3:]}{i}", "a", sup)


@then(parsers.parse('no property of "{cls}" is "rdf:type"'))
def no_type_property(ctx, cls):
    assert RDF_TYPE not in [p.property for p in klass(ctx["run"], cls).property_partitions]


@then(parsers.parse('the other types of "{cls}" list "{other}"'))
def co_types(ctx, cls, other):
    assert expand(other) in [c.class_iri for c in klass(ctx["run"], cls).co_types]


# --- raw statistics ---


@given(parsers.parse('class "{cls}" has {n:d} instances'))
def instances(ctx, cls, n):
    ctx["class"], ctx["n"] = cls, n
    for i in range(n):
        ctx["fake"].add(f"ex:i{i}", "a", cls)


@given(parsers.parse('their numbers of "{p}" values are {counts}'))
def numbers_of_values(ctx, p, counts):
    for i, count in enumerate(int(c) for c in re.split(r", | and ", counts)):
        for v in range(count):
            ctx["fake"].add(f"ex:i{i}", p, Literal(f"v{v}"))


@then(parsers.parse('the histogram of "{p}" on "{cls}" is:'))
def histogram(ctx, p, cls, datatable):
    bins = {b.values_per_subject: b.subjects for b in prop(klass(ctx["run"], cls), p).cardinality_histogram}
    assert bins == {int(n): int(s) for n, s in datatable[1:]}


@then(parsers.parse('{n:d} instances of "{cls}" were observed'))
def observed(ctx, n, cls):
    assert klass(ctx["run"], cls).observed_instances == n


@given(parsers.parse('the "{p}" values of "{cls}" are {values}'))
def literal_values(ctx, p, cls, values):
    ctx["class"] = cls
    for i, (text, lang) in enumerate(re.findall(r'"([^"]*)"(?:@(\w+))?', values)):
        ctx["fake"].add(f"ex:i{i}", "a", cls)
        ctx["fake"].add(f"ex:i{i}", p, Literal(text, lang=lang or None))


@then(parsers.parse('the literal value groups of "{p}" are:'))
def literal_groups(ctx, p, datatable):
    parts = prop(klass(ctx["run"], ctx["class"]), p).value_partitions
    actual = sorted(
        (x.datatype, x.language or "", x.triples, x.min_length, x.max_length) for x in parts if x.node_kind == "literal"
    )
    expected = sorted((expand(dt), lang, int(n), int(lo), int(hi)) for dt, lang, n, lo, hi in datatable[1:])
    assert actual == expected


@given(parsers.parse('"{p}" on "{cls}" points to one resource typed "{t}" and one resource without a type'))
def typed_and_untyped(ctx, p, cls, t):
    ctx["class"] = cls
    fake = ctx["fake"]
    fake.add("ex:a", "a", cls)
    fake.add("ex:a", p, "ex:b")
    fake.add("ex:a", p, "ex:c")
    fake.add("ex:b", "a", t)


@then(parsers.parse('the object groups of "{p}" record 1 object of class "{t}" and 1 untyped object'))
def object_groups(ctx, p, t):
    parts = prop(klass(ctx["run"], ctx["class"]), p).value_partitions
    resources = sorted((x.object_class or "", x.distinct_objects) for x in parts if x.node_kind != "literal")
    assert resources == [("", 1), (expand(t), 1)]


@given(parsers.parse('an object of "{p}" is typed "{t}" only in another named graph'))
def typed_elsewhere(ctx, p, t):
    fake = ctx["fake"]
    fake.add("ex:a", "a", t, GRAPH_A)
    fake.add("ex:a", p, "ex:b", GRAPH_A)
    fake.add("ex:b", "a", t, GRAPH_B)
    ctx["selected"], ctx["class"], ctx["prop"] = [GRAPH_A], t, p


@given(parsers.parse("object types are looked up in {scope}"))
def lookup_scope(ctx, scope):
    ctx["cli"]["object_type_scope"] = {"the same graph": "same_graph", "any graph": "any_graph"}[scope]


@then(parsers.parse("that object is counted as {result}"))
def counted_as(ctx, result):
    parts = prop(klass(ctx["run"], ctx["class"], GRAPH_A), ctx["prop"]).value_partitions
    found = [(x.object_class, x.object_class_graph) for x in parts if x.node_kind == "iri"]
    expected = (None, None) if result == "untyped" else (EX + "Person", GRAPH_B)
    assert found == [expected]


# --- precision ---


@given("every measurement of a class answers within the timeout")
def answers_in_time(ctx):
    people(ctx["fake"], 3)
    ctx["class"] = "ex:Person"


@then(parsers.parse('the class is marked "{label}"'))
def marked(ctx, label):
    c = klass(ctx["run"], ctx["class"])
    shown = "exact" if c.precision_mode == "exact" else f"first {c.observed_instances} of {c.instances}"
    assert shown == label


@then("its observed instances equal its instance count")
def observed_all(ctx):
    c = klass(ctx["run"], ctx["class"])
    assert c.observed_instances == c.instances


@given(parsers.parse("a class with {n:d} instances"))
def big_class(ctx, n):
    """Counts and listings are answered by rule, so no 50 000 triples are stored."""
    fake, ctx["class"] = ctx["fake"], "ex:Big"
    fake.add("ex:big0", "a", "ex:Big")
    fake.on("Q3", [{"c": EX + "Big", "instances": str(n)}])


@given("the exact read of that class times out")
@given("the exact read of a class times out")
def exact_times_out(ctx):
    if "class" not in ctx:
        people(ctx["fake"], 3)
        ctx["class"] = "ex:Person"
    ctx["fake"].on("Q8", QueryTimeout("timed out"), when=exact)


@given(parsers.parse("the first N setting is {n:d}"))
def first_n(ctx, n):
    ctx["cli"]["first_n"] = n
    rows = [{"s": f"{EX}big{i}"} for i in range(n)]
    ctx["fake"].on("QS", rows)
    for name in ("Q5", "Q6", "Q7", "Q8"):
        ctx["fake"].on(name, [], when=lambda q: not exact(q))


@then(parsers.parse("its instance count is still {n:d}"))
def still(ctx, n):
    assert klass(ctx["run"], ctx["class"]).instances == n


@given("a class is read in first-N mode")
@given("the class is read in first-N mode")
def first_n_mode(ctx):
    if "class" not in ctx:
        people(ctx["fake"], 3)
        ctx["class"] = "ex:Person"
    ctx["cli"]["precision_policy"] = "first_n"


@when("its statistics are measured")
def measured(ctx):
    ctx["run"] = fingerprint(ctx)


@then("every measurement of that class uses the same listed instances")
def same_instances(ctx):
    blocks = {re.search(r"VALUES \?s \{[^}]*\}", q).group(0) for n in ("Q5", "Q6", "Q7", "Q8") for q in ctx["fake"].sent(n)}
    assert len(blocks) == 1 and len(ctx["fake"].sent("QS")) == 1


@given("a class with fewer instances than the first N setting")
def small_class(ctx):
    people(ctx["fake"], 3)
    ctx["class"] = "ex:Person"


@when(parsers.parse('it is fingerprinted once with policy "{a}" and once with policy "{b}"'))
def twice(ctx, a, b):
    ctx["runs"] = [fingerprint(ctx, precision_policy=a), fingerprint(ctx, precision_policy=b)]


@then("both reads give the same histograms, value groups and distinct counts")
def same_reads(ctx):
    def stats(run):
        c = klass(run, ctx["class"])
        return sorted(
            p.model_dump_json(include={"property", "cardinality_histogram", "value_partitions", "distinct_objects"})
            for p in c.property_partitions
        )

    assert stats(ctx["runs"][0]) == stats(ctx["runs"][1])


@given("a class whose listed instances include blank nodes")
def blank_instances(ctx):
    ctx["fake"].add("_:b1", "a", "ex:Person")
    ctx["fake"].add("ex:p1", "a", "ex:Person")
    ctx["class"] = "ex:Person"


@then("the class is marked as having a sample that may differ between measurements")
def sample_not_shared(ctx):
    assert klass(ctx["run"], ctx["class"]).sample_shared is False


@given(parsers.parse('the precision policy is "{policy}"'))
def policy(ctx, policy):
    ctx["cli"]["precision_policy"] = policy


@then("the class is recorded as a failure")
def class_failed(ctx):
    assert not graph(ctx["run"]).class_partitions
    assert [f.class_iri for f in ctx["run"].failures] == [expand(ctx["class"])]


@then('the class is marked "first N" without an exact try')
def first_n_without_exact(ctx):
    assert klass(ctx["run"], ctx["class"]).precision_mode == "first_n"
    assert not [q for q in ctx["fake"].sent("Q8") if exact(q)]


# --- failures ---


@given(parsers.parse('every read of class "{cls}" fails'))
def big_fails(ctx, cls):
    ctx["fake"].add("ex:big", "a", cls)
    ctx["fake"].on("Q8", QueryTimeout("timed out"), when=lambda q: f"<{expand(cls)}>" in q)
    ctx["failing"] = expand(cls)


@given("all other classes answer")
def others_answer(ctx):
    people(ctx["fake"], 2)


@then("the profile contains every other class")
def every_other(ctx):
    assert [c.class_iri for c in graph(ctx["run"]).class_partitions] == [EX + "Person"]


@then(parsers.parse('one failure names "{cls}", the failed measurement and the number of attempts'))
def failure_named(ctx, cls):
    (failure,) = ctx["run"].failures
    assert (failure.class_iri, failure.query_kind, failure.attempts) == (expand(cls), "co_types", 2)


MEASUREMENTS = {
    "top values": ("Q9", "top_values", {"depth": "rich_values"}),
    "property presence check": ("Q10", "property_presence", {"precision_policy": "first_n", "completeness_check": True}),
    "incoming links": ("Q11", "incoming_links", {"depth": "links"}),
}


@given(
    parsers.re(
        r"the (?P<measurement>top values|property presence check|incoming links) of a class (?P<fails>is rejected|times out)$"
    )
)
def measurement_fails(ctx, measurement, fails):
    name, _, cli = MEASUREMENTS[measurement]
    people(ctx["fake"], 3)
    ctx["fake"].add("ex:Person0", "ex:rare", "ex:x")
    ctx["fake"].on("QS", [{"s": f"{EX}Person1"}, {"s": f"{EX}Person2"}])
    ctx["fake"].on(name, QueryTimeout("timed out") if fails == "times out" else PermanentError("400 unsupported"))
    ctx["cli"].update(cli)
    ctx["class"], ctx["measurement"] = "ex:Person", measurement


@then("the class is still profiled")
def still_profiled(ctx):
    assert klass(ctx["run"], ctx["class"])


@then(parsers.parse("only failures of the {measurement} are recorded"))
def measurement_failure(ctx, measurement):
    kinds = [f.query_kind for f in ctx["run"].failures]
    assert kinds and set(kinds) == {MEASUREMENTS[measurement][1]}


@given("the endpoint rejects a class's measurement as malformed")
def malformed(ctx):
    people(ctx["fake"], 2)
    people(ctx["fake"], 2, cls="ex:Place")
    ctx["fake"].on("Q5", http_error(400), when=lambda q: "<http://example.org/Place>" in q)


@then("the failure is recorded without retrying")
def recorded_without_retry(ctx):
    (failure,) = ctx["run"].failures
    assert failure.attempts == 1 and failure.query_kind == "cardinality_votes"
    assert len([q for q in ctx["fake"].sent("Q5") if "Place" in q]) == 1


@then("that class is left out without a first-N attempt")
def left_out_without_first_n(ctx):
    assert EX + "Place" not in [c.class_iri for c in graph(ctx["run"]).class_partitions]
    assert not [q for q in ctx["fake"].sent("QS") if "Place" in q]


@then("the other classes are still profiled")
def others_profiled(ctx):
    assert EX + "Person" in [c.class_iri for c in graph(ctx["run"]).class_partitions]


@given("the endpoint refuses one class's cardinality measurement as forbidden after the graphs were listed")
def forbidden(ctx):
    people(ctx["fake"], 2)
    people(ctx["fake"], 2, cls="ex:Place")
    ctx["fake"].on("Q5", http_error(403), when=lambda q: "<http://example.org/Place>" in q)


@then("that measurement is recorded as a failure with one attempt")
def one_attempt(ctx):
    (failure,) = ctx["run"].failures
    assert failure.attempts == 1 and failure.query_kind == "cardinality_votes"


@given('the endpoint answers a measurement with "service unavailable" once')
def unavailable_once(ctx):
    people(ctx["fake"], 2)
    ctx["fake"].on("Q5", http_error(503), times=1)


@then("the measurement is retried")
def retried(ctx):
    assert len(ctx["fake"].sent("Q5")) == 2


@given("a class IRI contains a space")
def space_iri(ctx):
    people(ctx["fake"], 2)
    ctx["fake"].add("ex:odd", "a", "http://example.org/Bad Class")


@then("that class is skipped with a failure naming the IRI")
def skipped(ctx):
    (failure,) = ctx["run"].failures
    assert "http://example.org/Bad Class" in failure.message


@given(parsers.parse("the endpoint rejects queries listing {n:d} instances as too large"))
def values_too_large(ctx, n):
    people(ctx["fake"], 3)
    ctx["class"] = "ex:Person"
    ctx["fake"].on("Q8", http_error(413), when=lambda q: "VALUES ?s" in q)


@when("a class falls back to first-N mode")
def falls_back(ctx):
    ctx["fake"].on("Q8", QueryTimeout("timed out"), when=exact)
    ctx["run"] = fingerprint(ctx)


@then("a failure for that class suggests lowering the first N setting")
def suggests_lower(ctx):
    (failure,) = ctx["run"].failures
    assert "lower --first-n" in failure.message and failure.class_iri == EX + "Person"


# --- settings ---

SETTING_NAMES = {
    "the timeout": "timeout_seconds",
    "timeout": "timeout_seconds",
    "concurrency": "concurrency",
    "top K": "top_k",
}


@given(parsers.parse("the environment sets {setting} to {value:d}"))
def env_sets(ctx, setting, value):
    ctx["env"][f"RDF_FINGERPRINTER_{SETTING_NAMES[setting].upper()}"] = str(value)


@given("no command-line option is given")
def no_cli(ctx):
    ctx["cli"] = {}


@given(parsers.parse("the command line sets {setting} to {value:d}"))
def cli_sets(ctx, setting, value):
    ctx["cli"][SETTING_NAMES[setting]] = value


@given(parsers.parse("a library caller passes the configuration setting {setting} as {value:d}"))
def library_config(ctx, setting, value):
    ctx["config"] = {SETTING_NAMES[setting]: value}


@then(parsers.parse("the recorded {setting} is {value:d}"))
def recorded(ctx, setting, value):
    assert getattr(ctx["run"].settings, SETTING_NAMES[setting]) == value


@given(parsers.parse("a configuration file setting concurrency to {n:d}"))
def config_file(ctx, n):
    ctx["config_path"] = write_config(ctx["tmp"], {"concurrency": n})


@given(parsers.parse('a configuration file holding the key "{key}"'))
def config_file_with_key(ctx, key):
    ctx["config_path"] = write_config(ctx["tmp"], {key: 1})


def write_config(directory, content):
    path = directory / "config.json"
    path.write_text(json.dumps(content))
    return path


@when("the knowledge graph is fingerprinted with that file")
def with_file(ctx):
    try:
        ctx["config"] = load_config_file(ctx["config_path"])
        ctx["run"] = fingerprint(ctx)
    except UsageError as error:
        ctx["error"] = error


@then(parsers.parse('a usage error names "{key}"'))
def usage_error_names(ctx, key):
    assert isinstance(ctx.get("error"), UsageError) and key in str(ctx["error"])


# --- depth and switches ---


@given(parsers.parse('the depth is "{depth}"'))
def depth(ctx, depth):
    fake = ctx["fake"]
    people(fake, 2)
    fake.add("ex:Person0", "a", "ex:Agent")
    fake.add("ex:Person1", "a", "ex:Agent")
    fake.add("ex:Person0", "ex:knows", "ex:Person1")
    fake.add("ex:Person", "http://www.w3.org/2000/01/rdf-schema#subClassOf", "ex:Agent")
    ctx["cli"]["depth"] = depth


def _person(run):
    return klass(run, "ex:Person")


CONTENTS = {
    "instance counts, hierarchy and other types": lambda run: (
        _person(run).instances == 2 and graph(run).declared_subclass_edges and _person(run).co_types
    ),
    "property histograms": lambda run: any(p.cardinality_histogram for p in _person(run).property_partitions or []),
    "value groups and object classes": lambda run: any(
        x.object_class for p in _person(run).property_partitions or [] for x in p.value_partitions or []
    ),
    "value groups": lambda run: any(p.value_partitions for p in _person(run).property_partitions or []),
    "top values": lambda run: any(p.top_values for p in _person(run).property_partitions or []),
    "incoming links": lambda run: bool(_person(run).incoming_links),
    "top values or incoming links": lambda run: CONTENTS["top values"](run) or CONTENTS["incoming links"](run),
    "graph totals": lambda run: graph(run).triples is not None,
}


_CONTENT = "|".join(re.escape(k) for k in sorted(CONTENTS, key=len, reverse=True))


@then(parsers.re(rf"the profile contains no (?P<absent>{_CONTENT})$"))
def contains_no(ctx, absent):
    assert not CONTENTS[absent](ctx["run"])


@then(parsers.re(rf"the profile contains (?P<present>{_CONTENT})$"))
def contains(ctx, present):
    assert CONTENTS[present](ctx["run"])


DEFAULT_QUERIES = {"Q0", "Q3", "Q4", "Q8", "Q5", "Q6", "Q7"}  # graph list, counts, hierarchy, co-types, votes, values, objects


def sent_names(ctx):
    return {query_name(q).split()[0] for q in ctx["fake"].queries}


@then("the endpoint receives the graph list, class count, hierarchy, co-type, vote, value and object-class queries")
def default_queries(ctx):
    assert DEFAULT_QUERIES <= sent_names(ctx)


@then("it receives no graph-total, top-value or incoming-link query")
def no_deeper_queries(ctx):
    assert not sent_names(ctx) & {"Q1", "Q9", "Q11"}


@given("graph statistics are switched on")
def graph_stats(ctx):
    people(ctx["fake"], 2)
    ctx["fake"].add("ex:loose", "ex:name", Literal("untyped"))
    ctx["cli"]["graph_statistics"] = True


@then("each graph records its statements, distinct subjects, distinct objects, predicates and untyped subjects")
def graph_totals(ctx):
    g = graph(ctx["run"])
    assert (g.triples, g.distinct_subjects, g.untyped_subjects) == (5, 3, 1)
    assert g.distinct_objects == 4 and {p.property for p in g.predicate_partitions} == {RDF_TYPE, EX + "name"}


@given("the completeness check is switched on")
def completeness_on(ctx):
    ctx["cli"]["completeness_check"] = True


@given(parsers.parse('only an instance outside the first N uses "{p}"'))
def rare(ctx, p):
    ctx["fake"].add("ex:Person0", p, "ex:x")
    ctx["fake"].on("QS", [{"s": f"{EX}Person1"}, {"s": f"{EX}Person2"}])


@then(parsers.parse('"{p}" is listed on that class as present, without statistics'))
def present_only(ctx, p):
    found = prop(klass(ctx["run"], ctx["class"]), p)
    assert found.presence_only is True and not found.cardinality_histogram


# --- results are read as typed RDF terms ---


@given(parsers.parse("the endpoint answers the class count as the integer {n:d}"))
def count_as_integer(ctx, n):
    ctx["fake"].on("Q3", [{"c": URIRef(EX + "Person"), "instances": Literal(n)}])


@then(parsers.parse('the instance count of "{cls}" is {n:d}'))
def instance_count(ctx, cls, n):
    assert klass(ctx["run"], cls).instances == n


@given("the endpoint does not answer an exact read within the timeout")
def no_answer(ctx):
    ctx["fake"].on("Q8", TimeoutError("timed out"), when=exact)


@given(parsers.parse('the endpoint answers the top values "{first}" as a dateTime and "{second}" in language "{lang}"'))
def raw_top_values(ctx, first, second, lang):
    """rdflib refuses the tag `en_US`, so the answer is written as the endpoint's JSON text."""
    fake = ctx["fake"]
    fake.add("ex:i0", "ex:name", Literal("x"))
    bindings = [
        {"o": {"type": "literal", "value": first, "datatype": XSD + "dateTime"}, "triples": {"type": "literal", "value": "1"}},
        {"o": {"type": "literal", "value": second, "xml:lang": lang}, "triples": {"type": "literal", "value": "1"}},
    ]
    body = json.dumps({"head": {"vars": ["o", "triples"]}, "results": {"bindings": bindings}}).encode()
    once = fake._once
    fake._once = lambda query: (fake.queries.append(query) or body) if query_name(query).startswith("Q9") else once(query)


@given("top values are collected")
def top_values_collected(ctx):
    ctx["cli"]["depth"] = "rich_values"


@then(parsers.parse('the recorded top values are "{first}" and "{second}"'))
def recorded_top_values(ctx, first, second):
    values = [v.value for v in prop(klass(ctx["run"], "ex:Person"), "ex:name").top_values]
    assert values == [first, second]
