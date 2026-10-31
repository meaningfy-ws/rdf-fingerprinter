import pytest

from fingerprint.domain.analytics import analyse, cardinality_label, cardinality_statistics
from fingerprint.domain.profile import ProfileRun

EX = "http://example.org/"
RDFS_LABEL = "http://www.w3.org/2000/01/rdf-schema#label"
SKOS_PREF = "http://www.w3.org/2004/02/skos/core#prefLabel"


def prop(name, bins=None, **extra):
    """A raw property profile; `bins` maps values-per-subject to subjects."""
    profile = {"property": EX + name, **extra}
    if bins is not None:
        profile["cardinality_histogram"] = [{"values_per_subject": n, "subjects": s} for n, s in bins.items()]
    return profile


def cls(name, instances, properties=(), mode="exact", observed=None, co_types=None):
    return {
        "class_iri": EX + name,
        "instances": instances,
        "observed_instances": instances if observed is None else observed,
        "precision_mode": mode,
        "property_partitions": list(properties),
        "co_types": [{"class_iri": EX + c, "subjects": s} for c, s in (co_types or {}).items()],
    }


def run(*classes, edges=(), settings=None, **graph):
    return ProfileRun(
        endpoint="http://localhost/sparql",
        settings=settings or {},
        graphs=[
            {
                "class_partitions": list(classes),
                "declared_subclass_edges": [{"sub_class": EX + a, "super_class": EX + b} for a, b in edges],
                **graph,
            }
        ],
    )


def classes_of(raw_run):
    return {c.class_iri.removeprefix(EX): c for c in analyse(raw_run).graphs[0].class_partitions}


def props_of(analysed_class):
    return {p.property.removeprefix(EX): p for p in analysed_class.property_partitions}


# --- cardinality statistics (2.3) ---


@pytest.mark.parametrize(
    "observed, bins, expected",
    [
        (4, {1: 2, 2: 1}, dict(min=0, max=2, mean=1.0, confidence=0.75, mean_when_present=4 / 3)),
        (3, {1: 3}, dict(min=1, max=1, mean=1.0, confidence=1.0, is_mandatory=True, is_functional=True)),
        (5, {2: 5}, dict(min=2, max=2, mean=2.0, confidence=1.0, is_functional=False)),
        (10, {1: 1}, dict(min=0, max=1, mean=0.1, confidence=0.1, is_mandatory=False)),
    ],
)
def test_cardinality_statistics_keep_the_1x_meaning(observed, bins, expected):
    stats = cardinality_statistics(bins, observed)
    for key, value in expected.items():
        assert stats[key] == pytest.approx(value), key


def test_median_mode_and_stddev_include_the_zero_bin():
    stats = cardinality_statistics({1: 2, 2: 1}, 4)  # values 0, 1, 1, 2
    assert stats["median"] == 1.0
    assert stats["mode"] == 1
    assert stats["stddev"] == pytest.approx(0.7071, abs=1e-4)
    assert stats["subjects_without_property"] == 1
    assert stats["total_triples"] == 4


def test_mode_tie_takes_the_smallest_n():
    assert cardinality_statistics({1: 2, 2: 2}, 4)["mode"] == 1


def test_no_observed_instances_gives_no_means():
    stats = cardinality_statistics({}, 0)
    assert "mean" not in stats and "confidence" not in stats


# --- cardinality label (2.4) ---


@pytest.mark.parametrize(
    "observed, bins, label, support, alternatives, exact_count",
    [
        (100, {1: 97, 2: 3}, "exactly_one", 0.97, [], None),
        (100, {1: 100}, "exactly_one", 1.0, [], None),
        (100, {3: 96, 4: 4}, "exactly_n", 0.96, ["exactly_one"], 3),
        (100, {1: 50, 2: 50}, "one_or_more", 1.0, ["exactly_one"], None),
        (100, {1: 90}, "zero_or_one", 1.0, ["exactly_one"], None),
        (4, {1: 2, 2: 1}, "zero_or_more", 1.0, ["one_or_more", "zero_or_one"], None),
    ],
)
def test_cardinality_label(observed, bins, label, support, alternatives, exact_count):
    result = cardinality_label(bins, observed, 0.95)
    assert result["cardinality_label"] == label
    assert result["label_support"] == pytest.approx(support)
    assert result["alternative_labels"] == alternatives
    assert result.get("exact_count") == exact_count


def test_exactly_n_picks_the_smallest_qualifying_k():
    assert cardinality_label({2: 50, 3: 50}, 100, 0.5)["exact_count"] == 2


# --- value profile (2.5) ---


def literal(dt, triples, distinct=None, lang=None, total_length=None):
    part = {"node_kind": "literal", "datatype": dt, "triples": triples, "distinct_objects": distinct or triples}
    if lang is not None:
        part["language"] = lang
    if total_length is not None:
        part["total_length"] = total_length
    return part


def resource(triples, object_class=None, kind="iri", graph=None):
    part = {"node_kind": kind, "triples": triples, "distinct_objects": triples}
    if object_class:
        part["object_class"] = EX + object_class
    if graph:
        part["object_class_graph"] = graph
    return part


@pytest.mark.parametrize(
    "partitions, kind",
    [
        ([literal("xsd:string", 3)], "datatype_property"),
        ([resource(3, "Person")], "object_property"),
        ([literal("xsd:string", 1), resource(2)], "mixed"),
    ],
)
def test_property_kind(partitions, kind):
    p = prop("p", {1: 3}, value_partitions=partitions, distinct_objects=3)
    assert props_of(classes_of(run(cls("C", 3, [p])))["C"])["p"].property_kind == kind


def test_value_types_purity_languages_and_lengths():
    rdf_lang = "http://www.w3.org/1999/02/22-rdf-syntax-ns#langString"
    xsd_string = "http://www.w3.org/2001/XMLSchema#string"
    p = prop(
        "name",
        {1: 3},
        distinct_objects=3,
        value_partitions=[
            literal(rdf_lang, 2, lang="en", total_length=5),
            literal(xsd_string, 1, total_length=4),
        ],
    )
    a = props_of(classes_of(run(cls("Person", 3, [p])))["Person"])["name"]
    assert a.value_types == [rdf_lang, xsd_string]
    assert a.dominant_value_type == rdf_lang
    assert a.type_purity == pytest.approx(2 / 3)
    assert a.languages == ["en"]
    assert a.language_coverage == pytest.approx(2 / 3)
    assert a.mean_length == pytest.approx(3.0)
    assert a.distinct_ratio == 1.0


def test_untyped_object_ratio_uses_resource_triples():
    p = prop("knows", {1: 2}, distinct_objects=2, value_partitions=[resource(1, "Person"), resource(1)])
    a = props_of(classes_of(run(cls("Person", 2, [p])))["Person"])["knows"]
    assert a.untyped_object_ratio == 0.5
    assert a.language_coverage is None and a.mean_length is None


def test_identifier_like_and_enumeration_candidate():
    ident = prop("id", {1: 30}, distinct_objects=30, value_partitions=[literal("xsd:string", 30)])
    enum = prop("status", {1: 30}, distinct_objects=5, value_partitions=[literal("xsd:string", 30, distinct=5)])
    a = props_of(classes_of(run(cls("C", 30, [ident, enum])))["C"])
    assert a["id"].is_identifier_like is True and a["id"].is_enumeration_candidate is False
    assert a["status"].is_identifier_like is False and a["status"].is_enumeration_candidate is True


def test_top_values_share_and_entropy():
    same = prop("s", {1: 4}, distinct_objects=1, top_values=[{"value": "x", "triples": 4}])
    split = prop("t", {1: 4}, distinct_objects=4, top_values=[{"value": "a", "triples": 1}, {"value": "b", "triples": 1}])
    a = props_of(classes_of(run(cls("C", 4, [same, split])))["C"])
    assert a["s"].entropy_estimate == 0 and a["s"].top_k_share == 1.0
    # a, b and a remainder bucket of 2: −(¼ log ¼ · 2 + ½ log ½) = 1.5
    assert a["t"].entropy_estimate == pytest.approx(1.5) and a["t"].top_k_share == 0.5


def test_indicators_of_queries_not_run_are_absent():
    a = props_of(classes_of(run(cls("C", 3, [prop("p", {1: 3})])))["C"])["p"]
    assert a.property_kind is None and a.value_types is None and a.distinct_ratio is None
    assert a.top_k_share is None and a.entropy_estimate is None
    assert a.cardinality_label == "exactly_one"


# --- hierarchy (2.6) ---


def test_implied_parent():
    c = classes_of(run(cls("Student", 10, co_types={"Person": 10}), cls("Person", 20)))
    assert [(p.parent, p.source, p.co_type_ratio) for p in c["Student"].parents] == [(EX + "Person", "implied", 1.0)]
    assert c["Student"].hierarchy_depth == 1 and c["Person"].hierarchy_depth == 0


def test_declared_parent_wins_over_implied():
    c = classes_of(run(cls("Student", 10, co_types={"Person": 10}), cls("Person", 20), edges=[("Student", "Person")]))
    assert [p.source for p in c["Student"].parents] == ["declared"]


def test_inherited_refined_and_own_properties():
    person = cls("Person", 20, [prop("name", {1: 20}), prop("email", {1: 15})])
    student = cls("Student", 10, [prop("name", {1: 10}), prop("email", {1: 10}), prop("school", {1: 10})])
    c = classes_of(run(person, student, edges=[("Student", "Person")]))
    p = props_of(c["Student"])
    assert (p["name"].inheritance, p["email"].inheritance, p["school"].inheritance) == ("inherited", "refined", "own")
    assert c["Student"].own_property_count == 1
    assert all(x.inheritance == "own" for x in props_of(c["Person"]).values())


def test_mutually_implied_classes_are_equivalent():
    a = cls("A", 5, [prop("p", {1: 5})], co_types={"B": 5})
    b = cls("B", 5, [prop("p", {1: 5})], co_types={"A": 5})
    c = classes_of(run(a, b))
    assert [p.parent for p in c["A"].parents] == [EX + "B"]
    assert [p.parent for p in c["B"].parents] == [EX + "A"]
    assert c["A"].hierarchy_depth == 0 and c["B"].hierarchy_depth == 0
    assert props_of(c["A"])["p"].inheritance == "own"


def test_parent_without_profile_is_listed_not_compared():
    student = cls("Student", 10, [prop("name", {1: 10})])
    c = classes_of(run(student, edges=[("Student", "Agent")]))
    assert [(p.parent, p.source) for p in c["Student"].parents] == [(EX + "Agent", "declared")]
    assert props_of(c["Student"])["name"].inheritance == "own"
    assert c["Student"].hierarchy_depth == 1


def test_declared_cycle_has_finite_depth():
    c = classes_of(run(cls("A", 1), cls("B", 1), cls("C", 1), edges=[("A", "B"), ("B", "C"), ("C", "A")]))
    assert all(isinstance(x.hierarchy_depth, int) for x in c.values())


# --- exactness and stored profiles (2.7) ---


def test_first_n_class_is_not_exact():
    c = classes_of(run(cls("Big", 50000, [prop("p", {1: 10000})], mode="first_n", observed=10000)))["Big"]
    assert c.is_exact is False and props_of(c)["p"].is_exact is False
    assert c.sample_ratio == pytest.approx(0.2)


def test_presence_only_property_has_no_statistics():
    rare = prop("rare", presence_only=True)
    c = classes_of(run(cls("Big", 50000, [rare], mode="first_n", observed=10000)))["Big"]
    a = props_of(c)["rare"]
    assert a.is_exact is False and a.inheritance == "own"
    assert a.min is None and a.max is None and a.mean is None and a.confidence is None and a.cardinality_label is None


def test_exact_class_is_exact():
    c = classes_of(run(cls("C", 3, [prop("p", {1: 3})])))["C"]
    assert c.is_exact is True and props_of(c)["p"].is_exact is True


def test_analytics_from_a_json_loaded_profile_are_equal():
    raw = run(cls("Person", 4, [prop("name", {1: 2, 2: 1})]), cls("Student", 2, co_types={"Person": 2}))
    stored = ProfileRun.model_validate_json(raw.model_dump_json())
    assert analyse(stored) == analyse(raw)


# --- further indicators (2.8) ---


def test_class_indicators():
    props = [
        {"property": RDFS_LABEL, "cardinality_histogram": [{"values_per_subject": 1, "subjects": 80}]},
        {"property": SKOS_PREF, "cardinality_histogram": [{"values_per_subject": 1, "subjects": 90}]},
        prop("id", {1: 100}),
    ]
    c = classes_of(run(cls("C", 100, props)))["C"]
    assert c.label_coverage == pytest.approx(0.9)
    assert c.mandatory_property_count == 1
    assert c.mean_out_degree == pytest.approx(2.7)


def test_graph_indicators():
    knows = prop("knows", {1: 2}, value_partitions=[resource(2, "Person", graph=EX + "g2")])
    raw = run(
        cls("Person", 2, [knows, prop("name", {1: 2})]),
        graph=EX + "g1",
        distinct_subjects=4,
        untyped_subjects=1,
    )
    g = analyse(raw).graphs[0]
    assert g.class_count == 1 and g.property_count == 2
    assert g.typed_subject_ratio == 0.75
    assert g.vocabularies == [EX]
    assert g.cross_graph_object_types == [EX + "g2"]


@pytest.mark.parametrize(
    "label, exact, bounds, uml",
    [
        ("exactly_one", None, (1, 1), "1"),
        ("zero_or_one", None, (None, 1), "0..1"),
        ("one_or_more", None, (1, None), "1..*"),
        ("zero_or_more", None, (None, None), "0..*"),
        ("exactly_n", 3, (3, 3), "3"),
        (None, None, (None, None), "0..*"),
    ],
)
def test_label_bounds_and_multiplicity(label, exact, bounds, uml):
    from fingerprint.domain.analytics import label_bounds, multiplicity

    assert label_bounds(label, exact) == bounds and multiplicity(label, exact) == uml
