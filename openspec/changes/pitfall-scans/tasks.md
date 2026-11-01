> Derives from: the EPIC `pitfall-scans` (proposal.md)

## 1. Model and contract

- [x] 1.1 Model per design D-3 (stats) and D-6/D-7 (views); `make generate-models`; round-trip a profile with `pitfalls`, and load one without them (pitfall-scans › The pitfall scan stage)
- [x] 1.2 `fingerprint/domain/pitfalls.py`: `parse_header`, importance order, `robot_level`, `at_or_above`, test-first (design D-1; pitfall-scans › Pitfall check contract)
- [x] 1.3 Gherkin `tests/features/pitfall_scans.feature` for the new capability; scenarios added to `fingerprint_report.feature` (section, badge, escaping, exit 5, format, update refused); step stubs

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

- [x] 4.1 Report views and the template: section, contents entry, badges, search over checks (design D-6; fingerprint-report › Pitfalls in the report, › Report content)
- [x] 4.2 `PitfallsGenerator`, the `pitfalls_tsv` package and `RepresentationFormat.pitfalls` (design D-7; pitfall-scans › Pitfalls TSV format)
- [x] 4.3 Golden files for the page and the TSV with a fixed scanned profile

## 5. CLI, library and exit status

- [x] 5.1 `fingerprint_report(..., checks=None)`; the `main.py` options and usage errors; exit 5 with `--fail-on` (design D-9; pitfall-scans › Scan settings and options, › Fail on findings; fingerprint-report › Exit status, › Read-only and credential-safe, › Formats rendered after collecting)
- [x] 5.2 `fingerprint-gen-pitfalls` and the script in `pyproject.toml`

## 6. Tooling, docs and release prep

- [x] 6.1 The `oxigraph-scan` compose service, `RDF_FINGERPRINTER_SCAN_PORT` and `make scan-files` (design D-10; developer-tooling › Scan files locally)
- [x] 6.2 e2e `tests/e2e/test_pitfall_scan.py` on Oxigraph (schema graph plus data, `--format pitfalls`, exit 5)
- [x] 6.3 Docs: `pitfalls.adoc` with the catalogue, the nav, and the CLI, settings and exit-status tables; a unit test that every packaged id is in the docs table (design D-11)
- [x] 6.4 CHANGELOG 3.1.0, `pyproject.toml` 3.1.0; `make check-all` and `make test-e2e`; `make scan-files` on brainframe into `../rdf-fingerprinter/temp/brainframe-fingerprint/pitfalls/` (design D-12)

## 7. Report order, taxonomy and one caveats section (developer requests, 2026-11-01)

- [x] 7.1 Views: `DocumentPropertyGroup`, `DocumentClass.property_groups`, `TaxonomyNode`, `DocumentGraph.taxonomy`; `make generate-models` (design D-13, D-14)
- [x] 7.2 `DocumentGenerator`: the class and property order and the taxonomy tree (fingerprint-report › Class and property order, › Taxonomy view)
- [x] 7.3 Template: property group rows, the `#taxonomy` section with popularity bars, pitfalls inside *Caveats and pitfalls* (design D-15; fingerprint-report › Pitfalls in the report)
- [x] 7.4 Gherkin for the new scenarios (spec titles); refresh the goldens; regenerate the brainframe fingerprint into `../rdf-fingerprinter/temp/brainframe-fingerprint/`

## 8. Findings, namespace table and class indicator (developer requests, 2026-11-01)

- [x] 8.1 `used_namespaces`: the ontology's own IRI from a finding adds no namespace (design D-16; namespace-prefixes › Every namespace has a prefix)
- [x] 8.2 Views `PrefixDeclaration.uses`, `DocumentClass.data_properties`, `.object_properties`; `make generate-models`; the generator's namespace order and class counts (design D-17, D-18; fingerprint-report › Namespace table order, › Class indicator)
- [x] 8.3 Template: source group rows and the uses column, the class indicator in the contents and headings; Gherkin for the new scenarios; refresh the goldens; regenerate the brainframe fingerprint

## Roadmap

- [x] 1.1 · [x] 1.2 · [x] 1.3 · [x] 2.1 · [x] 2.2 · [x] 2.3 · [x] 3.1 · [x] 3.2 · [x] 3.3 · [x] 3.4 · [x] 4.1 · [x] 4.2 · [x] 4.3 · [x] 5.1 · [x] 5.2 · [x] 6.1 · [x] 6.2 · [x] 6.3 · [x] 6.4 · [x] 7.1 · [x] 7.2 · [x] 7.3 · [x] 7.4 · [x] 8.1 · [x] 8.2 · [x] 8.3

## Verification

`make check-all`, `make test-e2e` and `openspec validate pitfall-scans --strict` pass, and `make scan-files` on brainframe reproduces the inventory's counts in `inputs/brainframe-modelling-analysis.md`: the "Ontology" column for the schema checks on the schema graph, and the "Ont. + data" column for the data checks on the data graph.
