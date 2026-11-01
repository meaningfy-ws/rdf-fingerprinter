> Derives from: EPIC llm-schema-tools (`proposal.md`, DEC-1 to DEC-28; stage 1 only since DEC-28); design in `design.md` (P-1 to P-10, P-13, P-14, P-16).

Each task is test-first (`superpowers:test-driven-development`): write the named tests red, then
the code, then **the task's named tests green**. `make test` as a whole stays red while Gherkin
scenarios are unbound (table "Still red until bound" below); every other test must stay green, and
the exit (task 1.14) requires everything green. The tasks of the former stages 2 and 3 moved to
`../llm-schema-server/inputs/carried-over-tasks.md` (DEC-28). Each task is one commit (`Refs: llm-schema-tools P-n`). Before
editing an existing symbol, run GitNexus impact (`AGENTS.md`, "Implementation loop"). Gherkin
titles are already in `tests/features/` (design "Scenario → feature map"); the tasks below write
their step definitions. Scenario titles are cited as `cap › Requirement › Scenario`.

### Still red until bound

| Scenarios (feature file) | Red items | Red from | Green after |
|---|---|---|---|
| statistics-collection: the 5 of `› Term labels and descriptions are collected` (9 items: `Label predicate priority` has 5 rows), and `› Default depth`, `› Measurements per depth` (2 rows) | 12 | this PLAN's commit | 1.3 |
| profile-representations: the 4 of `› Pattern view`; the 6 of `› Pattern schema output` except `Unusual IRIs…` (17 items: 10 lines, 1, 4 values, 1 first-N, 1 `A single IRI value is written as a prefixed name`); the 5 of `› Term labels and descriptions in the outputs` (7 items); the 2 of `› Size filters` | 30 | this PLAN's commit | 1.8 |
| profile-representations: the 2 of `› Enriched ShExC output` (8 items), and `› Pattern schema output › Unusual IRIs in the LLM outputs` (its ShExC steps need 1.9) | 9 | this PLAN's commit | 1.9 |
| profile-representations: `› Empty default graph`, the 2 new rows of `› Golden file per output` | 3 | this PLAN's commit | 1.10 |
| **Total** (`pytest tests/bdd` failures) | **54** (12 statistics-collection + 42 profile-representations) | | |

## 1. The schema outputs and labels

- [ ] 1.1 Model: the additions of design "Model changes" to `model/fingerprint_stats.yaml`, `fingerprint_analytics.yaml` and `fingerprint_views.yaml`; `make generate-models`; the three new domain modules (`annotations`, `patterns`, `shex`) added to the `generated` contract in `.importlinter`
  - Layer: domain (model). Depends on: —.
  - Tests: `tests/unit/adapters/test_profile_file.py` round-trip of a run with `term_annotations`, and of the sample profile and `scanned-profile.json` (3.1, no field → `None`); `make check-models` green.
- [ ] 1.2 `fingerprint/domain/vocabulary.py` constants and `fingerprint/domain/annotations.py` (`select_annotations`, `merge_annotations`, `shown`)
  - Layer: domain. Depends on: 1.1.
  - Tests: TC-A1, TC-A2 (Hypothesis, `annotation_values()` in `tests/unit/domain/strategies.py`), TC-A3; 100% branch coverage.
- [ ] 1.3 Q12 (`q12_term_annotations.rq`, `QUERY_FILES["Q12"]`, `terms_values`, `render(..., terms=)`) and `_Collection.term_annotations` in `profile_graph`; `QUERY_KIND["Q12"]`; step definitions for the statistics-collection scenarios of this change
  - Layer: adapters, service_layer. Depends on: 1.2.
  - Tests: TC-Q1, TC-C1; Gherkin `statistics-collection › Term labels and descriptions are collected` (5 scenarios) and `› Depth and switches select the queries › Default depth`, `› Measurements per depth`, through `FakeSparql`; IT-1 (`tests/e2e/test_queries.py::test_term_annotations_of_the_scheme`).
- [ ] 1.4 `make oxigraph-load-test-data` then `make refresh-sample-profile`; review the diff (expected: `"term_annotations": []` per graph); if labels are found, add them as named facts to `tests/sample_data.py`
  - Layer: tests (canonical data). Depends on: 1.3.
  - Tests: IT-2 (the drift test) and `tests/guards/test_sample_data.py` green.
- [ ] 1.5 `fingerprint/adapters/ontology_file.py` (`load_ontology`, `OntologyFileError`); fixture `tests/test_data/ontology/labels.ttl` (design §E, "Glossary with the label fixture") and its RDF/XML twin `labels.rdf`
  - Layer: adapters. Depends on: 1.1.
  - Tests: TC-O1.
- [ ] 1.6 `fingerprint/domain/patterns.py`, part 1: names, groups (N2), nested test (P-4), filters (P-3, P-10), edges, stat tokens and value quoting (design §B steps 1–5)
  - Layer: domain. Depends on: 1.1.
  - Tests: TC-P1, TC-P2, TC-P4, TC-P5, TC-P7 (`=name` from top values); 100% branch coverage of the new code.
- [ ] 1.7 `fingerprint/domain/patterns.py`, part 2: chains and their assignment (P-5), `via` (N6), header, glossary (N9), prefixes (N8), `nested_blocks`, `reaching_edges` (design §B steps 6–10)
  - Layer: domain. Depends on: 1.2, 1.6.
  - Tests: TC-P3, TC-P6 (Hypothesis). The `› Pattern view` scenarios need the generator, so they are bound in 1.8.
- [ ] 1.8 `PatternGenerator`, template package `fingerprint_report_templates/pattern_schema/`, `RepresentationFormat.pattern`, `GENERATORS`; `representations.with_ontology` and the size checks in `validate_options`; `gen_pattern` with `--ontology`, `--min-instances` and `--max-classes`; script `fingerprint-gen-pattern` in `pyproject.toml`
  - Layer: service_layer, entrypoints, templates. Depends on: 1.5, 1.7.
  - Tests: TC-G1, TC-E1; Gherkin `profile-representations › Pattern view` (4, steps on builder profiles), `› Pattern schema output` (6, `Unusual IRIs…` still red until 1.9), `› Term labels and descriptions in the outputs` (5) and `› Size filters` (2).
- [ ] 1.9 `fingerprint/domain/shex.py`, `ShexGenerator`, template package `shex_schema/`, `RepresentationFormat.shex`, `gen_shex` (same options), script `fingerprint-gen-shex`; `pyshexc==0.10.3.post1` in the `test` group
  - Layer: domain, service_layer, entrypoints, templates. Depends on: 1.8.
  - Tests: TC-S1; Gherkin `profile-representations › Enriched ShExC output` (2) and the ShExC part of `› Pattern schema output › Unusual IRIs in the LLM outputs`.
- [ ] 1.10 Step definitions for the MODIFIED profile-representations scenarios (`› No files for empty graphs › Empty default graph`, the two new rows of `› Golden outputs › Golden file per output`); `make refresh-golden` writes the six golden files; review them against design §E (the worked example)
  - Layer: tests. Depends on: 1.9.
  - Tests: IT-3; Gherkin `› Generators share one framework › Custom template package` still green.
- [ ] 1.11 `Makefile` `check-wheel`: grep for `pattern_schema/templates/schema.txt`, `shex_schema/templates/schema.shex` and `q12_term_annotations.rq`
  - Layer: build. Depends on: 1.9.
  - Tests: `make build` green; `tests/guards/test_repository_wiring.py` green.
- [ ] 1.12 Record in `inputs/format-sizes.md` the Unicode code points (`wc -m`) of every golden `pattern-*` and `shex-*` file, with and without the prefix block and legend, and the SHACL golden files for reference (DEC-8)
  - Layer: docs (change inputs). Depends on: 1.10.
  - Tests: none (a record, not a gate).
- [ ] 1.13 Docs:
  - a new page `docs/modules/ROOT/pages/llm-schema.adoc` (the pattern schema and its grammar, the ShExC form, labels and `--ontology`, the size filters), in `nav.adoc`;
  - pointers from `representations.adoc`;
  - glossary terms: Pattern schema, Pattern view, Merged group, Nested group, Term annotation;
  - `use-cases/ucw2.adoc` "Out of Scope" no longer lists ShEx and LLM formats;
  - `statistics.adoc`: Q12 and the depth table;
  - a README section.
  - Layer: docs. Depends on: 1.10.
  - Tests: `make build-docs` green; links resolve.
- [ ] 1.14 Gate (design "Stage exit criteria"): `make check-all`, `make oxigraph-load-test-data` + `make test-e2e`, `make check-mutation` (≥ 0.950; survivors get a test in the owning tier, or dead code is deleted and listed here; `mutation_score.txt` raised if higher), `openspec validate llm-schema-tools --strict`
  - Layer: all. Depends on: 1.1–1.13.
  - Tests: IT-1, IT-2, IT-3, IT-4; every scenario of the "Still red until bound" table green.
- [ ] 1.15 Release 3.2.0 (P-16; DEC-12, confirmed in Round 6; 3.1.0 is already released by `pitfall-scans`):
  - `pyproject.toml` version `3.1.0` → `3.2.0`;
  - `CHANGELOG.md`: turn `## [Unreleased]` into `## [3.2.0] - <date>` (keep an empty `## [Unreleased]` above it), with Added (the two generators and their commands, `--format pattern|shex`, `--ontology`, the size filters, Q12 and `term_annotations`) and the note that 3.2 profiles with term annotations do not load in 3.1 or 3.0;
  - PR to `master` with green CI; merge; a bare tag `3.2.0`; `gh release create 3.2.0`; report the release URL (`AGENTS.md` "Release authority").
  - Layer: release. Depends on: 1.14.
  - Tests: `publish.yml` succeeds; `pip install rdf-fingerprinter==3.2.0` in a clean venv runs `fingerprint-gen-pattern --help`.

## Roadmap

- [ ] 1.1 · [ ] 1.2 · [ ] 1.5 · [ ] 1.6 · [ ] 1.3 · [ ] 1.4 · [ ] 1.7 · [ ] 1.8 · [ ] 1.9 · [ ] 1.10 · [ ] 1.11 · [ ] 1.12 · [ ] 1.13 · [ ] 1.14 · [ ] 1.15

## Verification

The change is complete when `make check-all`, `make test-e2e` and `make check-mutation` pass;
`openspec validate llm-schema-tools --strict` is clean; every spec scenario of the two deltas
has its same-titled Gherkin scenario passing (`tests/guards/test_traceability.py`); and the PLAN
passed the independent clarity gate (≥ 9/10) before task 1.1.
