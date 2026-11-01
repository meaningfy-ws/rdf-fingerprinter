> Derives from: the EPIC `pitfall-scans` (proposal.md)

## 1. Model and contract

- [x] 1.1 Model per design D-3 (stats) and D-6/D-7 (views); `make generate-models`; round-trip a profile with `pitfalls`, and load one without them (pitfall-scans › The pitfall scan stage)
- [x] 1.2 `fingerprint/domain/pitfalls.py`: `parse_header`, importance order, `robot_level`, `at_or_above`, test-first (design D-1; pitfall-scans › Pitfall check contract)
- [ ] 1.3 Gherkin `tests/features/pitfall_scans.feature` for the new capability; scenarios added to `fingerprint_report.feature` (section, badge, escaping, exit 5, format, update refused); step stubs

## 2. Catalogue

- [x] 2.1 Verify and adjust the 29 packaged checks already written in `fingerprint/adapters/queries/pitfalls/` (from `inputs/seed-queries/`) against the header contract and the D-1a table (pitfall-scans › The packaged catalogue)
- [x] 2.2 `fingerprint/adapters/pitfall_catalogue.py:load_catalogue` with validation, replace and skip (design D-2)
- [x] 2.3 One `.trig` fixture per check (positive and negative graphs) and `tests/unit/test_pitfall_checks.py` (design Test strategy)

## 3. Scan stage

- [x] 3.1 The query builders in `adapters/queries/__init__.py` (design D-5)
- [x] 3.2 `_Collection.scan_pitfalls`, `collect(..., checks=())`, failures of kind `pitfall` with `check_id` (design D-4; pitfall-scans › The pitfall scan stage)
- [x] 3.3 The settings `pitfall_scan`, `schema_graphs` (comma-split in the environment; each IRI checked) and `pitfall_examples` through `resolve_settings` (pitfall-scans › Scan settings and options; statistics-collection › Depth and switches select the queries)
- [x] 3.4 The findings' IRIs in the namespace table (design D-8; namespace-prefixes › Every namespace has a prefix)

## 4. Outputs

- [ ] 4.1 Report views and the template: section, contents entry, badges, search over checks (design D-6; fingerprint-report › Pitfalls in the report, › Report content)
- [ ] 4.2 `PitfallsGenerator`, the `pitfalls_tsv` package and `RepresentationFormat.pitfalls` (design D-7; pitfall-scans › Pitfalls TSV format)
- [ ] 4.3 Golden files for the page and the TSV with a fixed scanned profile

## 5. CLI, library and exit status

- [ ] 5.1 `fingerprint_report(..., checks=None)`; the `main.py` options and usage errors; exit 5 with `--fail-on` (design D-9; pitfall-scans › Scan settings and options, › Fail on findings; fingerprint-report › Exit status, › Read-only and credential-safe, › Formats rendered after collecting)
- [ ] 5.2 `fingerprint-gen-pitfalls` and the script in `pyproject.toml`

## 6. Tooling, docs and release prep

- [ ] 6.1 The `oxigraph-scan` compose service, `RDF_FINGERPRINTER_SCAN_PORT` and `make scan-files` (design D-10; developer-tooling › Scan files locally)
- [ ] 6.2 e2e `tests/e2e/test_pitfall_scan.py` on Oxigraph (schema graph plus data, `--format pitfalls`, exit 5)
- [ ] 6.3 Docs: `pitfalls.adoc` with the catalogue, the nav, and the CLI, settings and exit-status tables; a unit test that every packaged id is in the docs table (design D-11)
- [ ] 6.4 CHANGELOG 3.1.0, `pyproject.toml` 3.1.0; `make check-all` and `make test-e2e`; `make scan-files` on brainframe into `../rdf-fingerprinter/temp/brainframe-fingerprint/pitfalls/` (design D-12)

## Roadmap

- [x] 1.1 · [ ] 1.2 · [ ] 1.3 · [ ] 2.1 · [ ] 2.2 · [ ] 2.3 · [ ] 3.1 · [ ] 3.2 · [ ] 3.3 · [ ] 3.4 · [ ] 4.1 · [ ] 4.2 · [ ] 4.3 · [ ] 5.1 · [ ] 5.2 · [ ] 6.1 · [ ] 6.2 · [ ] 6.3 · [ ] 6.4

## Verification

`make check-all`, `make test-e2e` and `openspec validate pitfall-scans --strict` pass, and `make scan-files` on brainframe reproduces the inventory's counts in `inputs/brainframe-modelling-analysis.md`: the "Ontology" column for the schema checks on the schema graph, and the "Ont. + data" column for the data checks on the data graph.
