"""The collection algorithm: staged discovery, class-scoped queries, exact → first-N escalation (design.md)."""

import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from typing import Any

from fingerprint.adapters.exceptions import (
    EndpointUnreachable,
    PermanentError,
    QueryTimeout,
    RetriesExhausted,
    SparqlError,
)
from fingerprint.adapters.queries import render, subjects_exact, subjects_limit, subjects_values
from fingerprint.adapters.sparql import BLANK_NODE_PREFIX, SparqlPort, redact
from fingerprint.domain.analytics import drop_none
from fingerprint.domain.exceptions import IriRefError
from fingerprint.domain.generated.profile import Depth, PrecisionMode, ProfileRun, Settings
from fingerprint.domain.vocabulary import RDF_LANG_STRING

logger = logging.getLogger(__name__)

RDF_TYPE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
DEPTHS = tuple(depth.value for depth in Depth)  # the schema lists the levels in order
EXACT, FIRST_N = PrecisionMode.exact.value, PrecisionMode.first_n.value
MODES = {"auto": (EXACT, FIRST_N), "exact": (EXACT,), "first_n": (FIRST_N,)}  # keyed by PrecisionPolicy
TOO_LARGE = (400, 413)
QUERY_KIND = {
    "Q0": "graphs",
    "Q1": "triples",
    "Q2": "predicate_partitions",
    "Q2a": "predicate_partitions",
    "QU": "untyped_subjects",
    "Q3": "class_partitions",
    "Q3a": "class_partitions",
    "Q3b": "class_partitions",
    "Q4": "declared_hierarchy",
    "QS": "subject_stream",
    "Q5": "cardinality_votes",
    "Q6": "value_partitions",
    "Q7": "object_classes",
    "Q8": "co_types",
    "Q9": "top_values",
    "Q10": "property_presence",
    "Q11": "incoming_links",
}


def _int(value: str | None) -> int | None:
    return int(value) if value not in (None, "") else None


def _tool_version() -> str:
    try:
        return version("rdf-fingerprinter")
    except PackageNotFoundError:  # running from a source tree without installation
        return "unknown"


class _Collection:
    """One run's state: the settings, the port and the failures recorded so far."""

    def __init__(self, endpoint: str, settings: Settings, sparql: SparqlPort):
        self.endpoint = redact(endpoint)
        self.settings = settings
        self.sparql = sparql
        self.failures: list[dict[str, Any]] = []
        self._lock = threading.Lock()

    def depth_at_least(self, level: str) -> bool:
        return DEPTHS.index(self.settings.depth) >= DEPTHS.index(level)

    def fail(self, name: str, message: str, graph: str | None = None, cls: str | None = None, **extra: Any) -> None:
        logger.warning(message)
        failure = {"query_kind": QUERY_KIND[name], "message": message, "graph": graph or None, "class_iri": cls, **extra}
        with self._lock:
            self.failures.append({k: v for k, v in failure.items() if v is not None})

    def select(self, name: str, graph: str | None = None, **values: Any) -> list[dict[str, str | None]]:
        return self._run(name, self.sparql.select, graph, **values)

    def ask(self, name: str, graph: str | None = None, **values: Any) -> bool:
        return self._run(name, self.sparql.ask, graph, **values)

    def _run(self, name: str, send: Any, graph: str | None, **values: Any) -> Any:
        try:
            return send(render(name, graph, scope=self.settings.object_type_scope, **values))
        except EndpointUnreachable as error:
            if name == "Q0":
                raise
            # past discovery, an authorisation refusal concerns this query only (P-5: unreachable is Q0's verdict)
            raise PermanentError(str(error), error.status) from error

    # --- discovery ---

    def named_graphs(self) -> list[str]:
        selected = bool(self.settings.selected_graphs)
        try:
            return [row["g"] for row in self.select("Q0") if row["g"]]
        except (EndpointUnreachable, RetriesExhausted) as error:
            raise EndpointUnreachable(f"cannot reach endpoint {self.endpoint}: {error}") from error
        except (QueryTimeout, PermanentError) as error:
            reason = "timeout" if isinstance(error, QueryTimeout) else str(error)
            message = f"named graphs not listed ({reason}); profiling the default graph only"
            if selected:
                logger.warning(message)
            else:
                self.fail("Q0", message)
            return []

    def declared_edges(self) -> list[dict[str, str]]:
        try:
            rows = self.select("Q4")
        except SparqlError as error:
            self.fail("Q4", f"declared hierarchy not read: {error}")
            return []
        return [{"sub_class": r["sub"], "super_class": r["sup"]} for r in rows if r["sub"] and r["sup"]]

    def predicates(self, graph: str) -> list[dict[str, Any]] | None:
        try:
            return [{"property": r["p"], "triples": _int(r["triples"])} for r in self.select("Q2", graph) if r["p"]]
        except QueryTimeout:
            logger.warning("graph %s: Q2 timed out after %s s", graph or "default", self.settings.timeout_seconds)
        except PermanentError as error:
            logger.warning("graph %s: Q2 rejected by endpoint: %s", graph or "default", error)
        try:
            return [{"property": r["p"]} for r in self.select("Q2a", graph) if r["p"]]
        except SparqlError:
            self.fail("Q2a", f"graph {graph or 'default'}: predicates not listed; completeness check skipped", graph)
            return None

    def graph_totals(self, graph: str) -> dict[str, Any]:
        totals: dict[str, Any] = {}
        for name, columns in (("Q1", ("triples", "distinct_subjects", "distinct_objects")), ("QU", ("untyped_subjects",))):
            try:
                row = self.select(name, graph)[0]
                totals.update({c: _int(row[c]) for c in columns})
            except QueryTimeout:
                self.fail(name, f"graph {graph or 'default'}: {name} timed out after {self.settings.timeout_seconds} s", graph)
            except (SparqlError, IndexError) as error:
                self.fail(name, f"graph {graph or 'default'}: {name} failed: {error}", graph)
        return totals

    def class_counts(self, graph: str) -> dict[str, int]:
        label = graph or "default"
        try:
            return {r["c"]: int(r["instances"] or 0) for r in self.select("Q3", graph) if r["c"]}
        except QueryTimeout:
            logger.warning("graph %s: class counts timed out; counting per class", label)
        except PermanentError as error:
            logger.warning("graph %s: class counts rejected (%s); counting per class", label, error)
        try:
            classes = [r["c"] for r in self.select("Q3a", graph) if r["c"]]
        except SparqlError as error:
            self.fail("Q3a", f"graph {label}: classes not listed: {error}", graph)
            return {}
        counts = {}
        for cls in classes:
            try:
                counts[cls] = int(self.select("Q3b", graph, cls=cls)[0]["instances"] or 0)
            except IriRefError:
                self.fail("Q3b", f"skipping {cls!r}: not usable in a SPARQL query", graph, cls)
            except SparqlError as error:
                self.fail("Q3b", f"graph {label}: class {cls} not counted: {error}", graph, cls)
        return counts

    # --- per class ---

    def first_wave(self, graph: str, cls: str, instances: int, mode: str, done: list[str]) -> dict[str, Any]:
        """Q8 [+Q5] [+Q6, Q7] over one subject source; `done` records the queries run, for failure kinds."""
        profile: dict[str, Any] = {"class_iri": cls, "instances": instances, "precision_mode": mode}
        if mode == EXACT:
            subjects = subjects_exact(graph, cls)
            profile["observed_instances"] = instances
        else:
            done.append("QS")
            listed = [r["s"] for r in self.select("QS", graph, cls=cls, limit=self.settings.first_n) if r["s"]]
            profile["observed_instances"] = len(listed)
            profile["sample_shared"] = not any(s.startswith(BLANK_NODE_PREFIX) for s in listed)
            if profile["sample_shared"]:
                subjects = subjects_values(listed)
            else:
                logger.info("class %s: blank-node instances; first-N sample may differ between queries", cls)
                subjects = subjects_limit(graph, cls, self.settings.first_n)
        profile["_subjects"] = subjects

        done.append("Q8")
        profile["co_types"] = [
            {"class_iri": r["d"], "subjects": _int(r["subjects"])}
            for r in self.select("Q8", graph, cls=cls, subjects=subjects)
            if r["d"]
        ]
        properties: dict[str, dict[str, Any]] = {}

        def prop(iri: str) -> dict[str, Any]:
            return properties.setdefault(iri, {"property": iri})

        if self.depth_at_least("properties"):
            done.append("Q5")
            for r in self.select("Q5", graph, subjects=subjects):
                if not r["p"]:  # an empty group may come back as one unbound row
                    continue
                prop(r["p"]).setdefault("cardinality_histogram", []).append(
                    {"values_per_subject": _int(r["n"]), "subjects": _int(r["subjects"])}
                )
        if self.depth_at_least("values"):
            done.append("Q6")
            for r in self.select("Q6", graph, subjects=subjects):
                if not r["p"]:
                    continue
                p = prop(r["p"])
                p["distinct_objects"] = p.get("distinct_objects", 0) + (_int(r["distinct"]) or 0)
                if r["kind"] == "literal":
                    p.setdefault("value_partitions", []).append(
                        {
                            "node_kind": "literal",
                            "datatype": r["dt"] or (RDF_LANG_STRING if r["lang"] else None),
                            "language": r["lang"] or None,
                            "triples": _int(r["triples"]),
                            "distinct_objects": _int(r["distinct"]),
                            "min_length": _int(r["min_length"]),
                            "max_length": _int(r["max_length"]),
                            "total_length": _int(r["total_length"]),
                            "min_value": r["min_value"],
                            "max_value": r["max_value"],
                        }
                    )
            done.append("Q7")
            for r in self.select("Q7", graph, subjects=subjects):
                if not r["p"]:
                    continue
                prop(r["p"]).setdefault("value_partitions", []).append(
                    {
                        "node_kind": r["kind"],
                        "object_class": r["t"],
                        "object_class_graph": r["tg"],
                        "triples": _int(r["triples"]),
                        "distinct_objects": _int(r["objects"]),
                    }
                )
        profile["property_partitions"] = list(properties.values())
        return profile

    def second_wave(self, graph: str, profile: dict[str, Any], predicates: list[dict[str, Any]] | None) -> None:
        cls, subjects, exact = profile["class_iri"], profile["_subjects"], profile["precision_mode"] == EXACT
        if self.depth_at_least("rich_values"):
            for p in profile["property_partitions"]:
                try:
                    rows = self.select("Q9", graph, prop=p["property"], subjects=subjects, k=self.settings.top_k)
                    p["top_values"] = [{"value": r["o"], "triples": _int(r["triples"])} for r in rows]
                    p["top_values_exact"] = exact
                except (SparqlError, IriRefError) as error:
                    self.fail(
                        "Q9", f"class {cls}, property {p['property']}: Q9 failed: {error}", graph, cls, property=p["property"]
                    )
        if self.settings.completeness_check and not exact and predicates is not None and self.depth_at_least("properties"):
            seen = {p["property"] for p in profile["property_partitions"]} | {RDF_TYPE}
            for predicate in sorted({p["property"] for p in predicates} - seen):
                try:
                    if self.ask("Q10", graph, cls=cls, prop=predicate):
                        profile["property_partitions"].append({"property": predicate, "presence_only": True})
                except (SparqlError, IriRefError) as error:
                    self.fail("Q10", f"class {cls}, property {predicate}: Q10 failed: {error}", graph, cls, property=predicate)
        if self.depth_at_least("links"):
            try:
                profile["incoming_links"] = [
                    {"subject_class": r["sc"], "property": r["p"], "triples": _int(r["triples"])}
                    for r in self.select("Q11", graph, subjects=subjects)
                    if r["p"]
                ]
            except (SparqlError, IriRefError) as error:
                self.fail("Q11", f"class {cls}: Q11 failed: {error}", graph, cls)

    def profile_class(
        self, graph: str, cls: str, instances: int, predicates: list[dict[str, Any]] | None
    ) -> dict[str, Any] | None:
        modes = MODES[self.settings.precision_policy]
        last = "QS"
        for index, mode in enumerate(modes):
            done: list[str] = []
            try:
                profile = self.first_wave(graph, cls, instances, mode, done)
                break
            except IriRefError as error:
                self.fail(done[-1] if done else "Q8", f"skipping {error.iri!r}: not usable in a SPARQL query", graph, cls)
                return None
            except QueryTimeout:
                last = done[-1] if done else "Q8"
                following = modes[index + 1] if index + 1 < len(modes) else "nothing"
                logger.warning(
                    "class %s: %s timed out after %s s; trying %s", cls, mode, self.settings.timeout_seconds, following
                )
            except PermanentError as error:
                name = done[-1] if done else "Q8"
                if mode == FIRST_N and name != "QS" and error.status in TOO_LARGE:
                    message = f"class {cls}: endpoint rejected {self.settings.first_n}-IRI query; lower --first-n"
                else:
                    message = f"{name} rejected by endpoint: {error}"
                self.fail(name, message, graph, cls, attempts=index + 1)
                return None
        else:
            self.fail(last, f"class {cls}: not profiled after {len(modes)} attempts", graph, cls, attempts=len(modes))
            return None
        self.second_wave(graph, profile, predicates)
        queries = len(done)
        logger.info(
            "class %s: %s, %s of %s instances, %s queries", cls, mode, profile["observed_instances"], instances, queries
        )
        profile.pop("_subjects")
        return profile

    def profile_graph(self, graph: str, edges: list[dict[str, str]]) -> dict[str, Any]:
        label = graph or "default"
        logger.info("graph %s: profiling", label)
        result: dict[str, Any] = {"graph": graph or None}
        predicates = None
        if self.settings.graph_statistics:
            result.update(self.graph_totals(graph))
        if self.settings.graph_statistics or (self.settings.completeness_check and self.depth_at_least("properties")):
            predicates = self.predicates(graph)
            result["predicate_partitions"] = predicates or []
        if not self.depth_at_least("classes"):
            return result
        result["declared_subclass_edges"] = edges
        counts = self.class_counts(graph)
        usable = {}
        for cls, instances in counts.items():
            if cls.startswith(BLANK_NODE_PREFIX):
                self.fail("Q3", f"skipping {cls!r}: not usable in a SPARQL query", graph, cls)
            else:
                usable[cls] = instances
        ordered = sorted(usable, key=lambda c: (-usable[c], c))
        with ThreadPoolExecutor(max_workers=self.settings.concurrency) as pool:
            profiles = list(pool.map(lambda c: self.profile_class(graph, c, usable[c], predicates), ordered))
        result["class_partitions"] = [p for p in profiles if p]
        return result


def collect(endpoint: str, settings: Settings, sparql: SparqlPort) -> ProfileRun:
    """Collect the raw profile of every graph; raises EndpointUnreachable, records every other failure."""
    started = datetime.now(UTC)
    run = _Collection(endpoint, settings, sparql)
    named = run.named_graphs()
    graphs = list(settings.selected_graphs or ["", *named])
    edges = run.declared_edges() if run.depth_at_least("classes") else []
    profiles = []
    for graph in graphs:
        try:
            profiles.append(run.profile_graph(graph, edges))
        except IriRefError:
            run.fail("Q3", f"skipping {graph!r}: not usable in a SPARQL query", graph)
    return ProfileRun.model_validate(
        drop_none(
            {
                "endpoint": run.endpoint,
                "started_at": started,
                "finished_at": datetime.now(UTC),
                "tool_version": _tool_version(),
                "settings": settings.model_dump(),
                "graphs": profiles,
                "failures": run.failures,
            }
        )
    )
