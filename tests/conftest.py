"""Tests never reach prefix.cc: the lookup is off unless a test switches it on (readable-representations, design Risks)."""

import socket
from pathlib import Path

import pytest
from hypothesis import settings

from fingerprint.adapters.profile_file import load_profile
from fingerprint.domain.analytics import analyse
from fingerprint.service_layer.generators import GENERATORS
from tests.refresh_golden import render
from tests.sample_data import SAMPLE_PROFILE

E2E = Path(__file__).parent / "e2e"

settings.register_profile("ci", derandomize=True, deadline=None)
settings.register_profile("dev", deadline=None)
settings.load_profile("dev")


@pytest.fixture(autouse=True)
def _no_prefix_lookup(monkeypatch):
    monkeypatch.setenv("RDF_FINGERPRINTER_PREFIX_LOOKUP", "false")


@pytest.fixture(autouse=True)
def _no_network(request, monkeypatch):
    """Only tests/e2e/ may reach a network (lean-test-suite P-4); FakeSparql uses an in-memory store."""
    if E2E in request.path.parents:
        return

    def refuse(*args, **kwargs):
        raise RuntimeError("network access is not allowed outside tests/e2e/")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "getaddrinfo", refuse)  # a name lookup is network access too


@pytest.fixture(scope="session")
def sample_run():
    """The stored sample profile (a read-only model object; derive variants with `model_copy`)."""
    return load_profile(SAMPLE_PROFILE)


@pytest.fixture(scope="session")
def sample_analytics(sample_run):
    return analyse(sample_run)


@pytest.fixture(scope="session")
def sample_outputs(sample_run):
    """Every generator's files for the sample profile: generator name → {file name → text}."""
    return {name: render(sample_run, name) for name in sorted(GENERATORS)}


def pytest_collection_modifyitems(items):
    """Scenarios tagged @manual are checked by hand in a browser, not by pytest."""
    skip = pytest.mark.skip(reason="checked by hand (design Verification map)")
    for item in items:
        if item.get_closest_marker("manual"):
            item.add_marker(skip)
