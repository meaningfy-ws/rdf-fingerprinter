"""The reification stage over FakeSparql (singleton-property-pattern P-3 to P-9, P-14, design §B)."""

from pathlib import Path

from rdflib import URIRef

from fingerprint.adapters.exceptions import PermanentError
from fingerprint.adapters.reification_catalogue import packaged_templates
from fingerprint.domain.profile import QueryKind, ReificationKind
from fingerprint.service_layer.collection import collect
from fingerprint.service_layer.settings import resolve_settings
from tests.fakes import EX, FakeSparql

GRAPH = EX + "reifications"
SOURCE = Path(__file__).parents[2] / "test_data" / "reifications-source.ttl"
RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
Q = "ex:Person"


def sample() -> FakeSparql:
    fake = FakeSparql()
    fake.dataset.graph(URIRef(GRAPH)).parse(SOURCE)
    return fake


def run(fake, **cli):
    settings = resolve_settings(cli={"selected_graphs": [GRAPH], "completeness_check": False, **cli}, env={})
    return collect("http://fake/sparql", settings, fake, templates=packaged_templates())


def profile(fake, **cli):
    return run(fake, **cli).graphs[0]


def classes(graph):
    return {c.class_iri.removeprefix(EX): c for c in graph.class_partitions or []}


def sections(fake):
    return [q.splitlines()[0].removeprefix("# REIFY ") for q in fake.sent("REIFY")]


def fails_on(kind, section):
    return lambda q: q.startswith(f"# REIFY {kind} {section}")


def test_only_probes_hidden_terms_and_the_count_run_at_depth_graphs():
    fake = sample()
    graph = profile(fake, depth="graphs", graph_statistics=False)
    assert {s.split()[1] for s in sections(fake)} == {"probe", "hidden", "count"}
    assert list(graph.reification_kinds) == [
        "negative_property_assertion", "owl_axiom", "rdf_statement", "resource_as_predicate",
        "triple_term",
    ]  # fmt: skip
    assert graph.triple_term_reifications == 1


def test_graph_level_predicate_partitions_leave_out_the_machinery():
    graph = profile(sample(), depth="graphs", graph_statistics=True)
    predicates = {p.property for p in graph.predicate_partitions}
    assert EX + "rel1" not in predicates and RDF + "subject" not in predicates and EX + "legacy" in predicates


def test_machinery_leaves_classes_properties_and_links_and_the_relations_follow_their_class():
    graph = profile(sample(), depth="links")
    found = classes(graph)
    assert "Link" not in found and RDF + "Statement" not in {c.class_iri for c in found.values()}
    person = found["Person"]
    assert not {p.property for p in person.property_partitions} & {EX + "rel1", EX + "rel2"}
    assert [(r.kind, r.property, r.object_class, r.statements) for r in person.reified_relations] == [
        ("resource_as_predicate", EX + "Link", EX + "Org", 2),
        ("resource_as_predicate", EX + "Procedure", EX + "Org", 1),
        ("owl_axiom", EX + "knows", EX + "Person", 1),
        ("rdf_statement", EX + "knows", EX + "Person", 1),
        ("negative_property_assertion", EX + "worksFor", EX + "Org", 1),
    ]
    org = found["Org"]
    assert not [link for link in org.incoming_links or [] if link.property in (EX + "rel1", EX + "rel2")]
    assert org.reified_relations is None


def test_reifier_properties_are_merged_into_their_relation():
    link = classes(profile(sample(), depth="classes"))["Person"].reified_relations[0]
    assert link.property == EX + "Link"
    assert {(p.property, p.reifiers) for p in link.reifier_properties} == {
        ("http://www.w3.org/ns/prov#wasAttributedTo", 1),
        (RDF + "singletonPropertyOf", 2),
    }


def test_a_failed_probe_is_recorded_and_the_machinery_stays_ordinary():
    fake = sample()
    fake.on("REIFY", PermanentError("no"), when=fails_on("resource_as_predicate", "probe"))
    result = run(fake, depth="classes")
    (failure,) = result.failures
    assert (failure.query_kind, failure.check_id, failure.graph) == (QueryKind.reification, "resource_as_predicate", GRAPH)
    graph = result.graphs[0]
    assert ReificationKind.resource_as_predicate not in graph.reification_kinds and "Link" in classes(graph)
    assert not [s for s in sections(fake) if s.startswith("resource_as_predicate r")]


def test_a_failed_hidden_query_keeps_the_machinery_but_still_captures_the_relations():
    fake = sample()
    fake.on("REIFY", PermanentError("no"), when=fails_on("resource_as_predicate", "hidden"))
    result = run(fake, depth="classes")
    assert [f.check_id for f in result.failures] == ["resource_as_predicate"]
    found = classes(result.graphs[0])
    assert "Link" in found
    assert ReificationKind.resource_as_predicate in {r.kind for r in found["Person"].reified_relations}


def test_a_failed_relations_query_omits_the_relations_but_keeps_the_hiding():
    fake = sample()
    fake.on("REIFY", PermanentError("no"), when=fails_on("resource_as_predicate", "relations"))
    result = run(fake, depth="classes")
    assert [f.check_id for f in result.failures] == ["resource_as_predicate"]
    found = classes(result.graphs[0])
    assert "Link" not in found
    assert ReificationKind.resource_as_predicate not in {r.kind for r in found["Person"].reified_relations}


def test_a_failed_count_leaves_the_triple_term_count_unset():
    fake = sample()
    fake.on("REIFY", PermanentError("no"), when=fails_on("triple_term", "count"))
    result = run(fake, depth="graphs")
    assert result.graphs[0].triple_term_reifications is None and [f.check_id for f in result.failures] == ["triple_term"]


def test_no_kind_found_leaves_the_kinds_unset_and_nothing_is_captured():
    fake = FakeSparql()
    fake.add("ex:a", "a", Q, GRAPH)
    fake.add("ex:a", "ex:name", "n", GRAPH)
    fake.add("ex:legacy", "a", RDF + "Property", GRAPH)
    graph = profile(fake)
    assert graph.reification_kinds is None and graph.triple_term_reifications is None
    assert all(s.endswith("probe") for s in sections(fake))


def test_switch_off_sends_no_reification_query():
    fake = sample()
    graph = profile(fake, reifications=False)
    assert fake.sent("REIFY") == [] and graph.reification_kinds is None and "Link" in classes(graph)


def reified(fake, subject_classes, n=1, subject="ex:s", obj="ex:o", predicate="ex:p"):
    for c in subject_classes:
        fake.add(subject, "a", c, GRAPH)
    fake.add(obj, "a", "ex:B", GRAPH)
    for i in range(n):
        for p, o in (
            ("a", RDF + "Statement"),
            (RDF + "subject", subject),
            (RDF + "predicate", predicate),
            (RDF + "object", obj),
        ):
            fake.add(f"ex:st{i}", p, o, GRAPH)


def test_a_subject_with_two_classes_files_the_relation_under_both():
    fake = FakeSparql()
    reified(fake, ["ex:A", "ex:A2"])
    found = classes(profile(fake))
    assert [r.statements for r in found["A"].reified_relations] == [1] == [r.statements for r in found["A2"].reified_relations]


def test_a_statement_about_an_untyped_subject_is_dropped():
    fake = FakeSparql()
    reified(fake, [])
    graph = profile(fake)
    assert all(c.reified_relations is None for c in graph.class_partitions or [])


def test_a_relation_of_an_unprofiled_class_is_dropped():
    fake = FakeSparql()
    reified(fake, ["ex:A"])
    fake.on("Q8", PermanentError("no"), when=lambda q: "example.org/A>" in q)
    graph = profile(fake)
    assert "A" not in classes(graph) and all(c.reified_relations is None for c in graph.class_partitions)


def test_an_untyped_object_gives_a_relation_without_an_object_class():
    fake = FakeSparql()
    reified(fake, ["ex:A"])
    fake.dataset.graph(URIRef(GRAPH)).remove((URIRef(EX + "o"), None, None))
    (relation,) = classes(profile(fake))["A"].reified_relations
    assert relation.object_class is None and relation.property == EX + "p"


def test_relations_are_sorted_by_statements_then_predicate_then_object_class():
    fake = FakeSparql()
    reified(fake, ["ex:A"], n=1, predicate="ex:b")
    for i in range(3):
        for p, o in (
            ("a", RDF + "Statement"),
            (RDF + "subject", "ex:s"),
            (RDF + "predicate", "ex:z"),
            (RDF + "object", "ex:o"),
        ):
            fake.add(f"ex:big{i}", p, o, GRAPH)
    for p, o in (("a", RDF + "Statement"), (RDF + "subject", "ex:s"), (RDF + "predicate", "ex:a"), (RDF + "object", "ex:o")):
        fake.add("ex:small", p, o, GRAPH)
    order = [(r.property.removeprefix(EX), r.statements) for r in classes(profile(fake))["A"].reified_relations]
    assert order == [("z", 3), ("a", 1), ("b", 1)]
