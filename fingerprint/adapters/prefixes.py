"""Prefix sources: prefix files (the user's, the packaged one) and prefix.cc's prefix list (namespace-prefixes).

prefix.cc's certificate expired on 2025-12-31: the list is read over verified HTTPS first, and over plain HTTP only
when the certificate fails (developer, 2026-10-31). Its names are validated like a file's, so a tampered answer
can only change labels.
"""

import functools
import http.client
import json
import logging
import re
import ssl
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol

from fingerprint.adapters.exceptions import ConfigError
from fingerprint.domain.exceptions import IriRefError
from fingerprint.domain.iri import to_iriref
from fingerprint.domain.profile import NamespacePrefix, PrefixSource

logger = logging.getLogger(__name__)

_PREFIX_KEY = re.compile(r"[A-Za-z][A-Za-z0-9_.-]*:")
PREFIX_CC_LIST = "prefix.cc/popular/all.file.json"
_MAX_BYTES = 8 * 1024 * 1024  # the list is ~200 KB; a bigger answer is not the list


def _valid(prefix: str, namespace: Any) -> bool:
    if not (_PREFIX_KEY.fullmatch(prefix) and isinstance(namespace, str)):
        return False
    try:
        to_iriref(namespace)
    except IriRefError:
        return False
    return True


def load_prefixes(path: Path, source: PrefixSource, origin: str) -> list[NamespacePrefix]:
    """The `{"skos:": "http://…#"}` file at `path`, in file order; `origin` names who gave the path in errors."""
    try:
        table = json.loads(Path(path).read_text())
    except (OSError, ValueError) as error:
        raise ConfigError(f"{origin}: cannot read {path}: {error}") from error
    if not isinstance(table, dict):
        raise ConfigError(f"{origin}: {path} must hold a JSON object")
    for prefix, namespace in table.items():
        if not _valid(prefix, namespace):
            raise ConfigError(f"{origin}: {path}: {prefix!r} → {namespace!r} is not a prefix (`name:`) with a writable IRI")
    return [NamespacePrefix(prefix=p.rstrip(":"), namespace=ns, source=source) for p, ns in table.items()]


@functools.lru_cache(maxsize=4)
def _packaged(path: str) -> tuple[NamespacePrefix, ...]:
    return tuple(load_prefixes(Path(path), PrefixSource.packaged, "packaged prefixes"))


def load_packaged_prefixes(path: Path) -> list[NamespacePrefix]:
    """The packaged prefix file, read once per process."""
    return list(_packaged(str(path)))


class PrefixLookupError(Exception):
    """prefix.cc's list could not be fetched or read."""


class PrefixListSource(Protocol):
    """The port behind which prefix.cc sits; the unit tests use a fake."""

    def fetch(self) -> list[NamespacePrefix]: ...


def _certificate_failed(error: BaseException) -> bool:
    return isinstance(error, ssl.SSLCertVerificationError) or isinstance(
        getattr(error, "reason", None), ssl.SSLCertVerificationError
    )


class PrefixCcList:
    """prefix.cc's full prefix list, one download, reversed locally by the caller: no namespace is sent."""

    def __init__(self, timeout: float = 10, opener: Callable[..., Any] = urllib.request.urlopen):
        self.timeout = timeout
        self.opener = opener

    def fetch(self) -> list[NamespacePrefix]:
        try:
            try:
                body = self._get(f"https://{PREFIX_CC_LIST}")
            except (urllib.error.URLError, ssl.SSLError) as error:
                if not _certificate_failed(error):
                    raise
                logger.info("prefix.cc certificate not valid; fetched the prefix list over HTTP")
                body = self._get(f"http://{PREFIX_CC_LIST}")
            listing = json.loads(body)
        except (OSError, ValueError, http.client.HTTPException) as error:  # network, broken answers, bad JSON
            raise PrefixLookupError(str(error)) from error
        if not isinstance(listing, dict):
            raise PrefixLookupError("the prefix list is not a JSON object")
        entries = []
        for prefix, namespace in listing.items():
            name = prefix if prefix.endswith(":") else prefix + ":"
            if _valid(name, namespace):
                entries.append(NamespacePrefix(prefix=name[:-1], namespace=namespace, source=PrefixSource.prefix_cc))
            else:
                logger.debug("prefix.cc entry %r → %r skipped: not a prefix with a writable IRI", prefix, namespace)
        return entries

    def _get(self, url: str) -> bytes:
        with self.opener(url, timeout=self.timeout) as response:  # the timeout applies to each socket operation
            body = response.read(_MAX_BYTES + 1)
        if len(body) > _MAX_BYTES:
            raise PrefixLookupError(f"{url} answered more than {_MAX_BYTES} bytes")
        return body
