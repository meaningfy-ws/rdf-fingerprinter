> Derives from: EPIC llm-schema-split (`proposal.md`, DEC-1 to DEC-9); design in `design.md` (P-1 to P-5, §A–§E).

Each task is test-first (`superpowers:test-driven-development`): write the named tests red, then
the code, then the task's named tests green. Every test outside the "Still red until bound" table
stays green after every task; the gate (1.9) requires everything green. Each task is one commit
(`Refs: llm-schema-split P-n` or `DEC-n`). Before editing an existing symbol, run GitNexus impact
(`AGENTS.md`, "Implementation loop"); stop and report HIGH/CRITICAL. Scenario titles are cited as
`cap › Requirement › Scenario` (design "Scenario → feature map").

### Still red until bound

Task 1.1 writes the Gherkin of every new or reworded scenario; they fail until their step
definitions and code exist. The red count `pytest tests/bdd` prints after 1.1 is written in the
1.1 commit body, and each later task's commit body gives the count left.

| Scenarios | Red from | Green after |
|---|---|---|
| s-c › Term labels and descriptions are collected › Label predicate priority; Alt labels and notes are stored | 1.1 | 1.3 |
| p-r › CSV cells › Cell quoting | 1.1 | 1.4 |
| p-r › Pattern schema output (all 7), Prefix file, Patterns CSV, Glossary CSV, CSV cells › Every CSV parses, Term labels and descriptions in the outputs (all 8), No files for empty graphs, Size filters (both) | 1.1 | 1.7 |

## 1. Split the pattern schema

- [x] 1.1 Gherkin: bring `tests/features/profile_representations.feature` and
  `tests/features/statistics_collection.feature` in line with the delta specs (new scenarios,
  reworded steps, the Label-priority table's new column); remove the steps that read
  `pattern-*.txt` only where the scenario text changed
  - Layer: tests (features). Depends on: —.
  - Tests: `pytest tests/bdd --collect-only` collects every scenario of the design map; the red
    count is recorded in the commit body.
- [x] 1.2 Model (P-3, P-4): `model/fingerprint_stats.yaml` `TermAnnotation.alt_labels`, `.notes`;
  `model/fingerprint_views.yaml` `PatternFile(template, graph)`, the `PatternEdge` slots of design
  §B, the `PrefixDeclaration` counts of §C, `GlossaryEntry.kinds` and `.rows`, `GlossaryRow`, `GlossaryEntry.line` optional; the description
  of `RepresentationFormat.pattern` ("five files per graph"); `make generate-models`
  - Layer: domain (model). Depends on: —.
  - Tests: `make check-models`; a unit test that `sample-profile.json` (no alt labels or notes)
    loads (DEC-9).
- [x] 1.3 Annotations (design §A): `vocabulary.py` predicate tuples; `select_annotations`,
  `merge_annotations`; Q12 predicates and the `skosxl:altLabel` branch; `load_ontology` reads alt
  labels and notes; the label fixture grows (§E); step definitions of the s-c scenarios
  - Layer: domain + adapters. Depends on: 1.2.
  - Tests: the `select_annotations`, `merge_annotations` and Q12 unit tests of design "Unit
    tests"; `tests/unit/adapters/test_ontology_file.py` updated for the new predicates;
    `tests/unit/domain/test_annotations.py` and `tests/unit/domain/strategies.py` moved off
    `ALT_LABEL` and the 4-element `TERM_DESCRIPTION_PREDICATES`; s-c scenarios green.
- [x] 1.4 `csv_cell` (P-2) in `fingerprint/domain/patterns.py`, registered as a filter in
  `fingerprint/adapters/template_renderer.py::filters`; step definitions of `› CSV cells › Cell
  quoting`
  - Layer: domain + adapters. Depends on: —.
  - Tests: the `csv_cell` unit tests of design "Unit tests"; `Cell quoting` green.
- [x] 1.5 Pattern view (design §B–§D): `_Builder` sets the typed `PatternEdge` slots, `owner` and
  `path`; prefix counts on `PrefixDeclaration`; `GlossaryEntry.kinds`, `.rows` and the new
  `line` (alt labels; alt label as label); `fingerprint/domain/shex.py` glossary skips entries without a line
  - Layer: domain. Depends on: 1.2, 1.3.
  - Tests: `tests/unit/domain/test_patterns.py` for the prefix-count and glossary-line branches
    of design "Unit tests"; existing pattern-view unit tests stay green.
- [x] 1.6 Generator and templates (P-1): `PatternGenerator.outputs` emits five `PatternFile`s per
  graph; `pattern_schema/config.json` → `files.j2`; templates `prefixes.md`, `patterns.md`,
  `patterns.csv`, `glossary.md`, `glossary.csv`; delete `schema.txt`; `Makefile` `check-wheel`
  lists the six new template files instead of `schema.txt`
  - Layer: service + templates + build. Depends on: 1.4, 1.5.
  - Tests: `tests/unit/service_layer/test_pattern.py` (five names per graph, none `.txt`);
    `tests/unit/entrypoints/test_generate.py` (it reads `pattern-*.txt`), the `"pattern-"` file
    prefix in `tests/bdd/steps/filters.py` and `tests/bdd/steps/pattern.py` moved to the new
    names, so their checks still select files;
    `› Generators share one framework › Custom template package` still green; `make build`.
- [x] 1.7 Step definitions of the remaining p-r scenarios; `make refresh-golden` writes the 15
  new golden files and removes the 3 `pattern-*.txt`; review them against design §B–§D; IT-2
  (every golden CSV parses, header equals the column list, rows as wide as the header)
  - Layer: tests. Depends on: 1.6.
  - Tests: every scenario of the "Still red" table green; `test_representations_golden.py` green;
    ShExC goldens unchanged (IT-4).
- [x] 1.8 Docs: `docs/modules/ROOT/pages/llm-schema.adoc` (the five files, their columns, the
  alt labels and notes, sizes re-measured with `wc -m` on the new goldens), `representations.adoc`
  table row, `glossary.adoc` "Pattern schema", `statistics.adoc` Q12 predicates, README section;
  `CHANGELOG.md` `## [Unreleased]` with `### Changed` (**BREAKING**: the five files replace
  `pattern-*.txt`; alt labels no longer become pref labels; `skos:scopeNote` is a note; a custom
  `--template` package for the pattern schema now gets `view` = `PatternFile` five times per graph) and
  `### Added` (alt labels and notes in the profile and the glossary CSV)
  - Layer: docs. Depends on: 1.7.
  - Tests: `make build-docs` green.
- [x] 1.9 Gate (design "Stage exit criteria"): `make check-all`; `make oxigraph-load-test-data` +
  `make test-e2e` (no e2e test reads `pattern-*.txt`; IT-3 is that run); `openspec validate llm-schema-split
  --strict`; a code review by a reviewer agent; no `make check-mutation` and no
  `make check-all-deep` (developer, R4-2)
  - Layer: all. Depends on: 1.1–1.8.
  - Tests: all of the above green.
- [ ] 1.10 Release 3.4.0 (DEC-1, amended R4-1), per `AGENTS.md` "Branches" and "Release authority":
  - PR `feature/llm-schema-split` → `develop` (it also carries the archive of `llm-schema-tools`),
    CI green, merge;
  - `pyproject.toml` `3.3.0` → `3.4.0`; `CHANGELOG.md` `## [Unreleased]` → `## [3.4.0] - <date>`
    (an empty `## [Unreleased]` above it);
  - release PR `develop` → `master`, CI green, merge; bare tag `3.4.0`; `gh release create 3.4.0`;
    bring `develop` level with `master`; report the release URL.
  - Layer: release. Depends on: 1.9.
  - Tests: `publish.yml` succeeds; `pip install rdf-fingerprinter==3.4.0` in a clean venv runs
    `fingerprint-gen-pattern --help`.
