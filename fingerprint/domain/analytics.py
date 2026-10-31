"""Raw statistics → analytics: pure functions, no I/O (DEC-4, DEC-8; formulas in design.md)."""

import math
from collections import defaultdict
from typing import Any

from fingerprint.domain.generated.profile import (
    ClassProfile,
    GraphProfile,
    ProfileAnalytics,
    ProfileRun,
    PropertyProfile,
)

LABEL_PREDICATES = (
    "http://www.w3.org/2000/01/rdf-schema#label",
    "http://www.w3.org/2004/02/skos/core#prefLabel",
    "http://purl.org/dc/terms/title",
    "http://schema.org/name",
    "https://schema.org/name",
    "http://xmlns.com/foaf/0.1/name",
)
RDF_LANG_STRING = "http://www.w3.org/1999/02/22-rdf-syntax-ns#langString"

_ALTERNATIVES = {
    "zero_or_more": ["one_or_more", "zero_or_one"],
    "zero_or_one": ["exactly_one"],
    "one_or_more": ["exactly_one"],
    "exactly_n": ["exactly_one"],
    "exactly_one": [],
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


def cardinality_statistics(bins: dict[int, int], observed: int) -> dict[str, Any]:
    """Statistics of values per instance; the n = 0 bin is the observed instances without the property."""
    with_property = sum(bins.values())
    without = observed - with_property
    total = sum(n * s for n, s in bins.items())
    stats: dict[str, Any] = {
        "subjects_with_property": with_property,
        "subjects_without_property": without,
        "total_triples": total,
    }
    if bins:
        stats["max"] = max(bins)
        stats["min"] = 0 if without > 0 else min(bins)
        stats["is_functional"] = stats["max"] <= 1
        stats["mean_when_present"] = total / with_property
    if observed <= 0:
        return stats
    counts = sorted({**bins, 0: without}.items()) if without > 0 else sorted(bins.items())
    mean = total / observed
    stats.update(
        mean=mean,
        confidence=with_property / observed,
        is_mandatory=with_property == observed,
        median=(_weighted_value_at(counts, (observed - 1) // 2) + _weighted_value_at(counts, observed // 2)) / 2,
        mode=min(counts, key=lambda vc: (-vc[1], vc[0]))[0],
        stddev=math.sqrt(sum(c * (n - mean) ** 2 for n, c in counts) / observed),
    )
    return stats


def cardinality_label(bins: dict[int, int], observed: int, threshold: float) -> dict[str, Any]:
    """The accepted cardinality label at the threshold, with its support and the rejected stricter labels."""
    if observed <= 0:
        return {}

    def share(subjects: int) -> float:
        return subjects / observed

    present = share(sum(bins.values()))
    result: dict[str, Any]
    if present >= threshold:
        exactly_k = [k for k in sorted(bins) if k > 1 and share(bins[k]) >= threshold]
        if share(bins.get(1, 0)) >= threshold:
            result = {"cardinality_label": "exactly_one", "label_support": share(bins.get(1, 0))}
        elif exactly_k:
            k = exactly_k[0]
            result = {"cardinality_label": "exactly_n", "label_support": share(bins[k]), "exact_count": k}
        else:
            result = {"cardinality_label": "one_or_more", "label_support": present}
    else:
        at_most_one = share(observed - sum(s for n, s in bins.items() if n > 1))
        if at_most_one >= threshold:
            result = {"cardinality_label": "zero_or_one", "label_support": at_most_one}
        else:
            result = {"cardinality_label": "zero_or_more", "label_support": 1.0}
    result["alternative_labels"] = list(_ALTERNATIVES[result["cardinality_label"]])
    return result


def _ordered_by_triples(weights: dict[str, int]) -> list[str]:
    return sorted(weights, key=lambda key: (-weights[key], key))


def value_profile(profile: PropertyProfile, total: int, with_property: int, label: str | None, top_k: int) -> dict[str, Any]:
    """Indicators from value partitions (Q6/Q7) and top values (Q9); absent when those queries did not run."""
    result: dict[str, Any] = {}
    partitions = profile.value_partitions
    if partitions:
        literals = [p for p in partitions if p.node_kind == "literal"]
        literal_triples = sum(p.triples or 0 for p in literals)
        result["property_kind"] = (
            "datatype_property" if len(literals) == len(partitions) else "object_property" if not literals else "mixed"
        )
        types: dict[str, int] = defaultdict(int)
        languages: dict[str, int] = defaultdict(int)
        untyped = 0
        for p in partitions:
            if p.node_kind == "literal":
                types[p.datatype or (RDF_LANG_STRING if p.language else "")] += p.triples or 0
                if p.language:
                    languages[p.language] += p.triples or 0
            elif p.object_class:
                types[p.object_class] += p.triples or 0
            else:
                untyped += p.triples or 0
        types.pop("", None)
        value_types = _ordered_by_triples(types)
        if value_types:
            result.update(
                value_types=value_types,
                dominant_value_type=value_types[0],
                type_purity=_ratio(types[value_types[0]], total),
            )
        if languages:
            result["languages"] = _ordered_by_triples(languages)
        result["untyped_object_ratio"] = _ratio(untyped, total - literal_triples)
        result["language_coverage"] = _ratio(sum(languages.values()), literal_triples)
        result["mean_length"] = _ratio(sum(p.total_length or 0 for p in literals), literal_triples)
    if profile.distinct_objects is not None:
        result["distinct_ratio"] = _ratio(profile.distinct_objects, total)
        result["is_identifier_like"] = label == "exactly_one" and profile.distinct_objects == with_property
        result["is_enumeration_candidate"] = profile.distinct_objects <= top_k
    if profile.top_values is not None:
        top = [v.triples or 0 for v in profile.top_values]
        result["top_k_share"] = _ratio(sum(top), total)
        buckets = [t for t in [*top, total - sum(top)] if t > 0]
        result["entropy_estimate"] = -sum(t / total * math.log2(t / total) for t in buckets) if total else 0.0
    return {k: v for k, v in result.items() if v is not None}


def property_analytics(profile: PropertyProfile, cls: ClassProfile, threshold: float, top_k: int) -> dict[str, Any]:
    """Every property indicator except inheritance, which needs the parents."""
    raw = profile.model_dump(exclude_none=True)
    exact = cls.precision_mode != "first_n" and not profile.presence_only
    if profile.presence_only:
        return {**raw, "is_exact": False}
    observed = cls.observed_instances or 0
    bins = {b.values_per_subject: b.subjects for b in profile.cardinality_histogram or []}
    stats = cardinality_statistics(bins, observed)
    label = cardinality_label(bins, observed, threshold)
    values = value_profile(
        profile, stats["total_triples"], stats["subjects_with_property"], label.get("cardinality_label"), top_k
    )
    return {**raw, **stats, **label, **values, "is_exact": exact}


def _parents(cls: ClassProfile, declared: dict[str, set[str]]) -> list[dict[str, Any]]:
    observed = cls.observed_instances or 0
    co_types = {c.class_iri: c.subjects or 0 for c in cls.co_types or [] if c.class_iri}
    declared_here = declared.get(cls.class_iri, set())
    implied = {c for c, s in co_types.items() if observed > 0 and s == observed} - declared_here
    return [
        {"parent": parent, "source": source, "co_type_ratio": _ratio(co_types.get(parent, 0), observed)}
        for source, parents in (("declared", declared_here), ("implied", implied))
        for parent in sorted(parents)
    ]


def _depth(cls: str, parents: dict[str, set[str]], path: frozenset[str] = frozenset()) -> int:
    """Longest path to a class without parents; a class already on the path ends the branch (cycles)."""
    ups = parents.get(cls, set()) - path - {cls}
    return 1 + max(_depth(p, parents, path | {cls}) for p in ups) if ups else 0


def _inheritance(prop: dict[str, Any], parent_props: list[dict[str, dict[str, Any]]]) -> str:
    candidates = [props[prop["property"]] for props in parent_props if prop["property"] in props]
    if not candidates:
        return "own"
    if prop.get("presence_only"):
        return "inherited"

    def key(p: dict[str, Any]) -> tuple:
        return p.get("cardinality_label"), p.get("dominant_value_type")

    return "inherited" if any(key(p) == key(prop) for p in candidates) else "refined"


def _namespace(iri: str) -> str:
    cut = max(iri.rfind("#"), iri.rfind("/"))
    return iri[: cut + 1] if cut >= 0 else iri


def graph_analytics(graph: GraphProfile, threshold: float, top_k: int) -> dict[str, Any]:
    classes = graph.class_partitions or []
    declared: dict[str, set[str]] = defaultdict(set)
    for edge in graph.declared_subclass_edges or []:
        declared[edge.sub_class].add(edge.super_class)

    props_by_class = {
        c.class_iri: {p.property: property_analytics(p, c, threshold, top_k) for p in c.property_partitions or []}
        for c in classes
    }
    parents_by_class = {c.class_iri: _parents(c, declared) for c in classes}
    hierarchy: dict[str, set[str]] = {k: set(v) for k, v in declared.items()}
    hierarchy.update({c: {p["parent"] for p in ps} for c, ps in parents_by_class.items()})
    # Classes that are each other's parent are equivalent: not compared, not counted in depth.
    equivalent = {(a, b) for a, ups in hierarchy.items() for b in ups if a in hierarchy.get(b, set())}
    acyclic = {a: {b for b in ups if (a, b) not in equivalent} for a, ups in hierarchy.items()}

    analysed_classes: list[dict[str, Any]] = []
    for c in classes:
        observed = c.observed_instances or 0
        compared = [props_by_class[p] for p in acyclic.get(c.class_iri, set()) if p in props_by_class]
        props = [{**p, "inheritance": _inheritance(p, compared)} for p in props_by_class[c.class_iri].values()]
        analysed_classes.append(
            {
                **c.model_dump(exclude_none=True),
                "property_partitions": props,
                "parents": parents_by_class[c.class_iri],
                "hierarchy_depth": _depth(c.class_iri, acyclic),
                "own_property_count": sum(p["inheritance"] == "own" for p in props),
                "mandatory_property_count": sum(p.get("confidence") == 1 for p in props),
                "mean_out_degree": _ratio(sum(p.get("total_triples", 0) for p in props), observed),
                "label_coverage": max(
                    [p.get("confidence", 0) for p in props if p["property"] in LABEL_PREDICATES], default=0.0
                ),
                "sample_ratio": _ratio(observed, c.instances),
                "is_exact": c.precision_mode != "first_n" and all(p["is_exact"] for p in props),
            }
        )

    weights: dict[str, int] = defaultdict(int)
    properties: set[str] = set()
    for analysed in analysed_classes:
        weights[_namespace(analysed["class_iri"])] += analysed["instances"]
        for p in analysed["property_partitions"]:
            properties.add(p["property"])
            weights[_namespace(p["property"])] += p.get("total_triples", 0)
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
    result = {
        **graph.model_dump(exclude_none=True),
        "class_partitions": analysed_classes,
        "class_count": len(analysed_classes),
        "property_count": len(properties),
        "typed_subject_ratio": typed,
        "vocabularies": _ordered_by_triples(weights),
        "cross_graph_object_types": sorted(cross_graph),
    }
    return result


def _drop_none(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _drop_none(v) for k, v in value.items() if v is not None}
    if isinstance(value, list):
        return [_drop_none(v) for v in value]
    return value


def analyse(run: ProfileRun) -> ProfileAnalytics:
    """Derive every analytics value from a raw profile; the raw profile is not modified."""
    threshold = run.settings.acceptance_threshold or 0.95
    top_k = run.settings.top_k or 20
    graphs = [graph_analytics(g, threshold, top_k) for g in run.graphs or []]
    return ProfileAnalytics.model_validate(_drop_none({**run.model_dump(exclude_none=True), "graphs": graphs}))
