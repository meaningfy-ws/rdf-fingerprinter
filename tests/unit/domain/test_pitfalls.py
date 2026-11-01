"""The pitfall check header contract and levels (pitfall-scans › Pitfall check contract, › Fail on findings)."""

import pytest

from fingerprint.domain.pitfalls import PitfallCheckError, at_or_above, parse_header, robot_level
from fingerprint.domain.profile import PitfallImportance

GOOD = """# id: p35_untyped_property
# title: Relation used but never defined
# some free prose without a key
# importance: important
# scope: data
# source: OOPS! P35
# description: one line
PREFIX owl: <http://www.w3.org/2002/07/owl#>
SELECT ?entity ?property ?value WHERE { ?s ?entity ?o }
"""


def test_a_valid_header():
    check = parse_header(GOOD, origin="packaged")
    assert (check.check_id, check.importance, check.scope, check.source) == (
        "p35_untyped_property",
        "important",
        "data",
        "OOPS! P35",
    )
    assert check.heuristic is False and check.description == "one line" and check.query == GOOD and check.origin == "packaged"


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (("# id: p35_untyped_property\n", ""), "id"),
        (("important", "severe"), "importance"),
        (("data", "everything"), "scope"),
        (("# source: OOPS! P35\n", "# source: OOPS! P35\n# severity: high\n"), "severity"),
        (("# scope: data\n", "# scope: data\n# scope: schema\n"), "twice"),
        (("p35_untyped_property", "P35-Untyped"), "id"),
        (("# description: one line\n", "# description: one line\n# heuristic: maybe\n"), "heuristic"),
    ],
)
def test_invalid_headers_are_refused(change, message):
    with pytest.raises(PitfallCheckError, match=message):
        parse_header(GOOD.replace(*change, 1), origin="my.rq")


def test_levels_map_to_robot_and_order():
    assert [robot_level(i) for i in ("critical", "important", "minor")] == ["ERROR", "WARN", "INFO"]


def result(importance, count, check_id="c"):
    from fingerprint.domain.profile import PitfallResult

    return PitfallResult(check_id=check_id, title="t", importance=importance, scope="data", source="s", count=count)


def test_at_or_above_sums_counts_over_graphs_and_distinct_checks():
    from fingerprint.domain.profile import GraphProfile, ProfileRun

    graphs = [
        GraphProfile(pitfalls=[result("critical", 3, "a"), result("minor", 9, "b")]),
        GraphProfile(graph="http://g", pitfalls=[result("critical", 2, "a"), result("important", 0, "c")]),
        GraphProfile(),
    ]
    run = ProfileRun(endpoint="http://e", settings={}, graphs=graphs)
    assert at_or_above(run, PitfallImportance.critical) == (5, 1)
    assert at_or_above(run, PitfallImportance.important) == (5, 1)
    assert at_or_above(run, PitfallImportance.minor) == (14, 2)


def test_blank_lines_do_not_end_the_header_and_a_header_only_text_still_parses():
    spaced = GOOD.replace("# importance: important\n", "\n# importance: important\n", 1)
    assert parse_header(spaced, origin="x").importance == "important"
    header_only = "".join(line + "\n" for line in GOOD.splitlines() if line.startswith("#"))
    assert parse_header(header_only, origin="x").check_id == "p35_untyped_property"


def test_the_heuristic_flag_is_read_whatever_its_case():
    flagged = GOOD.replace("# description: one line\n", "# description: one line\n# heuristic: True\n")
    assert parse_header(flagged, origin="x").heuristic is True


def test_every_missing_key_is_named_in_the_header_order():
    with pytest.raises(PitfallCheckError, match=r"x: missing header key\(s\): id, title"):
        parse_header("\n".join(line for line in GOOD.splitlines() if not line.startswith(("# id", "# title"))), "x")
