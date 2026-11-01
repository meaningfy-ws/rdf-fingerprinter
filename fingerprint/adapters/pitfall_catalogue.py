"""The pitfall check catalogue: the packaged SPARQL files plus the user's (pitfall-scans DEC-1, DEC-7, DEC-8).

Every check is parsed here, before any query: it must be one SELECT of exactly ?entity ?property ?value, with no
dataset clause, so the scan stays read-only whatever the user supplies.
"""

import functools
from collections.abc import Iterable
from importlib.resources import files
from pathlib import Path

from rdflib.plugins.sparql import prepareQuery

from fingerprint.domain.pitfalls import PitfallCheckError, parse_header
from fingerprint.domain.profile import PitfallCheck

VARIABLES = {"entity", "property", "value"}


def validate(text: str, origin: str) -> PitfallCheck:
    """The check in `text`, or PitfallCheckError naming `origin`."""
    check = parse_header(text, origin)
    try:
        prepared = prepareQuery(text)
    except Exception as error:  # rdflib raises pyparsing errors and others for bad SPARQL
        raise PitfallCheckError(f"{origin}: not a SPARQL query: {error}") from error
    algebra = prepared.algebra
    if algebra.name != "SelectQuery":
        raise PitfallCheckError(f"{origin}: must be a SELECT query, not {algebra.name}")
    if algebra.get("datasetClause"):
        raise PitfallCheckError(f"{origin}: must have no FROM / FROM NAMED clause (the scan sets the dataset)")
    projected = {str(v) for v in algebra.get("PV") or []}
    if projected != VARIABLES:
        raise PitfallCheckError(f"{origin}: must select ?entity ?property ?value, not {' '.join(sorted(projected))}")
    return check


@functools.cache
def _packaged() -> tuple[PitfallCheck, ...]:
    folder = files("fingerprint.adapters.queries") / "pitfalls"
    entries = sorted((f for f in folder.iterdir() if f.name.endswith(".rq")), key=lambda f: f.name)
    return tuple(validate(f.read_text(), "packaged") for f in entries)


def packaged_checks() -> list[PitfallCheck]:
    """The packaged catalogue, parsed once per process."""
    return list(_packaged())


def load_catalogue(user_dir: str | Path | None = None, skip: Iterable[str] = ()) -> list[PitfallCheck]:
    """Packaged checks, then the user's `.rq` files (a user id equal to a packaged one replaces it), minus `skip`."""
    checks = {c.check_id: c for c in packaged_checks()}  # dict-ok: lookup index id → check
    if user_dir is not None:
        folder = Path(user_dir)
        if not folder.is_dir():
            raise PitfallCheckError(f"--pitfall-checks {folder}: not a directory")
        seen: set[str] = set()
        for path in sorted(folder.glob("*.rq")):
            check = validate(path.read_text(), str(path))
            if check.check_id in seen:
                raise PitfallCheckError(f"{path}: id {check.check_id!r} is used by another user check")
            seen.add(check.check_id)
            checks[check.check_id] = check
    unknown = sorted(set(skip) - checks.keys())
    if unknown:
        raise PitfallCheckError(f"--skip-pitfall: unknown check(s) {', '.join(unknown)} (known: {', '.join(sorted(checks))})")
    return [c for c_id, c in sorted(checks.items()) if c_id not in set(skip)]
