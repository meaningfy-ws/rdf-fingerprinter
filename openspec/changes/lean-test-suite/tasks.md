> Derives from: EPIC lean-test-suite (proposal.md)

Starts after `readable-representations` (the namespace-prefixes work) is merged (DEC-10; met 2026-10-31, PR #42). Each group is
one commit or more; deletions per module are their own commits (design Risks).

## 1. Baseline

- [x] 1.1 Record the baseline in `inputs/baseline.md`: test count per file and tier, line and branch coverage per layer, unit run time, spec vs feature scenario titles per capability (matched, spec-only, feature-only)
- [ ] 1.2 Add `mutmut` and `hypothesis` to the Poetry dev group; first `mutmut run` on `fingerprint/domain` and `fingerprint/service_layer`; record score, survivors and run time in `inputs/baseline.md` (P-7)

## 2. Fences and layout (no test content changes)

- [ ] 2.1 Move files into the P-1 layout (`tests/unit/<layer>/`, `tests/bdd/` from `tests/unit/steps/`, `tests/guards/`, `tests/fakes.py`); `pytest.ini` paths; the suite passes with the same count as 1.1
- [ ] 2.2 `.importlinter`: `root_packages = fingerprint tests` and the P-4 test contracts; `make check-architecture` keeps every existing contract and passes the new ones (Requirement: Fenced test tiers)
- [ ] 2.3 No-network autouse fixture in `tests/conftest.py`, with a guard test proving a socket connect fails under `tests/unit/` (Requirement: Fenced test tiers — Scenario: A unit test reaches the network)
- [ ] 2.4 Guard tests for the import contracts' scenario (a fixture module that violates a contract, checked through `lint-imports` on a temporary config), or an allow-list entry naming `make check-architecture` if that is not practical (Scenario: A domain test imports the service layer)

## 3. Traceability

- [ ] 3.1 `tests/guards/test_traceability.py` and `tests/guards/untraced_scenarios.txt` per P-3, including the stale-entry check (Requirement: Requirement-traced tests)
- [ ] 3.2 Align titles per capability: rename feature scenarios to the spec title; where the spec title is the less clear one, change it in this change's delta of that capability; add missing Gherkin scenarios for spec-only titles; remove or spec feature-only scenarios (`fingerprint-report`, `statistics-collection`, `profile-analytics`, `profile-representations`, and any capability merged before the start)
- [ ] 3.3 Allow-list entries for `developer-tooling` scenarios, each naming the guard test or check that proves it; the guard passes

## 4. Canonical sample data

- [ ] 4.1 `make refresh-sample-profile` and `make refresh-golden` (P-5, replacing `UPDATE_GOLDEN=1`); regenerate and confirm no data change against the stored files (Requirement: Canonical sample data — Scenario: Regenerating without a data change)
- [ ] 4.2 `tests/sample_data.py` with the `CONTINENTS` and `TREATIES` facts; `tests/conftest.py` session fixtures `sample_run`, `sample_analytics`, `sample_outputs`
- [ ] 4.3 `tests/builders.py` from the `fakes.py` builders, returning model objects; the nine files with inline raw profiles switched to fixtures and builders; bare numbers about the sample data replaced by `sample_data` names
- [ ] 4.4 Extend `test_a_live_collection_equals_the_sample_profile` to name the differing class or property on failure (Scenario: The stored profile drifts)

## 5. Shared steps and outputs

- [ ] 5.1 `tests/bdd/conftest.py` as the one step library; duplicated step definitions merged; one `test_<capability>.py` per feature file binding `scenarios()`
- [ ] 5.2 Turtle golden comparisons by isomorphism with the triple diff on failure (P-8); SHACL-validates-source check kept

## 6. Properties and gate

- [ ] 6.1 Hypothesis `ci` profile and `tests/unit/domain/strategies.py`; the P-9 properties; the parametrised example rows they cover removed per P-6
- [ ] 6.2 `make test`: `--cov-branch`, 90% overall, 100% `fingerprint/domain/` excluding generated modules (P-7); add the tests the gap list demands, in the tier P-2 names (Requirement: Coverage and mutation gate — Scenario: An untested domain branch)
- [ ] 6.3 `make check-mutation` and `tests/guards/mutation_score.txt` (P-7); report run time; developer decides where it runs (design Open Questions) and the CI workflow is updated accordingly (Scenario: The mutation score drops)

## 7. Remove redundancy

- [ ] 7.1 P-6 per module in `domain/`: delete tests another tier owns; one commit per module, coverage and killed-mutant set unchanged
- [ ] 7.2 P-6 per module in `adapters/` and `entrypoints/` (coverage unchanged; mutation not scored here)
- [ ] 7.3 P-6 per module in `service_layer/`
- [ ] 7.4 Surviving mutants: a test in the owning tier, or the dead code deleted and listed here; `mutation_score.txt` raised

## 8. Docs and conventions

- [ ] 8.1 `docs/modules/ROOT/pages/development.adoc`: the tiers, the ownership table (P-2), the canonical data and refresh targets, the gate
- [ ] 8.2 `AGENTS.md` *Working conventions*: one line for the test-tier rule and the sample-data rule, pointing at the docs page
- [ ] 8.3 Record the outcome in `inputs/baseline.md` (before/after: test count, run time, branch coverage, mutation score)

## Roadmap

- [x] 1.1 · [ ] 1.2 · [ ] 2.1 · [ ] 2.2 · [ ] 2.3 · [ ] 2.4 · [ ] 3.1 · [ ] 3.2 · [ ] 3.3 · [ ] 4.1 · [ ] 4.2 · [ ] 4.3 · [ ] 4.4 · [ ] 5.1 · [ ] 5.2 · [ ] 6.1 · [ ] 6.2 · [ ] 6.3 · [ ] 7.1 · [ ] 7.2 · [ ] 7.3 · [ ] 7.4 · [ ] 8.1 · [ ] 8.2 · [ ] 8.3

## Verification

`make check-all`, `make test-e2e` (after `make oxigraph-load-test-data`) and `make check-mutation` pass; `openspec validate lean-test-suite --strict`; the clarity gate scores design.md + tasks.md ≥9/10.
