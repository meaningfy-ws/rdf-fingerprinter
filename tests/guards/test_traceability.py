"""Every spec scenario is proven by a titled feature scenario or an allow-listed test (lean-test-suite P-3, TC-1..TC-3)."""

from pathlib import Path

import pytest

from tests.guards.traceability import trace

ROOT = Path(__file__).parents[2]
CAP = "fingerprint-report"


def spec(*titles: str, requirement: str = "R") -> str:
    scenarios = "".join(f"\n#### Scenario: {t}\n- **WHEN** x\n" for t in titles)
    return f"## Requirements\n### Requirement: {requirement}\nThe thing SHALL work.\n{scenarios}"


def feature(*titles: str, keyword: str = "Scenario") -> str:
    body = "".join(f"  {keyword}: {t}\n    Given a step\n" for t in titles)
    return f"Feature: F\n{body}"


class Tree:
    """A small repo under tmp_path: specs, features, allow-list and a test module the entries may name."""

    def __init__(self, root: Path):
        self.root = root
        self.specs = root / "openspec" / "specs"
        self.features = root / "tests" / "features"
        self.allow = root / "tests" / "guards" / "untraced_scenarios.txt"
        self.features.mkdir(parents=True)
        self.allow.parent.mkdir(parents=True)
        self.allow.write_text("")
        (root / "tests" / "guards" / "test_proof.py").write_text(
            "def test_proof():\n    pass\n\n\nclass TestK:\n    def test_method(self):\n        pass\n"
        )

    def add_spec(self, cap: str, text: str, base: Path | None = None) -> None:
        path = (base or self.specs) / cap / "spec.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def add_feature(self, cap: str, text: str) -> None:
        (self.features / f"{cap.replace('-', '_')}.feature").write_text(text)

    def allow_list(self, *lines: str) -> None:
        self.allow.write_text("\n".join(lines) + "\n")

    def trace(self, delta_roots: tuple[Path, ...] = ()) -> list[str]:
        return [str(p) for p in trace(self.specs, self.features, self.allow, delta_roots=delta_roots, root=self.root)]


@pytest.fixture
def tree(tmp_path):
    return Tree(tmp_path)


PROOF = "tests/guards/test_proof.py::test_proof"


def entry(title: str = "X", node: str = PROOF, cap: str = CAP, reason: str = "why") -> str:
    return f"{cap} | {title} | {node} | {reason}"


# TC-1: a spec scenario with no test


def test_a_traced_spec_scenario_is_clean(tree):
    tree.add_spec(CAP, spec("X"))
    tree.add_feature(CAP, feature("X"))
    assert tree.trace() == []


def test_a_spec_scenario_without_a_feature_scenario_names_the_capability_and_title(tree):
    tree.add_spec(CAP, spec("X"))
    tree.add_feature(CAP, feature("Y"))
    problems = [p for p in tree.trace() if "'X'" in p]
    assert len(problems) == 1
    assert CAP in problems[0]


@pytest.mark.parametrize("keyword", ["Scenario Outline", "Scenario Template", "Example"])
def test_every_scenario_keyword_traces_a_spec_scenario(tree, keyword):
    tree.add_spec(CAP, spec("X"))
    tree.add_feature(CAP, feature("X", keyword=keyword))
    assert tree.trace() == []


def test_a_spec_scenario_outline_is_traced(tree):
    tree.add_spec(CAP, spec("X").replace("#### Scenario: X", "#### Scenario Outline: X"))
    tree.add_feature(CAP, feature("X", keyword="Scenario Outline"))
    assert tree.trace() == []


def test_a_scenario_inside_a_rule_block_is_traced(tree):
    tree.add_spec(CAP, spec("X"))
    tree.add_feature(CAP, "Feature: F\n  Rule: R\n    Scenario: X\n      Given a\n")
    assert tree.trace() == []


def test_trailing_spaces_in_titles_are_ignored(tree):
    tree.add_spec(CAP, "### Requirement: R\n#### Scenario: X   \n")
    tree.add_feature(CAP, "Feature: F\n  Scenario: X  \n    Given a\n")
    assert tree.trace() == []


def test_a_capability_without_a_feature_file_needs_every_scenario_allow_listed(tree):
    tree.add_spec(CAP, spec("X", "Z"))
    tree.allow_list(entry("X"))
    problems = tree.trace()
    assert len(problems) == 1
    assert "'Z'" in problems[0]


def test_an_allow_listed_scenario_needs_no_feature_scenario(tree):
    tree.add_spec(CAP, spec("X"))
    tree.add_feature(CAP, feature("Other"))
    tree.allow_list(entry("X"))
    assert [p for p in tree.trace() if "'X'" in p] == []


# TC-2: an orphan feature scenario


def test_an_orphan_feature_scenario_names_the_feature_file_and_title(tree):
    tree.add_spec(CAP, spec("X"))
    tree.add_feature(CAP, feature("X", "Y"))
    problems = tree.trace()
    assert len(problems) == 1
    assert "fingerprint_report.feature" in problems[0]
    assert "'Y'" in problems[0]


def test_the_same_title_in_two_capabilities_is_checked_per_capability(tree):
    tree.add_spec("cap-a", spec("Shared"))
    tree.add_spec("cap-b", spec("Other"))
    tree.add_feature("cap-a", feature("Shared"))
    tree.add_feature("cap-b", feature("Shared", "Other"))
    problems = tree.trace()
    assert len(problems) == 1
    assert "cap_b.feature" in problems[0]
    assert "'Shared'" in problems[0]


def test_a_feature_file_of_no_capability_is_all_orphans(tree):
    tree.add_feature("ghost", feature("Y"))
    problems = tree.trace()
    assert len(problems) == 1
    assert "ghost.feature" in problems[0]


# duplicates (problem 3)


def test_a_duplicate_title_in_one_spec_is_a_problem(tree):
    tree.add_spec(CAP, spec("X", "X"))
    tree.add_feature(CAP, feature("X"))
    problems = tree.trace()
    assert len(problems) == 1
    assert "twice" in problems[0] and "spec.md" in problems[0]


def test_a_duplicate_title_in_one_feature_file_is_a_problem(tree):
    tree.add_spec(CAP, spec("X"))
    tree.add_feature(CAP, feature("X", "X"))
    problems = tree.trace()
    assert len(problems) == 1
    assert "twice" in problems[0] and "fingerprint_report.feature" in problems[0]


# TC-3: the allow-list (problem 4)


def test_an_entry_naming_a_missing_function_names_the_entry(tree):
    tree.add_spec(CAP, spec("X"))
    tree.allow_list(entry("X", "tests/guards/test_proof.py::test_missing"))
    problems = tree.trace()
    assert any("test_missing" in p and "untraced_scenarios.txt" in p for p in problems)


@pytest.mark.parametrize(
    "node",
    [
        "tests/guards/test_proof.py::TestK::test_method",
        "tests/guards/test_proof.py::test_proof[a]",
        "tests/guards/test_nofile.py::test_proof",
        "tests/guards/test_proof.py",
        "tests/guards/test_proof.py::helper",
    ],
)
def test_an_entry_must_name_a_plain_module_level_test_function(tree, node):
    tree.add_spec(CAP, spec("X"))
    tree.allow_list(entry("X", node))
    assert any(node in p and "untraced_scenarios.txt:1" in p for p in tree.trace())


def test_an_entry_naming_a_missing_scenario_is_a_problem(tree):
    tree.add_spec(CAP, spec("X"))
    tree.add_feature(CAP, feature("X"))
    tree.allow_list(entry("Gone"))
    problems = tree.trace()
    assert len(problems) == 1
    assert "'Gone'" in problems[0]


def test_a_three_field_line_is_malformed(tree):
    tree.add_spec(CAP, spec("X"))
    tree.add_feature(CAP, feature("X"))
    tree.allow_list(f"{CAP} | X | {PROOF}")
    problems = tree.trace()
    assert len(problems) == 1
    assert "malformed" in problems[0]


def test_comments_and_blank_lines_are_skipped(tree):
    tree.add_spec(CAP, spec("X"))
    tree.allow_list("# a comment", "", entry("X"))
    assert tree.trace() == []


# spec deltas of the change in flight


def delta_root(tree):
    return tree.root / "openspec" / "changes" / "c" / "specs"


def test_an_added_delta_scenario_must_be_traced(tree):
    tree.add_spec(CAP, spec("X"))
    tree.add_feature(CAP, feature("X"))
    tree.add_spec(CAP, "## ADDED Requirements\n### Requirement: N\n#### Scenario: New\n", delta_root(tree))
    problems = tree.trace((delta_root(tree),))
    assert len(problems) == 1
    assert "'New'" in problems[0]


def test_an_added_delta_scenario_is_traced_by_a_feature_scenario(tree):
    tree.add_spec(CAP, spec("X"))
    tree.add_feature(CAP, feature("X", "New"))
    tree.add_spec(CAP, "## ADDED Requirements\n### Requirement: N\n#### Scenario: New\n", delta_root(tree))
    assert tree.trace((delta_root(tree),)) == []


def test_a_modified_requirement_replaces_its_base_scenarios(tree):
    tree.add_spec(CAP, spec("Old", "Keep", requirement="R") + "### Requirement: S\n#### Scenario: Other\n")
    tree.add_feature(CAP, feature("Renamed", "Other"))
    tree.add_spec(CAP, "## MODIFIED Requirements\n### Requirement: R\n#### Scenario: Renamed\n", delta_root(tree))
    assert tree.trace((delta_root(tree),)) == []


def test_a_delta_for_a_new_capability_is_traced(tree):
    tree.add_spec("fresh", "## ADDED Requirements\n### Requirement: N\n#### Scenario: New\n", delta_root(tree))
    problems = tree.trace((delta_root(tree),))
    assert len(problems) == 1
    assert "fresh" in problems[0] and "'New'" in problems[0]


# the real tree


def test_every_spec_scenario_is_traced():
    # Only planned changes (a tasks.md exists) count; a bare proposal promises no tests yet.
    changes = ROOT / "openspec" / "changes"
    deltas = tuple(sorted(d for d in changes.glob("*/specs") if (d.parent / "tasks.md").exists()))
    problems = trace(
        ROOT / "openspec" / "specs",
        ROOT / "tests" / "features",
        ROOT / "tests" / "guards" / "untraced_scenarios.txt",
        delta_roots=deltas,
        root=ROOT,
    )
    assert not problems, "\n" + "\n".join(f"  {p}" for p in problems)
