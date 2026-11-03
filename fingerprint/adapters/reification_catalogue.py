"""The reification template catalogue: packaged `.rq` files split into sections (singleton-property-pattern P-1, P-2).

A file is a header (`# id:`, `# title:`, `# family:`) and sections, each opened by a `# REIFY <kind> <section>` line.
Every section is filled for the default graph and parsed with rdflib here, before any query runs.
"""

import functools
import re
from importlib.resources import files

from rdflib.plugins.sparql import prepareQuery

from fingerprint.adapters.queries import reification_query
from fingerprint.domain.profile import ReificationKind, ReificationTemplate

# section name -> (query form, projected variables); an ASK projects none
SECTIONS = {
    "probe": ("AskQuery", ()),
    "relations": ("SelectQuery", ("subjectClass", "predicate", "objectClass", "statements")),
    "reifier-properties": ("SelectQuery", ("subjectClass", "predicate", "objectClass", "reifierProperty", "reifiers")),
    "hidden": ("SelectQuery", ("term",)),
    "count": ("SelectQuery", ("count",)),
}  # dict-ok: module-level lookup table
HEADER_KEYS = ("id", "title", "family")
_SECTION_LINE = re.compile(r"#\s*REIFY\s+(\S+)\s+(\S+)\s*")
_KEY_LINE = re.compile(r"#\s*(\w+)\s*:\s*(.*?)\s*")


class ReificationTemplateError(ValueError):
    """A template file that breaks the contract; the message names the file (its origin) and the reason."""


def _split(text: str, origin: str) -> tuple[dict[str, str], dict[str, str]]:  # dict-ok: file being parsed
    """(header values, section texts by name); each section text keeps its `# REIFY` line, the query's name."""
    header: dict[str, str] = {}  # dict-ok: file being parsed
    chunks: dict[str, list[str]] = {}  # dict-ok: file being parsed
    current: list[str] | None = None
    kinds: set[str] = set()
    for line in text.splitlines():
        marker = _SECTION_LINE.fullmatch(line.strip())
        if marker:
            kind, name = marker.groups()
            kinds.add(kind)
            if name not in SECTIONS:
                raise ReificationTemplateError(f"{origin}: unknown section {name!r} (known: {', '.join(SECTIONS)})")
            if name in chunks:
                raise ReificationTemplateError(f"{origin}: section {name!r} given twice")
            current = chunks[name] = []
        if current is not None:
            current.append(line)
        elif (key := _KEY_LINE.fullmatch(line.strip())) and key.group(1) in HEADER_KEYS:
            header[key.group(1)] = key.group(2)
    missing = [key for key in HEADER_KEYS if not header.get(key)]
    if missing:
        raise ReificationTemplateError(f"{origin}: missing header key(s): {', '.join(missing)}")
    if header["id"] not in ReificationKind._value2member_map_:
        raise ReificationTemplateError(f"{origin}: id {header['id']!r} is not a reification kind")
    if kinds - {header["id"]}:
        raise ReificationTemplateError(f"{origin}: the kind in a `# REIFY` line must equal the id {header['id']!r}")
    return header, {name: "\n".join(lines).strip() + "\n" for name, lines in chunks.items()}  # dict-ok: file being parsed


def _validate_section(template: ReificationTemplate, name: str, origin: str) -> None:
    form, variables = SECTIONS[name]
    try:
        algebra = prepareQuery(reification_query(template, name, None)).algebra
    except (KeyError, ValueError) as error:
        raise ReificationTemplateError(f"{origin}: {name}: unknown placeholder or stray $: {error}") from error
    except Exception as error:  # rdflib raises pyparsing errors and others for bad SPARQL
        raise ReificationTemplateError(f"{origin}: {name}: not a SPARQL query: {error}") from error
    if algebra.name != form:
        raise ReificationTemplateError(f"{origin}: {name} must be {'an ASK' if form == 'AskQuery' else 'a SELECT'} query")
    if algebra.get("datasetClause"):
        raise ReificationTemplateError(f"{origin}: {name} must have no FROM clause (the collector sets the graph)")
    projected = {str(v) for v in algebra.get("PV") or []}
    if form == "SelectQuery" and projected != set(variables):
        wanted = " ".join(f"?{v}" for v in variables)
        raise ReificationTemplateError(f"{origin}: {name} must select exactly {wanted}, not {' '.join(sorted(projected))}")


def validate(text: str, origin: str) -> ReificationTemplate:
    """The template in `text`, or ReificationTemplateError naming `origin`."""
    header, sections = _split(text, origin)
    if "probe" not in sections:
        raise ReificationTemplateError(f"{origin}: no probe section")
    template = ReificationTemplate(
        id=header["id"],
        title=header["title"],
        family=header["family"],
        probe=sections["probe"],
        relations=sections.get("relations"),
        reifier_properties=sections.get("reifier-properties"),
        hidden=sections.get("hidden"),
        count=sections.get("count"),
    )
    for name in sections:
        _validate_section(template, name, origin)
    return template


@functools.cache
def _packaged() -> tuple[ReificationTemplate, ...]:
    folder = files("fingerprint.adapters.queries") / "reifications"
    entries = sorted((f for f in folder.iterdir() if f.name.endswith(".rq")), key=lambda f: f.name)
    return tuple(validate(f.read_text(), f.name) for f in entries)


def packaged_templates() -> list[ReificationTemplate]:
    """The packaged templates, parsed once per process."""
    return list(_packaged())
