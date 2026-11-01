"""Step definitions for pitfall_scans.feature: the scan through the CLI over FakeSparql."""

import pytest
from click.testing import CliRunner
from pytest_bdd import given, parsers, scenarios, then, when

from fingerprint.adapters.exceptions import QueryTimeout
from fingerprint.adapters.pitfall_catalogue import packaged_checks
from fingerprint.adapters.sparql import SparqlHttpClient
from fingerprint.domain.profile import ProfileRun
from fingerprint.entrypoints.cli import generate
from fingerprint.entrypoints.cli import main as cli
from fingerprint.service_layer import handlers
from tests.unit.fakes import EX, FakeSparql

scenarios("pitfall_scans.feature")

OWL = "http://www.w3.org/2002/07/owl#"
GRAPHS = {"data": EX + "graph/data", "schema": EX + "graph/schema"}
HEADER = "# id: {id}\n# title: T\n# importance: minor\n# scope: data\n# source: me\n"
SELECT = "SELECT ?entity ?property ?value WHERE { ?entity ?property ?value }\n"
BAD = {
    "has no id": "# title: T\n# importance: minor\n# scope: data\n# source: me\n" + SELECT,
    "has importance severe": HEADER.replace("minor", "severe").format(id="a") + SELECT,
    "holds an INSERT DATA update": HEADER.format(id="a") + "INSERT DATA { <urn:a> <urn:b> <urn:c> }\n",
    "selects ?s ?p ?o": HEADER.format(id="a") + "SELECT ?s ?p ?o WHERE { ?s ?p ?o }\n",
    "does not parse": HEADER.format(id="a") + "SELECT ?entity ?property ?value WHERE {\n",
    "has the unknown header key severity": HEADER.format(id="a") + "# severity: high\n" + SELECT,
    "has a FROM clause": HEADER.format(id="a")
    + "SELECT ?entity ?property ?value FROM <urn:g> WHERE { ?entity ?property ?value }\n",
}


@pytest.fixture
def ctx(tmp_path):
    output = tmp_path / "output"
    output.mkdir()
    return {"tmp": tmp_path, "output": output, "args": []}


@given('a store whose graph "data" uses an undeclared relation and whose graph "schema" holds the ontology')
def store(ctx, monkeypatch):
    fake = FakeSparql()
    data, schema = GRAPHS["data"], GRAPHS["schema"]
    fake.add("ex:a", "a", "ex:Person", graph=data)
    fake.add("ex:a", "ex:undeclared", "ex:b", graph=data)
    fake.add("ex:a", "ex:knows", "ex:b", graph=data)
    fake.add("ex:Person", "a", OWL + "Class", graph=schema)
    fake.add("ex:knows", "a", OWL + "ObjectProperty", graph=schema)
    fake.add("ex:knows", "http://www.w3.org/2000/01/rdf-schema#domain", "ex:Person", graph=schema)
    fake.add("ex:knows", "http://www.w3.org/2000/01/rdf-schema#domain", "ex:Agent", graph=schema)
    monkeypatch.setattr(handlers, "SparqlHttpClient", lambda endpoint, timeout: fake)
    ctx["fake"] = fake


def invoke(ctx, *args):
    base = ["-e", "http://fake/sparql", "-o", str(ctx["output"]), "--depth", "classes", *ctx["args"], *args]
    ctx["result"] = CliRunner().invoke(cli.fingerprint_endpoint, base)


def profile(ctx) -> ProfileRun:
    return ProfileRun.model_validate_json((ctx["output"] / "profile.json").read_text())


def graph_results(ctx, name):
    graph = next(g for g in profile(ctx).graphs if g.graph == GRAPHS[name])
    return {r.check_id: r for r in graph.pitfalls or []}


def options(text):
    """`--pitfalls`, `--pitfall-examples 1`, `--skip-pitfall "x"`, `--fail-on x`, `--format pitfalls`, graphs."""
    args = []
    if "with --pitfalls" in text:
        args.append("--pitfalls")
    for flag in ("--pitfall-examples", "--fail-on", "--format", "--skip-pitfall"):
        if flag in text:
            args += [flag, text.split(flag, 1)[1].split()[0].strip('"')]
    if 'on graph "' in text:
        args += ["--graph", GRAPHS[text.split('on graph "', 1)[1].split('"')[0]]]
    if 'schema graph "' in text:
        args += ["--schema-graph", GRAPHS[text.split('schema graph "', 1)[1].split('"')[0]]]
    return args


@when(parsers.re(r"the fingerprint command runs (?P<text>with --pitfalls.*|without --pitfalls.*)$"))
def runs(ctx, text):
    if "that check folder" in text:
        ctx["args"] += ["--pitfall-checks", str(ctx["tmp"] / "checks")]
    invoke(ctx, *options(text))


@when("the packaged catalogue is loaded")
def catalogue(ctx):
    ctx["checks"] = packaged_checks()


@then("it holds 29 checks with unique ids, each OOPS!-derived one naming its pitfall code")
def catalogue_size(ctx):
    ids = [c.check_id for c in ctx["checks"]]
    assert len(ids) == 29 == len(set(ids))
    assert all(c.source.startswith("OOPS! P") for c in ctx["checks"] if not c.check_id.startswith("x_"))


@given(parsers.parse("a user check file that {problem}"))
def bad_check(ctx, problem):
    folder = ctx["tmp"] / "checks"
    folder.mkdir()
    (folder / "bad.rq").write_text(BAD[problem])


@given(parsers.parse('a valid user check with the id "{check_id}"'))
def user_check(ctx, check_id):
    folder = ctx["tmp"] / "checks"
    folder.mkdir()
    (folder / "mine.rq").write_text(HEADER.replace("scope: data", "scope: schema").format(id=check_id) + SELECT)


@given(parsers.parse('the count query of "{check_id}" times out'))
def count_times_out(ctx, check_id):
    ctx["fake"].on("PITFALL", QueryTimeout("timed out"), when=lambda q: q.startswith(f"# PITFALL {check_id} count"))


@then(parsers.parse("it exits with {code:d}"))
def exits(ctx, code):
    assert ctx["result"].exit_code == code, ctx["result"].output


@then(parsers.parse("it exits with {code:d} naming the file"))
def exits_naming_file(ctx, code):
    assert ctx["result"].exit_code == code and "bad.rq" in ctx["result"].output, ctx["result"].output


@then(parsers.parse('it exits with {code:d} naming "{option}"'))
def exits_naming_option(ctx, code, option):
    assert ctx["result"].exit_code == code and option in ctx["result"].output, ctx["result"].output


@then("no query was sent")
def no_query(ctx):
    assert ctx["fake"].queries == []


@then(parsers.parse('the profile of "{name}" has a "{check_id}" result whose example entity is "{entity}"'))
def result_with_example(ctx, name, check_id, entity):
    examples = graph_results(ctx, name)[check_id].examples
    assert EX + entity.removeprefix("ex:") in {e.entity.text for e in examples}


@then(parsers.parse('the profile of "{name}" has results only for schema checks'))
def schema_only(ctx, name):
    scopes = {c.check_id: c.scope for c in packaged_checks()}
    found = graph_results(ctx, name)
    assert found and {scopes[i] for i in found} == {"schema"}


@then("no pitfall query was sent")
def no_pitfall_query(ctx):
    assert ctx["fake"].sent("PITFALL") == []


@then("no graph profile has pitfall results")
def no_results(ctx):
    assert all(g.pitfalls is None for g in profile(ctx).graphs)


@then(parsers.parse("every result has at most {n:d} example"))
def bounded(ctx, n):
    assert all(len(r.examples or []) <= n for g in profile(ctx).graphs for r in g.pitfalls or [])


@then(parsers.parse('a failure of kind pitfall names "{check_id}"'))
def failure_named(ctx, check_id):
    assert [f.check_id for f in profile(ctx).failures if f.query_kind == "pitfall"] == [check_id]


@then(parsers.parse("the \"{check_id}\" result's source names the user's file"))
def user_source(ctx, check_id):
    assert "mine.rq" in graph_results(ctx, "schema")[check_id].source


@then(parsers.parse('no query of check "{check_id}" was sent'))
def not_sent(ctx, check_id):
    assert not [q for q in ctx["fake"].sent("PITFALL") if q.startswith(f"# PITFALL {check_id} ")]
    assert ctx["result"].exit_code == 0, ctx["result"].output


@then("the output folder holds one pitfalls TSV per scanned graph")
def tsv_files(ctx):
    names = sorted(p.name for p in ctx["output"].glob("pitfalls-*.tsv"))
    assert len(names) == 2 and all(n.startswith(("pitfalls-data-", "pitfalls-schema-")) for n in names)


@then("fingerprint-gen-pitfalls writes the same files from the saved profile without a query")
def offline(ctx, monkeypatch):
    def refuse(self, *args, **kwargs):
        raise AssertionError("a generator queried the endpoint")

    monkeypatch.setattr(SparqlHttpClient, "_once", refuse)
    again = ctx["tmp"] / "again"
    again.mkdir()
    result = CliRunner().invoke(generate.gen_pitfalls, [str(ctx["output"] / "profile.json"), "-o", str(again)])
    assert result.exit_code == 0, result.output
    for path in ctx["output"].glob("pitfalls-*.tsv"):
        assert (again / path.name).read_text() == path.read_text()
