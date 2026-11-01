"""The shared step library of the Gherkin tier (lean-test-suite P-1).

The step definitions live in `tests/bdd/steps/<area>.py` and are imported here, so every scenario
sees one definition per step wording. The fixtures all areas share are defined below.
"""

import pytest
from rdflib import Literal

from fingerprint.domain.profile import Settings
from fingerprint.entrypoints.cli import main as cli
from fingerprint.service_layer import handlers
from tests.bdd.steps.analytics import *  # noqa: F403
from tests.bdd.steps.filters import *  # noqa: F403
from tests.bdd.steps.pattern import *  # noqa: F403
from tests.bdd.steps.pitfalls import *  # noqa: F403
from tests.bdd.steps.prefixes import *  # noqa: F403
from tests.bdd.steps.report import *  # noqa: F403
from tests.bdd.steps.representations import *  # noqa: F403
from tests.bdd.steps.shex import *  # noqa: F403
from tests.bdd.steps.statistics import *  # noqa: F403
from tests.fakes import FakeSparql


@pytest.fixture
def ctx(tmp_path):
    """The scenario's state: its folders, plus the defaults every area reads."""
    output = tmp_path / "output"
    output.mkdir()
    return {
        "tmp": tmp_path,
        "output": output,
        # prefix sources (namespace_prefixes)
        "user": [],
        "packaged": [],
        "lookup": None,
        # a hand-built profile (profile_analytics)
        "classes": {},
        "edges": [],
        "settings": Settings(),
        # collection settings (statistics_collection)
        "cli": {},
        "env": {},
        "selected": None,
        "config": None,
    }


@pytest.fixture
def store(monkeypatch):
    """Two people and two cities behind the fingerprint command and the library call."""
    fake = FakeSparql()
    for i in range(2):
        fake.add(f"ex:p{i}", "a", "ex:Person")
        fake.add(f"ex:p{i}", "ex:name", Literal(f"n{i}"))
        fake.add(f"ex:c{i}", "a", "ex:City")
    monkeypatch.setattr(handlers, "SparqlHttpClient", lambda endpoint, timeout: fake)
    return fake


@pytest.fixture
def lookups(monkeypatch):
    """The prefix.cc lookups the fingerprint command builds (none is fetched from the network)."""
    built = []

    class Recording:
        def __init__(self):
            built.append(self)

        def fetch(self):
            return []

    monkeypatch.setattr(cli, "PrefixCcList", Recording)
    return built
