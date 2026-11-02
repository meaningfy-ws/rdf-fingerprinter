> Derives from: EPIC lean-fast-suite (`proposal.md`, DEC-1 to DEC-9); design in `design.md` (P-1 to P-7).

Work in the worktree `/home/lps/work/repos/rdf-fingerprinter-lean-fast-suite` (branch
`feature/lean-fast-suite`, off `develop`); source `temp/env.sh` before any `poetry`/`make` command
so its own `.venv` is used, never the shared one. Each task is test-first where it adds behaviour
(`superpowers:test-driven-development`): the named guard tests red, then the change, then green.
Every task ends with `make check-all` green (from 2.3 on, the new gate). One commit per task
(`Refs: lean-fast-suite DEC-n / P-n`), by the leader. Before editing an existing symbol, run GitNexus
impact (`AGENTS.md`, "Implementation loop"); stop and report HIGH/CRITICAL. No production code
under `fingerprint/` changes (No-gos); a test that reveals a bug is reported, not fixed.

## 1. Spec binding

- [x] 1.1 Bind the delta's new scenarios (design P-7 map): write the four new wiring tests in
  `tests/guards/test_repository_wiring.py` red, update `test_check_all_runs_every_static_check_and_the_tests`
  (check-all = check-quality + test), delete `test_the_fast_gate_skips_the_property_tests` and
  `test_the_deep_gate_runs_weekly_and_on_demand`, and update `tests/guards/untraced_scenarios.txt`
  (two entries out, four in, "Mutation score drops" reason no longer says weekly).
  Each new or updated wiring test carries `@pytest.mark.xfail(strict=True, reason="until task <n>")` naming the
  task that makes it pass (table at the end); that task removes the marker, so the gate stays green
  between tasks and a test that passes early fails loudly. Commit 1.1 together with the PLAN: the
  guard counts this delta as soon as `tasks.md` exists.
  **Acceptance:** `make check-all` green; the four new tests and the updated one report `xfailed`.

## 2. One parallel feature gate (DEC-4, DEC-7; P-1, P-2)

- [x] 2.1 Add `pytest-xdist` to the dev group (`poetry add --group dev pytest-xdist`); register the
  `release` marker in `pytest.ini`; mark `test_shapes_report_no_violation_on_their_own_data` with it
  (P-2). **Acceptance:** `pytest --collect-only -m release -q` lists the 9 cases and nothing else.
- [x] 2.2 Run `pytest tests --ignore=tests/e2e -m "not release" -n auto --hypothesis-profile=ci`
  twice; fix any test that fails only in parallel (tmp paths, global state — error matrix), never by
  serialising it. Check the domain coverage report still lists `fingerprint/domain/*` under xdist.
  **Acceptance:** two consecutive parallel runs green with equal pass counts.
- [x] 2.3 Makefile (P-1): `test` (parallel, Hypothesis `ci`, `-m "not release"`, floors),
  `check-all: check-quality test`, `test-release`, `test-properties`, `check-release`; delete
  `test-fast`, `check-all-fast`, `check-all-deep`; split `load-test-data` out of
  `oxigraph-load-test-data` (P-6). **Acceptance:** wiring tests "The gate runs every
  self-contained test" and "The release gate runs what the feature gate leaves out" green;
  `make check-all` green.
- [x] 2.4 Measure (DEC-4 checkpoint): `make test` wall time ×2, test count, package and domain
  branch coverage; write them into the commit body. **Acceptance:** numbers recorded; coverage
  equal to the seed (99% / 100%).

## 3. Cheaper scenarios and domain proof (P-4, P-5; DEC-9)

- [x] 3.1 Pitfall scenarios go/no-go (P-4): time the 18 pitfall scenarios under `-n auto`
  (`--durations`); if under 10% of 2.4's `make test`, record "skipped, below threshold" in the
  commit and tick the task. Otherwise narrow the catalogue in `tests/bdd/steps/pitfalls.py` per P-4,
  leaving the four whole-catalogue scenarios unnarrowed. **Acceptance:** `pytest tests/bdd/test_pitfall_scans.py`
  green; no `.feature` text changed.
- [x] 3.2 `patterns.py` example tests (P-5) in `tests/unit/domain/test_patterns.py`. **Acceptance:**
  `pytest tests/unit/domain -m "not hypothesis" --cov=fingerprint.domain.patterns --cov-branch --cov-report=term-missing`
  shows 100% for `fingerprint/domain/patterns.py`.

## 4. Prune `tests/unit/service_layer` (DEC-1, DEC-2; P-3)

- [ ] 4.1 Baseline: `make check-mutation` on the tree after 3.2 (background, ~1 h); save
  `temp/mutation-baseline.txt` (`mutmut results --all true`) and `temp/coverage-baseline.json`
  (`coverage json` of `make test`). Not committed (temp/). **Acceptance:** both files exist; the
  score ≥ `tests/guards/mutation_score.txt`.
- [ ] 4.2 Prune for `collection.py` (`test_collection.py`), per P-3 steps 2–5.
- [ ] 4.3 Prune for `representations.py` and the generators (`test_representations.py`,
  `test_document.py`, `test_generator.py`, `test_pattern.py`, `test_plantuml.py`, `test_shacl.py`,
  `test_shex.py`, `test_pitfalls_tsv.py`), one P-3 run per module, one commit for the group.
- [ ] 4.4 Prune for `handlers.py`, `settings.py`, `prefixes.py` (`test_handlers.py`,
  `test_settings.py`, `test_config.py`, `test_prefixes.py`, `test_pitfall_scan.py`).
  **Acceptance (each of 4.2–4.4):** per-file branch coverage and each module's killed-mutant set
  equal to the baseline; commit body lists tests before/after and every restored test with its reason.

## 5. Close the measurement (DEC-2, DEC-4)

- [ ] 5.1 Full `make check-mutation` on the pruned tree; commit `tests/guards/mutation_score.txt`
  if it rose. **Acceptance:** exit 0 (score not below the stored one).
- [ ] 5.2 Re-measure as in 2.4 and fill the before/after table. If `make test` is clearly slower than 152 s (over 167 s, design P-1),
  stop and ask the developer about a no-coverage local variant (DEC-4 checkpoint).
  **Acceptance:** table in the commit body.

## 6. CI (DEC-6; P-6)

- [ ] 6.1 `release-check.yml` (PR into `master` + dispatch: Oxigraph service, `make load-test-data`,
  `make test-release test-e2e`, wheel install + `fingerprint --help`); delete `deep.yml`;
  `mutation.yml` on `release: published` + dispatch, no schedule; `ci.yml` comment updated.
  **Acceptance:** wiring tests "A release PR runs the release checks" and "Mutation testing runs
  after a release" green; `make check-all` green.
- [ ] 6.2 Local release gate: `make oxigraph-load-test-data` then `make check-release`.
  **Acceptance:** exit 0. (Exercising `release-check.yml` on GitHub needs a push — the developer decides.)

## 7. Docs and rules

- [ ] 7.1 `docs/modules/ROOT/pages/development.adoc`: the gate table (`#test-gate`) and the tier
  profile (`#test-profile`) rewritten for the feature gate / release gate, with 5.2's numbers and
  the session table (coding loop, feature, after a domain or adapter change, release, after release);
  `#test-mutation` says "after a release" instead of weekly. `AGENTS.md`: *Make targets* and
  *Release authority* (`make check-release` replaces "`make check-all` and `make test-e2e`").
  `CHANGELOG.md`: Unreleased entry, removed targets marked BREAKING for contributors.
  **Acceptance:** `make check-all` green (incl. `check-spec`); no remaining mention of
  `check-all-fast`, `check-all-deep`, `test-fast` or `deep.yml` outside `openspec/changes/archive/`
  and `CHANGELOG.md` history (`grep -rn`).

## Scenario → task

| Scenario (developer-tooling) | Green after |
|---|---|
| Single quality gate › Clean tree passes (updated) | 2.3 |
| Single quality gate › The gate runs every self-contained test | 2.3 |
| Release gate › The release gate runs what the feature gate leaves out | 2.3 |
| CI runs the gate › A release PR runs the release checks | 6.1 |
| Coverage and mutation gate › Mutation testing runs after a release | 6.1 |
