"""SPARQL access: the port the service layer depends on and its SPARQLWrapper implementation (P-2, P-5)."""

import http.client
import json
import logging
import socket
import time
import urllib.error
from collections.abc import Callable
from typing import Any, Protocol

from SPARQLWrapper import JSON, POST, SPARQLWrapper
from SPARQLWrapper.SPARQLExceptions import (
    EndPointInternalError,
    EndPointNotFound,
    QueryBadFormed,
    SPARQLWrapperException,
    Unauthorized,
    URITooLong,
)

logger = logging.getLogger(__name__)

Row = dict[str, str | None]

TIMEOUT_MARKERS = ("timeout", "time limit", "timed out", "estimated execution time")
BACKOFF_SECONDS = (1, 4)
EXCERPT = 200


class SparqlError(Exception):
    """A query that could not be answered; the message is meant for the log and the report."""


class QueryTimeout(SparqlError):
    """The endpoint did not answer in time; the caller escalates or falls back."""


class RetriesExhausted(QueryTimeout):
    """A transient error that persisted through every retry."""


class TransientError(SparqlError):
    """A failure worth retrying (overload, dropped connection)."""


class PermanentError(SparqlError):
    """The endpoint rejected the query; retrying cannot help."""


class EndpointUnreachable(SparqlError):
    """The endpoint cannot be used at all (no connection, authentication required)."""


class SparqlPort(Protocol):
    def select(self, query: str) -> list[Row]: ...

    def ask(self, query: str) -> bool: ...


def query_name(query: str) -> str:
    """Every query template starts with a `# <name>` comment line."""
    first = query.lstrip().splitlines()[0] if query.strip() else ""
    return first.removeprefix("#").strip() if first.startswith("#") else first[:60]


def _excerpt(body: Any) -> str:
    text = body.decode("utf-8", "replace") if isinstance(body, bytes) else str(body)
    return " ".join(text.split())[:EXCERPT]


def classify(error: BaseException) -> SparqlError:
    """Map a client exception to the failure classes of P-5."""
    if isinstance(error, SparqlError):
        return error
    if isinstance(error, (socket.timeout, TimeoutError)):
        return QueryTimeout(f"timed out: {error}")
    if isinstance(error, Unauthorized):
        return EndpointUnreachable("401 authentication required")
    if isinstance(error, EndPointInternalError):
        message = _excerpt(error)
        if any(marker in message.lower() for marker in TIMEOUT_MARKERS):
            return QueryTimeout(f"500 {message}")
        return PermanentError(f"500 {message}")
    if isinstance(error, SPARQLWrapperException):
        status = {QueryBadFormed: 400, EndPointNotFound: 404, URITooLong: 414}.get(type(error), "")
        return PermanentError(f"{status} {_excerpt(error)}".strip())
    if isinstance(error, urllib.error.HTTPError):
        body = _excerpt(error.read() if error.fp else b"")
        message = f"{error.code} {body}".strip()
        if error.code == 504:
            return QueryTimeout(message)
        if error.code in (429, 502, 503):
            return TransientError(message)
        if error.code in (401, 403, 407):
            return EndpointUnreachable(message)
        return PermanentError(message)
    if isinstance(error, urllib.error.URLError):
        if isinstance(error.reason, (socket.timeout, TimeoutError)):
            return QueryTimeout(f"timed out: {error.reason}")
        return TransientError(str(error.reason))
    if isinstance(error, (ConnectionError, http.client.HTTPException, OSError)):
        return TransientError(f"{type(error).__name__}: {error}")
    return PermanentError(f"unreadable response: {error}")


def rows_from_json(result: dict[str, Any]) -> list[Row]:
    """SELECT results as plain rows; blank nodes as `_:id`, unbound variables as None."""
    variables = result["head"]["vars"]
    rows = []
    for binding in result["results"]["bindings"]:
        row: Row = {}
        for var in variables:
            term = binding.get(var)
            row[var] = None if term is None else ("_:" + term["value"] if term["type"] == "bnode" else term["value"])
        rows.append(row)
    return rows


class SparqlWrapperClient:
    """JSON over HTTP POST; a new SPARQLWrapper per call, so one client is safe to share between threads."""

    def __init__(self, endpoint: str, timeout_seconds: int, sleep: Callable[[float], None] = time.sleep):
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds
        self._sleep = sleep

    def select(self, query: str) -> list[Row]:
        return rows_from_json(self._with_retries(query, ask=False))

    def ask(self, query: str) -> bool:
        return bool(self._with_retries(query, ask=True)["boolean"])

    def _with_retries(self, query: str, ask: bool) -> dict[str, Any]:
        for attempt in range(len(BACKOFF_SECONDS) + 1):
            try:
                return self._once(query, ask)
            except Exception as raw:  # classified below; nothing is swallowed
                error = classify(raw)
                if not isinstance(error, TransientError):
                    raise error from raw
                if attempt == len(BACKOFF_SECONDS):
                    raise RetriesExhausted(f"{error} (after {attempt} retries)") from raw
                logger.info("retrying %s (%d/%d): %s", query_name(query), attempt + 1, len(BACKOFF_SECONDS), error)
                self._sleep(BACKOFF_SECONDS[attempt])
        raise AssertionError("unreachable")

    def _once(self, query: str, ask: bool) -> dict[str, Any]:
        wrapper = SPARQLWrapper(self.endpoint)
        wrapper.setMethod(POST)
        wrapper.setReturnFormat(JSON)
        wrapper.setTimeout(self.timeout_seconds)
        wrapper.setQuery(query)
        response = wrapper.query().response
        try:
            return json.loads(response.read())
        except ValueError as error:
            raise PermanentError(f"unreadable response: {error}") from error
