"""Steps of the ShExC scenarios of profile_representations.feature (UC-B2.1); PyShExC parses, in tests only (DEC-27)."""

from pyshexc.parser_impl.generate_shexj import parse
from pytest_bdd import parsers, then


@then(parsers.parse('the ShExC lists "{iri}" after "{marker}"'))
def shex_lists_after(ctx, iri, marker):
    (line,) = [ln for ln in ctx["shex"].splitlines() if ln.startswith(marker)]
    assert iri in line.removeprefix(marker).split()


@then("the ShExC parses")
def shex_parses(ctx):
    assert parse(ctx["shex"]) is not None


@then("each of the three files parses with PyShExC")
def files_parse(ctx):
    assert len(ctx["texts"]) == 3
    for name, text in ctx["texts"].items():
        assert parse(text) is not None, name
