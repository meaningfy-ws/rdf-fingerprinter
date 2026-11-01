"""FakeSparql: the real client's classification and retries over an in-memory rdflib store (P-2, P-8)."""

import json
import threading
from collections.abc import Callable
from typing import Any

import rdflib.plugins.sparql
from rdflib import BNode, Dataset, Literal, URIRef

from fingerprint.adapters.sparql import SparqlHttpClient, query_name

EX = "http://example.org/"


def term(value: str | Any) -> Any:
    """`ex:a` / `http://…` → IRI, `_:b` → blank node; anything else is passed through (use rdflib Literal)."""
    if not isinstance(value, str):
        return value
    if value.startswith("_:"):
        return BNode(value[2:])
    if value.startswith("ex:"):
        return URIRef(EX + value[3:])
    if value == "a":
        return URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
    if value.startswith("http"):
        return URIRef(value)
    return Literal(value)


def _binding(value: Any) -> dict[str, str]:
    if isinstance(value, BNode):
        return {"type": "bnode", "value": str(value)}
    if isinstance(value, str) and value.startswith("_:"):
        return {"type": "bnode", "value": value[2:]}
    if isinstance(value, Literal):
        typed = {"datatype": str(value.datatype)} if value.datatype else {}
        return {"type": "literal", "value": str(value)} | typed | ({"xml:lang": value.language} if value.language else {})
    return {"type": "uri" if isinstance(value, URIRef) else "literal", "value": str(value)}


# A FROM graph the fake does not hold must not be fetched over HTTP (pitfall-scans design, Risks).
rdflib.plugins.sparql.SPARQL_LOAD_GRAPHS = False


class FakeSparql(SparqlHttpClient):
    """Answers from `dataset`, unless a rule for the query's name (Q5, QS, …) says otherwise."""

    def __init__(self) -> None:
        super().__init__("http://fake/sparql", timeout_seconds=1, sleep=lambda seconds: None)
        self.dataset = Dataset()
        self.queries: list[str] = []
        self._rules: list[dict[str, Any]] = []
        self._lock = threading.Lock()  # rdflib's query parser is not thread-safe

    def add(self, s: Any, p: Any, o: Any, graph: str | None = None) -> None:
        target = self.dataset.graph(URIRef(graph)) if graph else self.dataset.default_graph
        target.add((term(s), term(p), term(o)))

    def on(
        self,
        name: str,
        outcome: BaseException | list[dict[str, str | None]],
        when: Callable[[str], bool] | None = None,
        times: int | None = None,
    ) -> None:
        """Raise `outcome` (or answer these rows) for queries named `name` matching `when`, `times` times."""
        self._rules.append({"name": name, "outcome": outcome, "when": when or (lambda q: True), "times": times})

    def sent(self, name: str) -> list[str]:
        return [q for q in self.queries if query_name(q).split()[0] == name]

    def _once(self, query: str) -> bytes:
        """The SPARQL JSON answer body, as the endpoint would send it."""
        name = query_name(query).split()[0]
        with self._lock:
            self.queries.append(query)
            rule = next((r for r in self._rules if r["name"] == name and r["times"] != 0 and r["when"](query)), None)
            if rule:
                if rule["times"] is not None:
                    rule["times"] -= 1
                if isinstance(rule["outcome"], BaseException):
                    raise rule["outcome"]
                rows = rule["outcome"]
                answer = {
                    "head": {"vars": list(rows[0]) if rows else []},
                    "results": {"bindings": [{k: _binding(v) for k, v in r.items() if v is not None} for r in rows]},
                }
                return json.dumps(answer).encode()
            return self.dataset.query(query).serialize(format="json")


def files(documents) -> dict[str, str]:
    """Rendered documents as file name → text, for assertions."""
    return {d.file_name: d.text for d in documents}
