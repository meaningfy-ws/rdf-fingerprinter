"""Raw statistics → analytics: pure functions, no I/O (DEC-4, DEC-8; formulas in design.md)."""

import math
from collections import defaultdict

from fingerprint.domain.profile import (
    CardinalityBin,
    CardinalityChoice,
    CardinalityLabel,
    CardinalityStatistics,
    ClassAnalytics,
    ClassProfile,
    GraphAnalytics,
    GraphProfile,
    Inheritance,
    NodeKind,
    ParentClass,
    ParentSource,
    PrecisionMode,
    ProfileAnalytics,
    ProfileRun,
    PropertyAnalytics,
    PropertyKind,
    PropertyProfile,
    ValueIndicators,
    ValuePartition,
)
from fingerprint.domain.vocabulary import RDF_LANG_STRING  # noqa: F401 — also importable from here (2.0)

LABEL_PREDICATES = (
    "http://www.w3.org/2000/01/rdf-schema#label",
    "http://www.w3.org/2004/02/skos/core#prefLabel",
    "http://purl.org/dc/terms/title",
    "http://schema.org/name",
    "https://schema.org/name",
    "http://xmlns.com/foaf/0.1/name",
)

_ALTERNATIVES = {
    CardinalityLabel.zero_or_more: [CardinalityLabel.one_or_more, CardinalityLabel.zero_or_one],
    CardinalityLabel.zero_or_one: [CardinalityLabel.exactly_one],
    CardinalityLabel.one_or_more: [CardinalityLabel.exactly_one],
    CardinalityLabel.exactly_n: [CardinalityLabel.exactly_one],
    CardinalityLabel.exactly_one: [],
}


def _ratio(numerator: float, denominator: float) -> float | None:
    """A ratio whose denominator is 0 is absent (design: zero denominators)."""
    return numerator / denominator if denominator else None


def _weighted_value_at(counts: list[tuple[int, int]], position: int) -> int:
    """The value at a 0-based position of the sorted, expanded histogram."""
    seen = 0
    for value, count in counts:
        seen += count
        if position < seen:
            return value
    raise IndexError(position)


def _subjects_per_n(histogram: list[CardinalityBin]) -> dict[int, int]:  # dict-ok: lookup index n → subjects
    return {b.values_per_subject: b.subjects for b in histogram}  # dict-ok: lookup index


def cardinality_statistics(histogram: list[CardinalityBin], observed: int) -> CardinalityStatistics:
    """Statistics of values per instance; the n = 0 bin is the observed instances without the property."""
    bins = _subjects_per_n(histogram)
    with_property = sum(bins.values())
    without = observed - with_property
    total = sum(n * s for n, s in bins.items())
    shape = CardinalityStatistics(
        subjects_with_property=with_property,
        subjects_without_property=without,
        total_triples=total,
        max=max(bins) if bins else None,
        min=(0 if without > 0 else min(bins)) if bins else None,
        is_functional=max(bins) <= 1 if bins else None,
        mean_when_present=total / with_property if bins else None,
    )
    if observed <= 0:
        return shape
    counts = sorted([*bins.items(), (0, without)]) if without > 0 else sorted(bins.items())
    mean = total / observed
    return shape.model_copy(
        update={
            "mean": mean,
            "confidence": with_property / observed,
            "is_mandatory": with_property == observed,
            "median": (_weighted_value_at(counts, (observed - 1) // 2) + _weighted_value_at(counts, observed // 2)) / 2,
            "mode": min(counts, key=lambda vc: (-vc[1], vc[0]))[0],
            "stddev": math.sqrt(sum(c * (n - mean) ** 2 for n, c in counts) / observed),
        }
    )


def cardinality_label(histogram: list[CardinalityBin], observed: int, threshold: float) -> CardinalityChoice:
    """The accepted cardinality label at the threshold, with its support and the rejected stricter labels;
    no label without observed instances."""
    if observed <= 0:
        return CardinalityChoice()
    bins = _subjects_per_n(histogram)

    def share(subjects: int) -> float:
        return subjects / observed

    present = share(sum(bins.values()))
    exact_count = None
    if present >= threshold:
        exactly_k = [k for k in sorted(bins) if k > 1 and share(bins[k]) >= threshold]
        if share(bins.get(1, 0)) >= threshold:
            label, support = CardinalityLabel.exactly_one, share(bins.get(1, 0))
        elif exactly_k:
            exact_count = exactly_k[0]
            label, support = CardinalityLabel.exactly_n, share(bins[exact_count])
        else:
            label, support = CardinalityLabel.one_or_more, present
    else:
        at_most_one = share(observed - sum(s for n, s in bins.items() if n > 1))
        if at_most_one >= threshold:
            label, support = CardinalityLabel.zero_or_one, at_most_one
        else:
            label, support = CardinalityLabel.zero_or_more, 1.0
    return CardinalityChoice(
        cardinality_label=label, label_support=support, exact_count=exact_count, alternative_labels=_ALTERNATIVES[label]
    )


_BOUNDS: dict[str, tuple[int | None, int | None]] = {
    CardinalityLabel.exactly_one: (1, 1),
    CardinalityLabel.zero_or_one: (None, 1),
    CardinalityLabel.one_or_more: (1, None),
    CardinalityLabel.zero_or_more: (None, None),
}


def label_bounds(label: str | None, exact_count: int | None = None) -> tuple[int | None, int | None]:
    """The (min, max) values per instance a cardinality label allows; None is unbounded or no label."""
    if label is None:
        return None, None
    if label == CardinalityLabel.exactly_n:
        return exact_count, exact_count
    return _BOUNDS[label]


def multiplicity(label: str | None, exact_count: int | None = None) -> str:
    """UML multiplicity of a label: `1`, `0..1`, `1..*`, `0..*` or `n`; no label reads as `0..*`."""
    low, high = label_bounds(label, exact_count)
    if low is not None and low == high:
        return str(low)
    return f"{low or 0}..{'*' if high is None else high}"


def _ordered_by_triples(weights: dict[str, int]) -> list[str]:  # dict-ok: lookup index key → triples
    return sorted(weights, key=lambda key: (-weights[key], key))


def value_type_indicators(partitions: list[ValuePartition], total: int) -> ValueIndicators:
    """The value types (datatypes and object classes), the dominant one with its purity, and the untyped share of
    the resource objects (Q6/Q7); the other indicators stay absent."""
    literal_triples = sum(p.triples or 0 for p in partitions if p.node_kind == NodeKind.literal)
    types: dict[str, int] = defaultdict(int)  # dict-ok: lookup index value type → triples
    untyped = 0
    for p in partitions:
        if p.node_kind == NodeKind.literal:
            types[p.datatype or (RDF_LANG_STRING if p.language else "")] += p.triples or 0
        elif p.object_class:
            types[p.object_class] += p.triples or 0
        else:
            untyped += p.triples or 0
    types.pop("", None)
    value_types = _ordered_by_triples(types)
    return ValueIndicators(
        value_types=value_types or None,
        dominant_value_type=value_types[0] if value_types else None,
        type_purity=_ratio(types[value_types[0]], total) if value_types else None,
        untyped_object_ratio=_ratio(untyped, total - literal_triples),
    )


def _partition_indicators(partitions: list[ValuePartition], total: int) -> ValueIndicators:
    """Kind, value types, languages and lengths from the value partitions (Q6/Q7)."""
    literals = [p for p in partitions if p.node_kind == NodeKind.literal]
    literal_triples = sum(p.triples or 0 for p in literals)
    if len(literals) == len(partitions):
        kind = PropertyKind.datatype_property
    else:
        kind = PropertyKind.object_property if not literals else PropertyKind.mixed
    languages: dict[str, int] = defaultdict(int)  # dict-ok: lookup index language → triples
    for p in literals:
        if p.language:
            languages[p.language] += p.triples or 0
    return value_type_indicators(partitions, total).model_copy(
        update={
            "property_kind": kind,
            "languages": _ordered_by_triples(languages) or None,
            "language_coverage": _ratio(sum(languages.values()), literal_triples),
            "mean_length": _ratio(sum(p.total_length or 0 for p in literals), literal_triples),
        }
    )


def value_profile(profile: PropertyProfile, total: int, with_property: int, label: str | None, top_k: int) -> ValueIndicators:
    """Indicators from value partitions (Q6/Q7) and top values (Q9); absent when those queries did not run."""
    partitions = profile.value_partitions
    indicators = _partition_indicators(partitions, total) if partitions else ValueIndicators()
    if profile.distinct_objects is not None:
        indicators = indicators.model_copy(
            update={
                "distinct_ratio": _ratio(profile.distinct_objects, total),
                "is_identifier_like": label == CardinalityLabel.exactly_one and profile.distinct_objects == with_property,
                "is_enumeration_candidate": profile.distinct_objects <= top_k,
            }
        )
    if profile.top_values is not None:
        top = [v.triples or 0 for v in profile.top_values]
        buckets = [t for t in [*top, total - sum(top)] if t > 0]
        indicators = indicators.model_copy(
            update={
                "top_k_share": _ratio(sum(top), total),
                "entropy_estimate": -sum(t / total * math.log2(t / total) for t in buckets) if total else 0.0,
            }
        )
    return indicators


def property_analytics(profile: PropertyProfile, cls: ClassProfile, threshold: float, top_k: int) -> PropertyAnalytics:
    """Every property indicator except inheritance, which needs the parents."""
    if profile.presence_only:
        return PropertyAnalytics(**profile.model_dump(exclude_none=True), is_exact=False)
    exact = cls.precision_mode != PrecisionMode.first_n
    observed = cls.observed_instances or 0
    histogram = profile.cardinality_histogram or []
    stats = cardinality_statistics(histogram, observed)
    choice = cardinality_label(histogram, observed, threshold)
    values = value_profile(
        profile, stats.total_triples or 0, stats.subjects_with_property or 0, choice.cardinality_label, top_k
    )
    return PropertyAnalytics(
        **profile.model_dump(exclude_none=True),
        **stats.model_dump(exclude_none=True),
        **choice.model_dump(exclude_none=True),
        **values.model_dump(exclude_none=True),
        is_exact=exact,
    )


def _parents(cls: ClassProfile, declared: dict[str, set[str]]) -> list[ParentClass]:  # dict-ok: lookup index
    observed = cls.observed_instances or 0
    co_types = {c.class_iri: c.subjects or 0 for c in cls.co_types or [] if c.class_iri}  # dict-ok: lookup index
    declared_here = declared.get(cls.class_iri, set())
    implied = {c for c, s in co_types.items() if observed > 0 and s == observed} - declared_here
    return [
        ParentClass(parent=parent, source=source, co_type_ratio=_ratio(co_types.get(parent, 0), observed))
        for source, parents in ((ParentSource.declared, declared_here), (ParentSource.implied, implied))
        for parent in sorted(parents)
    ]


def _depth(cls: str, parents: dict[str, set[str]], path: frozenset[str] = frozenset()) -> int:  # dict-ok: lookup index
    """Longest path to a class without parents; a class already on the path ends the branch (cycles)."""
    ups = parents.get(cls, set()) - path - {cls}
    return 1 + max(_depth(p, parents, path | {cls}) for p in ups) if ups else 0


def _inheritance(
    prop: PropertyAnalytics, parent_props: list[dict[str, PropertyAnalytics]]
) -> Inheritance:  # dict-ok: lookup index
    candidates = [props[prop.property] for props in parent_props if prop.property in props]
    if not candidates:
        return Inheritance.own
    if prop.presence_only:
        return Inheritance.inherited

    def key(p: PropertyAnalytics) -> tuple:
        return p.cardinality_label, p.dominant_value_type

    return Inheritance.inherited if any(key(p) == key(prop) for p in candidates) else Inheritance.refined


def _namespace(iri: str) -> str:
    cut = max(iri.rfind("#"), iri.rfind("/"))
    return iri[: cut + 1] if cut >= 0 else iri


def _acyclic_hierarchy(
    declared: dict[str, set[str]], parents_by_class: dict[str, list[ParentClass]]
) -> dict[str, set[str]]:  # dict-ok: lookup indexes class → parents
    """Every class's parents, declared or implied, without pairs that are each other's parent: those are
    equivalent classes, neither compared nor counted in depth."""
    hierarchy = {k: set(v) for k, v in declared.items()}  # dict-ok: lookup index class → parents
    hierarchy.update({c: {p.parent for p in ps} for c, ps in parents_by_class.items()})  # dict-ok: lookup index
    equivalent = {(a, b) for a, ups in hierarchy.items() for b in ups if a in hierarchy.get(b, set())}
    return {a: {b for b in ups if (a, b) not in equivalent} for a, ups in hierarchy.items()}  # dict-ok: lookup index


def _class_analytics(
    c: ClassProfile, props: list[PropertyAnalytics], parents: list[ParentClass], depth: int
) -> ClassAnalytics:
    observed = c.observed_instances or 0
    return ClassAnalytics(
        **c.model_dump(exclude_none=True, exclude={"property_partitions"}),
        property_partitions=props,
        parents=parents,
        hierarchy_depth=depth,
        own_property_count=sum(p.inheritance == Inheritance.own for p in props),
        mandatory_property_count=sum(p.confidence == 1 for p in props),
        mean_out_degree=_ratio(sum(p.total_triples or 0 for p in props), observed),
        label_coverage=max([p.confidence or 0 for p in props if p.property in LABEL_PREDICATES], default=0.0),
        sample_ratio=_ratio(observed, c.instances),
        is_exact=c.precision_mode != PrecisionMode.first_n and all(p.is_exact for p in props),
    )


def _vocabularies(classes: list[ClassAnalytics]) -> tuple[list[str], int]:
    """Namespaces by weight (instances of their classes, triples of their properties), and the property count."""
    weights: dict[str, int] = defaultdict(int)  # dict-ok: lookup index namespace → weight
    properties: set[str] = set()
    for analysed in classes:
        weights[_namespace(analysed.class_iri)] += analysed.instances
        for p in analysed.property_partitions or []:
            properties.add(p.property)
            weights[_namespace(p.property)] += p.total_triples or 0
    return _ordered_by_triples(weights), len(properties)


def graph_analytics(graph: GraphProfile, threshold: float, top_k: int) -> GraphAnalytics:
    classes = graph.class_partitions or []
    declared: dict[str, set[str]] = defaultdict(set)  # dict-ok: lookup index class → declared parents
    for edge in graph.declared_subclass_edges or []:
        declared[edge.sub_class].add(edge.super_class)
    props_by_class = {  # dict-ok: lookup index class → property → analytics
        c.class_iri: {
            p.property: property_analytics(p, c, threshold, top_k) for p in c.property_partitions or []
        }  # dict-ok: lookup index
        for c in classes
    }
    parents_by_class = {c.class_iri: _parents(c, declared) for c in classes}  # dict-ok: lookup index
    acyclic = _acyclic_hierarchy(declared, parents_by_class)

    analysed_classes = []
    for c in classes:
        compared = [props_by_class[p] for p in acyclic.get(c.class_iri, set()) if p in props_by_class]
        props = [
            p.model_copy(update={"inheritance": _inheritance(p, compared).value}) for p in props_by_class[c.class_iri].values()
        ]
        analysed_classes.append(_class_analytics(c, props, parents_by_class[c.class_iri], _depth(c.class_iri, acyclic)))

    vocabularies, property_count = _vocabularies(analysed_classes)
    cross_graph = {
        part.object_class_graph
        for c in classes
        for p in c.property_partitions or []
        for part in p.value_partitions or []
        if part.object_class_graph and part.object_class_graph != graph.graph
    }
    typed = (
        _ratio(graph.distinct_subjects - graph.untyped_subjects, graph.distinct_subjects)
        if graph.distinct_subjects is not None and graph.untyped_subjects is not None
        else None
    )
    return GraphAnalytics(
        **graph.model_dump(exclude_none=True, exclude={"class_partitions"}),
        class_partitions=analysed_classes,
        class_count=len(analysed_classes),
        property_count=property_count,
        typed_subject_ratio=typed,
        vocabularies=vocabularies,
        cross_graph_object_types=sorted(cross_graph),
    )


def analyse(run: ProfileRun) -> ProfileAnalytics:
    """Derive every analytics value from a raw profile; the raw profile is not modified."""
    threshold, top_k = run.settings.acceptance_threshold, run.settings.top_k
    graphs = [graph_analytics(g, threshold, top_k) for g in run.graphs or []]
    return ProfileAnalytics(**run.model_dump(exclude_none=True, exclude={"graphs"}), graphs=graphs)
