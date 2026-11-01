"""Steps of the pattern schema scenarios of profile_representations.feature (UC-B2.1) over hand-built and sample profiles."""

import re

from click.testing import CliRunner
from pytest_bdd import given, parsers, then, when

from fingerprint.adapters.profile_file import save_profile
from fingerprint.domain.profile import (
    Depth,
    LangText,
    NamespacePrefix,
    ObjectTypeScope,
    PrefixSource,
    TermAnnotation,
    ValueCount,
)
from fingerprint.entrypoints.cli import generate
from fingerprint.service_layer.prefixes import resolve_namespaces
from tests.bdd.steps.representations import generated, only
from tests.builders import klass, literals, profile_run, prop, resources
from tests.fakes import EX
from tests.refresh_golden import render
from tests.sample_data import TEST_DATA

LABELS = TEST_DATA / "ontology" / "labels.ttl"
TEXT = re.compile(r'"([^"]*)"(?:@([A-Za-z-]+))?')  # a label as written in a step: "text" or "text"@lang
INDENT = 2


def iri(curie: str) -> str:
    return EX + curie.removeprefix("ex:")


def name_of(header: str) -> str:
    return header.removeprefix("(:").split(") ", 1)[0]


def pattern_text(ctx) -> str:
    """The one pattern file of a hand-built profile."""
    return only(ctx["texts"])


def block_lines(text: str, name: str) -> list[str]:
    """The lines of the block of group `name`, header first; empty when it has none."""
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines) if line.startswith(f"(:{name})") or line.startswith(f"(:{name} ")), None)
    if start is None:
        return []
    end = next((i for i in range(start + 1, len(lines)) if not lines[i].startswith(" ")), len(lines))
    return lines[start:end]


def level_of(line: str) -> int:
    return (len(line) - len(line.lstrip(" "))) // INDENT


def edge_line(text: str, property_name: str) -> str:
    return next(line for line in text.splitlines() if line.lstrip().startswith(f"-{property_name}->"))


def pattern_files(texts: dict[str, str]) -> dict[str, str]:
    return {name: text for name, text in texts.items() if name.startswith("pattern-")}


# --- the pattern view: hand-built profiles ---


@given(parsers.re(r'a profile where (?P<chain>"ex:\w+" (?:reaches blank nodes of|those of) .+)$'))
def blank_node_chain(ctx, chain):
    links = re.findall(r'"(ex:\w+)" (?:reaches blank nodes of|those of) "(ex:\w+)" by "(ex:\w+)"', chain)
    names = list(dict.fromkeys(n for source, target, _ in links for n in (source, target)))
    reach = {source: [] for source in names}
    for source, target, via in links:
        reach[source].append(
            prop(iri(via), {1: 2}, resources(2, iri(target), "blank_node").model_copy(update={"distinct_objects": 2}))
        )
    ctx["run"] = profile_run(*(klass(iri(n), 2, *reach[n]) for n in names))


@given(parsers.parse('a profile where 3 distinct blank nodes of "{note}" are reached and "{same}" has 5 instances'))
def unreached_instances(ctx, note, same):
    reached = resources(3, iri(note), "blank_node").model_copy(update={"distinct_objects": 3})
    ctx["run"] = profile_run(klass(EX + "Owner", 3, prop(EX + "note", {1: 3}, reached)), klass(iri(note), 5))


@given(parsers.parse('a profile collected across graphs where "{p}" points to "{cls}" typed in graph "{graph}"'))
def other_graph_target(ctx, p, cls, graph):
    typed = resources(2, iri(cls)).model_copy(update={"object_class_graph": graph})
    ctx["run"] = profile_run(klass(EX + "A", 2, prop(iri(p), {1: 2}, typed)), object_type_scope=ObjectTypeScope.any_graph)


@given(
    parsers.parse(
        'a profile where "{big}" has 50000 instances, 10000 of them read in first-N mode, and "{p}" on 9000 of those'
    )
)
def first_n_profile(ctx, big, p):
    ctx["run"] = profile_run(klass(iri(big), 50000, prop(iri(p), {1: 9000}, literals(9000)), observed=10000))


VALUES = {"the empty string": "", 'the letter "a"': "a"}


@given(parsers.parse("a profile where the lowest and highest values of a literal property are both {value}"))
def lowest_and_highest(ctx, value):
    text = "a" * 70 if value.startswith("70 times") else VALUES.get(value, value.strip('"'))
    both = literals(10).model_copy(update={"min_value": text, "max_value": text})
    ctx["run"] = profile_run(klass(EX + "A", 10, prop(EX + "p", {1: 10}, both)))


@then(parsers.parse("the property's edge ends in {written}"))
def edge_ends_in(ctx, written):
    assert edge_line(pattern_text(ctx), "ex:p").endswith(" " + written)


STATUS = "http://ex.org/status/active"


def status_profile(top_values):
    status = prop(EX + "status", {1: 4}, resources(4)).model_copy(update={"distinct_objects": 1, "top_values": top_values})
    return profile_run(klass(EX + "A", 4, status), depth=Depth.rich_values)


@given(
    parsers.parse(
        'a profile collected at depth "rich_values" where every object of "ex:status" is the IRI "{value}", '
        "recorded as its top value"
    )
)
def single_iri_value(ctx, value):
    assert value == STATUS
    ctx["run"] = status_profile([ValueCount(value=value, triples=4)])


@given(parsers.parse('the prefix table maps "{prefix}" to "{namespace}"'))
def prefix_maps(ctx, prefix, namespace):
    # added after resolution: resolve_namespaces scans terms, not top values, so it would drop this namespace
    resolved = resolve_namespaces(ctx["run"])
    entry = NamespacePrefix(prefix=prefix, namespace=namespace, source=PrefixSource.user)
    ctx["run"] = resolved.model_copy(update={"namespaces": sorted([*resolved.namespaces, entry], key=lambda e: e.prefix)})


@then(parsers.parse('the "{p}" edge is "{line}"'))
def edge_is(ctx, p, line):
    assert edge_line(pattern_text(ctx), p).strip() == line


@then(parsers.parse('the prefix "{prefix}" is declared'))
def prefix_declared(ctx, prefix):
    assert f"PREFIX {prefix}: <" in pattern_text(ctx)


@then(parsers.parse('the same profile without top values gives the edge "{line}"'))
def without_top_values(ctx, line):
    plain = status_profile(None).model_copy(update={"namespaces": ctx["run"].namespaces})
    assert edge_line(only(generated(ctx, "pattern", plain)), "ex:status").strip() == line


@then(parsers.parse('the "{name}" block header is "{header}"'))
def block_header(ctx, name, header):
    assert block_lines(pattern_text(ctx), name)[0] == header


@then(parsers.parse('its "{p}" edge holds "{statistic}"'))
def edge_holds(ctx, p, statistic):
    assert f" {statistic}" in edge_line(pattern_text(ctx), p)


@then(parsers.parse('the "{name}" block holds {levels}'))
def block_holds_at_levels(ctx, name, levels):
    lines = block_lines(pattern_text(ctx), name)
    assert lines, f"no block for {name}"
    for text, level in re.findall(r'"([^"]+)" at level (\d)', levels):
        assert any(level_of(ln) == int(level) and ln.strip().startswith(text) for ln in lines), (text, level, lines)


@then("no line lies below level 3")
def nothing_below_three(ctx):
    assert all(level_of(line) <= 3 for line in pattern_text(ctx).splitlines())


@then(parsers.parse('neither "{first}" nor "{second}" begins a block'))
def neither_begins_block(ctx, first, second):
    assert not block_lines(pattern_text(ctx), first) and not block_lines(pattern_text(ctx), second)


@then(parsers.parse('"{name}" is expanded once, under "{edge}"'))
def expanded_once(ctx, name, edge):
    text = pattern_text(ctx)
    assert not block_lines(text, name)
    owner = block_lines(text, "ex:A")
    at = next(i for i, line in enumerate(owner) if line.strip().startswith(edge))
    assert level_of(owner[at]) == 1 and level_of(owner[at + 1]) == 2  # its own edges follow the edge into it
    assert sum(f"-> (:{name})" in line for line in owner) == 2  # the edge into it, and its one self link


@then(parsers.parse('its nested line "{line}" is followed by no deeper line'))
def nested_line_ends(ctx, line):
    lines = pattern_text(ctx).splitlines()
    at = next(i for i, ln in enumerate(lines) if ln.strip() == line)
    assert at + 1 == len(lines) or level_of(lines[at + 1]) <= level_of(lines[at]) or not lines[at + 1].startswith(" ")


@then(parsers.parse('"{name}" begins a block'))
def begins_block(ctx, name):
    assert block_lines(pattern_text(ctx), name)


@then(parsers.parse('the edges into "{name}" are not followed by nested lines'))
def edges_into_not_nested(ctx, name):
    lines = pattern_text(ctx).splitlines()
    into = [i for i, ln in enumerate(lines) if ln.startswith(" ") and f"-> (:{name})" in ln]
    assert into and all(i + 1 == len(lines) or level_of(lines[i + 1]) <= level_of(lines[i]) for i in into)


@then(parsers.parse('the "{p}" edge target is "{target}"'))
def edge_target_is(ctx, p, target):
    assert f"-> {target}" in edge_line(pattern_text(ctx), p)


# --- the sample profile's pattern files ---


@then(parsers.parse('"{file}" holds, at level {level:d}, the line "{line}"'))
def holds_line_at_level(ctx, file, level, line):
    lines = ctx["texts"][file].splitlines()
    assert any(ln == INDENT * level * " " + line for ln in lines), line


@then("in every file no group name begins two blocks and no property begins two edges at the same place")
def no_duplicates(ctx):
    for text in pattern_files(ctx["texts"]).values():
        headers = [name_of(ln) for ln in text.splitlines() if ln.startswith("(:")]
        assert len(headers) == len(set(headers))
        seen = []
        for line in text.splitlines():
            if line.startswith("(:"):
                seen = []
            elif line.startswith(" "):
                key = (level_of(line), line.strip().split("->")[0])
                seen = [k for k in seen if k[0] <= key[0]]
                assert key not in seen, line
                seen.append(key)


@then(parsers.parse("{names} begin no block"))
def begin_no_block(ctx, names):
    for name in re.findall(r'"([^"]+)"', names):
        assert all(not block_lines(t, name) for t in pattern_files(ctx["texts"]).values()), name


@then("every declared prefix is used")
def prefixes_used(ctx):
    for text in pattern_files(ctx["texts"]).values():
        body = "\n".join(ln for ln in text.splitlines() if not ln.startswith(("PREFIX ", "# ")))
        for prefix in re.findall(r"^PREFIX (\S*): ", text, re.M):
            assert f"{prefix}:" in body or f"{prefix}:" in " ".join(
                ln for ln in text.splitlines() if ln.startswith("# glossary")
            ), prefix


# --- term labels and descriptions ---


def with_annotations(run, notes):
    return run.model_copy(update={"graphs": [g.model_copy(update={"term_annotations": notes}) for g in run.graphs]})


def langs(text: str) -> list[LangText]:
    return [LangText(text=t, language=lang or None) for t, lang in TEXT.findall(text)]


@given("the label fixture ontology")
def label_fixture(ctx):
    ctx["ontology"] = LABELS


@given(parsers.parse("a profile whose data labels \"{term}\" '{label}' with the description '{description}'"))
def data_labels_and_description(ctx, term, label, description):
    note = TermAnnotation(term=iri(term), labels=langs(label), descriptions=langs(description))
    ctx["run"] = with_annotations(profile_run(klass(iri(term), 2)), [note])


@given(parsers.re(r'a profile whose data labels "(?P<term>[^"]+)" (?P<labels>".*)$'))
def data_labels(ctx, term, labels):
    ctx["run"] = with_annotations(profile_run(klass(iri(term), 2)), [TermAnnotation(term=iri(term), labels=langs(labels))])


@given(parsers.parse("an ontology that labels \"{term}\" '{label}' with no description"))
def ontology_labels(ctx, term, label):
    path = ctx["tmp"] / "labels.ttl"
    text, language = TEXT.search(label).groups()
    path.write_text(f'<{iri(term)}> <http://www.w3.org/2000/01/rdf-schema#label> "{text}"@{language} .\n')
    ctx["ontology"] = path


@given("an ontology file that is not RDF")
def not_rdf(ctx):
    ctx["ontology"] = ctx["tmp"] / "notes.ttl"
    ctx["ontology"].write_text("this is not turtle")


@given("a profile saved before 3.2, with no term annotations")
def saved_before_annotations(ctx, sample_run):
    ctx["run"] = with_annotations(sample_run, None)


def run_command(ctx, *options):
    """The pattern command over the scenario's profile, into the scenario's output folder."""
    saved = save_profile(ctx["run"], ctx["tmp"])
    ctx["result"] = CliRunner().invoke(generate.gen_pattern, [str(saved), "-o", str(ctx["output"]), *options])
    ctx["texts"] = {p.name: p.read_text() for p in ctx["output"].iterdir()}


@when("the pattern schema is generated from it with that ontology")
def pattern_with_ontology(ctx):
    run_command(ctx, "--ontology", str(ctx["ontology"]))


@when(parsers.parse('the pattern schema is generated from it with "{options}"'))
def pattern_with_options(ctx, options):
    run_command(ctx, *options.split())
    assert ctx["result"].exit_code == 0, ctx["result"].output


@then("it is written")
def pattern_written(ctx):
    assert pattern_files(ctx["texts"])


def glossary_lines(text: str) -> list[str]:
    lines = text.splitlines()
    return lines[lines.index("# glossary") + 1 :] if "# glossary" in lines else []


@then(parsers.parse("the glossary holds the line '{line}'"))
def glossary_holds(ctx, line):
    assert any(line in glossary_lines(text) for text in pattern_files(ctx["texts"]).values())


@then(parsers.parse('the glossary has no line for "{name}"'))
def glossary_lacks(ctx, name):
    assert all(not ln.startswith(name + " ") for t in pattern_files(ctx["texts"]).values() for ln in glossary_lines(t))


@then(parsers.parse('the glossary line of "{name}" shows {shown}'))
def glossary_shows(ctx, name, shown):
    (line,) = [ln for ln in glossary_lines(pattern_text(ctx)) if ln.startswith(name + " ")]
    rest = line.removeprefix(f"{name} {shown}")
    assert line.startswith(f"{name} {shown}") and (rest == "" or rest.startswith(":")), line


@then(parsers.parse('its glossary is "{line}"'))
def glossary_is(ctx, line):
    assert all(t.splitlines()[-1] == line for t in pattern_files(ctx["texts"]).values())


@then("it exits 2 with a message naming the ontology file")
def exits_naming_ontology(ctx):
    assert ctx["result"].exit_code == 2 and ctx["ontology"].name in ctx["result"].output


# --- size filters ---


def file_named(ctx, name):
    ctx["file"] = ctx["texts"][name]
    return ctx["file"]


@then(parsers.parse('"{file}" has no block "{header}"'))
def has_no_block(ctx, file, header):
    assert not any(ln.startswith(header) for ln in file_named(ctx, file).splitlines())


@then(parsers.parse('it holds the line "{line}"'))
def holds_line(ctx, line):
    assert line in ctx["file"].splitlines()


@then(parsers.parse('it still holds the line "{line}"'))
def still_holds_line(ctx, line):
    assert any(ln.strip() == line for ln in ctx["file"].splitlines())


@then("each file has one block, the largest named group of its graph")
def one_block_each(ctx, sample_run):
    unfiltered = render(sample_run, "pattern")
    assert pattern_files(ctx["texts"]).keys() == unfiltered.keys()
    for file, text in pattern_files(ctx["texts"]).items():
        headers = [ln for ln in text.splitlines() if ln.startswith("(:")]
        largest = next(ln for ln in unfiltered[file].splitlines() if ln.startswith("(:"))
        assert len(headers) == 1 and name_of(headers[0]) == name_of(largest)
