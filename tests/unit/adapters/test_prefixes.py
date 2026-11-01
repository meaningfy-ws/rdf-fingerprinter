"""Prefix files and prefix.cc's list (namespace-prefixes: precedence inputs, best-effort lookup)."""

import io
import json
import logging
import ssl
import urllib.error

import pytest

from fingerprint.adapters.exceptions import ConfigError
from fingerprint.adapters.prefixes import PrefixCcList, PrefixLookupError, load_prefixes
from fingerprint.domain.profile import NamespacePrefix, PrefixSource


def test_a_prefix_file_keeps_its_order_and_names_its_source(tmp_path):
    path = tmp_path / "p.json"
    path.write_text('{"b:": "http://b.org/", "a:": "http://a.org/"}')
    assert load_prefixes(path, PrefixSource.user, "--prefixes") == [
        NamespacePrefix(prefix="b", namespace="http://b.org/", source=PrefixSource.user),
        NamespacePrefix(prefix="a", namespace="http://a.org/", source=PrefixSource.user),
    ]


@pytest.mark.parametrize("content", [None, "[]", "{bad", '{"x": "http://ex.org/"}', '{"ex:": "http://ex.org/a b"}'])
def test_a_bad_prefix_file_names_its_origin_and_path(tmp_path, content):
    path = tmp_path / "p.json"
    if content is not None:
        path.write_text(content)
    with pytest.raises(ConfigError, match="--prefixes") as raised:
        load_prefixes(path, PrefixSource.user, "--prefixes")
    assert str(path) in str(raised.value)


class Answer(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def opener(answers):
    """A urlopen stand-in: each URL maps to bytes or to an exception to raise."""
    calls = []

    def open_(url, timeout):
        calls.append((url, timeout))
        answer = answers[url.split("://")[0]]
        if isinstance(answer, BaseException):
            raise answer
        return Answer(answer)

    open_.calls = calls
    return open_


LISTING = json.dumps({"foaf": "http://xmlns.com/foaf/0.1/", "bad name": "http://x.org/", "dc": "not an iri <"}).encode()


def test_the_list_is_read_over_https_and_validated():
    fake = opener({"https": LISTING})
    entries = PrefixCcList(opener=fake).fetch()
    assert entries == [NamespacePrefix(prefix="foaf", namespace="http://xmlns.com/foaf/0.1/", source=PrefixSource.prefix_cc)]
    assert fake.calls == [("https://prefix.cc/popular/all.file.json", 10)]


@pytest.mark.parametrize(
    "answers",
    [
        {"https": urllib.error.URLError("unreachable")},
        {"https": TimeoutError("timed out")},
        {"https": b"<html>"},
        {"https": b"[1, 2]"},
        {"https": urllib.error.URLError(ssl.SSLCertVerificationError("expired")), "http": urllib.error.URLError("down")},
    ],
    ids=["unreachable", "timeout", "not-json", "not-an-object", "http-down-too"],
)
def test_failures_are_lookup_errors_without_retries(answers):
    fake = opener(answers)
    with pytest.raises(PrefixLookupError):
        PrefixCcList(opener=fake).fetch()
    assert len(fake.calls) <= 2


def test_the_http_line_is_logged_only_when_the_http_fetch_succeeds(caplog):
    expired = urllib.error.URLError(ssl.SSLCertVerificationError("expired"))
    fake = opener({"https": expired, "http": urllib.error.URLError("down")})
    with caplog.at_level(logging.INFO), pytest.raises(PrefixLookupError):
        PrefixCcList(opener=fake).fetch()
    assert "fetched the prefix list over HTTP" not in caplog.text
