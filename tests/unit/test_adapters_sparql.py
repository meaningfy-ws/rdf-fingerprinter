import io
import json
import urllib.error
import urllib.parse

import pytest
from rdflib import BNode, Literal, URIRef
from rdflib.query import ResultException

from fingerprint import __version__
from fingerprint.adapters import sparql
from fingerprint.adapters.sparql import (
    EndpointUnreachable,
    PermanentError,
    QueryTimeout,
    RetriesExhausted,
    SparqlHttpClient,
    TransientError,
    classify,
)


def http_error(code: int, body: bytes = b"") -> urllib.error.HTTPError:
    return urllib.error.HTTPError("http://x", code, "status", {}, io.BytesIO(body))  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "error, expected",
    [
        (TimeoutError("timed out"), QueryTimeout),
        (TimeoutError(), QueryTimeout),
        (urllib.error.URLError(TimeoutError("timed out")), QueryTimeout),
        (http_error(504), QueryTimeout),
        (http_error(500, b"Query exceeded the Time Limit"), QueryTimeout),
        (http_error(500, b"estimated execution time 900 s"), QueryTimeout),
        (http_error(500, b"syntax error"), PermanentError),
        (http_error(502), TransientError),
        (http_error(503), TransientError),
        (http_error(429), TransientError),
        (urllib.error.URLError(ConnectionRefusedError()), TransientError),
        (ConnectionResetError(), TransientError),
        (http_error(400, b"bad"), PermanentError),
        (http_error(413), PermanentError),
        (http_error(401), EndpointUnreachable),
        (http_error(403), EndpointUnreachable),
        (http_error(407), EndpointUnreachable),
        (ValueError("not json"), PermanentError),
        (ResultException("No boolean or results in json!"), PermanentError),
        (KeyError("head"), PermanentError),
    ],
)
def test_classify(error, expected):
    assert type(classify(error)) is expected


def test_a_500_message_keeps_the_status_and_an_excerpt(monkeypatch):
    monkeypatch.setenv("RDF_FINGERPRINTER_ERROR_EXCERPT_LENGTH", "12")
    assert str(classify(http_error(500, b"syntax   error near SELECT"))) == "500 syntax error"


XSD_INTEGER = "http://www.w3.org/2001/XMLSchema#integer"
SELECT_ANSWER = {
    "head": {"vars": ["s", "n"]},
    "results": {
        "bindings": [
            {"s": {"type": "uri", "value": "http://e/a"}, "n": {"type": "literal", "value": "5", "datatype": XSD_INTEGER}},
            {"s": {"type": "bnode", "value": "b0"}},
        ]
    },
}


class Flaky(SparqlHttpClient):
    def __init__(self, failures, answer=SELECT_ANSWER):
        super().__init__("http://x", timeout_seconds=1, sleep=self.record)
        self.failures, self.answer, self.calls, self.slept = list(failures), answer, 0, []

    def record(self, seconds):
        self.slept.append(seconds)

    def _once(self, query):
        self.calls += 1
        if self.failures:
            raise self.failures.pop(0)
        return self.answer if isinstance(self.answer, bytes) else json.dumps(self.answer).encode()


def test_rows_hold_typed_terms_blank_nodes_and_unbound_variables():
    rows = Flaky([]).select("# Q1 x\nSELECT")
    assert rows[0]["s"] == URIRef("http://e/a") and rows[0]["n"].toPython() == 5
    assert isinstance(rows[0]["n"], Literal)
    assert rows[1]["s"] == BNode("b0") and rows[1]["n"] is None


def test_ask_reads_the_boolean():
    assert Flaky([], answer={"head": {}, "boolean": True}).ask("# Q10 x\nASK") is True


def test_transient_error_is_retried_with_backoff():
    client = Flaky([http_error(503)])
    assert len(client.select("# Q1 x\nSELECT")) == 2
    assert client.calls == 2 and client.slept == [1]


def test_three_transient_failures_become_a_timeout():
    client = Flaky([http_error(503)] * 3)
    with pytest.raises(RetriesExhausted) as raised:
        client.select("# Q1 x\nSELECT")
    assert isinstance(raised.value, QueryTimeout)
    assert client.calls == 3 and client.slept == [1, 4]


def test_the_backoff_comes_from_the_configuration(monkeypatch):
    monkeypatch.setenv("RDF_FINGERPRINTER_RETRY_BACKOFF_SECONDS", "2")
    client = Flaky([http_error(503)] * 2)
    with pytest.raises(RetriesExhausted):
        client.select("# Q1 x\nSELECT")
    assert client.calls == 2 and client.slept == [2]


def test_permanent_error_is_not_retried():
    client = Flaky([http_error(400, b"bad")])
    with pytest.raises(PermanentError):
        client.select("# Q5 x\nSELECT")
    assert client.calls == 1


@pytest.mark.parametrize("answer", [b"not json", {"unexpected": True}, {"head": {}, "boolean": True}])
def test_an_unreadable_select_answer_is_a_permanent_error(answer):
    client = Flaky([], answer=answer)
    with pytest.raises(PermanentError):
        client.select("# Q1 x\nSELECT")
    assert client.calls == 1


@pytest.mark.parametrize("answer", [b"not json", {"unexpected": True}, SELECT_ANSWER])
def test_an_unreadable_ask_answer_is_a_permanent_error(answer):
    with pytest.raises(PermanentError):
        Flaky([], answer=answer).ask("# Q10 x\nASK")


class Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_the_query_is_a_sparql_protocol_form_post_with_the_timeout(monkeypatch):
    sent = []

    def urlopen(request, timeout):
        sent.append((request, timeout))
        return Response(json.dumps(SELECT_ANSWER).encode())

    monkeypatch.setattr(sparql.urllib.request, "urlopen", urlopen)
    SparqlHttpClient("http://e/sparql", timeout_seconds=7).select("# Q1 x\nSELECT * {}")
    request, timeout = sent[0]
    assert timeout == 7 and request.get_method() == "POST" and request.full_url == "http://e/sparql"
    assert urllib.parse.parse_qs(request.data.decode()) == {"query": ["# Q1 x\nSELECT * {}"]}
    assert request.get_header("Content-type") == "application/x-www-form-urlencoded"
    assert request.get_header("Accept") == "application/sparql-results+json"
    assert request.get_header("User-agent") == f"rdf-fingerprinter/{__version__}"
