"""Steps of the namespace-filter scenarios of profile_representations.feature (namespace-filter, UC-B2.1).

Every generation goes through `generate_representations` or `generate_from_profile_file`, the documented entry
points, so the term filter and its warnings apply as they do for the commands.
"""

import logging
import re

from bs4 import BeautifulSoup
from pytest_bdd import given, parsers, then, when
from rdflib import RDF, Graph, URIRef
from rdflib.namespace import SH

from fingerprint.adapters.profile_file import save_profile
from fingerprint.domain.profile import PitfallExample, PitfallResult, PitfallTerm
from fingerprint.domain.views import GeneratorOptions
from fingerprint.service_layer.representations import generate_from_profile_file, generate_representations
from tests import builders
from tests.builders import EX, ORG, REL, filter_profile, klass, literals, prop, with_namespaces

OUTPUTS = {"pattern schema": "pattern", "ShExC": "shex", "shapes": "shacl", "diagram": "puml", "report": "doc"}
EVERY_OUTPUT = tuple(OUTPUTS.values())
PREFIX_OF_FILE = {
    "pattern-": "pattern",
    "shex-": "shex",
    "shapes-": "shacl",
    "diagram-": "puml",
    "main.html": "doc",
    "pitfalls-": "pitfalls",
}
CURIE = re.compile(r"(?P<prefix>[a-z]+):(?P<local>\w+)")


# --- generating ---


def run_filtered(ctx, caplog, formats, how, *, from_file=False):
    """Generate `formats` with the options `how` names ('no filter option', 'exclude "a" and include "b"')."""
    options = GeneratorOptions(
        exclude_namespaces=re.findall(r'exclude "([^"]+)"', how), include_namespaces=re.findall(r'include "([^"]+)"', how)
    )
    ctx["n"] = ctx.get("n", 0) + 1
    folder = ctx["tmp"] / f"filtered-{ctx['n']}"
    folder.mkdir()
    with caplog.at_level(logging.WARNING):
        if from_file:
            generate_from_profile_file(ctx["saved"], folder, formats, options=options)
        else:
            generate_representations(ctx["run"], folder, formats, options=options)
    texts = {p.name: p.read_text(encoding="utf-8") for p in sorted(folder.iterdir())}
    ctx["by_format"] = {
        fmt: {n: t for n, t in texts.items() if n.startswith(prefix)}
        for prefix, fmt in PREFIX_OF_FILE.items()
        if fmt in formats
    }
    ctx["texts"], ctx["formats"] = texts, list(formats)
    ctx["log"], ctx["warnings"] = caplog.text, [r.getMessage() for r in caplog.records if r.levelno >= logging.WARNING]
    caplog.clear()


@when(parsers.parse("the shapes, the diagram and the report are generated {how}"))
def shapes_diagram_report(ctx, caplog, how):
    run_filtered(ctx, caplog, ("shacl", "puml", "doc"), how)


@when(parsers.re(r"(?:the outputs are|every output is) generated with (?P<how>.+)"))
def every_output(ctx, caplog, how):
    run_filtered(ctx, caplog, EVERY_OUTPUT, how)


@when(parsers.re(r"the (?P<output>pattern schema|ShExC|shapes|diagram|report) is generated with (?P<how>.+)"))
def one_output(ctx, caplog, output, how):
    run_filtered(ctx, caplog, (OUTPUTS[output],), how)


@when(parsers.parse("the pattern schema is generated from the file {how}"))
def pattern_from_file(ctx, caplog, how):
    run_filtered(ctx, caplog, ("pattern",), how.removeprefix("again "), from_file=True)
    ctx.setdefault("schemas", []).append(next(iter(ctx["texts"].values())))


@when(parsers.parse("the pitfalls file and the report are generated with {how}"))
def pitfalls_and_report(ctx, caplog, how):
    run_filtered(ctx, caplog, ("pitfalls", "doc"), how)


# --- profiles ---


@given("the filter test profile")
def the_filter_profile(ctx):
    ctx["run"] = filter_profile()


@given("the filter test profile saved to a file")
def the_saved_filter_profile(ctx):
    ctx["run"] = filter_profile()
    ctx["saved"] = save_profile(ctx["run"], ctx["tmp"])
    ctx["bytes"] = ctx["saved"].read_bytes()


@given(parsers.parse('"ex:Person" has the property "{iri}"'))
def person_has_property(ctx, iri):
    graph = ctx["run"].graphs[0]
    classes = [
        c.model_copy(update={"property_partitions": [*c.property_partitions, prop(iri, {1: 2}, literals(2))]})
        if c.class_iri == EX + "Person"
        else c
        for c in graph.class_partitions
    ]
    ctx["run"] = ctx["run"].model_copy(update={"graphs": [graph.model_copy(update={"class_partitions": classes})]})


@given(parsers.parse('a profile where all 5 "ex:Agent" instances are also the 5 "org:Member" instances'))
def merged_classes(ctx):
    name = prop(EX + "name", {1: 5}, literals(5))
    ctx["run"] = builders.profile_run(
        klass(EX + "Agent", 5, name, co_types=[(ORG + "Member", 5)]),
        klass(ORG + "Member", 5, name, co_types=[(EX + "Agent", 5)]),
    )


@given(
    parsers.parse(
        'a profile with the namespaces "ex", "rel", "relx" under "http://example.org/" and "org" at "http://org.example/"'
    )
)
def four_namespaces(ctx):
    """One class of `org` whose properties `p` come from each of the four namespaces."""
    table = (("ex", EX), ("rel", REL), ("relx", EX + "relx/"), ("org", ORG))
    properties = [prop(f"{namespace}p", {1: 2}, literals(2)) for _, namespace in table]
    ctx["run"] = with_namespaces(builders.profile_run(klass(ORG + "Thing", 2, *properties)), *table)


@given(parsers.parse('a scanned profile whose finding names "rel:r1" as an example'))
def finding_on_rel(ctx):
    example = PitfallExample(entity=PitfallTerm(text=REL + "r1", kind="iri"))
    finding = PitfallResult(check_id="x", title="T", importance="minor", scope="data", source="s", count=1, examples=[example])
    run = filter_profile()
    ctx["run"] = run.model_copy(update={"graphs": [g.model_copy(update={"pitfalls": [finding]}) for g in run.graphs]})


# --- what an output writes ---


def class_block(fmt, texts, cls):
    """The lines a text output spends on `cls`, or None when it has no block for it."""
    lines = "\n".join(texts.values()).splitlines()
    heads = {
        "pattern": lambda ln: ln.startswith("(:") and cls in ln[2:].split(")")[0].split("&"),
        "shex": lambda ln: ln == f"{cls} {{",
        "puml": lambda ln: ln.startswith(f'class "{cls}" as'),
    }
    start = next((i for i, ln in enumerate(lines) if heads[fmt](ln)), None)
    if start is None:
        return None
    end = next(
        (i for i in range(start + 1, len(lines)) if lines[i] == "}" or (fmt == "pattern" and lines[i][:1] in "(#")), len(lines)
    )
    return lines[start:end]


def shacl_entry(text, cls, name):
    g = Graph().parse(data=text, format="turtle")
    nm = g.namespace_manager
    expand = lambda curie: URIRef(g.namespace_manager.expand_curie(curie))  # noqa: E731
    for shape in g.subjects(SH.targetClass, expand(cls)):
        for p in g.objects(shape, SH.property):
            if g.value(p, SH.path) == expand(name):
                return " ".join(
                    f"{a.n3(nm)} {b.n3(nm)}" for a, b in sorted(g.predicate_objects(p)) if a not in (SH.path, RDF.type)
                )
    return None


def doc_entry(text, cls, name):
    for section in BeautifulSoup(text, "html.parser").select("details.cls"):
        if section.select_one("summary h3 .curie").get_text() != cls:
            continue
        for row in section.select("tbody tr:not(.group)"):
            if row.select_one(".curie").get_text() == name:
                return row.get_text("")
    return None


def entry(ctx, cls, name):
    """What the last-generated output writes for property `name` of class `cls` (a line of text), else None."""
    (fmt,) = ctx["formats"]
    texts = ctx["by_format"][fmt]
    if fmt == "shacl":
        return next((e for t in texts.values() if (e := shacl_entry(t, cls, name))), None)
    if fmt == "doc":
        return next((e for t in texts.values() if (e := doc_entry(t, cls, name))), None)
    marks = {"pattern": f"-{name}->", "shex": f"{name} ", "puml": f"{name} : "}
    return next((ln.strip() for ln in class_block(fmt, texts, cls) or [] if ln.strip().startswith(marks[fmt])), None)


def written_text(fmt, text):
    """The text of an output as a reader sees it: the report's CURIEs are split across markup, so take their text."""
    if fmt != "doc":
        return text
    return "\n".join(c.get_text() for c in BeautifulSoup(text, "html.parser").select(".curie"))


def names(text, prefix):
    return re.findall(rf"(?<![\w/#.:-]){re.escape(prefix)}:", text)


@then(parsers.parse('it holds no "{prefix}:" name'))
def holds_no_name(ctx, prefix):
    (fmt,) = ctx["formats"]
    assert not names("\n".join(ctx["by_format"][fmt].values()), prefix)


@then(parsers.parse('it writes "{name}" for "{cls}"'))
def writes_for(ctx, name, cls):
    assert entry(ctx, cls, name) is not None


@then(parsers.parse('every output writes "{name}" for "{cls}"'))
def every_output_writes(ctx, name, cls):
    for fmt in ctx["formats"]:
        assert entry(ctx | {"formats": [fmt]}, cls, name) is not None, fmt


@then(parsers.parse('no output writes "{name}"'))
def no_output_writes(ctx, name):
    """Per format, the inverse of `every_output_writes` (the report splits a CURIE across markup, so a text search
    cannot see it); the raw text search stays for the full IRI of a leak."""
    for fmt in ctx["formats"]:
        assert entry(ctx | {"formats": [fmt]}, "ex:Person", name) is None, fmt
    assert all(name not in text for text in ctx["texts"].values())


@then(parsers.parse('no output writes an "{prefix}:" property'))
def no_output_writes_prefix(ctx, prefix):
    assert not names("\n".join(ctx["texts"].values()), prefix)


@then(parsers.parse('no output holds a "{prefix}:" name'))
def no_output_holds(ctx, prefix):
    assert not names("\n".join(ctx["texts"].values()), prefix)


@then(parsers.parse('every output gives "{name}" the type "{datatype}"'))
def every_output_types(ctx, name, datatype):
    for fmt in ctx["formats"]:
        assert datatype in entry(ctx | {"formats": [fmt]}, "ex:Person", name), fmt


@then(parsers.parse('the report has no "{cls}" section'))
def report_has_no_section(ctx, cls):
    page = BeautifulSoup(ctx["by_format"]["doc"]["main.html"], "html.parser")
    assert all(s.select_one("summary h3").get_text().strip() != cls for s in page.select("details.cls"))


def links_by(ctx, name):
    """The arrows of the diagram files labelled with property `name`."""
    lines = (ln for text in ctx["by_format"]["puml"].values() for ln in text.splitlines())
    return [ln for ln in lines if "-->" in ln and ln.endswith(f" : {name}")]


WRITTEN = [
    (r'an edge "(?P<line>.+)"', lambda line, e, *_: e.startswith(line) and "(:" not in e.split(" ")[1]),
    (r'the triple constraint "(?P<line>.+)"', lambda line, e, *_: e.startswith(line)),
    (
        r'the attribute "(?P<line>.+)" with no link',
        lambda line, e, ctx: e.startswith(line) and not links_by(ctx, "ex:memberOf"),
    ),
    (r'a property shape with "(?P<line>.+)" and no sh:class', lambda line, e, *_: line in e and "sh:class" not in e),
    (r'a row whose value types do not name "(?P<line>.+)"', lambda line, e, *_: line not in e),
]


@then(parsers.parse('"{name}" is written as {written}'))
def written_as(ctx, name, written):
    e = entry(ctx, "ex:Person", name)
    assert e is not None
    for pattern, check in WRITTEN:
        if match := re.fullmatch(pattern, written):
            assert check(match["line"], e, ctx), e
            return
    raise AssertionError(f"no check for {written}")


@then(parsers.parse('a block is headed "{head}"'))
def block_headed(ctx, head):
    assert any(ln.startswith(head) for t in ctx["texts"].values() for ln in t.splitlines())


# --- warnings and results ---


@then(parsers.parse('one warning says "{message}"'))
def one_warning(ctx, message):
    assert ctx["warnings"] == [message]


@then(parsers.parse('a warning says "{name}" hides no term'))
def hides_no_term(ctx, name):
    assert f"--exclude-namespace {name}: no term in this namespace; ignored" in ctx["warnings"]


@then("the outputs are as without the option")
def as_without(ctx, caplog):
    got = ctx["by_format"]
    run_filtered(ctx, caplog, EVERY_OUTPUT, "no filter option")
    assert ctx["by_format"] == got


@then(parsers.parse("the excluded namespaces are {excluded}"))
def excluded_are(ctx, excluded):
    """A namespace is excluded when its property `p` is in no output of the class `org:Thing` (and the ones to keep are)."""
    wanted, _, warning = excluded.partition(", and a warning says ")
    expected = set() if wanted == "none" else set(wanted.split(", "))
    text = "\n".join(written_text(fmt, t) for fmt, ts in ctx["by_format"].items() for t in ts.values())
    present = {p for p in ("ex", "rel", "relx", "org") if re.search(rf"(?<![\w/#.:-]){p}:p\b", text)}
    assert {"ex", "rel", "relx", "org"} - present == expected
    if warning:
        assert f"--exclude-namespace {warning.removesuffix(' is no namespace')}: no such namespace; ignored" in ctx["warnings"]


@then("the profile file is unchanged")
def profile_unchanged(ctx):
    assert ctx["saved"].read_bytes() == ctx["bytes"]


@then(parsers.parse('the first pattern schema holds no "{prefix}:" name and the second holds "{name}"'))
def first_and_second(ctx, prefix, name):
    first, second = ctx["schemas"]
    assert not names(first, prefix) and name in second


@then(parsers.parse('both still list "{name}" as an example'))
def both_list(ctx, name):
    pitfalls = "\n".join(ctx["by_format"]["pitfalls"].values()) if "pitfalls" in ctx["by_format"] else ""
    page = BeautifulSoup(ctx["by_format"]["doc"]["main.html"], "html.parser")
    assert name in pitfalls or REL + "r1" in pitfalls
    assert any(c.get_text() == name for c in page.select("#pitfalls .curie"))


# --- the note of the excluded namespaces ---


@then(parsers.re(r'it carries the line "(?P<line>[^"]+)"(?P<every> in every file)?'))
def carries_line(ctx, line, every):
    files = [t for ts in ctx["by_format"].values() for t in ts.values()]
    assert files
    for text in files if every else files[:1]:
        assert line in text.splitlines()


@then(parsers.parse('it carries the same text for the graph under its caveats and "{prefix}" marked excluded in its table'))
def carries_in_report(ctx, prefix):
    page = BeautifulSoup(ctx["by_format"]["doc"]["main.html"], "html.parser")
    assert "rel (classes 0, properties 2, values 0)" in page.select_one("#caveats").get_text(" ")
    assert page.select_one(f'#namespaces tr[data-prefix="{prefix}"].excluded') is not None


@then("it carries no note of excluded namespaces")
def carries_no_note(ctx):
    assert not any("excluded namespaces" in t for ts in ctx["by_format"].values() for t in ts.values())
