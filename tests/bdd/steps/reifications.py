"""Steps of the reification scenarios of statistics_collection.feature: `collect` over FakeSparql."""

from pytest_bdd import given, parsers, then, when

from fingerprint.domain.profile import ReificationKind
from tests.bdd.steps.statistics import EX, RDF, expand, fingerprint, graph, klass, people

PROV = "http://www.w3.org/ns/prov#"
NP = "http://www.nanopub.org/nschema#"
SINGLETON = RDF + "singletonPropertyOf"
KINDS = {
    "RDF statement": "rdf_statement",
    "resource as predicate": "resource_as_predicate",
}  # dict-ok: module-level lookup table


def iri(curie: str) -> str:
    for prefix, ns in (("prov:", PROV), ("np:", NP)):
        if curie.startswith(prefix):
            return ns + curie.removeprefix(prefix)
    return expand(curie)


def link(fake, i, predicate, subject_class="ex:A", object_class="ex:B"):
    """One statement of `predicate` from a fresh subject to a fresh object."""
    fake.add(f"ex:s{i}", "a", subject_class)
    fake.add(f"ex:o{i}", "a", object_class)
    fake.add(f"ex:s{i}", predicate, f"ex:o{i}")


def statements(fake, n, subject_class, predicate, object_class):
    for i in range(n):
        link(fake, i, "ex:unrelated", subject_class, object_class)
        fake.add(f"ex:st{i}", "a", RDF + "Statement")
        for p, o in (("subject", f"ex:s{i}"), ("predicate", predicate), ("object", f"ex:o{i}")):
            fake.add(f"ex:st{i}", RDF + p, o)


def relations(ctx, curie):
    return klass(ctx["run"], curie).reified_relations or []


def profiled(ctx):
    ctx["run"] = fingerprint(ctx)


def kinds_sent(ctx):
    return [q.splitlines()[0].removeprefix("# REIFY ") for q in ctx["fake"].sent("REIFY")]


# --- givens ---


@given("a graph with no rdf:Statement node")
def no_statement(ctx):
    people(ctx["fake"], 2)


@given("reifications is off")
def reifications_off(ctx):
    people(ctx["fake"], 1)
    ctx["cli"]["reifications"] = False


@given(
    parsers.parse(
        '{n:d} distinct predicate IRIs typed "{t}", each linking a subject of class "{a}" to an object of class "{b}", '
        'each with rdf:singletonPropertyOf "{generic}" and "{reifier}"'
    )
)
def singletons(ctx, n, t, a, b, generic, reifier):
    for i in range(n):
        link(ctx["fake"], i, f"ex:sp{i}", a, b)
        ctx["fake"].add(f"ex:sp{i}", "a", t)
        ctx["fake"].add(f"ex:sp{i}", SINGLETON, generic)
        ctx["fake"].add(f"ex:sp{i}", iri(reifier), "ex:someone")
    ctx["n"] = n


@given(
    parsers.parse(
        '{n:d} rdf:Statement nodes whose rdf:subject is of class "{a}", '
        'rdf:predicate is "{p}" and rdf:object is of class "{b}"'
    )
)
def rdf_statements(ctx, n, a, p, b):
    statements(ctx["fake"], n, a, p, b)


@given(
    parsers.parse(
        'predicate IRIs typed "{t}", not a property type, linking class "{a}" to class "{b}", one of them used {n:d} times'
    )
)
def resources_as_predicates(ctx, t, a, b, n):
    for i in range(n):
        link(ctx["fake"], i, "ex:proc0", a, b)
    for i in (1, 2):
        link(ctx["fake"], n + i, f"ex:proc{i}", a, b)
    for i in range(3):
        ctx["fake"].add(f"ex:proc{i}", "a", t)
    ctx["n"] = n + 2


@given(
    parsers.parse(
        'predicate IRIs typed only rdf:Property, used once each, one of them with rdf:singletonPropertyOf "{generic}"'
    )
)
def only_property(ctx, generic):
    for i in range(3):
        link(ctx["fake"], i, f"ex:old{i}")
        ctx["fake"].add(f"ex:old{i}", "a", RDF + "Property")
    ctx["fake"].add("ex:old0", SINGLETON, generic)
    ctx["n"] = 3


@given("a graph with 12 rdf:reifies triples")
def reifies(ctx):
    people(ctx["fake"], 1)
    for i in range(12):
        ctx["fake"].add(f"ex:r{i}", RDF + "reifies", f"ex:t{i}")


@given(parsers.parse('a graph holding {n:d} nanopublication heads with "{assertion}", "{provenance}" and "{info}"'))
def nanopublications(ctx, n, assertion, provenance, info):
    people(ctx["fake"], 1)
    for i in range(n):
        ctx["fake"].add(f"ex:np{i}", "a", NP + "Nanopublication")
        for predicate, part in ((assertion, "assertion"), (provenance, "provenance"), (info, "info")):
            ctx["fake"].add(f"ex:np{i}", iri(predicate), f"ex:np{i}-{part}")


@given(
    parsers.parse(
        '3 singleton predicate IRIs typed rdf:Property and "{cls}", and 2 ordinary predicates typed rdf:Property only'
    )
)
def mixed_class(ctx, cls):
    for i in range(3):
        link(ctx["fake"], i, f"ex:sp{i}")
        ctx["fake"].add(f"ex:sp{i}", SINGLETON, "ex:isRelatedTo")
        ctx["fake"].add(f"ex:sp{i}", "a", RDF + "Property")
        ctx["fake"].add(f"ex:sp{i}", "a", cls)
    for i in (3, 4):
        link(ctx["fake"], i, f"ex:old{i}")
        ctx["fake"].add(f"ex:old{i}", "a", RDF + "Property")


# --- whens ---


@when("the graph is profiled")
def graph_profiled(ctx):
    profiled(ctx)


@when("a graph with singleton properties is profiled")
def singletons_profiled(ctx):
    for i in range(2):
        link(ctx["fake"], i, f"ex:sp{i}")
        ctx["fake"].add(f"ex:sp{i}", SINGLETON, "ex:isRelatedTo")
    profiled(ctx)


# --- thens ---


@then("the collector issues the rdf:Statement probe and not its capture query")
def probe_only(ctx):
    sent = kinds_sent(ctx)
    assert "rdf_statement probe" in sent and not [s for s in sent if s.startswith("rdf_statement r")]


@then("no probe is issued")
def no_probe(ctx):
    assert ctx["fake"].sent("REIFY") == []


@then("every singleton predicate IRI is an ordinary property")
def singletons_ordinary(ctx):
    assert {EX + "sp0", EX + "sp1"} <= {p.property for p in klass(ctx["run"], "ex:A").property_partitions}


def only_relation(ctx, curie, kind, predicate, target, count):
    (relation,) = relations(ctx, curie)
    assert (relation.kind, relation.property, relation.object_class, relation.statements) == (
        KINDS[kind],
        iri(predicate),
        iri(target),
        count,
    )
    ctx["relation"] = relation


@then(parsers.parse('class "{curie}" has one reified relation of kind {kind}, "{p}" to "{target}", {count:d} statements'))
def one_relation(ctx, curie, kind, p, target, count):
    only_relation(ctx, curie, kind, p, target, count)


@then(parsers.parse('class "{curie}" has one reified relation of kind {kind}, named "{p}", to "{target}", counting every use'))
def one_relation_every_use(ctx, curie, kind, p, target):
    only_relation(ctx, curie, kind, p, target, ctx["n"])


@then(parsers.parse('its reifier property "{p}" is on {count:d}'))
def reifier_property(ctx, p, count):
    assert [(q.property, q.reifiers) for q in ctx["relation"].reifier_properties] == [(iri(p), count)]


@then(parsers.parse('its reifier properties are "{p}" on {a:d} and "{q}" on {b:d}'))
def reifier_properties(ctx, p, a, q, b):
    assert {(r.property, r.reifiers) for r in ctx["relation"].reifier_properties} == {(iri(p), a), (iri(q), b)}


@then(parsers.parse('no relation is named "{p}"'))
def no_relation_named(ctx, p):
    assert iri(p) not in {r.property for c in graph(ctx["run"]).class_partitions for r in c.reified_relations or []}


@then("each stays an ordinary property")
def each_ordinary(ctx):
    found = {p.property for p in klass(ctx["run"], "ex:A").property_partitions}
    assert {EX + f"old{i}" for i in range(ctx["n"])} <= found


@then("no reified relation is reported for them")
def none_reported(ctx):
    assert all(c.reified_relations is None for c in graph(ctx["run"]).class_partitions)


def counted(ctx, kind, n):
    assert {(c.kind, c.count) for c in graph(ctx["run"]).reification_counts} >= {(kind, n)}


@then("the graph profile counts 12 triple terms")
def triple_terms(ctx):
    counted(ctx, ReificationKind.triple_term, 12)


@then(parsers.parse("the graph profile counts {n:d} nanopublications"))
def nanopublications_counted(ctx, n):
    counted(ctx, ReificationKind.nanopublication, n)


@then("no class has a relation for them")
def no_relations(ctx):
    none_reported(ctx)


@then(parsers.parse('class "{curie}" has no ordinary property for any of the 50 predicate IRIs'))
def no_singleton_rows(ctx, curie):
    found = {p.property for p in klass(ctx["run"], curie).property_partitions}
    assert not {EX + f"sp{i}" for i in range(ctx["n"])} & found


@then(parsers.parse('the profile has no class "{curie}"'))
def profile_lacks_class(ctx, curie):
    assert iri(curie) not in {c.class_iri for c in graph(ctx["run"]).class_partitions}


@then(parsers.parse('class "{curie}" is absent'))
def class_absent(ctx, curie):
    assert expand(curie) not in {c.class_iri for c in graph(ctx["run"]).class_partitions}


@then(parsers.parse("class rdf:Property is present with {n:d} instances"))
def property_class_whole(ctx, n):
    assert klass(ctx["run"], RDF + "Property").instances == n


@then("the profile has no class rdf:Statement")
def no_statement_class(ctx):
    assert RDF + "Statement" not in {c.class_iri for c in graph(ctx["run"]).class_partitions}


@then("it has no property rdf:subject, rdf:predicate or rdf:object")
def no_statement_properties(ctx):
    found = {p.property for c in graph(ctx["run"]).class_partitions for p in c.property_partitions or []}
    assert not found & {RDF + "subject", RDF + "predicate", RDF + "object"}
