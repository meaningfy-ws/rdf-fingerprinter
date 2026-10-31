import pytest

from fingerprint.domain.iri import to_iriref


def test_wraps_a_valid_iri():
    assert to_iriref("http://example.org/Person") == "<http://example.org/Person>"


@pytest.mark.parametrize(
    "iri",
    [
        "http://example.org/a b",
        "http://example.org/<x>",
        'http://example.org/"x"',
        "http://example.org/{x}",
        "http://example.org/a|b",
        "http://example.org/a^b",
        "http://example.org/a`b",
        "http://example.org/a\\b",
        "http://example.org/a\nb",
        "http://example.org/a\x00b",
    ],
)
def test_rejects_characters_outside_iriref(iri):
    with pytest.raises(ValueError):
        to_iriref(iri)
