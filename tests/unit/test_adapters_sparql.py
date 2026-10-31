import io
import urllib.error

import pytest
from SPARQLWrapper.SPARQLExceptions import EndPointInternalError, QueryBadFormed, Unauthorized

from fingerprint.adapters.sparql import (
    EndpointUnreachable,
    PermanentError,
    QueryTimeout,
    RetriesExhausted,
    SparqlWrapperClient,
    TransientError,
    classify,
    rows_from_json,
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
        (EndPointInternalError(b"Query exceeded the Time Limit"), QueryTimeout),
        (EndPointInternalError(b"estimated execution time 900 s"), QueryTimeout),
        (EndPointInternalError(b"syntax error"), PermanentError),
        (http_error(502), TransientError),
        (http_error(503), TransientError),
        (http_error(429), TransientError),
        (urllib.error.URLError(ConnectionRefusedError()), TransientError),
        (ConnectionResetError(), TransientError),
        (QueryBadFormed(b"bad"), PermanentError),
        (http_error(413), PermanentError),
        (Unauthorized(b""), EndpointUnreachable),
        (http_error(403), EndpointUnreachable),
        (http_error(407), EndpointUnreachable),
        (ValueError("not json"), PermanentError),
    ],
)
def test_classify(error, expected):
    assert type(classify(error)) is expected


def test_rows_from_json_marks_blank_nodes_and_unbound_variables():
    result = {
        "head": {"vars": ["s", "t"]},
        "results": {
            "bindings": [
                {"s": {"type": "uri", "value": "http://e/a"}, "t": {"type": "literal", "value": "1"}},
                {"s": {"type": "bnode", "value": "b0"}},
            ]
        },
    }
    assert rows_from_json(result) == [{"s": "http://e/a", "t": "1"}, {"s": "_:b0", "t": None}]


class Flaky(SparqlWrapperClient):
    def __init__(self, failures):
        super().__init__("http://x", timeout_seconds=1, sleep=self.record)
        self.failures, self.calls, self.slept = list(failures), 0, []

    def record(self, seconds):
        self.slept.append(seconds)

    def _once(self, query, ask):
        self.calls += 1
        if self.failures:
            raise self.failures.pop(0)
        return {"head": {"vars": ["x"]}, "results": {"bindings": [{"x": {"type": "literal", "value": "1"}}]}}


def test_transient_error_is_retried_with_backoff():
    client = Flaky([http_error(503)])
    assert client.select("# Q1 x\nSELECT") == [{"x": "1"}]
    assert client.calls == 2 and client.slept == [1]


def test_three_transient_failures_become_a_timeout():
    client = Flaky([http_error(503)] * 3)
    with pytest.raises(RetriesExhausted) as raised:
        client.select("# Q1 x\nSELECT")
    assert isinstance(raised.value, QueryTimeout)
    assert client.calls == 3 and client.slept == [1, 4]


def test_permanent_error_is_not_retried():
    client = Flaky([QueryBadFormed(b"bad")])
    with pytest.raises(PermanentError):
        client.select("# Q5 x\nSELECT")
    assert client.calls == 1


def test_malformed_json_is_a_permanent_error():
    class Broken(Flaky):
        def _once(self, query, ask):
            return {"unexpected": True}

    with pytest.raises(PermanentError):
        Broken([]).select("# Q1 x\nSELECT")
    with pytest.raises(PermanentError):
        Broken([]).ask("# Q10 x\nASK")
