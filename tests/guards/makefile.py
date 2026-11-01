"""Read the repository's Makefile, so a guard follows an edit of a recipe instead of copying it."""

import re
import shlex
from pathlib import Path

MAKEFILE = Path(__file__).parents[2] / "Makefile"


def recipe(target: str) -> tuple[list[str], str]:
    """The prerequisites and the recipe text of a Makefile target."""
    match = re.search(rf"^{re.escape(target)}:([^\n#]*)(?:##[^\n]*)?\n((?:\t[^\n]*\n)*)", MAKEFILE.read_text(), re.MULTILINE)
    assert match, f"Makefile has no target {target}"
    return match.group(1).split(), match.group(2)


def command_args(target: str, command: str) -> list[str]:
    """The arguments given to `command` (e.g. `coverage report`) in the target's recipe, as the shell splits them."""
    lines = [line for line in recipe(target)[1].splitlines() if f" {command} " in f" {line} "]
    assert len(lines) == 1, f"expected one `{command}` line in {target}, found {len(lines)}"
    words = shlex.split(lines[0])
    return words[words.index(command.split()[-1]) + 1 :]
