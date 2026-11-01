"""The collection algorithm: staged discovery, class-scoped queries, exact → first-N escalation (design.md)."""

import logging
import threading
import time
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from typing import Any

# Only rdflib's term and row types: collection reads the client's typed results, never a graph or store (P-8).
from rdflib import BNode, URIRef
from rdflib.query import ResultRow

from fingerprint import __version__
from fingerprint.adapters.exceptions import (
    EndpointUnreachable,
    PermanentError,
    QueryTimeout,
    RetriesExhausted,
    SparqlError,
)
from fingerprint.adapters.queries import (
    pitfall_ask_query,
    pitfall_count_query,
    pitfall_example_query,
    render,
    subjects_exact,
    subjects_limit,
    subjects_values,
)
from fingerprint.adapters.sparql import SparqlPort, redact
from fingerprint.domain.exceptions import IriRefError
from fingerprint.domain.profile import (
    CardinalityBin,
    ClassProfile,
    CoTypeCount,
    Depth,
    Failure,
    GraphProfile,
    IncomingLink,
    NodeKind,
    PitfallCheck,
    PitfallExample,
    PitfallResult,
    PitfallScope,
    PitfallTerm,
    PrecisionMode,
    PrecisionPolicy,
    PredicatePartition,
    ProfileRun,
    PropertyProfile,
    QueryKind,
    Settings,
    SubclassEdge,
    ValueCount,
    ValuePartition,
)
from fingerprint.domain.vocabulary import BLANK_NODE_PREFIX, RDF_LANG_STRING, RDF_TYPE

logger = logging.getLogger(__name__)

DEPTHS = tuple(depth.value for depth in Depth)  # the schema lists the levels in order
EXACT, FIRST_N = PrecisionMode.exact, PrecisionMode.first_n
MODES = {PrecisionPolicy.auto: (EXACT, FIRST_N), PrecisionPolicy.exact: (EXACT,), PrecisionPolicy.first_n: (FIRST_N,)}
TOO_LARGE = (400, 413)
QUERY_KIND = {
    "Q0": QueryKind.graphs,
    "Q1": QueryKind.triples,
    "Q2": QueryKind.predicate_partitions,
    "Q2a": QueryKind.predicate_partitions,
    "QU": QueryKind.untyped_subjects,
    "Q3": QueryKind.class_partitions,
    "Q3a": QueryKind.class_partitions,
    "Q3b": QueryKind.class_partitions,
    "Q4": QueryKind.declared_hierarchy,
    "QS": QueryKind.subject_stream,
    "Q5": QueryKind.cardinality_votes,
    "Q6": QueryKind.value_partitions,
    "Q7": QueryKind.object_classes,
    "Q8": QueryKind.co_types,
    "Q9": QueryKind.top_values,
    "Q10": QueryKind.property_presence,
    "Q11": QueryKind.incoming_links,
    "PITFALL": QueryKind.pitfall,
}


def _text(term: Any) -> str | None:
    """A term as profile text: IRIs and literals by their lexical form, blank nodes as `_:<id>`."""
    if term is None:
        return None
    return BLANK_NODE_PREFIX + term if isinstance(term, BNode) else str(term)


def _term(term: Any) -> str:
    """A bound term as profile text."""
    text = _text(term)
    assert text is not None, "an unbound term where the query binds one"
    return text


def _int(term: Any) -> int | None:
    return int(term) if term is not None and str(term) != "" else None


class _Collection:
    """One run's state: the settings, the port and the failures recorded so far."""

    def __init__(self, endpoint: str, settings: Settings, sparql: SparqlPort):
        self.endpoint = redact(endpoint)
        self.settings = settings
        self.sparql = sparql
        self.failures: list[Failure] = []
        self._lock = threading.Lock()

    def depth_at_least(self, level: Depth) -> bool:
        return DEPTHS.index(self.settings.depth) >= DEPTHS.index(level)

    def fail(
        self,
        name: str,
        message: str,
        graph: str | None = None,
        cls: str | None = None,
        property: str | None = None,
        attempts: int | None = None,
        check_id: str | None = None,
    ) -> None:
        logger.warning(message)
        failure = Failure(
            query_kind=QUERY_KIND[name],
            message=message,
            graph=graph or None,
            class_iri=cls,
            property=property,
            attempts=attempts,
            check_id=check_id,
        )
        with self._lock:
            self.failures.append(failure)

    def select(self, name: str, graph: str | None = None, **values: Any) -> list[ResultRow]:
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
            return [str(row["g"]) for row in self.select("Q0") if row["g"]]
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

    def declared_edges(self) -> list[SubclassEdge]:
        try:
            rows = self.select("Q4")
        except SparqlError as error:
            self.fail("Q4", f"declared hierarchy not read: {error}")
            return []
        return [SubclassEdge(sub_class=_term(r["sub"]), super_class=_term(r["sup"])) for r in rows if r["sub"] and r["sup"]]

    def predicates(self, graph: str) -> list[PredicatePartition] | None:
        try:
            rows = self.select("Q2", graph)
            return [PredicatePartition(property=str(r["p"]), triples=_int(r["triples"])) for r in rows if r["p"]]
        except QueryTimeout:
            logger.warning("graph %s: Q2 timed out after %s s", graph or "default", self.settings.timeout_seconds)
        except PermanentError as error:
            logger.warning("graph %s: Q2 rejected by endpoint: %s", graph or "default", error)
        try:
            return [PredicatePartition(property=str(r["p"])) for r in self.select("Q2a", graph) if r["p"]]
        except SparqlError:
            self.fail("Q2a", f"graph {graph or 'default'}: predicates not listed; completeness check skipped", graph)
            return None

    def graph_totals(self, graph: str) -> GraphProfile:
        totals: list[tuple[str, Any]] = []
        for name, columns in (("Q1", ("triples", "distinct_subjects", "distinct_objects")), ("QU", ("untyped_subjects",))):
            try:
                row = self.select(name, graph)[0]
                totals += [(c, _int(row[c])) for c in columns]
            except QueryTimeout:
                self.fail(name, f"graph {graph or 'default'}: {name} timed out after {self.settings.timeout_seconds} s", graph)
            except (SparqlError, IndexError) as error:
                self.fail(name, f"graph {graph or 'default'}: {name} failed: {error}", graph)
        return GraphProfile(graph=graph or None, **{column: count for column, count in totals})

    def class_counts(self, graph: str) -> list[tuple[str, int]]:
        """(class, instances) pairs; blank-node classes keep their `_:` text, to be reported as skipped."""
        label = graph or "default"
        try:
            return [(_term(r["c"]), int(r["instances"] or 0)) for r in self.select("Q3", graph) if r["c"]]
        except QueryTimeout:
            logger.warning("graph %s: class counts timed out; counting per class", label)
        except PermanentError as error:
            logger.warning("graph %s: class counts rejected (%s); counting per class", label, error)
        try:
            classes = [_term(r["c"]) for r in self.select("Q3a", graph) if r["c"]]
        except SparqlError as error:
            self.fail("Q3a", f"graph {label}: classes not listed: {error}", graph)
            return []
        counts = []
        for cls in classes:
            try:
                counts.append((cls, int(self.select("Q3b", graph, cls=cls)[0]["instances"] or 0)))
            except IriRefError:
                self.fail("Q3b", f"skipping {cls!r}: not usable in a SPARQL query", graph, cls)
            except SparqlError as error:
                self.fail("Q3b", f"graph {label}: class {cls} not counted: {error}", graph, cls)
        return counts

    # --- per class ---

    def first_wave(
        self, graph: str, cls: str, instances: int, mode: PrecisionMode, done: list[str]
    ) -> tuple[ClassProfile, Any]:
        """Q8 [+Q5] [+Q6, Q7] over one subject source, and that source for the second wave; `done` records the
        queries run, for failure kinds."""
        sample_shared = None
        if mode == EXACT:
            subjects = subjects_exact(graph, cls)
            observed = instances
        else:
            done.append("QS")
            listed = [r["s"] for r in self.select("QS", graph, cls=cls, limit=self.settings.first_n) if r["s"]]
            observed = len(listed)
            sample_shared = not any(isinstance(s, BNode) for s in listed)
            if sample_shared:
                subjects = subjects_values([str(s) for s in listed])
            else:
                logger.info("class %s: blank-node instances; first-N sample may differ between queries", cls)
                subjects = subjects_limit(graph, cls, self.settings.first_n)

        done.append("Q8")
        co_types = [
            CoTypeCount(class_iri=_term(r["d"]), subjects=_int(r["subjects"]))
            for r in self.select("Q8", graph, cls=cls, subjects=subjects)
            if r["d"]
        ]
        # Rows of Q5–Q7 grouped by property IRI, in first-seen order; each property is built once below.
        order: list[str] = []
        bins: dict[str, list[CardinalityBin]] = {}  # dict-ok: lookup index by property IRI
        partitions: dict[str, list[ValuePartition]] = {}  # dict-ok: lookup index by property IRI
        distinct: dict[str, int] = {}  # dict-ok: lookup index by property IRI

        def seen(iri: str) -> str:
            if iri not in order:
                order.append(iri)
            return iri

        if self.depth_at_least(Depth.properties):
            done.append("Q5")
            for r in self.select("Q5", graph, subjects=subjects):
                if r["p"]:  # an empty group may come back as one unbound row
                    histogram = bins.setdefault(seen(str(r["p"])), [])
                    histogram.append(CardinalityBin(values_per_subject=int(r["n"]), subjects=int(r["subjects"])))
        if self.depth_at_least(Depth.values):
            done.append("Q6")
            for r in self.select("Q6", graph, subjects=subjects):
                if not r["p"]:
                    continue
                iri = seen(str(r["p"]))
                distinct[iri] = distinct.get(iri, 0) + (_int(r["distinct"]) or 0)
                if str(r["kind"]) == NodeKind.literal.value:
                    partitions.setdefault(iri, []).append(self.literal_partition(r))
            done.append("Q7")
            for r in self.select("Q7", graph, subjects=subjects):
                if r["p"]:
                    partitions.setdefault(seen(str(r["p"])), []).append(
                        ValuePartition(
                            node_kind=NodeKind(str(r["kind"])),
                            object_class=_text(r["t"]),
                            object_class_graph=_text(r["tg"]),
                            triples=_int(r["triples"]),
                            distinct_objects=_int(r["objects"]),
                        )
                    )
        properties = [
            PropertyProfile(
                property=iri,
                cardinality_histogram=bins.get(iri),
                distinct_objects=distinct.get(iri),
                value_partitions=partitions.get(iri),
            )
            for iri in order
        ]
        profile = ClassProfile(
            class_iri=cls,
            instances=instances,
            precision_mode=mode,
            observed_instances=observed,
            sample_shared=sample_shared,
            co_types=co_types,
            property_partitions=properties,
        )
        return profile, subjects

    @staticmethod
    def literal_partition(r: ResultRow) -> ValuePartition:
        return ValuePartition(
            node_kind=NodeKind.literal,
            datatype=_text(r["dt"]) or (RDF_LANG_STRING if r["lang"] else None),
            language=_text(r["lang"]) or None,
            triples=_int(r["triples"]),
            distinct_objects=_int(r["distinct"]),
            min_length=_int(r["min_length"]),
            max_length=_int(r["max_length"]),
            total_length=_int(r["total_length"]),
            min_value=_text(r["min_value"]),
            max_value=_text(r["max_value"]),
        )

    def second_wave(
        self, graph: str, profile: ClassProfile, subjects: Any, predicates: list[PredicatePartition] | None
    ) -> ClassProfile:
        cls, exact = profile.class_iri, profile.precision_mode == EXACT
        properties = list(profile.property_partitions or [])
        incoming = None
        if self.depth_at_least(Depth.rich_values):
            for index, p in enumerate(properties):
                try:
                    rows = self.select("Q9", graph, prop=p.property, subjects=subjects, k=self.settings.top_k)
                    top = [ValueCount(value=_text(r["o"]), triples=_int(r["triples"])) for r in rows]
                    properties[index] = p.model_copy(update={"top_values": top, "top_values_exact": exact})
                except (SparqlError, IriRefError) as error:
                    self.fail("Q9", f"class {cls}, property {p.property}: Q9 failed: {error}", graph, cls, property=p.property)
        if self.settings.completeness_check and not exact and predicates is not None and self.depth_at_least(Depth.properties):
            seen = {p.property for p in properties} | {RDF_TYPE}
            for predicate in sorted({p.property for p in predicates} - seen):
                try:
                    if self.ask("Q10", graph, cls=cls, prop=predicate):
                        properties.append(PropertyProfile(property=predicate, presence_only=True))
                except (SparqlError, IriRefError) as error:
                    self.fail("Q10", f"class {cls}, property {predicate}: Q10 failed: {error}", graph, cls, property=predicate)
        if self.depth_at_least(Depth.links):
            try:
                incoming = [
                    IncomingLink(subject_class=_text(r["sc"]), property=_text(r["p"]), triples=_int(r["triples"]))
                    for r in self.select("Q11", graph, subjects=subjects)
                    if r["p"]
                ]
            except (SparqlError, IriRefError) as error:
                self.fail("Q11", f"class {cls}: Q11 failed: {error}", graph, cls)
        return profile.model_copy(update={"property_partitions": properties, "incoming_links": incoming})

    def profile_class(
        self, graph: str, cls: str, instances: int, predicates: list[PredicatePartition] | None
    ) -> ClassProfile | None:
        modes = MODES[self.settings.precision_policy]
        last = "QS"
        for index, mode in enumerate(modes):
            done: list[str] = []
            try:
                profile, subjects = self.first_wave(graph, cls, instances, mode, done)
                break
            except IriRefError as error:
                self.fail(done[-1] if done else "Q8", f"skipping {error.iri!r}: not usable in a SPARQL query", graph, cls)
                return None
            except QueryTimeout:
                last = done[-1] if done else "Q8"
                following = modes[index + 1].value if index + 1 < len(modes) else "nothing"
                logger.warning(
                    "class %s: %s timed out after %s s; trying %s", cls, mode.value, self.settings.timeout_seconds, following
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
        profile = self.second_wave(graph, profile, subjects, predicates)
        queries = len(done)
        logger.info(
            "class %s: %s, %s of %s instances, %s queries", cls, mode.value, profile.observed_instances, instances, queries
        )
        return profile

    def profile_graph(self, graph: str, edges: list[SubclassEdge]) -> GraphProfile:
        label = graph or "default"
        logger.info("graph %s: profiling", label)
        result = self.graph_totals(graph) if self.settings.graph_statistics else GraphProfile(graph=graph or None)
        predicates = None
        if self.settings.graph_statistics or (self.settings.completeness_check and self.depth_at_least(Depth.properties)):
            predicates = self.predicates(graph)
            result = result.model_copy(update={"predicate_partitions": predicates or []})
        if not self.depth_at_least(Depth.classes):
            return result
        usable = []
        for cls, instances in self.class_counts(graph):
            if cls.startswith(BLANK_NODE_PREFIX):
                self.fail("Q3", f"skipping {cls!r}: not usable in a SPARQL query", graph, cls)
            else:
                usable.append((cls, instances))
        ordered = sorted(usable, key=lambda pair: (-pair[1], pair[0]))
        with ThreadPoolExecutor(max_workers=self.settings.concurrency) as pool:
            profiles = list(pool.map(lambda pair: self.profile_class(graph, pair[0], pair[1], predicates), ordered))
        return result.model_copy(update={"declared_subclass_edges": edges, "class_partitions": [p for p in profiles if p]})


def _pitfall_term(term: Any) -> PitfallTerm | None:
    """A pitfall row's term as text and kind (a literal's lexical form); None when the variable is unbound."""
    if term is None:
        return None
    if isinstance(term, URIRef):
        return PitfallTerm(text=str(term), kind=NodeKind.iri)
    if isinstance(term, BNode):
        return PitfallTerm(text=str(term), kind=NodeKind.blank_node)
    return PitfallTerm(text=str(term), kind=NodeKind.literal)


UNJOINED_DEFAULT = "the default graph's data checks ran without the schema graphs"


class _PitfallScan:
    """The pitfall stage of one run (pitfall-scans design D-4): per graph, the checks its scope selects."""

    def __init__(self, collection: "_Collection", checks: Sequence[PitfallCheck]):
        self.collection = collection
        self.checks = list(checks)
        self.schema_graphs = list(collection.settings.schema_graphs or [])

    def selected(self, graph: str) -> tuple[list[PitfallCheck], list[str]]:
        """(checks, schema graphs to join): every check alone without schema graphs; else schema checks on a
        schema graph (alone) and data checks on the others (joined with the schema graphs)."""
        if not self.schema_graphs:
            return self.checks, []
        if graph in self.schema_graphs:
            return [c for c in self.checks if c.scope == PitfallScope.schema], []
        return [c for c in self.checks if c.scope == PitfallScope.data], self.schema_graphs

    def scan(self, graph: str) -> list[PitfallResult] | None:
        """The results of one graph, or None when it holds no triple (or the emptiness check failed)."""
        run = self.collection
        label = graph or "default"
        try:
            if not run.sparql.ask(pitfall_ask_query(graph)):
                logger.info("graph %s: empty; no pitfall scan", label)
                return None
        except SparqlError as error:
            run.fail("PITFALL", f"graph {label}: pitfall scan skipped, emptiness check failed: {error}", graph)
            return None
        checks, joined = self.selected(graph)
        if not graph and self.schema_graphs:  # no FROM for the default graph (DEC-20)
            logger.warning("graph default: %s", UNJOINED_DEFAULT)
        with ThreadPoolExecutor(max_workers=run.settings.concurrency) as pool:  # map keeps the order (DEC-21)
            outcomes = list(pool.map(lambda check: self.check(graph, check, joined), checks))
        results = [r for r in outcomes if r is not None]
        found = sum(1 for r in results if r.count)
        logger.info("graph %s: %d pitfall checks, %d with findings", label, len(results), found)
        return results

    def check(self, graph: str, check: PitfallCheck, joined: list[str]) -> PitfallResult | None:
        run, label = self.collection, graph or "default"
        started = time.monotonic()
        try:
            rows = run.sparql.select(pitfall_count_query(check.check_id, check.query, graph, joined))
            count = int(rows[0]["n"]) if rows else 0
        except (SparqlError, TypeError, ValueError) as error:  # TypeError/ValueError: an unbound or odd ?n
            message = f"graph {label}: pitfall {check.check_id}: count failed: {error}"
            run.fail("PITFALL", message, graph, check_id=check.check_id)
            return None
        examples: list[PitfallExample] = []
        if count:
            limit = run.settings.pitfall_examples
            try:
                answer = run.sparql.select(pitfall_example_query(check.check_id, check.query, graph, joined, limit))
                examples = [
                    PitfallExample(
                        entity=_pitfall_term(r["entity"]),
                        property=_pitfall_term(r["property"]),
                        value=_pitfall_term(r["value"]),
                    )
                    for r in answer
                ]
            except SparqlError as error:
                message = f"graph {label}: pitfall {check.check_id}: examples failed: {error}"
                run.fail("PITFALL", message, graph, check_id=check.check_id)
        return PitfallResult(
            check_id=check.check_id,
            title=check.title,
            description=check.description,
            importance=check.importance,
            scope=check.scope,
            source=check.source if check.origin == "packaged" else f"{check.source} ({check.origin})",
            heuristic=check.heuristic,
            count=count,
            examples=examples,
            seconds=round(time.monotonic() - started, 3),
        )


def collect(endpoint: str, settings: Settings, sparql: SparqlPort, checks: Sequence[PitfallCheck] = ()) -> ProfileRun:
    """Collect the raw profile of every graph; raises EndpointUnreachable, records every other failure.
    With `pitfall_scan` on, the `checks` run on every graph after it is profiled (pitfall-scans)."""
    started = datetime.now(UTC)
    run = _Collection(endpoint, settings, sparql)
    named = run.named_graphs()
    graphs = list(settings.selected_graphs or ["", *named])
    scan = _PitfallScan(run, checks) if settings.pitfall_scan else None
    if scan:  # schema graphs are always profiled, so their schema findings have a place (design D-4)
        graphs += [g for g in scan.schema_graphs if g not in graphs]
    edges = run.declared_edges() if run.depth_at_least(Depth.classes) else []
    profiles = []
    for graph in graphs:
        try:
            profile = run.profile_graph(graph, edges)
            if scan:
                profile = profile.model_copy(update={"pitfalls": scan.scan(graph)})
            profiles.append(profile)
        except IriRefError:
            run.fail("Q3", f"skipping {graph!r}: not usable in a SPARQL query", graph)
    return ProfileRun(
        endpoint=run.endpoint,
        started_at=started,
        finished_at=datetime.now(UTC),
        tool_version=__version__,
        settings=settings,
        graphs=profiles,
        failures=run.failures,
    )
