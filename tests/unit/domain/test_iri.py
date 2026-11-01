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


# --- Turtle and display terms (profile-representations P-7) ---

from fingerprint.domain.exceptions import IriRefError  # noqa: E402
from fingerprint.domain.iri import curie, turtle_number, turtle_string, turtle_term  # noqa: E402
from fingerprint.domain.prefixes import PrefixTable  # noqa: E402
from fingerprint.domain.profile import NamespacePrefix  # noqa: E402

PREFIXES = PrefixTable(
    NamespacePrefix(prefix=p, namespace=ns, source="packaged")
    for p, ns in {"skos": "http://www.w3.org/2004/02/skos/core#", "ex": "http://ex.org/"}.items()
)


@pytest.mark.parametrize(
    "iri, term, prefix",
    [
        ("http://www.w3.org/2004/02/skos/core#Concept", "skos:Concept", "skos"),
        ("http://ex.org/a-b_c.d", "ex:a-b_c.d", "ex"),
        ("http://ex.org/q?a=1&b='x'", "<http://ex.org/q?a=1&b='x'>", None),
        ("http://ex.org/ș/ü", "<http://ex.org/ș/ü>", None),
        ("http://ex.org/ends.", "<http://ex.org/ends.>", None),
        ("http://other.org/x", "<http://other.org/x>", None),
    ],
)
def test_turtle_term_shortens_only_safe_local_names(iri, term, prefix):
    assert turtle_term(iri, PREFIXES) == (term, prefix)


def test_turtle_term_refuses_an_unwritable_iri():
    with pytest.raises(IriRefError):
        turtle_term("http://ex.org/a b", PREFIXES)


@pytest.mark.parametrize(
    "text, literal",
    [("plain", '"plain"'), ('say "hi"', '"say \\"hi\\""'), ("a\nb\\c", '"a\\nb\\\\c"'), ("ș", '"ș"')],
)
def test_turtle_string_escapes(text, literal):
    assert turtle_string(text) == literal


@pytest.mark.parametrize("value, literal", [(3, "3"), (0.5, "0.5"), (1.0, "1.0"), (0.123456, "0.1235"), (True, "true")])
def test_turtle_number(value, literal):
    assert turtle_number(value) == literal


def test_curie_shortens_any_matching_namespace_for_display():
    assert curie("http://ex.org/q?a=1", PREFIXES) == "ex:q?a=1"
    assert curie("http://other.org/x", PREFIXES) == "http://other.org/x"
