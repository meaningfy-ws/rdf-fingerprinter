"""SPARQL access: the port the service layer depends on and its HTTP implementation (P-2, P-5).

Queries go out as SPARQL 1.1 Protocol form POSTs through the standard library, which applies the
per-query timeout; rdflib reads the JSON answer into typed terms (domain-object-model P-5).
"""

import http.client
import logging
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from io import BytesIO
from typing import Any, Protocol

from rdflib.query import Result, ResultRow

from fingerprint import __version__, config
from fingerprint.adapters.exceptions import (  # noqa: F401 — also importable from here (2.0)
    EndpointUnreachable,
    PermanentError,
    QueryTimeout,
    RetriesExhausted,
    SparqlError,
    TransientError,
)

logger = logging.getLogger(__name__)

BLANK_NODE_PREFIX = "_:"
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
    if isinstance(error, (ConnectionError, http.client.HTTPException, OSError)):
        return TransientError(f"{type(error).__name__}: {error}")
    return PermanentError(f"unreadable response: {error}")  # also an answer rdflib cannot parse


class SparqlHttpClient:
    """One HTTP request per call, so one client is safe to share between threads."""

    def __init__(self, endpoint: str, timeout_seconds: int, sleep: Callable[[float], None] = time.sleep):
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds
        self._sleep = sleep

    def select(self, query: str) -> list[ResultRow]:
        """Rows of `URIRef`, `BNode` and typed `Literal` terms; an unbound variable is None."""
        result = self._with_retries(query)
        if result.type != "SELECT":
            raise PermanentError(f"unreadable response: {result.type} answer to a SELECT query")
        return list(result)  # type: ignore[arg-type]

    def ask(self, query: str) -> bool:
        result = self._with_retries(query)
        if result.type != "ASK":
            raise PermanentError(f"unreadable response: {result.type} answer to an ASK query")
        return bool(result.askAnswer)

    def _with_retries(self, query: str) -> Result:
        backoff = config.retry_backoff_seconds
        for attempt in range(len(backoff) + 1):
            try:
                return Result.parse(BytesIO(self._once(query)), format="json")
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
        request = urllib.request.Request(self.endpoint, data=body, headers=HEADERS, method="POST")
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            return response.read()
