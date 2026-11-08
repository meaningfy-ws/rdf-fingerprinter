"""The API reference names every format that writes files, with its files (consumer-api-gaps C-4)."""

from pathlib import Path

from fingerprint.service_layer.generators import DOC, GENERATORS

PAGE = Path(__file__).parents[2] / "docs" / "modules" / "ROOT" / "pages" / "api-reference.adoc"


def test_the_api_reference_has_a_row_for_every_format():
    text = PAGE.read_text()
    missing = [f.value for f in GENERATORS if f != DOC and f"| `{f.value}` |" not in text]
    assert not missing, missing
