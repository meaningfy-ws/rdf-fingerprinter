"""Tests never reach prefix.cc: the lookup is off unless a test switches it on (readable-representations, design Risks)."""

import pytest


@pytest.fixture(autouse=True)
def _no_prefix_lookup(monkeypatch):
    monkeypatch.setenv("RDF_FINGERPRINTER_PREFIX_LOOKUP", "false")


def pytest_collection_modifyitems(items):
    """Scenarios tagged @manual are checked by hand in a browser, not by pytest."""
    skip = pytest.mark.skip(reason="checked by hand (design Verification map)")
    for item in items:
        if item.get_closest_marker("manual"):
            item.add_marker(skip)
