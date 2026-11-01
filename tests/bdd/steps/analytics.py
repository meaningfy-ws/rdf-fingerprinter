"""Steps of profile_analytics.feature: model-object profiles through the pure `analyse` function."""

import pytest
from pytest_bdd import given, parsers, then, when

from fingerprint.adapters.profile_file import load_profile, save_profile
from fingerprint.domain.analytics import analyse
from fingerprint.domain.profile import ClassProfile, CoTypeCount, ValueCount
from tests.builders import klass, literals, profile_run, prop, resources
from tests.fakes import EX

PREFIXES = {
    "ex:": EX,
    "rdfs:": "http://www.w3.org/2000/01/rdf-schema#",
    "skos:": "http://www.w3.org/2004/02/skos/core#",
}
CLASS = "ex:C"
PROPERTY = "ex:p"
PERSON = EX + "Person"


def expand(curie: str) -> str:
    for prefix, namespace in PREFIXES.items():
        if curie.startswith(prefix):
            return namespace + curie.removeprefix(prefix)
    return curie


def get_class(ctx, curie=CLASS, instances=10) -> ClassProfile:
    """The scenario's class, created with `instances` the first time it is named."""
    return ctx["classes"].setdefault(expand(curie), klass(expand(curie), instances))


def change_class(ctx, curie=CLASS, **fields) -> None:
    ctx["classes"][expand(curie)] = get_class(ctx, curie).model_copy(update=fields)


def add_property(ctx, curie=PROPERTY, bins=None, cls=CLASS, *partitions, **fields) -> None:
    added = prop(expand(curie), bins, *partitions).model_copy(update=fields)
    change_class(ctx, cls, property_partitions=[*(get_class(ctx, cls).property_partitions or []), added])


def add_co_type(ctx, sub: str, sup: str, subjects: int = 10) -> None:
    change_class(
        ctx, sub, co_types=[*(get_class(ctx, sub).co_types or []), CoTypeCount(class_iri=expand(sup), subjects=subjects)]
    )


def scenario_run(ctx):
    run = profile_run(*ctx["classes"].values(), edges=ctx["edges"])
    return run.model_copy(update={"settings": ctx["settings"]})


def analysed_class(ctx, curie=CLASS):
    return next(c for c in ctx["result"].graphs[0].class_partitions if c.class_iri == expand(curie))


def analysed_property(ctx, curie=PROPERTY, cls=CLASS):
    return next(p for p in analysed_class(ctx, cls).property_partitions if p.property == expand(curie))


def parse_histogram(text: str) -> dict[int, int]:
    return {int(n): int(s) for n, s in (pair.split(":") for pair in text.split(", "))}


# --- shared ---


@when("the analytics are computed")
def compute(ctx):
    stored = load_profile(ctx["saved"]) if "saved" in ctx else scenario_run(ctx)
    ctx["result"] = analyse(stored)


# --- analytics from a stored profile ---


@given("a raw profile stored as a file")
def stored_profile(ctx):
    add_property(ctx, bins={1: 7, 2: 3})
    ctx["saved"] = save_profile(scenario_run(ctx), ctx["tmp"])


@given("no endpoint is reachable")
def no_endpoint():
    """Analysis takes no endpoint at all; nothing to set up."""


@then("they equal the analytics computed right after collection")
def equal_to_fresh(ctx):
    assert ctx["result"] == analyse(scenario_run(ctx))


# --- cardinality statistics and labels ---


@given(parsers.parse("{observed:d} observed instances of a class"))
def observed_instances(ctx, observed):
    get_class(ctx, instances=observed)


@given(parsers.parse("the histogram of a property is {histogram}"))
def histogram_of_property(ctx, histogram):
    add_property(ctx, bins=parse_histogram(histogram))


@given(parsers.parse("the acceptance threshold is {threshold:g}"))
def threshold(ctx, threshold):
    ctx["settings"] = ctx["settings"].model_copy(update={"acceptance_threshold": threshold})


@then(parsers.parse("min is {min:d}, max is {max:d}, mean is {mean:g} and confidence is {confidence:g}"))
def statistics(ctx, min, max, mean, confidence):
    p = analysed_property(ctx)
    assert (p.min, p.max) == (min, max)
    assert p.mean == pytest.approx(mean) and p.confidence == pytest.approx(confidence)


@then(parsers.parse("the mean when present is {mean:g}"))
def mean_when_present(ctx, mean):
    assert analysed_property(ctx).mean_when_present == pytest.approx(mean, abs=0.005)


@then(parsers.parse('the label is "{label}" with support {support:g}'))
def label(ctx, label, support):
    p = analysed_property(ctx)
    assert p.cardinality_label == label and p.label_support == pytest.approx(support)


@then(parsers.re(r'the rejected alternatives are "(?P<alternatives>[^"]*)"'))
def alternatives(ctx, alternatives):
    expected = [a for a in alternatives.split(", ") if a]
    assert (analysed_property(ctx).alternative_labels or []) == expected


# --- value profile ---


@given("a property whose objects are literals and resources")
def mixed_objects(ctx):
    add_property(ctx, PROPERTY, {1: 10}, CLASS, literals(5), resources(5, PERSON), distinct_objects=10)


@then(parsers.parse('its kind is "{kind}"'))
def kind(ctx, kind):
    assert analysed_property(ctx).property_kind == kind


@given("every instance has exactly one value of a property")
def one_value_each(ctx):
    add_property(ctx, PROPERTY, {1: 10}, CLASS, literals(10))


@given("all values are different")
def all_different(ctx):
    last = get_class(ctx).property_partitions[-1]
    change_class(
        ctx, property_partitions=[*get_class(ctx).property_partitions[:-1], last.model_copy(update={"distinct_objects": 10})]
    )


@then("the property is identifier-like")
def identifier_like(ctx):
    assert analysed_property(ctx).is_identifier_like is True


@given("every value of a property is the same")
def same_value(ctx):
    add_property(ctx, bins={1: 10}, distinct_objects=1, top_values=[ValueCount(value="x", triples=10)])


@then("its entropy estimate is 0")
def zero_entropy(ctx):
    assert analysed_property(ctx).entropy_estimate == 0


# --- hierarchy ---


@given(parsers.parse('every observed "{sub}" is also typed "{sup}"'))
def implied(ctx, sub, sup):
    add_co_type(ctx, sub, sup)
    get_class(ctx, sup, instances=20)


@given("no subclass statement is declared")
def no_edges(ctx):
    ctx["edges"].clear()


@then(parsers.parse('"{sup}" is an implied parent of "{sub}"'))
def is_implied_parent(ctx, sup, sub):
    assert (expand(sup), "implied") in [(p.parent, p.source) for p in analysed_class(ctx, sub).parents]


@given(parsers.parse('"{sub}" has the parent "{sup}"'))
def has_parent(ctx, sub, sup):
    get_class(ctx, sub)
    get_class(ctx, sup, instances=20)
    ctx["edges"].append((expand(sub), expand(sup)))


@given(parsers.parse('"{prop}" is labelled "exactly_one" on both'))
def exactly_one_on_both(ctx, prop):
    for c in list(ctx["classes"].values()):
        add_property(ctx, prop, {1: c.instances}, c.class_iri)


@given(parsers.parse('"{prop}" is labelled "zero_or_one" on "{sup}" and "exactly_one" on "{sub}"'))
def refined_label(ctx, prop, sup, sub):
    add_property(ctx, prop, {1: 10}, sup)  # 10 of 20
    add_property(ctx, prop, {1: 10}, sub)  # 10 of 10


@then(parsers.parse('on "{cls}" "{inherited}" is inherited and "{refined}" is refined'))
def inherited_and_refined(ctx, cls, inherited, refined):
    assert analysed_property(ctx, inherited, cls).inheritance == "inherited"
    assert analysed_property(ctx, refined, cls).inheritance == "refined"


@given(parsers.parse('every observed "{a}" is an "{b}" and every observed "{b2}" is an "{a2}"'))
def mutual(ctx, a, b, b2, a2):
    add_co_type(ctx, a, b)
    add_co_type(ctx, b, a)


@then("each is an implied parent of the other")
def each_parent(ctx):
    a, b = ctx["classes"]
    assert [p.parent for p in analysed_class(ctx, a).parents] == [b]
    assert [p.parent for p in analysed_class(ctx, b).parents] == [a]


@then("both have the hierarchy depth they would have without those parents")
def depth_without(ctx):
    assert all(analysed_class(ctx, c).hierarchy_depth == 0 for c in ctx["classes"])


@given(parsers.parse('"{sub}" is declared a subclass of "{sup}"'))
def declared_subclass(ctx, sub, sup):
    get_class(ctx, sub)
    add_property(ctx, "ex:name", {1: 10}, sub)
    ctx["edges"].append((expand(sub), expand(sup)))


@given(parsers.parse('"{cls}" has no instances in the graph'))
def no_instances(ctx, cls):
    assert expand(cls) not in ctx["classes"]


@then(parsers.parse('"{sup}" is listed as a declared parent of "{sub}"'))
def declared_parent(ctx, sup, sub):
    assert [(p.parent, p.source) for p in analysed_class(ctx, sub).parents] == [(expand(sup), "declared")]


@then(parsers.parse('every property of "{cls}" is its own'))
def all_own(ctx, cls):
    assert all(p.inheritance == "own" for p in analysed_class(ctx, cls).property_partitions)


@given(parsers.parse('the declared subclass statements form a cycle between "{a}" and "{b}"'))
def cycle(ctx, a, b):
    get_class(ctx, a)
    get_class(ctx, b)
    ctx["edges"] += [(expand(a), expand(b)), (expand(b), expand(a))]


@then("both classes get a finite hierarchy depth")
def finite_depth(ctx):
    assert all(isinstance(analysed_class(ctx, c).hierarchy_depth, int) for c in ctx["classes"])


# --- further indicators ---


@given(parsers.parse('{first:d} of {total:d} instances of a class have "{label1}" and {second:d} have "{label2}"'))
def labelled(ctx, first, total, label1, second, label2):
    get_class(ctx, instances=total)
    add_property(ctx, label1, {1: first})
    add_property(ctx, label2, {1: second})


@then(parsers.parse("the class's label coverage is {coverage:g}"))
def label_coverage(ctx, coverage):
    assert analysed_class(ctx).label_coverage == pytest.approx(coverage)


# --- exactness ---


@given("a class was read in first-N mode")
def first_n_class(ctx):
    ctx["classes"][expand(CLASS)] = klass(expand(CLASS), 50000, prop(expand(PROPERTY), {1: 10000}), observed=10000)


@then("the class and all its properties are marked not exact")
def not_exact(ctx):
    c = analysed_class(ctx)
    assert c.is_exact is False and all(p.is_exact is False for p in c.property_partitions)


@given("a property was found only by the completeness check")
def presence_only(ctx):
    ctx["classes"][expand(CLASS)] = klass(expand(CLASS), 50000, prop(expand(PROPERTY), presence_only=True), observed=10000)


@then("it is marked not exact")
def property_not_exact(ctx):
    assert analysed_property(ctx).is_exact is False


@then("it has no min, max, mean, confidence or label")
def no_statistics(ctx):
    p = analysed_property(ctx)
    assert (p.min, p.max, p.mean, p.confidence, p.cardinality_label) == (None,) * 5
