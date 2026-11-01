"""Regenerates the stored sample profile from the loaded test store: `make refresh-sample-profile` (P-5).

Run `make oxigraph-load-test-data` first. An unchanged collection leaves the file alone; a changed one is
written with the stored timestamps and tool version, so the diff shows only data.
"""

from fingerprint.adapters.profile_file import load_profile
from fingerprint.adapters.sparql import SparqlHttpClient
from fingerprint.domain.profile import ProfileRun
from fingerprint.service_layer.collection import collect
from tests import LOCAL_ENDPOINT
from tests.sample_data import SAMPLE_PROFILE, VARYING, differences, same_profile


def refreshed(stored: ProfileRun, fresh: ProfileRun) -> ProfileRun | None:
    """The run to write, or None when `fresh` equals `stored` apart from what varies between runs."""
    if same_profile(stored, fresh):
        return None
    return fresh.model_copy(update={name: getattr(stored, name) for name in VARYING})


def main() -> None:
    stored = load_profile(SAMPLE_PROFILE)
    timeout = stored.settings.timeout_seconds
    fresh = collect(LOCAL_ENDPOINT, stored.settings, SparqlHttpClient(LOCAL_ENDPOINT, timeout))
    new = refreshed(stored, fresh)
    if new is None:
        print(f"{SAMPLE_PROFILE.name} is up to date with {LOCAL_ENDPOINT}")
        return
    SAMPLE_PROFILE.write_text(new.model_dump_json(indent=2, exclude_none=True) + "\n", encoding="utf-8")
    print(f"{SAMPLE_PROFILE.name} rewritten; differences from the stored profile:")
    print("\n".join(f"  {line}" for line in differences(stored, fresh)))


if __name__ == "__main__":
    main()
