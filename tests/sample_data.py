"""Facts about the canonical sample datasets and the comparison of profiles (lean-test-suite P-5).

The facts are typed in by hand from `tests/test_data/*-source-ap.rdf`, so they are an expectation
independent of the stored sample profile; `tests/guards/test_sample_data.py` checks the two agree.
"""

import json
from dataclasses import dataclass
from pathlib import Path

from fingerprint.domain.profile import ProfileRun

TEST_DATA = Path(__file__).parent / "test_data"
SAMPLE_PROFILE = TEST_DATA / "profiles" / "sample-profile.json"
GOLDEN = TEST_DATA / "golden"
GRAPH_BASE = "http://publications.europa.eu/resources/authority/"
EUVOC = "http://publications.europa.eu/ontology/euvoc#"
SKOS = "http://www.w3.org/2004/02/skos/core#"
SKOSXL = "http://www.w3.org/2008/05/skos-xl#"
OWL = "http://www.w3.org/2002/07/owl#"
RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
RDFS = "http://www.w3.org/2000/01/rdf-schema#"
DCT = "http://purl.org/dc/terms/"
LEXVO = "http://lexvo.org/ontology#"
VBAP = "http://publications.europa.eu/ontology/vbap#"


@dataclass(frozen=True)
class PropertyFact:
    iri: str
    min: int
    max: int


@dataclass(frozen=True)
class ClassFact:
    iri: str
    instances: int
    properties: tuple[PropertyFact, ...]


@dataclass(frozen=True)
class DatasetFacts:
    """`graphs`: the graphs the dataset is loaded into (None is the default graph)."""

    name: str
    graphs: tuple[str | None, ...]
    classes: tuple[ClassFact, ...]


CONTINENTS = DatasetFacts(
    "continents",
    (None, GRAPH_BASE + "continents"),
    (
        ClassFact(
            EUVOC + "Continent",
            6,
            (
                PropertyFact(EUVOC + "startDate", 1, 1),
                PropertyFact(EUVOC + "status", 1, 1),
                PropertyFact(EUVOC + "xlNotation", 1, 1),
                PropertyFact(DCT + "created", 1, 1),
                PropertyFact(SKOS + "inScheme", 1, 1),
                PropertyFact(SKOS + "topConceptOf", 1, 1),
                PropertyFact(SKOSXL + "prefLabel", 24, 24),
            ),
        ),
        ClassFact(
            EUVOC + "XlNotation",
            6,
            (
                PropertyFact(EUVOC + "startDate", 1, 1),
                PropertyFact(EUVOC + "status", 1, 1),
                PropertyFact(DCT + "created", 1, 1),
                PropertyFact(DCT + "type", 1, 1),
                PropertyFact(RDF + "value", 1, 1),
            ),
        ),
        ClassFact(
            OWL + "Ontology",
            1,
            (
                PropertyFact(EUVOC + "startDate", 1, 1),
                PropertyFact(EUVOC + "status", 1, 1),
                PropertyFact(DCT + "created", 1, 1),
                PropertyFact(DCT + "identifier", 1, 1),
                PropertyFact(RDFS + "comment", 1, 1),
                PropertyFact(OWL + "imports", 1, 1),
                PropertyFact(SKOSXL + "prefLabel", 1, 1),
            ),
        ),
        ClassFact(
            SKOS + "Concept",
            6,
            (
                PropertyFact(EUVOC + "startDate", 1, 1),
                PropertyFact(EUVOC + "status", 1, 1),
                PropertyFact(EUVOC + "xlNotation", 1, 1),
                PropertyFact(DCT + "created", 1, 1),
                PropertyFact(SKOS + "inScheme", 1, 1),
                PropertyFact(SKOS + "topConceptOf", 1, 1),
                PropertyFact(SKOSXL + "prefLabel", 24, 24),
            ),
        ),
        ClassFact(
            SKOS + "ConceptScheme",
            1,
            (
                PropertyFact(EUVOC + "startDate", 1, 1),
                PropertyFact(EUVOC + "status", 1, 1),
                PropertyFact(DCT + "created", 1, 1),
                PropertyFact(DCT + "identifier", 1, 1),
                PropertyFact(RDFS + "comment", 1, 1),
                PropertyFact(OWL + "imports", 1, 1),
                PropertyFact(SKOSXL + "prefLabel", 1, 1),
            ),
        ),
        ClassFact(
            SKOSXL + "Label",
            145,
            (
                PropertyFact(LEXVO + "script", 0, 1),
                PropertyFact(EUVOC + "startDate", 1, 1),
                PropertyFact(EUVOC + "status", 1, 1),
                PropertyFact(DCT + "created", 1, 1),
                PropertyFact(DCT + "type", 1, 1),
                PropertyFact(SKOSXL + "literalForm", 1, 1),
            ),
        ),
    ),
)

TREATIES = DatasetFacts(
    "treaties",
    (GRAPH_BASE + "treaties",),
    (
        ClassFact(
            EUVOC + "Treaty",
            104,
            (
                PropertyFact("http://data.europa.eu/eli/ontology#date_document", 0, 1),
                PropertyFact("http://data.europa.eu/eli/ontology#first_date_entry_in_force", 0, 1),
                PropertyFact("http://lemon-model.net/lemon#context", 1, 2),
                PropertyFact(EUVOC + "endDate", 0, 1),
                PropertyFact(EUVOC + "officialJournalDate", 0, 1),
                PropertyFact(EUVOC + "officialJournalNumber", 0, 1),
                PropertyFact(EUVOC + "officialJournalSeries", 0, 1),
                PropertyFact(EUVOC + "signatureLocation", 0, 2),
                PropertyFact(EUVOC + "startDate", 1, 1),
                PropertyFact(EUVOC + "status", 1, 1),
                PropertyFact(EUVOC + "xlChangeNote", 0, 1),
                PropertyFact(EUVOC + "xlDefinition", 0, 2),
                PropertyFact(EUVOC + "xlHistoryNote", 0, 1),
                PropertyFact(EUVOC + "xlNotation", 1, 6),
                PropertyFact(DCT + "created", 1, 1),
                PropertyFact(DCT + "dateAccepted", 1, 1),
                PropertyFact(DCT + "dateSubmitted", 1, 1),
                PropertyFact(DCT + "isReplacedBy", 0, 1),
                PropertyFact(DCT + "replaces", 0, 1),
                PropertyFact(DCT + "type", 1, 1),
                PropertyFact(SKOS + "inScheme", 1, 1),
                PropertyFact(SKOS + "topConceptOf", 1, 1),
                PropertyFact(SKOSXL + "altLabel", 0, 74),
                PropertyFact(SKOSXL + "prefLabel", 23, 24),
            ),
        ),
        ClassFact(
            EUVOC + "XlNotation",
            357,
            (
                PropertyFact(EUVOC + "endDate", 0, 1),
                PropertyFact(EUVOC + "startDate", 0, 1),
                PropertyFact(EUVOC + "status", 0, 1),
                PropertyFact(DCT + "created", 0, 1),
                PropertyFact(DCT + "type", 1, 1),
                PropertyFact(RDF + "value", 1, 1),
            ),
        ),
        ClassFact(
            EUVOC + "XlNote",
            12,
            (
                PropertyFact(EUVOC + "startDate", 1, 1),
                PropertyFact(EUVOC + "status", 1, 1),
                PropertyFact(DCT + "created", 1, 1),
                PropertyFact(DCT + "source", 0, 1),
                PropertyFact(RDF + "value", 1, 1),
            ),
        ),
        ClassFact(
            OWL + "Ontology",
            1,
            (
                PropertyFact(EUVOC + "startDate", 1, 1),
                PropertyFact(EUVOC + "status", 1, 1),
                PropertyFact(DCT + "created", 1, 1),
                PropertyFact(DCT + "identifier", 1, 1),
                PropertyFact(RDFS + "comment", 1, 1),
                PropertyFact(OWL + "imports", 2, 2),
                PropertyFact(SKOSXL + "prefLabel", 1, 1),
            ),
        ),
        ClassFact(
            SKOS + "Concept",
            104,
            (
                PropertyFact("http://data.europa.eu/eli/ontology#date_document", 0, 1),
                PropertyFact("http://data.europa.eu/eli/ontology#first_date_entry_in_force", 0, 1),
                PropertyFact("http://lemon-model.net/lemon#context", 1, 2),
                PropertyFact(EUVOC + "endDate", 0, 1),
                PropertyFact(EUVOC + "officialJournalDate", 0, 1),
                PropertyFact(EUVOC + "officialJournalNumber", 0, 1),
                PropertyFact(EUVOC + "officialJournalSeries", 0, 1),
                PropertyFact(EUVOC + "signatureLocation", 0, 2),
                PropertyFact(EUVOC + "startDate", 1, 1),
                PropertyFact(EUVOC + "status", 1, 1),
                PropertyFact(EUVOC + "xlChangeNote", 0, 1),
                PropertyFact(EUVOC + "xlDefinition", 0, 2),
                PropertyFact(EUVOC + "xlHistoryNote", 0, 1),
                PropertyFact(EUVOC + "xlNotation", 1, 6),
                PropertyFact(DCT + "created", 1, 1),
                PropertyFact(DCT + "dateAccepted", 1, 1),
                PropertyFact(DCT + "dateSubmitted", 1, 1),
                PropertyFact(DCT + "isReplacedBy", 0, 1),
                PropertyFact(DCT + "replaces", 0, 1),
                PropertyFact(DCT + "type", 1, 1),
                PropertyFact(SKOS + "inScheme", 1, 1),
                PropertyFact(SKOS + "topConceptOf", 1, 1),
                PropertyFact(SKOSXL + "altLabel", 0, 74),
                PropertyFact(SKOSXL + "prefLabel", 23, 24),
            ),
        ),
        ClassFact(
            SKOS + "ConceptScheme",
            1,
            (
                PropertyFact(EUVOC + "startDate", 1, 1),
                PropertyFact(EUVOC + "status", 1, 1),
                PropertyFact(DCT + "created", 1, 1),
                PropertyFact(DCT + "identifier", 1, 1),
                PropertyFact(RDFS + "comment", 1, 1),
                PropertyFact(OWL + "imports", 2, 2),
                PropertyFact(SKOSXL + "prefLabel", 1, 1),
            ),
        ),
        ClassFact(
            SKOSXL + "Label",
            4530,
            (
                PropertyFact(LEXVO + "script", 0, 1),
                PropertyFact(EUVOC + "endDate", 0, 1),
                PropertyFact(EUVOC + "startDate", 0, 1),
                PropertyFact(EUVOC + "status", 1, 1),
                PropertyFact(DCT + "created", 0, 1),
                PropertyFact(DCT + "type", 1, 1),
                PropertyFact(SKOSXL + "literalForm", 1, 1),
            ),
        ),
    ),
)


# --- comparing two profile runs, ignoring what varies between runs (DEC-5) ---

VARYING = {"started_at", "finished_at", "tool_version"}
# The nested lists of a run, outermost first: (list name, the key that identifies a row, its label).
LEVELS = (
    ("graphs", "graph", "graph"),
    ("class_partitions", "class_iri", "class"),
    ("property_partitions", "property", "property"),
)


def same_profile(a: ProfileRun, b: ProfileRun) -> bool:
    """True when the runs differ at most in timestamps, tool version and row order."""
    return not differences(a, b)


def differences(stored: ProfileRun, fresh: ProfileRun) -> list[str]:
    """One line per graph, class, property or setting that differs, each naming where."""
    return _node_differences("run", _dump(stored), _dump(fresh), LEVELS)


def _dump(run: ProfileRun):
    return run.model_dump(mode="json", exclude_none=True, exclude=VARYING)  # dict-ok: comparing JSON dumps


def _fields(node, skip, prefix=""):
    """(dotted name, value) of the node's own fields: nested objects such as settings are flattened."""
    for key, value in node.items():
        if isinstance(value, dict):
            yield from _fields(value, (), f"{prefix}{key}.")
        elif key not in skip:
            yield prefix + key, value


def _node_differences(label: str, stored, fresh, levels) -> list[str]:  # dict-ok: JSON dumps
    child_list = levels[0][0] if levels else None
    own_stored = dict(_fields(stored, (child_list,)))  # dict-ok: JSON dumps
    own_fresh = dict(_fields(fresh, (child_list,)))  # dict-ok: JSON dumps
    found = [
        f"{label}: {key} differs ({_short(own_stored.get(key))} stored, {_short(own_fresh.get(key))} fresh)"
        for key in sorted(own_stored.keys() | own_fresh.keys())
        if _ordered(own_stored.get(key)) != _ordered(own_fresh.get(key))
    ]
    if levels:
        found += _child_differences(label, stored.get(child_list, []), fresh.get(child_list, []), levels)
    return found


def _child_differences(label: str, stored, fresh, levels) -> list[str]:
    _, identity, noun = levels[0]
    stored, fresh = _by(identity, stored), _by(identity, fresh)
    found = []
    for key in sorted(stored.keys() | fresh.keys(), key=str):
        name = "default" if key is None else key
        if key not in fresh or key not in stored:
            side = "stored" if key in stored else "fresh"
            found.append(f"{label}: {noun} {name} only in the {side} profile")
        else:
            prefix = "" if label == "run" else label + " "
            found += _node_differences(f"{prefix}{noun} {name}", stored[key], fresh[key], levels[1:])
    return found


def _by(identity: str, rows):
    return {row.get(identity): row for row in rows}  # dict-ok: JSON dumps


def _ordered(value):
    """Lists sorted by their JSON text: stores may return rows in any order."""
    if isinstance(value, dict):
        return {key: _ordered(item) for key, item in value.items()}  # dict-ok: comparing JSON dumps
    if isinstance(value, list):
        return sorted((_ordered(item) for item in value), key=lambda item: json.dumps(item, sort_keys=True))
    return value


def _short(value) -> str:
    text = repr(value)
    return text if len(text) <= 60 else text[:57] + "..."
