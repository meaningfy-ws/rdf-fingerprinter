"""Every packaged pitfall check is listed in the docs catalogue (pitfall-scans design D-11)."""

from pathlib import Path

from fingerprint.adapters.pitfall_catalogue import packaged_checks

PAGE = Path(__file__).parents[2] / "docs" / "modules" / "ROOT" / "pages" / "pitfalls.adoc"


def test_the_docs_catalogue_lists_every_check():
    text = PAGE.read_text()
    missing = [c.check_id for c in packaged_checks() if f"| `{c.check_id}` | {c.importance} | {c.scope} |" not in text]
    assert not missing, missing
