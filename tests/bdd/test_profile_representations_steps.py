"""Step definitions for profile_representations.feature (UC-W2, UC-B2.1) over hand-built and sample profiles."""

import json
import logging
import re
import shutil
from pathlib import Path

import pytest
from bs4 import BeautifulSoup
from click.testing import CliRunner
from pytest_bdd import given, parsers, scenarios, then, when
from rdflib import RDF, Graph, Literal, Namespace, URIRef

from fingerprint.adapters.profile_file import load_profile, save_profile
from fingerprint.adapters.sparql import SparqlHttpClient
from fingerprint.adapters.template_renderer import JinjaTemplateRenderer
from fingerprint.domain.analytics import analyse
from fingerprint.domain.prefixes import namespace_of
from fingerprint.domain.views import GeneratorOptions
from fingerprint.entrypoints.cli import generate
from fingerprint.service_layer.generators import GENERATORS
from fingerprint.service_layer.generators.generator import META_NAMESPACES
from fingerprint.service_layer.representations import generate_from_profile_file, make_generator, with_threshold
from tests.builders import XSD, klass, literals, profile_run, prop, resources
from tests.fakes import EX, files

scenarios("profile_representations.feature")

DATA = Path(__file__).parents[1] / "test_data"
SAMPLE = DATA / "profiles" / "sample-profile.json"
SH = Namespace("http://www.w3.org/ns/shacl#")
FP = Namespace("https://data.meaningfy.ws/fingerprint/")
PREFIXES = {"ex": EX, "xsd": XSD}
FORMATS = {"shapes": "shacl", "diagram": "puml", "document": "doc"}


@pytest.fixture
def ctx(tmp_path):
    output = tmp_path / "output"
    output.mkdir()
    return {"tmp": tmp_path, "output": output}


def generated(ctx, name, run=None):
    """The texts of one format for the scenario's run (hand-built profiles use the ex: prefix)."""
    generator = make_generator(name, analyse(run or ctx["run"]), JinjaTemplateRenderer())
    texts = files(generator.serialize())
    ctx.setdefault("skipped", []).extend(generator.skipped)
    return texts


def only(texts):
    """The one file's text, or every module file of a diagram joined (the overview carries no class)."""
    if len(texts) == 1:
        (text,) = texts.values()
        return text
    return "\n".join(t for name, t in sorted(texts.items()) if "--" in name)


def property_shape(g, path):
    (shape,) = g.subjects(SH.path, URIRef(path))
    return shape


# --- the saved profile ---


@given("a saved profile of the test data")
def saved_sample(ctx):
    ctx["profile"] = shutil.copy(SAMPLE, ctx["tmp"] / "profile.json")


@given("an endpoint that fails on any query")
def failing_endpoint(ctx, monkeypatch):
    ctx["queried"] = []

    def refuse(self, *args, **kwargs):
        ctx["queried"].append(self)
        raise AssertionError("a representation must not query")

    monkeypatch.setattr(SparqlHttpClient, "_once", refuse)


@when("every representation is generated from the saved profile")
def generate_all_from_file(ctx):
    ctx["paths"] = generate_from_profile_file(ctx["profile"], ctx["output"], ["shacl", "puml", "doc"])


@then("the shapes, the diagram and the document are written")
def all_written(ctx):
    names = {p.name for p in ctx["paths"]}
    assert "main.html" in names and any(n.startswith("shapes-") for n in names)
    assert any(n.startswith("diagram-") for n in names)


@then("the endpoint was never queried")
def never_queried(ctx):
    assert ctx["queried"] == []


@given("a saved profile with a property whose label support is 0.8")
def saved_with_support(ctx):
    ctx["run"] = profile_run(klass(EX + "Person", 10, prop(EX + "name", {1: 8, 2: 2}, literals(12))))
    ctx["profile"] = save_profile(ctx["run"], ctx["tmp"])


@when("the shapes are generated at threshold 1.0 and again at 0.5")
def shapes_at_two_thresholds(ctx):
    run = load_profile(ctx["profile"])
    ctx["graphs"] = {
        t: Graph().parse(data=only(generated(ctx, "shacl", with_threshold(run, t))), format="turtle") for t in (1.0, 0.5)
    }


@then("the property has its accepted counts only at threshold 0.5")
def counts_only_at_half(ctx):
    strict, loose = ctx["graphs"][1.0], ctx["graphs"][0.5]
    assert strict.value(property_shape(strict, EX + "name"), SH.maxCount) is None
    assert loose.value(property_shape(loose, EX + "name"), SH.maxCount) == Literal(1)


@given("a profile run")
def a_profile_run(ctx):
    ctx["run"] = load_profile(SAMPLE)


@when("it is saved and loaded again")
def save_and_load(ctx):
    ctx["loaded"] = load_profile(save_profile(ctx["run"], ctx["tmp"]))


@then("the loaded run equals the saved one")
def loaded_equals(ctx):
    assert ctx["loaded"] == ctx["run"]


UNUSABLE = {
    "a profile path that does not exist": None,
    "a profile file that is not JSON": "{not json",
    "a JSON file that does not match a profile": json.dumps({"graphs": "nope"}),
}


@given(parsers.re("(?P<file>" + "|".join(UNUSABLE) + ")$"))
def unusable(ctx, file):
    ctx["profile"] = ctx["tmp"] / "bad-profile.json"
    if UNUSABLE[file] is not None:
        ctx["profile"].write_text(UNUSABLE[file])


@when("the shapes are generated from it")
def shapes_from_bad_file(ctx):
    ctx["result"] = CliRunner().invoke(generate.gen_shacl, [str(ctx["profile"]), "-o", str(ctx["output"])])


@then(parsers.parse("the command exits with {code:d}"))
def command_exits(ctx, code):
    assert ctx["result"].exit_code == code, ctx["result"].output


@then("the message names the file")
def message_names_file(ctx):
    assert "bad-profile.json" in ctx["result"].output


@then("nothing is written")
def nothing_written(ctx):
    assert not list(ctx["output"].iterdir())


@given("a custom template package that reads a constant from its configuration")
def custom_package(ctx):
    package = ctx["tmp"] / "mine"
    (package / "templates").mkdir(parents=True)
    (package / "templates" / "shapes.ttl").write_text("# {{ conf.title }}")
    (package / "config.json").write_text(json.dumps({"template": "shapes.ttl", "conf": {"title": "Our shapes"}}))
    ctx["package"] = package


@when("the shapes are generated with that template package")
def shapes_with_package(ctx):
    paths = generate_from_profile_file(SAMPLE, ctx["output"], ["shacl"], template_location=ctx["package"])
    ctx["texts"] = [p.read_text() for p in paths]


@then("the output shows the constant")
def shows_constant(ctx):
    assert ctx["texts"] and all(t == "# Our shapes" for t in ctx["texts"])


# --- valid outputs whatever the data holds ---


@given(parsers.re(r'a profile whose (?P<where>class IRI|property IRI) is "?(?P<iri>[^"]+?)"?$'))
def profile_with_iri(ctx, where, iri):
    ctx["iri"] = iri
    if where == "class IRI":
        ctx["run"] = profile_run(klass(iri, 4, prop(EX + "p", {1: 4}, literals(4))), klass(EX + "Other", 2))
    else:
        ctx["run"] = profile_run(klass(EX + "Person", 4, prop(iri, {1: 4}, literals(4))))


@when("every representation is generated")
def generate_all(ctx, caplog):
    with caplog.at_level(logging.WARNING):
        texts = {name: generated(ctx, name) for name in ("shacl", "puml", "doc")}
    ctx["log"] = caplog.text
    ctx["outputs"] = {name: only(t) for name, t in texts.items()}


@then("the shapes parse as Turtle")
def shapes_parse(ctx):
    Graph().parse(data=ctx["outputs"]["shacl"], format="turtle")


@then("the diagram declares each class once")
def diagram_classes_once(ctx):
    declared = re.findall(r'^class "([^"]+)" as C\d+', ctx["outputs"]["puml"], re.M)
    assert len(declared) == len(set(declared)) == len(ctx["run"].graphs[0].class_partitions)


@then(parsers.parse('the document shows "{iri}" by its short name, with the full IRI as its title'))
def document_shows(ctx, iri):
    assert BeautifulSoup(ctx["outputs"]["doc"], "html.parser").find(class_="curie", title=iri) is not None


@then("that class is absent from the shapes and the diagram")
def class_absent(ctx):
    assert "script" not in ctx["outputs"]["shacl"] and "script" not in ctx["outputs"]["puml"]


@then("a warning names the skipped IRI")
def warning_names_iri(ctx):
    assert ctx["iri"] in ctx["log"]


@then("the document lists the IRI under caveats as text")
def caveat_lists_iri(ctx):
    soup = BeautifulSoup(ctx["outputs"]["doc"], "html.parser")
    assert all("alert(1)" not in script.get_text() for script in soup.find_all("script"))
    assert ctx["iri"] in soup.find(id="caveats").get_text(" ")


# --- shapes say no more than the profile observed ---

LABELS = {
    "exactly one": {1: 4},
    "zero or one": {1: 2},
    "one or more": {1: 2, 2: 2},
    "zero or more": {1: 1, 3: 1},
    "exactly 3": {3: 4},
}


@given(parsers.parse("a property whose accepted label is {label}"))
def property_with_label(ctx, label):
    ctx["run"] = profile_run(klass(EX + "Person", 4, prop(EX + "p", LABELS[label], literals(4))))


@when("the shapes are generated")
def shapes_generated(ctx):
    ctx["graph"] = Graph().parse(data=only(generated(ctx, "shacl")), format="turtle")


@then(parsers.parse("its property shape has minimum count {low} and maximum count {high}"))
def property_counts(ctx, low, high):
    g = ctx["graph"]
    shape = property_shape(g, EX + "p")
    assert g.value(shape, SH.minCount) == (None if low == "none" else Literal(int(low)))
    assert g.value(shape, SH.maxCount) == (None if high == "none" else Literal(int(high)))


USAGE = {
    "presence only": prop(EX + "p", presence_only=True),
    "confidence 0.3 and label support 1.0": prop(EX + "p", {1: 3}, literals(3)),
    "confidence 1.0 and label support 0.9": prop(EX + "p", {1: 9, 2: 1}, literals(11)),
    "confidence 1.0 and label support 1.0": prop(EX + "p", {1: 10}, literals(10)),
}


@given(parsers.parse("at threshold 0.8 a property of a class read in {mode} with {usage}"))
def property_with_usage(ctx, mode, usage):
    observed = 10 if mode == "exact" else None
    instances = 10 if mode == "exact" else 40
    cls = klass(EX + "Person", instances, USAGE[usage], observed=observed if observed else 10)
    ctx["run"] = profile_run(cls, acceptance_threshold=0.8)


@then(parsers.parse("its property shape has severity {severity}"))
def property_severity(ctx, severity):
    g = ctx["graph"]
    expected = None if severity == "Violation" else SH[severity]
    assert g.value(property_shape(g, EX + "p"), SH.severity) == expected


@given("a class with a declared subclass and a property every instance has")
def class_with_subclass(ctx):
    ctx["run"] = profile_run(
        klass(EX + "Agent", 4, prop(EX + "p", {1: 4}, literals(4))), edges=[(EX + "Person", EX + "Agent")]
    )


@given("a property whose literals carry a language but no datatype")
def lang_literals(ctx):
    ctx["run"] = profile_run(klass(EX + "Person", 4, prop(EX + "p", {1: 4}, literals(4, datatype=None, language="ro"))))


@then("its property shape allows language-tagged strings")
def allows_lang_string(ctx):
    g = ctx["graph"]
    assert g.value(property_shape(g, EX + "p"), SH.datatype) == RDF.langString


@given("a class read from its first 10 of 50 instances")
def sampled_class(ctx):
    ctx["run"] = profile_run(klass(EX + "Person", 50, prop(EX + "p", {1: 10}, literals(10)), observed=10))


@then("its node shape records 10 observed of 50 instances and the first-N mode")
def node_shape_sampled(ctx):
    g = ctx["graph"]
    (shape,) = g.subjects(SH.targetClass, URIRef(EX + "Person"))
    assert (g.value(shape, FP.observedInstances), g.value(shape, FP.instances)) == (Literal(10), Literal(50))
    assert g.value(shape, FP.precisionMode) == Literal("first_n")


SOURCE = {"default": "continents", "continents": "continents", "treaties": "treaties"}


@given("the shapes generated from the profile of the test data")
def sample_shapes(ctx):
    texts = files(GENERATORS["shacl"](analyse(load_profile(SAMPLE)), JinjaTemplateRenderer()).serialize())
    ctx["shapes"] = texts


@when("the test data is validated against them")
def validate_test_data(ctx):
    import pyshacl

    ctx["results"] = []
    for name, text in ctx["shapes"].items():
        source = next(f for key, f in SOURCE.items() if name.startswith(f"shapes-{key}"))
        data = Graph().parse(DATA / f"{source}-source-ap.rdf")
        ctx["results"].append(
            pyshacl.validate(data, shacl_graph=Graph().parse(data=text, format="turtle"), inference="none")[1]
        )


@then("no result has severity Violation")
def no_violation(ctx):
    assert all(not list(r.subjects(SH.resultSeverity, SH.Violation)) for r in ctx["results"])


# --- the diagram and the document ---


@given(
    parsers.parse(
        'a profile with class "{cls}" whose own property "{p}" has exactly one value and whose implied parent is "{parent}"'
    )
)
def diagram_profile(ctx, cls, p, parent):
    expand = {"ex:": EX}
    iri = lambda curie: expand[curie[:3]] + curie[3:]  # noqa: E731
    ctx["run"] = profile_run(klass(iri(cls), 4, prop(iri(p), {1: 4}, literals(4)), co_types=[(iri(parent), 4)]))


@when("the diagram is generated")
def diagram_generated(ctx):
    ctx["diagram"] = only(generated(ctx, "puml"))


@then(parsers.parse('the diagram declares "{cls}" once with attribute "{p}" of multiplicity "{m}"'))
def diagram_declares(ctx, cls, p, m):
    assert re.findall(rf'^class "{re.escape(cls)}" as \w+', ctx["diagram"], re.M).__len__() == 1
    assert f"{p} : xsd:string [{m}]" in ctx["diagram"]


@then(parsers.parse('it draws a dashed generalisation from "{child}" to "{parent}"'))
def dashed(ctx, child, parent):
    aliases = dict(re.findall(r'class "([^"]+)" as (\w+)', ctx["diagram"]))
    assert f"{aliases[child]} ..|> {aliases[parent]}" in ctx["diagram"]


FOAF = "http://xmlns.com/foaf/0.1/"


def diagram_files(ctx, module_size=None):
    options = GeneratorOptions(module_size=module_size)
    return files(make_generator("puml", analyse(ctx["run"]), JinjaTemplateRenderer(), options=options).serialize())


def module_classes(text):
    """The classes a module diagram draws in full (reference boxes are not its own)."""
    return re.findall(r'^class "ex:([^"]+)" as C\d+ \{$', text, re.M)


@given(
    parsers.parse(
        'the namespace "ex" holds the classes A to G, with A and B linked twice, B and C, C and D, and E and F once, '
        "and G linked to none"
    )
)
def classes_a_to_g(ctx):
    links = {"A": ["B", "B"], "B": ["C"], "C": ["D"], "E": ["F"]}
    ctx["run"] = profile_run(
        *(
            klass(
                EX + name,
                2,
                *(prop(EX + f"p{n}", {1: 2}, resources(2, EX + target)) for n, target in enumerate(links.get(name, ()))),
            )
            for name in "ABCDEFG"
        )
    )


@given(parsers.parse('the namespace "ex" holds {count:d} classes, each linked to the next'))
def chain_of_classes(ctx, count):
    ctx["run"] = profile_run(
        *(klass(EX + f"C{n:02}", 2, prop(EX + "next", {1: 2}, resources(2, EX + f"C{n + 1:02}"))) for n in range(count - 1)),
        klass(EX + f"C{count - 1:02}", 2),
    )


@given(
    parsers.parse('3 classes of "ex" have object properties whose values are "foaf:Person", and no "foaf" class is profiled')
)
def three_link_to_foaf(ctx):
    ctx["run"] = profile_run(
        *(klass(EX + f"C{n}", 2, prop(EX + "knows", {1: 2}, resources(2, FOAF + "Person"))) for n in range(3))
    )


@when(parsers.parse("the diagrams are generated with module size {size:d}"))
def diagrams_with_module_size(ctx, size):
    ctx["size"], ctx["diagrams"] = size, diagram_files(ctx, size)


@when("the diagrams are generated")
def diagrams_generated(ctx):
    ctx["diagrams"] = diagram_files(ctx)


@then(parsers.parse('the module "{name}" holds {classes}'))
def module_holds(ctx, name, classes):
    assert sorted(module_classes(ctx["diagrams"][f"diagram-default--{name}.puml"])) == re.findall(r"[A-Z]", classes)


def module_files(ctx):
    return {n: t for n, t in ctx["diagrams"].items() if "--" in n}


@then(parsers.parse("there are at least {count:d} module diagrams of at most {size:d} classes each"))
def many_small_modules(ctx, count, size):
    modules = module_files(ctx)
    assert len(modules) >= count and all(len(module_classes(t)) <= size for t in modules.values())


@then("every class is in exactly one of them")
def each_class_once(ctx):
    placed = sorted(c for t in module_files(ctx).values() for c in module_classes(t))
    assert placed == sorted(c.class_iri.removeprefix(EX) for c in ctx["run"].graphs[0].class_partitions)


@then("generating again gives the same files with the same contents")
def deterministic(ctx):
    assert diagram_files(ctx, ctx["size"]) == ctx["diagrams"]


@then(parsers.parse('the overview has the package "{ns}" and the package "{other}" marked referenced'))
def overview_packages(ctx, ns, other):
    overview = ctx["diagrams"]["diagram-default.puml"]
    assert f'package "{ns} (3 classes)"' in overview and f'package "{other} (referenced)"' in overview


@then(parsers.parse('one arrow from "{source}" to "{target}" is labelled {count:d}'))
def overview_arrow(ctx, source, target, count):
    overview = ctx["diagrams"]["diagram-default.puml"]
    aliases = dict(re.findall(r'package "(\w+)[^"]*" as (N\d+)', overview))
    assert f"{aliases[source]} --> {aliases[target]} : {count}" in overview


@when("the document is generated")
def document_generated(ctx):
    run = ctx["run"] if "run" in ctx else load_profile(ctx["profile"])
    ctx["soup"] = BeautifulSoup(only(generated(ctx, "doc", run)), "html.parser")


@when("the document command renders it into an empty folder")
def document_command(ctx):
    result = CliRunner().invoke(generate.gen_doc, [str(ctx["profile"]), "-o", str(ctx["output"])])
    assert result.exit_code == 0, result.output
    ctx["soup"] = BeautifulSoup((ctx["output"] / "main.html").read_text(), "html.parser")


@then("the folder holds the report and no profile.html")
def folder_holds_report(ctx):
    names = {p.name for p in ctx["output"].iterdir()}
    assert "main.html" in names and "profile.html" not in names


@then("it has an overview, the namespaces, one chapter per graph with a section per class, and caveats")
def document_sections(ctx):
    soup, run = ctx["soup"], load_profile(SAMPLE)
    assert soup.find(id="overview") and soup.find(id="namespaces") and soup.find(id="caveats")
    chapters = soup.select('main > section[id^="graph-"]')
    assert len(chapters) == len(run.graphs)
    shown = [[c for c in g.class_partitions if namespace_of(c.class_iri) not in META_NAMESPACES] for g in run.graphs]
    assert [len(c.select("details.cls")) for c in chapters] == [len(s) for s in shown]


@given("a profile with a class read from its first 10 of 50 instances and one recorded failure")
def sampled_and_failure(ctx):
    failure = {"query_kind": "co_types", "class_iri": EX + "Big", "message": "class Big: not profiled after 2 attempts"}
    ctx["run"] = profile_run(klass(EX + "Person", 50, prop(EX + "p", {1: 10}, literals(10)), observed=10), failures=[failure])


@then("the collection section lists the failure and the caveats list the sampled class")
def caveats_list(ctx):
    assert "not profiled after 2 attempts" in ctx["soup"].find(id="collection").get_text(" ")
    assert "ex:Person" in ctx["soup"].find(id="caveats").get_text(" ")


@then(parsers.parse('the class section shows "{text}"'))
def class_section_shows(ctx, text):
    assert text in ctx["soup"].select_one("details.cls").get_text(" ")


# --- golden files ---


@given("the fixed test profile")
def fixed_profile(ctx):
    ctx["run"] = load_profile(SAMPLE)


@when(parsers.parse("the {output} is generated from it"))
def output_generated(ctx, output):
    ctx["texts"] = files(make_generator(FORMATS[output], analyse(ctx["run"]), JinjaTemplateRenderer()).serialize())


@then("it equals its golden file")
def equals_golden(ctx):
    for name, text in ctx["texts"].items():
        assert text == (DATA / "golden" / name).read_text(encoding="utf-8"), name


# --- shape names, filters and empty graphs (readable-representations) ---


@given(parsers.parse('a profile with the class "{cls}" and its property "{p}"'))
def class_and_property(ctx, cls, p):
    ctx["run"] = profile_run(klass(cls, 2, prop(p, {1: 2}, literals(2))))


@when(parsers.parse('the shapes are generated with the shapes namespace "{namespace}"'))
def shapes_in_namespace(ctx, namespace):
    options = GeneratorOptions(shapes_namespace=None if namespace == "none" else namespace)
    generator = make_generator("shacl", analyse(ctx["run"]), JinjaTemplateRenderer(), options=options)
    ctx["graph"] = Graph().parse(data=only(files(generator.serialize())), format="turtle")


@then(parsers.parse('the node shape is "{node}" and the property shape is "{prop_shape}"'))
def shape_names(ctx, node, prop_shape):
    g = ctx["graph"]
    assert (URIRef(node), RDF.type, SH.NodeShape) in g and (URIRef(node), SH.property, URIRef(prop_shape)) in g


@given(parsers.parse('a profile holding both the classes "{first}" and "{second}"'))
def colliding_classes(ctx, first, second):
    ctx["run"] = profile_run(klass(first, 1), klass(second, 1, prop(EX + "p", {1: 1}, literals(1))))


@then(parsers.parse('the node shapes are "{first}" and "{second}", in class IRI order'))
def colliding_shapes(ctx, first, second):
    g = ctx["graph"]
    names = [
        str(g.value(predicate=SH.targetClass, object=URIRef(c)))
        for c in sorted(("http://ex.org/a#Thing", "http://ex.org/a/Thing"))
    ]
    assert names == [first, second]


@given(parsers.parse('a profile holding the classes "{first}" and "{second}"'))
def two_classes(ctx, first, second):
    ctx["run"] = profile_run(klass(first, 1, prop(first + "_p", {1: 1}, literals(1))), klass(second, 1))


@when(parsers.parse("the shapes and the diagram are generated {how}"))
def filtered(ctx, how, caplog):
    names = re.findall(r'"([^"]+)"', how)
    options = GeneratorOptions(
        include_namespaces=names if "include" in how else [], exclude_namespaces=names if "exclude" in how else []
    )
    with caplog.at_level(logging.WARNING):
        texts = {}
        for name in ("shacl", "puml"):
            texts.update(
                files(make_generator(name, analyse(ctx["run"]), JinjaTemplateRenderer(), options=options).serialize())
            )
        if "exclude" in how or "include" in how:
            from fingerprint.service_layer.prefixes import resolve_namespaces
            from fingerprint.service_layer.representations import warn_unknown_filters

            warn_unknown_filters(resolve_namespaces(ctx["run"]), options)
    ctx["texts"], ctx["log"] = texts, caplog.text


@then(parsers.parse('"{cls}" has a node shape and a box'))
def has_shape_and_box(ctx, cls):
    joined = "\n".join(ctx["texts"].values())
    assert f"sh:targetClass {cls}" in joined and f'class "{cls}"' in joined


@then(parsers.parse('"{cls}" has neither'))
def has_neither(ctx, cls):
    joined = "\n".join(ctx["texts"].values())
    assert f"sh:targetClass {cls}" not in joined and f'class "{cls}"' not in joined


@then(parsers.parse('a warning names "{name}"'))
def warning_names(ctx, name):
    assert f"--exclude-namespace {name}: no such namespace; ignored" in ctx["log"]


@given("a profile whose default graph is empty")
def empty_default(ctx):
    ctx["run"] = profile_run()


@then("no shapes or diagram file is written for it")
def no_files_for_empty(ctx):
    assert ctx["texts"] == {}
