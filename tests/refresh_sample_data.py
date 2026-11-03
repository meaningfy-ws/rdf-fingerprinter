"""Regenerates the stored sample profile from the loaded test store: `make refresh-sample-profile` (P-5).

Run `make oxigraph-load-test-data` first. An unchanged collection leaves the file alone; a changed one is
written with the stored timestamps and tool version, so the diff shows only data.
"""

from rdflib import URIRef

from fingerprint.adapters.profile_file import load_profile
from fingerprint.adapters.reification_catalogue import packaged_templates
from fingerprint.adapters.sparql import SparqlHttpClient
from fingerprint.domain.profile import ProfileRun, Settings
from fingerprint.service_layer.collection import collect
from tests import LOCAL_ENDPOINT
from tests.fakes import FakeSparql
from tests.sample_data import (
    REIFIED_GRAPH,
    REIFIED_PROFILE,
    REIFIED_SOURCE,
    SAMPLE_PROFILE,
    VARYING,
    differences,
    same_profile,
)


def refreshed(stored: ProfileRun, fresh: ProfileRun) -> ProfileRun | None:
    """The run to write, or None when `fresh` equals `stored` apart from what varies between runs."""
    if same_profile(stored, fresh):
        return None
    return fresh.model_copy(update={name: getattr(stored, name) for name in VARYING})


def collect_reified(settings: Settings) -> ProfileRun:
    """The reification sample, collected in memory: no store holds it (P-15)."""
    fake = FakeSparql()
    fake.dataset.graph(URIRef(REIFIED_GRAPH)).parse(REIFIED_SOURCE)
    return collect("http://fake/sparql", settings, fake, templates=packaged_templates())


def refresh(path, collect_fresh, first_settings: Settings | None = None) -> None:
    """Write `path` when the fresh collection differs from the stored profile (a new file when none is stored)."""
    stored = load_profile(path) if path.exists() else None
    fresh = collect_fresh(stored.settings if stored else first_settings)
    new = refreshed(stored, fresh) if stored else fresh
    if new is None:
        print(f"{path.name} is up to date")
        return
    path.write_text(new.model_dump_json(indent=2, exclude_none=True) + "\n", encoding="utf-8")
    print(f"{path.name} rewritten" + ("; differences from the stored profile:" if stored else " (new)"))
    if stored:
        print("\n".join(f"  {line}" for line in differences(stored, fresh)))


def main() -> None:
    refresh(
        SAMPLE_PROFILE,
        lambda settings: collect(
            LOCAL_ENDPOINT,
            settings,
            SparqlHttpClient(LOCAL_ENDPOINT, settings.timeout_seconds),
            templates=packaged_templates() if settings.reifications else (),
        ),
    )
    refresh(REIFIED_PROFILE, collect_reified, Settings(selected_graphs=[REIFIED_GRAPH]))


if __name__ == "__main__":
    main()
