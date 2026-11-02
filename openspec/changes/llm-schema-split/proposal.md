# EPIC: Split the pattern schema into prefixes, patterns and glossary files, each searchable

## Appetite

**MEDIUM.** One capability, the pattern output, is reshaped into five files with two CSV indexes;
its neighbour `statistics-collection` is touched lightly (the term-annotation query asks for more
predicates and the profile keeps alt labels and notes). It is not SMALL: it adds new outputs and
a model change. It is not LARGE: no boundary moves and the pattern view stays the single source.

**Golden-thread parents:**
- Archived change `2026-11-02-llm-schema-tools`: DEC-13 (arrow notation, glossary below the
  patterns), DEC-16 (prefixed names), DEC-17 and DEC-20 (one description, the label predicates),
  DEC-18 (one view rendered several ways).
- Living specs: `openspec/specs/profile-representations/spec.md` ("Pattern view", "Pattern schema
  output", "Term labels and descriptions in the outputs") and
  `openspec/specs/statistics-collection/spec.md` ("Term labels and descriptions are collected").

**Seeds** (secondary, never groomed): `inputs/qa-round-1.md` — the developer's request and the
answers of rounds 1 and 2.

## Why

The 3.2 pattern schema is one `.txt` per graph: prefixes, legend, class blocks and glossary
together. An agent or a tool that wants only part of it — the glossary entry of one term, the
edges of one class, the prefixes — must read the whole file and parse a compact notation. Split
files, each with a CSV index that holds the facts as rows, let a tool `grep`, filter or load
(DuckDB, pandas) exactly the part it needs, and let a caller choose which parts go into a prompt.

## Solution outline

`fingerprint-gen-pattern` (and `fingerprint --format pattern`) writes, per graph with a block,
five files instead of `pattern-<slug>.txt`. All are rendered from the one pattern view; no fact is
computed twice, and every file names terms by the same prefixed names, so rows join on them.

| File | Holds |
|---|---|
| `prefixes-<slug>.md` | one row per prefix the graph's files use: prefix, namespace, classes, properties, instances, triples |
| `patterns-<slug>.md` | the legend, the hidden/excluded notes, and the class blocks in the 3.2 arrow notation, one `##` heading per block |
| `patterns-<slug>.csv` | one row per edge, nested blank-node edges included, with typed statistic columns |
| `glossary-<slug>.md` | the 3.2 glossary lines (one language per term), plus the alt labels |
| `glossary-<slug>.csv` | one row per term and language: term, IRI, kind, language, pref label, alt labels, definition, notes |

The term-annotation data grows to match the glossary CSV: collection (Q12) and the `--ontology`
reader also read alt labels and notes, and the profile stores them. The ShExC output keeps its one
file.

## Key decisions

- **DEC-1** (R1-1): **Five files replace `pattern-<slug>.txt`; the `.txt` is removed, not
  deprecated.** Release **3.4.0** (*amended in R4-1*: the developer keeps the 3.x line, so the
  breaking output change ships as a MINOR release, marked **BREAKING** in the CHANGELOG; it was
  4.0.0, SemVer MAJOR). Rejected: keeping the `.txt` for one more minor release; 4.0.0 (R4-1).
- **DEC-2** (R1-1): **The indexes are CSV, and their rows carry the facts**, not pointers into the
  `.md`. A tool answers from the rows alone. CSV: flat, one record per line for `grep`, loads into
  DuckDB, pandas or a spreadsheet. RFC 4180 quoting, UTF-8, header row, `\n` line ends. Rejected:
  JSON (a pretty-printed record spans lines) and JSON Lines.
- **DEC-3** (R1-3): **Prefix statistics** per prefix, counted over the graph's shown view: classes
  and properties it names, instances of those classes, triples of those properties. All derived
  from the saved profile; no query. Rejected: term counts only; counts of value IRIs.
- **DEC-4** (R1-4): **`patterns-<slug>.csv` has typed columns**, one row per edge line of the
  `.md`, so a filter needs no token parsing. The exact columns are fixed in the PLAN. Rejected: one
  text column of statistic tokens.
- **DEC-5** (R1-5, R2-1, R2-2): **The glossary CSV has one row per term and language**, with
  columns `term, iri, kind, language, pref_label, alt_labels, definition, notes`. A term with
  notes only has rows here but no line in the glossary `.md`.
  - `pref_label`: the first of `skos:prefLabel`, `skosxl:prefLabel`/`skosxl:literalForm`,
    `rdfs:label`, `dcterms:title`; empty when none. `skos:altLabel` is no longer promoted to it
    (this revises llm-schema-tools DEC-20).
  - `alt_labels`: every `skos:altLabel` and `skosxl:altLabel`/`skosxl:literalForm` value.
  - `definition`: the first of `skos:definition`, `rdfs:comment`, `dcterms:description` (revises
    llm-schema-tools DEC-17, which also took `skos:scopeNote`).
  - `notes`: every value of `skos:scopeNote`, `skos:note`, `skos:example`, `skos:editorialNote`,
    `skos:historyNote`, `skos:changeNote`, and the `rdfs:comment`/`dcterms:description` values not
    used as the definition.
  - The ontology-wins precedence (llm-schema-tools DEC-7) holds per field, now four fields.
  Rejected: only the shown language; the 200-character cut in the CSV.
- **DEC-6** (R2-4): **Multi-valued cells are joined with ` | `**, values sorted. Rejected: `; `
  (notes are prose and contain it).
- **DEC-7** (R2-3): **`glossary-<slug>.md` stays compact**: the 3.2 line (shown language, label,
  description cut at 200 characters) with ` alt: a | b` added; when a term has no pref label, the
  first alt label is the label shown. Notes are only in the CSV. The ShExC glossary comments reuse
  the same line. Rejected: a full per-language section per term.
- **DEC-8** (R1-6): **One command writes all five files**: `fingerprint-gen-pattern`, and
  `--format pattern`. Rejected: separate `-gen-glossary` and `-gen-prefixes` commands.
- **DEC-10** (R3-1, added before implementation): **Each glossary term carries a minimal kind
  code**: `C` class, `dP` data property (literal objects), `oP` object property (IRI, class or
  blank-node objects); also `D` datatype and `P` property with no collected objects. Several
  codes are joined (`dP/oP` in the `.md` line, ` | ` in the CSV `kind` column). The code follows
  the name in the glossary line, so the ShExC glossary comments carry it too. Derived from the
  pattern view's edge targets; no query. Rejected: the words `class`/`property`/`datatype`.
- **DEC-9**: **Profiles saved by 3.x load.** Their stored labels become pref labels and their
  descriptions become definitions; they have no alt labels or notes. No profile version bump.

## Rabbit-holes

- **A query language over the CSVs.** Tools filter them; the library ships no search.
- **Splitting the ShExC.** It stays one parseable file.
- **Re-ordering or re-wording the arrow notation.** `patterns-<slug>.md` keeps the 3.2 lines; only
  the prefix block and glossary leave it, and headings are added.
- **Size of notes.** Only class and property IRIs are annotated, so the volume is bounded by the
  schema; no cap is added.

## No-gos

- No JSON or JSON Lines indexes; no Parquet.
- No change to the ShExC output beyond its glossary lines (DEC-7).
- No new query; Q12 asks for more predicates only.
- No labels for value IRIs (llm-schema-tools DEC-16 holds).
- No work on `llm-schema-server` (R1-2).
- No new `fingerprint-gen-*` command (DEC-8).

---

## What Changes

- **BREAKING:** `fingerprint-gen-pattern` and `fingerprint --format pattern` write
  `prefixes-<slug>.md`, `patterns-<slug>.md`, `patterns-<slug>.csv`, `glossary-<slug>.md` and
  `glossary-<slug>.csv` per graph; `pattern-<slug>.txt` is no longer written.
- **BREAKING:** the glossary label no longer falls back to `skos:altLabel` as the pref label, and
  the description no longer takes `skos:scopeNote` (it becomes a note). The 3.2 glossary line of a
  term with only alt labels or only a scope note changes.
- The term-annotation query (Q12) and the `--ontology` reader collect alt labels and notes; the
  profile's `TermAnnotation` gains `alt_labels` and `notes` (optional).
- The ShExC glossary comments gain ` alt: …`.
- Version 3.4.0 and its `CHANGELOG.md` entry (DEC-1 as amended in R4-1).

## Capabilities

### New Capabilities
None.

### Modified Capabilities
- `profile-representations`: "Pattern schema output" becomes the five files; new requirements for
  the prefix file, the patterns CSV and the glossary CSV; "Term labels and descriptions in the
  outputs" gains alt labels and notes.
- `statistics-collection`: "Term labels and descriptions are collected" gains the alt-label and
  note predicates and the definition/notes split.

## Impact

- **Code:** `fingerprint/domain/annotations.py`, `vocabulary.py`, `patterns.py` (rows for the
  CSVs, prefix counts); `fingerprint/adapters/ontology_file.py`;
  `fingerprint/adapters/queries/q12_term_annotations.rq`;
  `fingerprint/service_layer/generators/pattern.py` (five outputs; CSVs written with the standard
  `csv` module); `fingerprint_report_templates/pattern_schema/`; `model/fingerprint_stats.yaml`
  and `model/fingerprint_views.yaml`, then `make generate-models`.
- **Tests:** golden files regenerated (`make refresh-golden`), the label fixture extended with alt
  labels and notes, scenarios for the CSV columns and the separator, a check that each CSV parses
  with `csv.DictReader` and has its header.
- **Docs:** the pattern-schema page under `docs/modules/ROOT/pages/` and `CHANGELOG.md`.
- **Dependencies:** none.
- **Release:** 3.4.0.
