> Derives from: EPIC lean-test-suite (proposal.md)

Starts after `readable-representations` (the namespace-prefixes work) is merged (DEC-10; met
2026-10-31, PR #42). Each task leaves `make test` green; deletions per module are their own commits
(design Risks). Requirements named below are in `specs/developer-tooling/spec.md` of this change.

## 1. Baseline

- [x] 1.1 Record the baseline in `inputs/baseline.md`: tests per file and tier, coverage per layer, run time, spec vs feature titles per capability
- [ ] 1.2 `hypothesis` and `mutmut` pinned in the Poetry `test` group; `[tool.mutmut]` per P-7; first `mutmut run`; score, survivors, run time and the needed `also_copy` recorded in `inputs/baseline.md` (P-7; DEC-6)

## 2. Fences and layout (test content unchanged)

- [x] 2.1 Move files to the P-1 layout, with an `__init__.py` in every new test directory; `pytest.ini`; `make test` runs `pytest tests --ignore=tests/e2e`; the suite passes with the baseline count (Requirement: Fenced test tiers; P-1)
- [x] 2.2 `.importlinter`: `root_packages` (one per line) and the P-4 test contracts; the four existing contracts still kept (Requirement: Fenced test tiers; P-4)
- [x] 2.3 No-network autouse fixture and TC-4 (Requirement: Fenced test tiers — Scenario: A unit test reaches the network)
- [x] 2.4 TC-5: pytest wrapper running `lint-imports` on a temporary tree with a violating domain test (Scenario: A domain test imports the service layer)

## 3. Traceability

- [x] 3.1 `tests/guards/traceability.py` (`trace()`) with TC-1..TC-3 on `tmp_path` trees; the real-tree test written but marked `xfail(strict=True)` until 3.7 (Requirement: Requirement-traced tests; P-3)
- [x] 3.2 Align `fingerprint-report`: feature titles renamed to spec titles; spec-only scenarios get Gherkin; feature-only scenarios deleted or added to the spec through a MODIFIED delta in this change (P-3; design Risks)
- [x] 3.3 Align `namespace-prefixes` (as 3.2; 11 spec scenarios lack Gherkin today)
- [x] 3.4 Align `profile-analytics` (as 3.2)
- [x] 3.5 Align `profile-representations` (as 3.2)
- [x] 3.6 Align `statistics-collection` (as 3.2; 1 of 29 titles matches today)
- [ ] 3.7 `tests/guards/untraced_scenarios.txt` for `developer-tooling` (each entry a pytest node id); `xfail` removed; the guard passes (Requirement: Requirement-traced tests)

## 4. Canonical sample data

- [ ] 4.1 `same_profile()` in `tests/sample_data.py`; `tests/refresh_sample_data.py`; `make refresh-sample-profile` and `make refresh-golden` (replacing `UPDATE_GOLDEN=1`); IT-1 (Requirement: Canonical sample data — Scenario: Regenerating without a data change; P-5)
- [ ] 4.2 `CONTINENTS` and `TREATIES` facts; session fixtures `sample_run`, `sample_analytics`, `sample_outputs` (Requirement: Canonical sample data; P-5)
- [ ] 4.3 `tests/builders.py` returning model objects; `tests/fakes.py` keeps only the doubles (P-5; DEC-5)
- [ ] 4.4 Domain-tier tests switched from inline raw profiles and bare numbers to builders, fixtures and named facts (DEC-4, DEC-5)
- [ ] 4.5 Adapter-, service- and entrypoint-tier tests switched likewise (DEC-4, DEC-5)
- [ ] 4.6 Gherkin steps switched likewise (DEC-4, DEC-5)
- [ ] 4.7 The drift test names the differing class or property on failure; IT-2 (Scenario: The stored profile drifts)

## 5. Shared steps and outputs

- [ ] 5.1 `tests/bdd/conftest.py` as the one step library: duplicated step definitions merged (P-1; DEC-2)
- [ ] 5.2 One `tests/bdd/test_<capability>.py` per feature file binding `scenarios()`; old step modules removed (P-1)
- [ ] 5.3 Turtle golden comparisons by isomorphism with the triple diff; TC-8; SHACL-validates-source kept (Requirement: Generated outputs compared by meaning; P-8)

## 6. Properties and gate

- [ ] 6.1 Hypothesis `ci`/`dev` profiles in `tests/conftest.py`; `tests/unit/domain/strategies.py` (P-9)
- [ ] 6.2 The P-9 properties; the example rows they cover removed per P-6 (DEC-7)
- [ ] 6.3 `make test` with `--cov-branch`, 90% overall and 100% `domain/` (generated excluded); missing tests added in the tier P-2 names; TC-7 (Requirement: Coverage and mutation gate — Scenario: An untested domain branch; P-7)
- [ ] 6.4 `make check-mutation`, `tests/guards/mutation_score.py` + TC-6, `tests/guards/mutation_score.txt`; full-run time recorded; CI job added per the design's Open Questions rule (Scenario: The mutation score drops; P-7)

## 7. Remove redundancy (P-6)

- [ ] 7.1 `domain/` modules: tests another tier owns deleted, one commit per module, coverage and killed set unchanged
- [ ] 7.2 `service_layer/` modules, likewise
- [ ] 7.3 `adapters/` and `entrypoints/` modules (coverage and P-2 ownership)
- [ ] 7.4 `tests/e2e/`: tests that never reach the store deleted or moved (P-2)
- [ ] 7.5 Surviving mutants: a test in the owning tier, or the dead code deleted and listed here; `mutation_score.txt` raised

## 8. Docs and conventions

- [ ] 8.1 `docs/modules/ROOT/pages/development.adoc`: tiers, the P-2 ownership table, canonical data and refresh targets, the gate
- [ ] 8.2 `AGENTS.md` *Working conventions*: the test-tier and sample-data rules (pointing at the docs page) and the moved path of `test_no_composed_dicts.py`
- [ ] 8.3 Outcome in `inputs/baseline.md`: before/after test count, run time, branch coverage, mutation score

## Roadmap

- [x] 1.1 · [ ] 1.2 · [x] 2.1 · [x] 2.2 · [x] 2.3 · [x] 2.4 · [x] 3.1 · [x] 3.2 · [x] 3.3 · [x] 3.4 · [x] 3.5 · [x] 3.6 · [ ] 3.7 · [ ] 4.1 · [ ] 4.2 · [ ] 4.3 · [ ] 4.4 · [ ] 4.5 · [ ] 4.6 · [ ] 4.7 · [ ] 5.1 · [ ] 5.2 · [ ] 5.3 · [ ] 6.1 · [ ] 6.2 · [ ] 6.3 · [ ] 6.4 · [ ] 7.1 · [ ] 7.2 · [ ] 7.3 · [ ] 7.4 · [ ] 7.5 · [ ] 8.1 · [ ] 8.2 · [ ] 8.3

## Verification

`make check-all`, `make test-e2e` (after `make oxigraph-load-test-data`) and `make check-mutation` pass; `openspec validate lean-test-suite --strict`; the clarity gate scores design.md + tasks.md ≥9/10.
