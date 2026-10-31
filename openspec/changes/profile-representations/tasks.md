> Derives from: EPIC profile-representations (proposal.md)

## 1. Scaffolding

- [ ] 1.0 Gherkin projected from UC-W2/UC-B2.1/UC-B2.2 (`docs/modules/ROOT/pages/use-cases/`), the spec scenarios and the error matrix, each scenario tagged with its UC id: `tests/features/profile_representations.feature`; the two `fingerprint-report` scenarios added to `tests/features/fingerprint_report.feature` (DEC-9)
- [ ] 1.1 rdflib declared as a runtime dependency, pySHACL added to the `test` group, lock updated; `fingerprint/service_layer/generators/` and `fingerprint/adapters/profile_file.py` created empty; `make check-architecture` green (P-12)
- [ ] 1.2 A fixed test profile `tests/test_data/profiles/sample-profile.json`, collected once from the existing continents and treaties data (`make oxigraph-load-test-data`) with fixed `started_at`/`finished_at`/`tool_version`, plus small hand-built profiles in `tests/unit/fakes.py` for first-N, failures and unusual IRIs (no new RDF data)

## 2. Saved profile (adapter, TDD)

- [ ] 2.1 `save_profile` / `load_profile` / `ProfileFileError` (P-5; Requirement: Profile file round-trip)
- [ ] 2.2 `fingerprint_report` writes `profile.json` after the report, failures included (P-15 signature); `generate_endpoint_fingerprint_report` keeps its return value (Requirement: The profile is saved with the report)

## 3. Generator framework (service layer, TDD)

- [ ] 3.1 `filters.py`: `turtle_iri` (via `to_iriref`), `turtle_term` (safe local names only), `turtle_string`, `turtle_number`, `curie` over the packaged `prefixes.json` (P-7, P-9; Requirement: Text outputs are escaped)
- [ ] 3.2 `base.py`: `Generator` with `visit_graph`/`visit_class`/`visit_property`, `view`, `serialize`, `check`, `write`; rendering through `ReportBuilder.template_env` with the filters; per-graph file names and slugs; `GeneratedOutputError`; custom `--template` packages and their config errors; guard test `test_report_builder_exposes_template_env` (P-1, P-2, P-11, P-14; Scenario: Custom template package)
- [ ] 3.3 `with_threshold` and the threshold check through `resolve_settings` (P-6; Requirement: Representations derive from the saved profile only)
- [ ] 3.4 Unwritable IRIs: hooks return `None`, WARNING logged, collected for caveats (P-8; Requirement: Text outputs are escaped — Scenarios: Unusual IRIs stay valid; An IRI that cannot be written is skipped, not broken)

## 4. SHACL generator

- [ ] 4.1 `ShaclGenerator` hooks: counts from the label, value constraints from `value_partitions` (langString rule), the severity table incl. presence-only, first-N and `any_graph` rows, classes with no observed instances, annotations, shape IRIs, used prefixes (DEC-5, P-9, P-10; Requirement: SHACL shapes)
- [ ] 4.2 Template package `fingerprint_report_templates/shacl_shapes/` (`config.json`, `templates/shapes.ttl`); `check` parses the Turtle
- [ ] 4.3 Golden file `tests/test_data/golden/shapes-*.ttl` from the sample profile; pySHACL conformance (`inference="none"`) at `sh:Violation`: the continents graph's shapes on `continents-source-ap.rdf`, the treaties graph's on `treaties-source-ap.rdf`, the default graph's on both files parsed into one graph (Requirements: Golden outputs; SHACL shapes)

## 5. PlantUML generator

- [ ] 5.1 `PlantumlGenerator` hooks: aliases, own/refined attributes, associations, multiplicities, declared/implied generalisations, parent boxes (DEC-6; Requirement: PlantUML class diagram)
- [ ] 5.2 Template package `fingerprint_report_templates/plantuml_diagram/` (`templates/diagram.puml`)
- [ ] 5.3 Golden file `tests/test_data/golden/diagram-*.puml`; structural check (one `@startuml`/`@enduml`, one `class` line per class) (Requirement: Golden outputs)

## 6. Profile document generator

- [ ] 6.1 `DocumentGenerator` hooks and the view (overview, namespaces, graph chapters, class sections, caveats) (DEC-7; Requirement: Application-profile document)
- [ ] 6.2 Template package `fingerprint_report_templates/profile_document/` (`templates/profile.html`, inline CSS in the SEMIC / SHACL Play style), autoescape on
- [ ] 6.3 Golden file `tests/test_data/golden/profile.html` (Requirement: Golden outputs)

## 7. Command line

- [ ] 7.1 `fingerprint/entrypoints/cli/generate.py`: `fingerprint-gen-shacl`, `fingerprint-gen-puml`, `fingerprint-gen-doc` with the shared arguments and exit codes 0/2/4; scripts in `pyproject.toml` (P-3, P-4, P-13; Requirement: Generators share one framework)
- [ ] 7.2 `fingerprint --format` (repeatable), generators run after the report; exit 4 when a generator fails (Requirement: Formats rendered after collecting)
- [ ] 7.3 Step definitions for `profile_representations.feature` and the new `fingerprint_report` scenarios, green; existing scenarios unchanged and green (Requirement: The statistics report is unchanged)
- [ ] 7.4 e2e: `fingerprint --format shacl --format puml --format doc` against the loaded Oxigraph, then each `fingerprint-gen-*` from the written `profile.json` with `RDF_FINGERPRINTER_TEST_ENDPOINT` pointed at an unreachable port, outputs written (Requirement: Representations derive from the saved profile only)

## 8. Docs and release

- [ ] 8.1 Antora page `docs/modules/ROOT/pages/representations.adoc` (commands, files, SHACL mapping and severities, custom templates); nav, getting-started and api-reference updated; how-it-works, UC-W2/UC-B2.x and AD-7..AD-10 brought in line with what was built (drop the "(2.1)" markers)
- [ ] 8.2 CHANGELOG 2.1.0, version bump in `pyproject.toml`
- [ ] 8.3 Pre-PR review (five lenses, `meaningfy-code-review`); act on findings
- [ ] 8.4 `/opsx:archive` the change into `openspec/specs/`

## Roadmap

- [ ] 1.0 · [ ] 1.1 · [ ] 1.2 · [ ] 2.1 · [ ] 2.2 · [ ] 3.1 · [ ] 3.2 · [ ] 3.3 · [ ] 3.4 · [ ] 4.1 · [ ] 4.2 · [ ] 4.3 · [ ] 5.1 · [ ] 5.2 · [ ] 5.3 · [ ] 6.1 · [ ] 6.2 · [ ] 6.3 · [ ] 7.1 · [ ] 7.2 · [ ] 7.3 · [ ] 7.4 · [ ] 8.1 · [ ] 8.2 · [ ] 8.3 · [ ] 8.4

## Verification

`make check-all` and `make test-e2e` (after `make oxigraph-load-test-data`) green; `openspec validate profile-representations --strict`; clarity gate ≥ 9/10 on this PLAN.
