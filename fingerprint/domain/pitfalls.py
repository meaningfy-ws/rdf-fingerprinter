"""The pitfall check header contract, the importance order and the ROBOT levels (pitfall-scans DEC-1, DEC-9, DEC-10).

Pure: the SPARQL itself is validated by the catalogue adapter (rdflib); here only the header is read.
"""

import re

from fingerprint.domain.profile import PitfallCheck, PitfallImportance, PitfallScope, ProfileRun

IMPORTANCE_ORDER = (PitfallImportance.critical, PitfallImportance.important, PitfallImportance.minor)
ROBOT_LEVELS = {"critical": "ERROR", "important": "WARN", "minor": "INFO"}  # dict-ok: module-level lookup table
REQUIRED = ("id", "title", "importance", "scope", "source")
OPTIONAL = ("heuristic", "description")
_KEY_LINE = re.compile(r"#\s*([A-Za-z_]+)\s*:(?!//)\s*(.*?)\s*$")  # `# https://…` is prose, not a key
_ID = re.compile(r"[a-z0-9_]+")


class PitfallCheckError(ValueError):
    """A check file that breaks the contract; the message names the file (its origin) and the reason."""


def parse_header(text: str, origin: str) -> PitfallCheck:
    """The check described by the leading `# key: value` lines of `text`; `#` lines without a key are prose."""
    values: dict[str, str] = {}  # dict-ok: header being parsed
    for line in (raw.strip() for raw in text.splitlines()):
        if not line:
            continue  # blank lines do not end the header
        if not line.startswith("#"):
            break
        match = _KEY_LINE.fullmatch(line)
        if not match:
            continue
        key, value = match.group(1).lower(), match.group(2)
        if key not in REQUIRED + OPTIONAL:
            raise PitfallCheckError(f"{origin}: unknown header key {key!r}")
        if key in values:
            raise PitfallCheckError(f"{origin}: header key {key!r} given twice")
        values[key] = value
    missing = [key for key in REQUIRED if not values.get(key)]
    if missing:
        raise PitfallCheckError(f"{origin}: missing header key(s): {', '.join(missing)}")
    if not _ID.fullmatch(values["id"]):
        raise PitfallCheckError(f"{origin}: id {values['id']!r} must match [a-z0-9_]+")
    if values["importance"] not in PitfallImportance.__members__:
        raise PitfallCheckError(f"{origin}: importance must be critical, important or minor, not {values['importance']!r}")
    if values["scope"] not in PitfallScope.__members__:
        raise PitfallCheckError(f"{origin}: scope must be schema or data, not {values['scope']!r}")
    heuristic = values.get("heuristic", "false").lower()
    if heuristic not in ("true", "false"):
        raise PitfallCheckError(f"{origin}: heuristic must be true or false, not {heuristic!r}")
    return PitfallCheck(
        check_id=values["id"],
        title=values["title"],
        description=values.get("description") or None,
        importance=PitfallImportance(values["importance"]),
        scope=PitfallScope(values["scope"]),
        source=values["source"],
        heuristic=heuristic == "true",
        query=text,
        origin=origin,
    )


def _name(importance: object) -> str:
    return str(getattr(importance, "value", importance))


def robot_level(importance: object) -> str:
    return ROBOT_LEVELS[_name(importance)]


def rank(importance: object) -> int:
    """0 for critical, 1 for important, 2 for minor."""
    return [i.value for i in IMPORTANCE_ORDER].index(_name(importance))


def at_or_above(run: ProfileRun, level: object) -> tuple[int, int]:
    """(rows, checks) at or above `level` over every graph: the sum of counts, and the distinct check ids."""
    results = [r for g in run.graphs or [] for r in g.pitfalls or [] if r.count and rank(r.importance) <= rank(level)]
    return sum(r.count for r in results), len({r.check_id for r in results})
