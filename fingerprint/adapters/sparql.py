"""SPARQL access: the port the service layer depends on and its HTTP implementation (P-2, P-5).

Queries go out as SPARQL 1.1 Protocol form POSTs through the standard library, which applies the
per-query timeout; rdflib reads the JSON answer into typed terms (domain-object-model P-5).
"""

import base64
import http.client
import json
import logging
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from typing import Any, Protocol

from rdflib import BNode, Literal, URIRef
from rdflib.query import ResultRow
from rdflib.term import Identifier, Variable

from fingerprint import __version__, config
from fingerprint.adapters.exceptions import (  # noqa: F401 — also importable from here (2.0)
    EndpointUnreachable,
    PermanentError,
    QueryTimeout,
    RetriesExhausted,
    SparqlError,
    TransientError,
)
from fingerprint.domain.vocabulary import BLANK_NODE_PREFIX  # noqa: F401 — also importable from here (2.0)

logger = logging.getLogger(__name__)

HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Accept": "application/sparql-results+json",
    "User-Agent": f"rdf-fingerprinter/{__version__}",
}


class SparqlPort(Protocol):
    def select(self, query: str) -> list[ResultRow]: ...

    def ask(self, query: str) -> bool: ...


def redact(url: str) -> str:
    """The endpoint URL without user info and query string, which may hold credentials; for logs and reports."""
    parts = urllib.parse.urlsplit(url)
    host = parts.hostname or ""
    netloc = f"{host}:{parts.port}" if parts.port else host
    return urllib.parse.urlunsplit((parts.scheme, netloc, parts.path, "", ""))


def query_name(query: str) -> str:
    """Every query template starts with a `# <name>` comment line."""
    first = query.lstrip().splitlines()[0] if query.strip() else ""
    return first.removeprefix("#").strip() if first.startswith("#") else first[:60]


def _excerpt(body: Any) -> str:
    text = body.decode("utf-8", "replace") if isinstance(body, bytes) else str(body)
    return " ".join(text.split())[: config.error_excerpt_length]


def classify(error: BaseException) -> SparqlError:
    """Map a client exception to the failure classes of P-5."""
    if isinstance(error, SparqlError):
        return error
    if isinstance(error, (socket.timeout, TimeoutError)):
        return QueryTimeout(f"timed out: {error}")
    if isinstance(error, urllib.error.HTTPError):
        body = _excerpt(error.read() if error.fp else b"")
        message = f"{error.code} {body}".strip()
        if error.code == 504 or (error.code == 500 and any(m in body.lower() for m in config.timeout_markers)):
            return QueryTimeout(message, error.code)
        if error.code in (429, 502, 503):
            return TransientError(message, error.code)
        if error.code in (401, 403, 407):
            return EndpointUnreachable(message, error.code)
        return PermanentError(message, error.code)
    if isinstance(error, urllib.error.URLError):
        if isinstance(error.reason, (socket.timeout, TimeoutError)):
            return QueryTimeout(f"timed out: {error.reason}")
        return TransientError(str(error.reason))
    if isinstance(error, http.client.InvalidURL):
        return PermanentError("the endpoint URL cannot be used")  # its text may hold credentials
    if isinstance(error, (ConnectionError, http.client.HTTPException, OSError)):
        return TransientError(f"{type(error).__name__}: {error}")
    return PermanentError(f"unreadable response: {error}")  # also an answer rdflib cannot parse


def _term(binding: dict[str, str]) -> Identifier:  # dict-ok: SPARQL JSON being parsed
    kind, value = binding["type"], binding["value"]
    if kind == "uri":
        return URIRef(value)
    if kind == "bnode":
        return BNode(value)
    if kind in ("literal", "typed-literal"):
        try:
            return Literal(value, lang=binding.get("xml:lang"), datatype=binding.get("datatype"), normalize=False)
        except ValueError:  # a language tag rdflib refuses (e.g. en_US): the text is what the profile keeps
            return Literal(value, normalize=False)
    raise ValueError(f"unknown term type {kind!r}")


def parse_answer(body: bytes) -> bool | list[ResultRow]:
    """A SPARQL JSON answer: the ASK boolean, or SELECT rows of rdflib terms in the endpoint's own lexical form.

    rdflib's `Result.parse` normalises literals (`…Z` → `+00:00`, `1.5E2` → `150.0`) and refuses lax language
    tags, which would change or drop profile values; the terms are built here instead, with `normalize=False`."""
    answer = json.loads(body)
    if "boolean" in answer:
        return bool(answer["boolean"])
    labels = [Variable(name) for name in answer["head"]["vars"]]
    return [
        ResultRow({Variable(name): _term(term) for name, term in binding.items()}, labels)  # dict-ok: rdflib row
        for binding in answer["results"]["bindings"]
    ]


class SparqlHttpClient:
    """One HTTP request per call, so one client is safe to share between threads."""

    def __init__(self, endpoint: str, timeout_seconds: int, sleep: Callable[[float], None] = time.sleep):
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds
        self._sleep = sleep
        # urllib does not read user info: send it as Basic authentication, never as part of the URL.
        parts = urllib.parse.urlsplit(endpoint)
        netloc = parts.netloc.rpartition("@")[2]
        self._url = urllib.parse.urlunsplit(parts._replace(netloc=netloc))
        self._headers = HEADERS
        if parts.username is not None:
            user = urllib.parse.unquote(parts.username)
            password = urllib.parse.unquote(parts.password or "")
            token = base64.b64encode(f"{user}:{password}".encode()).decode()
            self._headers = HEADERS | {"Authorization": f"Basic {token}"}  # dict-ok: urllib headers

    def select(self, query: str) -> list[ResultRow]:
        """Rows of `URIRef`, `BNode` and typed `Literal` terms; an unbound variable is None."""
        answer = self._with_retries(query)
        if isinstance(answer, bool):
            raise PermanentError("unreadable response: ASK answer to a SELECT query")
        return answer

    def ask(self, query: str) -> bool:
        answer = self._with_retries(query)
        if not isinstance(answer, bool):
            raise PermanentError("unreadable response: SELECT answer to an ASK query")
        return answer

    def _with_retries(self, query: str) -> bool | list[ResultRow]:
        backoff = config.retry_backoff_seconds
        for attempt in range(len(backoff) + 1):
            try:
                return parse_answer(self._once(query))
            except Exception as raw:  # classified below; nothing is swallowed
                error = classify(raw)
                if not isinstance(error, TransientError):
                    raise error from raw
                if attempt == len(backoff):
                    raise RetriesExhausted(f"{error} (after {attempt} retries)") from raw
                logger.info("retrying %s (%d/%d): %s", query_name(query), attempt + 1, len(backoff), error)
                self._sleep(backoff[attempt])
        raise AssertionError("unreachable")

    def _once(self, query: str) -> bytes:
        """The answer body of one SPARQL 1.1 Protocol POST."""
        body = urllib.parse.urlencode({"query": query}).encode()  # dict-ok: urllib form encoding
        request = urllib.request.Request(self._url, data=body, headers=self._headers, method="POST")
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            return response.read()
