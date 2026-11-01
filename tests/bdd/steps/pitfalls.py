"""Steps for the pitfall scan (pitfall_scans.feature, and the pitfall scenarios of the report, prefix and collection
features): the fingerprint command over FakeSparql with a data graph and a schema graph."""

import logging

from click.testing import CliRunner
from pytest_bdd import given, parsers, then, when

from fingerprint.adapters.exceptions import QueryTimeout
from fingerprint.adapters.pitfall_catalogue import packaged_checks
from fingerprint.adapters.sparql import SparqlHttpClient
from fingerprint.adapters.template_renderer import JinjaTemplateRenderer
from fingerprint.domain.analytics import analyse
from fingerprint.domain.profile import GraphProfile, PitfallExample, PitfallResult, PitfallTerm, ProfileRun
from fingerprint.entrypoints.cli import generate
from fingerprint.entrypoints.cli import main as cli
from fingerprint.service_layer import handlers
from fingerprint.service_layer.generators import GENERATORS
from tests.fakes import EX, FakeSparql

OWL = "http://www.w3.org/2002/07/owl#"
RDFS = "http://www.w3.org/2000/01/rdf-schema#"
GRAPHS = {"data": EX + "graph/data", "schema": EX + "graph/schema"}
HEADER = "# id: {id}\n# title: T\n# importance: minor\n# scope: data\n# source: me\n"
SELECT = "SELECT ?entity ?property ?value WHERE { ?entity ?property ?value }\n"
BAD = {
    "has no id": "# title: T\n# importance: minor\n# scope: data\n# source: me\n" + SELECT,
    "has importance severe": HEADER.replace("minor", "severe").format(id="a") + SELECT,
    "holds an INSERT DATA update": HEADER.format(id="a") + "INSERT DATA { <urn:a> <urn:b> <urn:c> }\n",
    "holds a DELETE WHERE update": HEADER.format(id="a") + "DELETE WHERE { ?s ?p ?o }\n",
    "selects ?s ?p ?o": HEADER.format(id="a") + "SELECT ?s ?p ?o WHERE { ?s ?p ?o }\n",
    "does not parse": HEADER.format(id="a") + "SELECT ?entity ?property ?value WHERE {\n",
    "has the unknown header key severity": HEADER.format(id="a") + "# severity: high\n" + SELECT,
    "has a FROM clause": HEADER.format(id="a")
    + "SELECT ?entity ?property ?value FROM <urn:g> WHERE { ?entity ?property ?value }\n",
}


@given('a store whose graph "data" uses an undeclared relation and whose graph "schema" holds the ontology')
def pitfall_store(ctx, monkeypatch):
    """`ex:undeclared` is used in data and declared nowhere; `ex:knows` is declared, with two domains (a P19 finding)."""
    fake = FakeSparql()
    data, schema = GRAPHS["data"], GRAPHS["schema"]
    fake.add("ex:a", "a", "ex:Person", graph=data)
    fake.add("ex:a", "ex:undeclared", "ex:b", graph=data)
    fake.add("ex:a", "ex:knows", "ex:b", graph=data)
    fake.add("ex:Person", "a", OWL + "Class", graph=schema)
    fake.add("ex:knows", "a", OWL + "ObjectProperty", graph=schema)
    fake.add("ex:knows", RDFS + "domain", "ex:Person", graph=schema)
    fake.add("ex:knows", RDFS + "domain", "ex:Agent", graph=schema)
    monkeypatch.setattr(handlers, "SparqlHttpClient", lambda endpoint, timeout: fake)
    ctx["fake"] = fake


def options(text: str) -> list[str]:
    """The CLI options a step phrase names: `--pitfalls`, the valued flags, `on graph "x"`, `schema graph "y"`."""
    args = ["--pitfalls"] if "with --pitfalls" in text else []
    for flag in ("--pitfall-examples", "--fail-on", "--format", "--skip-pitfall"):
        if flag in text:
            args += [flag, text.split(flag, 1)[1].split()[0].strip('"')]
    if 'on graph "' in text:
        args += ["--graph", GRAPHS[text.split('on graph "', 1)[1].split('"')[0]]]
    if 'schema graph "' in text:
        args += ["--schema-graph", GRAPHS[text.split('schema graph "', 1)[1].split('"')[0]]]
    return args


def profile(ctx) -> ProfileRun:
    return ProfileRun.model_validate_json((ctx["output"] / "profile.json").read_text())


def graph_results(ctx, name: str) -> dict[str, PitfallResult]:  # dict-ok: lookup index check id → result
    graph = next(g for g in profile(ctx).graphs if g.graph == GRAPHS[name])
    return {r.check_id: r for r in graph.pitfalls or []}


def scope_of(check_id: str) -> str:
    return next(c.scope for c in packaged_checks() if c.check_id == check_id)


@when(parsers.re(r"the fingerprint command runs (?P<text>with --pitfalls.*|without --pitfalls.*)$"))
def runs_with_scan_options(ctx, text, caplog):
    caplog.set_level(logging.INFO)
    args = ["-e", "http://fake/sparql", "-o", str(ctx["output"]), "--depth", "classes", *options(text)]
    if "that check folder" in text:
        args += ["--pitfall-checks", str(ctx["tmp"] / "checks")]
    ctx["result"] = CliRunner().invoke(cli.fingerprint_endpoint, args)
    ctx["log"] = caplog.text


@when("the packaged catalogue is loaded")
def catalogue(ctx):
    ctx["checks"] = packaged_checks()


@then(parsers.parse('check "{check_id}" has importance "{importance}", scope "{scope}" and source "{source}"'))
def check_metadata(ctx, check_id, importance, scope, source):
    check = next(c for c in ctx["checks"] if c.check_id == check_id)
    assert (check.importance, check.scope, check.source) == (importance, scope, source)


@then("it holds 29 checks with unique ids, each OOPS!-derived one naming its pitfall code")
def catalogue_size(ctx):
    ids = [c.check_id for c in ctx["checks"]]
    assert len(ids) == 29 == len(set(ids))
    assert all(c.source.startswith("OOPS! P") for c in ctx["checks"] if not c.check_id.startswith("x_"))


@given(parsers.parse("a user check file that {problem}"))
def bad_check(ctx, problem):
    folder = ctx["tmp"] / "checks"
    folder.mkdir(exist_ok=True)
    (folder / "bad.rq").write_text(BAD[problem])


@given(parsers.parse('a valid user check with the id "{check_id}"'))
def user_check(ctx, check_id):
    folder = ctx["tmp"] / "checks"
    folder.mkdir(exist_ok=True)
    (folder / "mine.rq").write_text(HEADER.replace("scope: data", "scope: schema").format(id=check_id) + SELECT)


@given(parsers.parse('the count query of "{check_id}" times out'))
def count_times_out(ctx, check_id):
    ctx["fake"].on("PITFALL", QueryTimeout("timed out"), when=lambda q: q.startswith(f"# PITFALL {check_id} count"))


@then(parsers.parse("it exits with {code:d} naming the file"))
def exits_naming_file(ctx, code):
    assert ctx["result"].exit_code == code and "bad.rq" in ctx["result"].output, ctx["result"].output


@then(parsers.parse('it exits with {code:d} naming "{option}"'))
def exits_naming_option(ctx, code, option):
    assert ctx["result"].exit_code == code and option in ctx["result"].output, ctx["result"].output


@then("no query was sent")
def no_query(ctx):
    assert ctx["fake"].queries == []


@then(parsers.parse('it logs the findings at or above "{level}"'))
def logs_findings(ctx, level):
    assert f"checks at or above {level}" in ctx["log"]


@then(parsers.parse('the profile of "{name}" has a "{check_id}" result whose example entity is "{entity}"'))
def result_with_example(ctx, name, check_id, entity):
    examples = graph_results(ctx, name)[check_id].examples
    assert EX + entity.removeprefix("ex:") in {e.entity.text for e in examples}


@then(parsers.parse('the profile of "{name}" has a "{check_id}" result'))
def has_result(ctx, name, check_id):
    assert check_id in graph_results(ctx, name)


@then(parsers.parse('the graph "{name}" is profiled too'))
def profiled_too(ctx, name):
    assert GRAPHS[name] in [g.graph for g in profile(ctx).graphs]


@then(parsers.parse('the profile of "{name}" has results only for {scope} checks'))
def scope_only(ctx, name, scope):
    found = graph_results(ctx, name)
    assert found and {scope_of(i) for i in found} == {scope}


@then("the default graph has no pitfall results and no check query was sent for it")
def default_not_scanned(ctx):
    default = next(g for g in profile(ctx).graphs if g.graph is None)
    counts = [q for q in ctx["fake"].sent("PITFALL") if " count\n" in q]
    assert default.pitfalls is None and counts and all("FROM" in q for q in counts)


@then(parsers.parse('the "{check_id}" result of "{name}" has count 0 and no examples, and no example query was sent for it'))
def found_nothing(ctx, check_id, name):
    result = graph_results(ctx, name)[check_id]
    assert result.count == 0 and not result.examples
    assert not [q for q in ctx["fake"].sent("PITFALL") if q.startswith(f"# PITFALL {check_id} examples")]


@then(parsers.parse("every result has at most {n:d} example"))
def bounded(ctx, n):
    assert all(len(r.examples or []) <= n for g in profile(ctx).graphs for r in g.pitfalls or [])


@then("no pitfall query was sent")
def no_pitfall_query(ctx):
    assert ctx["fake"].sent("PITFALL") == []


@then("no graph profile has pitfall results")
def no_results(ctx):
    assert all(g.pitfalls is None for g in profile(ctx).graphs)


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
    written = sorted(ctx["output"].glob("pitfalls-*.tsv"))
    assert written and all((again / p.name).read_text() == p.read_text() for p in written)


def one_result_profile(check_id: str, entity: str, prop: str | None, value: str, kind: str = "literal") -> ProfileRun:
    example = PitfallExample(
        entity=PitfallTerm(text=entity, kind="iri"),
        property=PitfallTerm(text=prop, kind="iri") if prop else None,
        value=PitfallTerm(text=value, kind=kind),
    )
    importance = next((c.importance for c in packaged_checks() if c.check_id == check_id), "minor")
    result = PitfallResult(
        check_id=check_id, title="T", importance=importance, scope="schema", source="s", count=1, examples=[example]
    )
    return ProfileRun(endpoint="http://e", settings={}, graphs=[GraphProfile(pitfalls=[result])])


@given(parsers.parse('a profile whose "{check_id}" result has the example "{entity}", "{prop}", "{value}"'))
def profile_with_example(ctx, check_id, entity, prop, value):
    ctx["run"] = one_result_profile(check_id, entity, prop, value)


@when("the pitfalls TSV is generated")
def tsv_generated(ctx):
    documents = GENERATORS["pitfalls"](analyse(ctx["run"]), JinjaTemplateRenderer()).serialize()
    ctx["texts"] = {d.file_name: d.text for d in documents}


@then(parsers.parse('the file holds the line "{line}"'))
def tsv_line(ctx, line):
    (text,) = ctx["texts"].values()
    assert line in text.splitlines()


@given(parsers.parse('a profile whose pitfall example entity is "{iri}"'))
def profile_with_pitfall_entity(ctx, iri):
    ctx["run"] = one_result_profile("x", iri, None, "http://not.an.iri.example/x")


@then(parsers.parse('the table holds a prefix for "{namespace}"'))
def table_holds(ctx, namespace):
    namespaces = {e.namespace for e in ctx["table"]}
    assert namespace in namespaces and "http://not.an.iri.example/" not in namespaces


@given(parsers.parse('its pitfall example entity is "{iri}"'))
def add_pitfall_entity(ctx, iri):
    (result,) = one_result_profile("x", iri, None, "v").graphs[0].pitfalls
    run = ctx["run"]
    ctx["run"] = run.model_copy(update={"graphs": [run.graphs[0].model_copy(update={"pitfalls": [result]})]})


@then(parsers.parse('the table has no entry for "{namespace}"'))
def table_lacks(ctx, namespace):
    assert namespace not in {e.namespace for e in ctx["table"]}
