"""Spec scenarios against feature scenarios and the allow-list (lean-test-suite P-3).

`trace()` returns the problems; an empty list means every spec scenario is proven.
"""

import ast
import re
from collections import Counter
from pathlib import Path
from typing import NamedTuple

from pytest_bdd.feature import get_features

SCENARIO_LINE = re.compile(r"^#### Scenario(?: Outline)?:\s*(.*?)\s*$")
REQUIREMENT_LINE = re.compile(r"^### Requirement:\s*(.*?)\s*$")
SECTION_LINE = re.compile(r"^## (ADDED|MODIFIED|REMOVED|RENAMED) Requirements\b")
RENAME_LINE = re.compile(r"^-?\s*(FROM|TO):\s*`?(?:### Requirement:)?\s*(.*?)`?\s*$")
FEATURE_SCENARIO_LINE = re.compile(r"^\s*(?:Scenario Outline|Scenario Template|Scenario|Example):\s*(.*?)\s*$")
ALLOW_LIST_FIELDS = 4


class Problem(NamedTuple):
    where: str
    message: str

    def __str__(self) -> str:
        return f"{self.where}: {self.message}"


class Requirements(NamedTuple):
    """A spec's scenario titles by requirement name, in file order (duplicates kept)."""

    by_requirement: dict[str, list[str]]  # dict-ok: parsed spec file, keyed by requirement name

    def titles(self) -> list[str]:
        return [title for titles in self.by_requirement.values() for title in titles]


def _parse_spec(path: Path, sections: tuple[str, ...] | None = None) -> dict[str, list[str]]:  # dict-ok: see Requirements
    """Requirement name -> scenario titles; with `sections`, only requirements under those `##` headings."""
    found: dict[str, list[str]] = {}  # dict-ok: see Requirements
    in_section, requirement = sections is None, None
    for line in path.read_text().splitlines():
        if section := SECTION_LINE.match(line):
            in_section, requirement = sections is None or section.group(1) in sections, None
        elif line.startswith("## "):
            in_section, requirement = sections is None, None
        elif (match := REQUIREMENT_LINE.match(line)) and in_section:
            requirement = match.group(1)
            found.setdefault(requirement, [])
        elif (match := SCENARIO_LINE.match(line)) and requirement is not None:
            found[requirement].append(match.group(1))
    return found


def _renames(path: Path) -> list[tuple[str, str]]:
    """The (FROM, TO) requirement names under `## RENAMED Requirements`, in file order."""
    names: list[str] = []
    in_section = False
    for line in path.read_text().splitlines():
        if section := SECTION_LINE.match(line):
            in_section = section.group(1) == "RENAMED"
        elif line.startswith("## "):
            in_section = False
        elif in_section and (match := RENAME_LINE.match(line)):
            names.append(match.group(2))
    return list(zip(names[0::2], names[1::2], strict=False))


def _spec_titles(base: Path, capability: str, delta_roots: tuple[Path, ...]) -> Requirements:
    """A capability's scenarios: the durable spec, then each delta (RENAMED, MODIFIED replaces, ADDED adds, REMOVED drops)."""
    spec = base / capability / "spec.md"
    requirements = _parse_spec(spec) if spec.exists() else {}
    for root in delta_roots:
        delta = root / capability / "spec.md"
        if delta.exists():
            for old, new in _renames(delta):
                requirements[new] = requirements.pop(old, [])
            requirements.update(_parse_spec(delta, ("ADDED", "MODIFIED")))
            for removed in _parse_spec(delta, ("REMOVED",)):
                requirements.pop(removed, None)
    return Requirements(requirements)


def _capabilities(specs_root: Path, features_root: Path, delta_roots: tuple[Path, ...]) -> list[str]:
    names = {p.parent.name for root in (specs_root, *delta_roots) for p in root.glob("*/spec.md")}
    names |= {p.stem.replace("_", "-") for p in features_root.glob("*.feature")}
    return sorted(names)


def _feature_titles(path: Path) -> tuple[set[str], list[str]]:
    """Titles by pytest-bdd's parser, and every title line of the file (the parser merges duplicates)."""
    titles = {s.name.strip() for feature in get_features([str(path)]) for s in feature.scenarios.values()}
    lines = [m.group(1) for line in path.read_text().splitlines() if (m := FEATURE_SCENARIO_LINE.match(line))]
    return titles, lines


def _twice(where: Path, titles: list[str]) -> list[Problem]:
    return [Problem(str(where), f"title '{t}' appears twice") for t, n in Counter(titles).items() if n > 1]


def _check_node(node: str, root: Path) -> str | None:
    """Why `node` is not `<file>::<module-level test function>`, or None when it is."""
    parts = node.split("::")
    if len(parts) != 2:
        return "not <path>::<function>"
    path, function = root / parts[0], parts[1]
    if not path.is_file():
        return f"file {parts[0]} does not exist"
    if not function.isidentifier() or not function.startswith("test"):
        return f"{function!r} is not a plain test function name"
    defined = {n.name for n in ast.parse(path.read_text()).body if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef)}
    return None if function in defined else f"{parts[0]} defines no module-level function {function}"


def _allow_list(
    path: Path, known: dict[str, set[str]], root: Path
) -> tuple[set[tuple[str, str]], list[Problem]]:  # dict-ok: capability -> titles lookup
    entries: set[tuple[str, str]] = set()
    problems: list[Problem] = []
    for number, raw in enumerate(path.read_text().splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        where = f"{path.name}:{number}"
        fields = [f.strip() for f in line.split("|")]
        if len(fields) != ALLOW_LIST_FIELDS:
            problems.append(Problem(where, f"malformed entry, expected {ALLOW_LIST_FIELDS} '|'-separated fields: {line}"))
            continue
        capability, title, node, _reason = fields
        if title not in known.get(capability, set()):
            problems.append(Problem(where, f"names no scenario '{title}' in capability {capability}"))
        elif reason := _check_node(node, root):
            problems.append(Problem(where, f"scenario '{title}' names {node}: {reason}"))
        else:
            entries.add((capability, title))
    return entries, problems


def trace(
    specs_root: Path,
    features_root: Path,
    allow_list_path: Path,
    delta_roots: tuple[Path, ...] = (),
    root: Path | None = None,
) -> list[Problem]:
    """Every problem found; `root` resolves the allow-list's node ids (default: the repo root)."""
    root = root or allow_list_path.parents[2]
    specs = {
        c: _spec_titles(specs_root, c, delta_roots) for c in _capabilities(specs_root, features_root, delta_roots)
    }  # dict-ok: capability -> parsed spec
    allowed, problems = _allow_list(allow_list_path, {c: set(r.titles()) for c, r in specs.items()}, root)
    for capability, requirements in specs.items():
        spec_titles = requirements.titles()
        problems += _twice(specs_root / capability / "spec.md", spec_titles)
        feature = features_root / f"{capability.replace('-', '_')}.feature"
        feature_titles, feature_lines = _feature_titles(feature) if feature.exists() else (set(), [])
        problems += _twice(feature, feature_lines)
        for title in dict.fromkeys(spec_titles):
            if title not in feature_titles and (capability, title) not in allowed:
                problems.append(Problem(capability, f"spec scenario '{title}' has no feature scenario or allow-list entry"))
        problems += [
            Problem(str(feature), f"feature scenario '{t}' is in no spec scenario of {capability}")
            for t in sorted(feature_titles - set(spec_titles))
        ]
    return problems
