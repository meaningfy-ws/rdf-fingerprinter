"""Steps of the ShExC scenarios of profile_representations.feature (UC-B2.1); PyShExC parses, in tests only (DEC-27)."""

from pyshexc.parser_impl.generate_shexj import parse
from pytest_bdd import parsers, then, when

from tests.bdd.steps.representations import generated, only


@when("the pattern schema and the ShExC are generated from it")
def pattern_and_shex_generated(ctx):
    ctx["pattern"] = only(generated(ctx, "pattern"))
    ctx["shex"] = only(generated(ctx, "shex"))


@then(parsers.parse('the pattern schema writes the class as "{written}"'))
def pattern_writes_class(ctx, written):
    assert any(line.startswith(f"(:{written}) ") for line in ctx["pattern"].splitlines())


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
