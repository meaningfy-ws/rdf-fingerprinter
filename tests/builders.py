"""Builders returning generated model objects, for tests that need a small hand-made profile (lean-test-suite P-5)."""

from fingerprint.domain.profile import (
    CardinalityBin,
    ClassProfile,
    CoTypeCount,
    Failure,
    GraphProfile,
    NodeKind,
    PrecisionMode,
    ProfileRun,
    PropertyProfile,
    QueryKind,
    Settings,
    SubclassEdge,
    ValuePartition,
)

XSD = "http://www.w3.org/2001/XMLSchema#"


def literals(triples: int, datatype: str | None = XSD + "string", language: str | None = None) -> ValuePartition:
    return ValuePartition(node_kind=NodeKind.literal, triples=triples, datatype=datatype, language=language)


def resources(triples: int, object_class: str | None = None, kind: str = "iri") -> ValuePartition:
    return ValuePartition(node_kind=NodeKind(kind), triples=triples, object_class=object_class)


def prop(iri: str, bins: dict[int, int] | None = None, *partitions: ValuePartition, presence_only: bool = False):
    """A property with its cardinality histogram ({values per subject: subjects}) and value partitions."""
    if presence_only:
        return PropertyProfile(property=iri, presence_only=True)
    histogram = [CardinalityBin(values_per_subject=n, subjects=s) for n, s in sorted((bins or {}).items())]
    return PropertyProfile(property=iri, cardinality_histogram=histogram, value_partitions=list(partitions))


def klass(iri: str, instances: int, *props: PropertyProfile, observed: int | None = None, co_types=()):
    exact = observed is None or observed == instances
    return ClassProfile(
        class_iri=iri,
        instances=instances,
        observed_instances=instances if observed is None else observed,
        precision_mode=PrecisionMode.exact if exact else PrecisionMode.first_n,
        property_partitions=list(props),
        co_types=[CoTypeCount(class_iri=c, subjects=s) for c, s in co_types] or None,
    )


def failure(class_iri: str, message: str, kind: QueryKind = QueryKind.co_types) -> Failure:
    return Failure(query_kind=kind, class_iri=class_iri, message=message)


def profile_run(*classes: ClassProfile, graph=None, edges=(), failures=(), **settings) -> ProfileRun:
    graph_profile = GraphProfile(
        graph=graph,
        class_partitions=list(classes),
        declared_subclass_edges=[SubclassEdge(sub_class=s, super_class=p) for s, p in edges] or None,
    )
    return ProfileRun(
        endpoint="http://e/sparql", settings=Settings(**settings), graphs=[graph_profile], failures=list(failures)
    )
