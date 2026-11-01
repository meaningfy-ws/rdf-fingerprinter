"""Tests never reach prefix.cc: the lookup is off unless a test switches it on (readable-representations, design Risks)."""

import socket
from pathlib import Path

import pytest

E2E = Path(__file__).parent / "e2e"


@pytest.fixture(autouse=True)
def _no_prefix_lookup(monkeypatch):
    monkeypatch.setenv("RDF_FINGERPRINTER_PREFIX_LOOKUP", "false")


@pytest.fixture(autouse=True)
def _no_network(request, monkeypatch):
    """Only tests/e2e/ may reach a network (lean-test-suite P-4); FakeSparql uses an in-memory store."""
    if E2E in request.path.parents:
        return

    def refuse(self, *args, **kwargs):
        raise RuntimeError("network access is not allowed outside tests/e2e/")

    monkeypatch.setattr(socket.socket, "connect", refuse)


def pytest_collection_modifyitems(items):
    """Scenarios tagged @manual are checked by hand in a browser, not by pytest."""
    skip = pytest.mark.skip(reason="checked by hand (design Verification map)")
    for item in items:
        if item.get_closest_marker("manual"):
            item.add_marker(skip)
