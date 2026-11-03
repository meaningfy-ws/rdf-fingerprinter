> Derives from: EPIC singleton-property-pattern (`proposal.md`, DEC-1 to DEC-11); design in `design.md` (P-1 to P-16). Stage 1 only.

Each task is test-first (`superpowers:test-driven-development`): write the named tests red, then the
code, then the task's named tests green. From task 0.1 on, the new Gherkin scenarios exist and stay
red until the task that binds them ("binds" below); every other test stays green. Commit after each
task (`Refs: singleton-property-pattern DEC-…, P-…`).

## 0. Scenarios first

- [x] 0.1 Write every scenario of the five spec deltas (design "Test case specifications" table) into its feature file with the spec's title, via `bdd-gherkin`; tag "Relation through a blank node" `@stage4`; add the `pytest_bdd_apply_tag` hook to `tests/bdd/conftest.py` (P-15 row of the layering table); `tests/guards/test_traceability.py` green

## 1. Remove the pitfall `x_individual_as_predicate` (DEC-10)

- [x] 1.1 Delete `fingerprint/adapters/queries/pitfalls/x_individual_as_predicate.rq`; remove it from `tests/unit/adapters/test_pitfall_checks.py`, `tests/unit/service_layer/test_pitfall_scan.py` (the clean-graph test keeps `p19_multiple_domains_or_ranges` and `p35_untyped_property`), `tests/bdd/steps/pitfalls.py`; the row in `docs/modules/ROOT/pages/pitfalls.adoc`; drop its result from `tests/test_data/profiles/scanned-profile.json` by hand (design §D: no target refreshes it); `make refresh-golden`; only `golden/scanned/main.html` changes, by that check's name — binds pitfall-scans "Catalogue size" (28) and "Each check finds its pitfall and only it"

## 2. Model (design "Layering and modules")

- [x] 2.1 The model rows of the layering table in `model/fingerprint_stats.yaml`, `model/fingerprint_analytics.yaml` and `model/fingerprint_views.yaml`; `make generate-models`; `make check-models` green; add `"reifications": true` to `scanned-profile.json` by hand; `make refresh-golden` shows no diff

## 3. The probe catalogue (P-1, P-2, P-16, design §A)

- [ ] 3.1 `reification_query` in `fingerprint/adapters/queries/__init__.py`; `fingerprint/adapters/reification_catalogue.py` (`packaged_templates()`, section split, fill-then-parse validation); `tests/unit/adapters/test_reification_catalogue.py` (each rejection of design "Test case specifications")
- [ ] 3.2 `tests/test_data/reifications-source.ttl` (design §C and §D)
- [ ] 3.3 The six stage-1 templates in `fingerprint/adapters/queries/reifications/` per design §A (`NOT_REIFIER_TYPES`, the `$distinct` subquery, P-5 dynamic hiding for every kind); a unit test runs each section, rendered for `graph=None`, over `reifications-source.ttl` in rdflib and asserts the §C rows

## 4. The collection stage (P-3 to P-9, P-14, design §B)

- [ ] 4.1 `_Reifications` in `fingerprint/service_layer/collection.py`: probes first at every depth, hidden terms at every depth, capture from depth `classes`, `QUERY_KIND["REIFY"]`, failures with `check_id=<kind>` (P-8), `reification_kinds` and `triple_term_reifications`; `tests/unit/service_layer/test_reifications.py` (probe and hidden only at depth `graphs`; the failure branches, with `FakeSparql.on(..., when=…)`)
- [ ] 4.2 The hidden-term filter (P-4, P-5, P-14): graph predicate partitions, classes next to the blank-node drop, `seen()`, Q10 predicates, co-types, Q11; relations attached and sorted (P-6, P-7); unit tests for the P-7 branches and the sort order
- [ ] 4.3 `--reifications/--no-reifications` in `fingerprint/entrypoints/cli/main.py`; step definitions in `tests/bdd/steps/` — binds every statistics-collection scenario except `@stage4`

## 5. Outputs (P-10, P-11, DEC-5, DEC-11)

- [ ] 5.1 P-10 in `fingerprint/domain/namespace_filter.py` with its cases in `tests/unit/domain/test_namespace_filter.py`
- [ ] 5.2 Report and profile document: `DocumentGenerator.end_class` builds the views; `main.html` renders the section after the properties and the kinds found (and the triple-term count when not zero) in the graph summary — binds fingerprint-report "Kinds found are named" and profile-analytics "Relations follow their class"
- [ ] 5.3 Pattern `~>` lines (`fingerprint/domain/patterns.py`), ShExC comment (`fingerprint/domain/shex.py`), SHACL `rdfs:comment` (`shacl.py`), PlantUML compartment (`plantuml.py`), and their templates (P-11) — binds profile-representations "Section present", "No section when none", "Shapes note reifications without constraining them"

## 6. Canonical data (design §D, P-15)

- [ ] 6.1 `tests/refresh_sample_data.py` writes `reified-profile.json` in memory (P-15); `tests/refresh_golden.py` renders `golden/reified/`; `REIFIED_*` facts in `tests/sample_data.py`, checked by `tests/guards/test_sample_data.py`; `make oxigraph-load-test-data`, `make refresh-sample-profile`, `make refresh-golden`; review: the sample profile changes only by `"reifications": true`, and the only other changes are the new reified files
- [ ] 6.2 e2e test in `tests/e2e/`: every rendered section of every packaged template is accepted by Oxigraph (P-15)

## 7. Docs

- [ ] 7.1 New page `docs/modules/ROOT/pages/reifications.adoc` (the kinds, what is hidden, mixed classes (P-14), the per-class section in each output, the `~>` notation, `--no-reifications`, what is not detected: `rdf:Property`-only predicates, n-ary relations through IRIs, triple-term decomposition, untyped subjects (P-7), `patterns.csv` unchanged); the options table in `getting-started.adoc`; the nav entry; a pointer for the `~>` lines in `llm-schema.adoc`; the `CHANGELOG.md` entry (BREAKING: pitfall removed)

## 8. Gate and release

- [ ] 8.1 `make check-all`
- [ ] 8.2 `make oxigraph-load-test-data` + `make test-e2e`
- [ ] 8.3 `make check-mutation` at or above the stored score; survivors get a test in the owning tier
- [ ] 8.4 Brainframe acceptance (design "Exit criteria", with its timing method), recorded with commands in `inputs/brainframe-evidence.md` under "After stage 1"; `openspec validate --all --strict`
- [ ] 8.5 Release (P-13): the developer chooses the version bump; then AGENTS.md "Release authority"

## Roadmap

- [x] 0.1 · [x] 1.1 · [x] 2.1 · [ ] 3.1 · [ ] 3.2 · [ ] 3.3 · [ ] 4.1 · [ ] 4.2 · [ ] 4.3 · [ ] 5.1 · [ ] 5.2 · [ ] 5.3 · [ ] 6.1 · [ ] 6.2 · [ ] 7.1 · [ ] 8.1 · [ ] 8.2 · [ ] 8.3 · [ ] 8.4 · [ ] 8.5

## Verification

`make check-release` (check-all, release tests, properties, e2e) green, `openspec validate --all --strict`, and the clarity gate ≥ 9/10 on this PLAN before task 0.1.
