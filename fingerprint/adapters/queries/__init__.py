"""The collection queries (design.md "Query templates") and how they are filled (P-3)."""

from collections.abc import Iterable
from importlib.resources import files
from string import Template

from fingerprint.domain.iri import to_iriref

QUERY_FILES = {
    "Q0": "q0_named_graphs.rq",
    "Q1": "q1_graph_totals.rq",
    "Q2": "q2_predicate_partitions.rq",
    "Q2a": "q2a_predicates.rq",
    "QU": "qu_untyped_subjects.rq",
    "Q3": "q3_class_partitions.rq",
    "Q3a": "q3a_classes.rq",
    "Q3b": "q3b_class_instances.rq",
    "Q4": "q4_declared_hierarchy.rq",
    "QS": "qs_subject_stream.rq",
    "Q5": "q5_cardinality_votes.rq",
    "Q6": "q6_value_partitions.rq",
    "Q7": "q7_object_classes.rq",
    "Q8": "q8_co_types.rq",
    "Q9": "q9_top_values.rq",
    "Q10": "q10_property_presence.rq",
    "Q11": "q11_incoming_links.rq",
}
_TEMPLATES = {name: Template((files(__package__) / file).read_text()) for name, file in QUERY_FILES.items()}


def _graph(graph: str | None) -> tuple[str, str]:
    """`GRAPH <g> {` / `}` for a named graph; nothing for the default graph."""
    return (f"GRAPH {to_iriref(graph)} {{", "}") if graph else ("", "")


def subjects_exact(graph: str | None, cls: str) -> str:
    graph_open, graph_close = _graph(graph)
    return f"{graph_open} ?s a {to_iriref(cls)} . {graph_close}"


def subjects_values(iris: Iterable[str]) -> str:
    """The first-N instances listed by QS, in one VALUES block."""
    return "VALUES ?s { " + " ".join(to_iriref(iri) for iri in iris) + " }"


def subjects_limit(graph: str | None, cls: str, limit: int) -> str:
    """Fallback when QS listed blank nodes, which VALUES cannot carry."""
    distinct = "" if graph else "DISTINCT "
    return f"{{ SELECT {distinct}?s {{ {subjects_exact(graph, cls)} }} LIMIT {int(limit)} }}"


def type_lookup(graph: str | None, scope: str) -> str:
    if scope == "any_graph":
        return "OPTIONAL { { ?o a ?t } UNION { GRAPH ?tg { ?o a ?t } } }"
    graph_open, graph_close = _graph(graph)
    return f"OPTIONAL {{ {graph_open} ?o a ?t . {graph_close} }}"


def render(
    name: str,
    graph: str | None = None,
    *,
    cls: str | None = None,
    prop: str | None = None,
    subjects: str = "",
    scope: str = "same_graph",
    limit: int | None = None,
    k: int | None = None,
) -> str:
    """The text of query `name` for one graph (None or "" is the default graph)."""
    graph_open, graph_close = _graph(graph)
    return _TEMPLATES[name].substitute(
        graph_open=graph_open,
        graph_close=graph_close,
        distinct="" if graph else "DISTINCT ",
        cls=to_iriref(cls) if cls else "",
        prop=to_iriref(prop) if prop else "",
        subjects=subjects,
        type_lookup=type_lookup(graph, scope),
        limit=int(limit) if limit is not None else "",
        k=int(k) if k is not None else "",
    )
