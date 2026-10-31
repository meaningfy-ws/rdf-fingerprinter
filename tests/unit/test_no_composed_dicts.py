"""Values are domain objects, never composed dicts (domain-object-model DEC-1, P-1).

Walks `fingerprint/**/*.py` and reports every dict built or typed outside the allowed forms. A
temporary count per file in `composed_dicts_allowlist.txt` holds the offenders not yet converted.
"""

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]
PACKAGE = ROOT / "fingerprint"
GENERATED = {PACKAGE / "domain" / "profile.py", PACKAGE / "domain" / "views.py"}
ALLOWLIST = Path(__file__).with_name("composed_dicts_allowlist.txt")
MARK = "# dict-ok:"
DICT_TYPES = {"dict", "Dict", "Mapping", "MutableMapping", "defaultdict", "OrderedDict", "Counter"}
DICT_CALLS = {"dict", "defaultdict", "OrderedDict", "Counter"}


def _name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _is_dict_type(annotation: ast.expr | None) -> bool:
    if isinstance(annotation, ast.Constant) and isinstance(annotation.value, str):
        annotation = ast.parse(annotation.value, mode="eval").body
    return annotation is not None and any(_name(n) in DICT_TYPES for n in ast.walk(annotation) if isinstance(n, ast.expr))


def _is_dict_call(node: ast.Call) -> bool:
    func = node.func
    if isinstance(func, ast.Attribute) and func.attr == "fromkeys" and _name(func.value) == "dict":
        return True
    return _name(func) in DICT_CALLS


def _is_table(statement: ast.stmt) -> bool:
    targets = statement.targets if isinstance(statement, ast.Assign) else [getattr(statement, "target", None)]
    return all(isinstance(t, ast.Name) and t.id.isupper() for t in targets)


class _Finder(ast.NodeVisitor):
    def __init__(self) -> None:
        self.found: list[tuple[int, int, int]] = []  # (first line, last line, line of the statement)
        self.functions = 0
        self.statement: ast.stmt | None = None
        self.exempt: set[int] = set()

    def visit(self, node: ast.AST) -> None:
        if isinstance(node, ast.stmt):
            outer, self.statement = self.statement, node
            self._visit_statement(node)
            self.statement = outer
        else:
            self._visit_expression(node)

    def _visit_statement(self, node: ast.stmt) -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            arguments = node.args
            header = (node.lineno, node.body[0].lineno - 1, node.lineno)  # the signature, however it is wrapped
            for arg in [*arguments.posonlyargs, *arguments.args, *arguments.kwonlyargs]:
                if _is_dict_type(arg.annotation):
                    self.found.append((arg.lineno, *header[1:]))
            if _is_dict_type(node.returns):
                self.found.append(header)
            self.functions += 1
            self.generic_visit(node)
            self.functions -= 1
            return
        if isinstance(node, ast.AnnAssign) and _is_dict_type(node.annotation):
            if self.functions or not _is_table(node):
                self.found.append((node.lineno, node.end_lineno or node.lineno, node.lineno))
        self.generic_visit(node)

    def _visit_expression(self, node: ast.AST) -> None:
        if isinstance(node, ast.Call):
            for keyword in node.keywords:
                if keyword.arg in (None, "update") and isinstance(keyword.value, (ast.Dict, ast.DictComp)):
                    self.exempt.add(id(keyword.value))
        builds = isinstance(node, (ast.Dict, ast.DictComp)) or (isinstance(node, ast.Call) and _is_dict_call(node))
        if builds and id(node) not in self.exempt:
            at_top = not self.functions and self.statement is not None and _is_table(self.statement)
            if not at_top and self.statement is not None:
                self.found.append((node.lineno, node.end_lineno or node.lineno, self.statement.lineno))
        self.generic_visit(node)


def offences(source: str) -> list[int]:
    """Line numbers of the composed dicts in `source`; a `# dict-ok:` mark on any line of the dict, the
    signature or the first line of the statement excepts it."""
    finder = _Finder()
    finder.visit(ast.parse(source))
    text = source.splitlines()

    def marked(first: int, last: int, statement: int) -> bool:
        return any(MARK in text[line - 1] for line in {*range(first, last + 1), statement})

    return sorted({first for first, last, statement in finder.found if not marked(first, last, statement)})


def _allowed() -> dict[str, int]:
    entries = (line.split() for line in ALLOWLIST.read_text().splitlines() if line.strip() and not line.startswith("#"))
    return {path: int(count) for path, count in entries}


def _modules() -> list[Path]:
    return sorted(p for p in PACKAGE.rglob("*.py") if p not in GENERATED)


@pytest.mark.parametrize("module", _modules(), ids=lambda p: str(p.relative_to(ROOT)))
def test_no_new_composed_dicts(module: Path):
    relative = str(module.relative_to(ROOT))
    found = offences(module.read_text())
    allowed = _allowed().get(relative, 0)
    assert len(found) <= allowed, f"{relative}: composed dicts at lines {found} (allowed {allowed}); use model objects"
    assert len(found) == allowed, f"{relative}: {len(found)} left, lower its count in {ALLOWLIST.name} to {len(found)}"


def test_the_allowlist_names_existing_files():
    assert all((ROOT / path).is_file() for path in _allowed())


@pytest.mark.parametrize(
    ("source", "lines"),
    [
        ("def f(p):\n    return {'path': p}\n", [2]),
        ("def f(p):\n    return {k: 1 for k in p}\n", [2]),
        ("def f(p):\n    return dict(a=p)\n", [2]),
        ("def f(p):\n    return dict.fromkeys(p)\n", [2]),
        ("from collections import defaultdict\ndef f():\n    return defaultdict(int)\n", [3]),
        ("def f(p: dict) -> None:\n    pass\n", [1]),
        ("def f(p) -> dict[str, int]:\n    pass\n", [1]),
        ("def f(p: 'Mapping[str, int] | None' = None):\n    pass\n", [1]),
        ("from typing import Mapping\ndef f(p: Mapping[str, int] | None = None):\n    pass\n", [2]),
        ("class A:\n    index: dict[str, int]\n", [2]),
        ("cache = {}\n", [1]),
        ("TABLE = {'a': 1}\n", []),
        ("TABLE: dict[str, int] = {'a': 1}\n", []),
        ("def f(m):\n    return m.model_copy(update={'a': 1})\n", []),
        ("def f(M):\n    return M(**{'class': 1})\n", []),
        ("def f(M, p):\n    return M(**{k: 1 for k in p})\n", []),
        ("def f(p):\n    return {'conf': p}  # dict-ok: eds4jinja2 configuration\n", []),
        ("def f(\n    p: dict,\n) -> None:  # dict-ok: 1.x API\n    pass\n", []),
        ("def f(c):\n    return {  # dict-ok: lookup index\n        k: {v: 1 for v in c}\n        for k in c\n    }\n", []),
        ("def f(c):\n    x = 1  # dict-ok: not this statement\n    return {}\n", [3]),
    ],
)
def test_the_check_finds_composed_dicts(source: str, lines: list[int]):
    assert offences(source) == lines
