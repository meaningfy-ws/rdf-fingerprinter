# EPIC: A lean feature gate and a release gate

> Parents: capability `developer-tooling` (Requirement: Single quality gate; Requirement: CI runs
> the gate; Requirement: Local end-to-end tests; Requirement: Requirement-traced tests); the
> archived `2026-11-01-lean-test-suite` change, whose DEC-2 (one owning tier per check) and design
> P-6 (redundancy removal) this EPIC finishes for the service layer; seeds in
> `inputs/seeds-2026-11-02.md`, decisions in `inputs/qa-round-1.md`.

## Appetite

MEDIUM — the test suite, the make targets and the CI workflows change; no production code does.
One tier (`tests/unit/service_layer`) is pruned, the fast/deep split is replaced by a feature gate
and a release gate, and the runner gains parallelism. Other tiers are touched only where a slow
scenario is made cheaper or `fingerprint/domain/patterns.py` gains its unit tests.

## Why

`make check-all` is the gate a developer runs on every feature and CI runs on every PR, yet it takes
over 5 minutes: 2.5 minutes of tests, doubled by coverage. Most of that time proves things twice:
the 396 service-layer unit tests reach only 75 lines and 26 branches that the BDD scenarios do not,
and one SHACL check runs both as a scenario and as a 9-case unit test. A slow gate gets skipped, and
a skipped gate catches nothing.

The fast/deep split (d5a76c0, 2026-11-01) answered the slowness by moving checks out of the way.
It sorts by cost, not by purpose: the deep gate differs from the fast one only by 18 Hypothesis
tests and the coverage minimums, both cheap once the suite runs in parallel, while the checks that
really need more — a SPARQL store, fresh random inputs, an hour of mutation testing — sit outside
both gates with no rule for when they run.

## Solution outline

Tests keep their folders by tier (`tests/unit/<layer>`, `tests/bdd`, `tests/guards`, `tests/e2e`):
the folder says who owns a check. Which tests run, and when, is decided by **what a run is for**:

| Run | When | Contains |
|---|---|---|
| Coding loop | while editing, no rule | the tests of the layer or file being changed |
| **Feature gate** — `make check-all` | every task or feature, before every push; CI on every PR | static checks; every self-contained test (unit, BDD, guards) in parallel; Hypothesis on the repeatable `ci` profile; the coverage minimums |
| **Release gate, local** — `make check-release` | before every release | the feature gate; `make test-properties` (Hypothesis with fresh random inputs); `make test-e2e` against the local Oxigraph |
| **Release gate, CI** | on every PR into `master` (only release PRs go there) | the feature gate plus the release-only checks of DEC-6 |

`make test-properties` and `make test-e2e` also have a trigger of their own in the coding loop:
after a change to `fingerprint/domain/` and to the adapters or queries respectively.

To make the feature gate fast enough to hold everything self-contained:

1. **BDD proves the service layer.** `tests/unit/service_layer` keeps only the tests that prove a
   branch or error path no scenario reaches, each named for what it alone proves.
2. **A check is proven once.** A check proven by a spec scenario is not proven again by a unit
   test; extra depth worth keeping (more inputs, more thresholds) moves to the release gate.
3. **Slow scenarios do only the work they assert.** A pitfall-scan scenario runs the checks it is
   about, not the whole catalogue.
4. **The suite runs in parallel.**
5. **Domain rules are proven in the domain tier.** `fingerprint/domain/patterns.py` gets plain unit
   tests.

The outcome has no fixed time budget: it is measured against the seed profile. The feature gate's
test count and wall time go down; branch coverage (99% package, 100% domain) and the mutation score
do not. The PLAN records the before and after.

## Key decisions

- **DEC-1 BDD owns the service layer's behaviour; the service unit tier keeps only the residue.**
  lean-test-suite DEC-2, applied to the tier where it was not finished — BDD already covers 93% of
  `fingerprint/service_layer/` alone. Rejected: keeping both tiers (double cost, no extra proof);
  moving all service tests into BDD (an error path with no user-visible scenario would need an
  invented one).
- **DEC-2 A deletion stays only when branch coverage and the killed-mutant set are unchanged,
  checked per module.** Delete a module's batch of candidates, run coverage and one mutmut run over
  that module, and restore any test whose loss drops either. Rejected: coverage plus the final
  mutation score only (a lost kill can hide behind a gain elsewhere); a mutmut run per deleted test
  (days of compute).
- **DEC-3 Tests are organised by tier and run by purpose.** Folders stay by tier, so ownership and
  the import fences hold; runs are the feature gate and the release gate. Rejected: grouping by
  cost (`slow` markers rot and hide important checks); by capability tags (every unit test would
  need tagging); a curated smoke set (a duplicate of other tests); test selection by change impact
  (a later, separate change — see No-gos).
- **DEC-4 One feature gate replaces `check-all-fast` and `check-all-deep`**, the same locally and in
  CI: static checks, every self-contained test, Hypothesis on the `ci` profile, the coverage
  minimums. This reverses d5a76c0's split. *Checkpoint:* the PLAN measures the gate after DEC-1,
  DEC-5 and DEC-7; if it is still clearly slower than the seed's 152 s serial run without coverage,
  a no-coverage local variant returns, decided on those numbers ("clearly": over 167 s, design P-1). Rejected: keeping two gates that
  differ by seconds; coverage only in CI (a local run could pass and the PR fail on a minimum).
- **DEC-5 The release gate holds what needs more than the feature gate.** Locally,
  `make check-release` = `make check-all` + `make test-properties` + `make test-e2e`. Extra depth
  moved out of the feature gate (first case: the 3 graphs × 3 thresholds matrix of "Shapes report
  no violation on their own data", behind a marker) runs here. Rejected: deleting that matrix (the
  0.1 and 0.5 thresholds would lose their check).
- **DEC-6 CI distinguishes the PR run from the release run.** Every PR runs the feature gate; a PR
  into `master` also runs the release-only checks, so they block the merge before anything is
  tagged. The release-only checks are the e2e tests against an Oxigraph service container loaded
  with `tests/test_data`, and a build-and-install check of the wheel (install it in a clean venv,
  run `fingerprint --help`). The mutation ratchet runs *after* a release, on the published GitHub
  Release and on demand, never blocking one; its weekly schedule goes. Rejected: running the release
  checks in `publish.yml` (a failure would come after the tag exists); mutation testing in the
  release check (an hour on every release PR).
- **DEC-7 Run the suite in parallel with pytest-xdist**, a new dev dependency, in the feature gate.
  e2e and mutmut stay serial. Rejected: staying serial (pruning alone leaves 12 cores idle).
- **DEC-8 `make test-properties` runs the Hypothesis tests on the `dev` profile** (fresh random
  inputs): the only run that can find a new counter-example, since the `ci` profile replays the
  same inputs. Locally only, after a domain change and in the release gate; never in CI, where a
  random failure could not be reproduced. Rejected: relying on the gates' `ci` profile (it finds
  nothing new).
- **DEC-9 `fingerprint/domain/patterns.py` gets plain unit tests in `tests/unit/domain`**, enough
  that the feature gate keeps 100% domain branch coverage without the BDD scenarios — lean-test-suite
  P-2 puts domain rules in the domain tier. Rejected: leaving its proof to BDD and Hypothesis.

## Rabbit-holes

- **Coverage as the only judge.** A test can add no line yet kill a mutant; DEC-2 exists so that
  coverage alone never deletes a test.
- **Session fixtures under xdist.** `sample_run` and `sample_outputs` are built once per worker; if
  that dominates, tune the worker count or the fixture, not a cache shared across processes.
- **mutmut and xdist together.** mutmut runs its own test process; keep it serial.
- **Hypothesis under xdist.** Check that the `ci` profile's examples stay reproducible per test
  when the tests are spread across workers.
- **Rewriting scenarios to make them fast.** Narrow what a slow scenario runs; never weaken what it
  asserts or change its spec title.
- **CI runner size.** GitHub's hosted runners have 4 vCPUs; xdist gains less there than on a
  12-core laptop.

## No-gos

- No production code changes; a test that reveals a bug is reported, not fixed here.
- No change to the spec scenarios or their titles, and no Gherkin scenario invented to carry a
  deleted unit test.
- No change to the coverage minimums (90% package, 100% domain) or the mutation-score ratchet.
- No fixed time budget; the outcome is "lower, with the same proof".
- No pruning of `tests/unit/domain`, `tests/unit/adapters`, `tests/unit/entrypoints`,
  `tests/guards` or `tests/e2e`.
- No randomised Hypothesis in CI, and no mutation testing that blocks a merge or a release.
- No new test folder or tier, no `slow`/cost markers, and no test-selection tooling (pytest-testmon,
  impact-based runs) — a candidate follow-up change for the coding loop.

---

## What Changes

- Prune `tests/unit/service_layer/` to the tests that prove a branch or error path no scenario
  reaches (DEC-1, DEC-2).
- `Makefile`: `check-all` becomes the feature gate (parallel, Hypothesis `ci`, coverage
  minimums); **BREAKING** for developers: `check-all-fast` and `check-all-deep` are removed. New
  `check-release` and `test-properties` (DEC-4, DEC-5, DEC-8).
- Mark the SHACL threshold matrix in `tests/unit/service_layer/test_representations_golden.py` as
  release-only; register the marker in `pytest.ini` (DEC-5).
- Narrow the pitfall-scan BDD steps (`tests/bdd/steps/pitfalls.py`) to the checks each scenario
  asserts.
- Add pytest-xdist to the dev dependencies (DEC-7).
- Add plain unit tests for `fingerprint/domain/patterns.py` (DEC-9).
- CI: `ci.yml` runs `make check-all` on every PR; a release job runs on PRs into `master`;
  `deep.yml` goes; `mutation.yml` runs on a published release and on demand instead of weekly (DEC-6).
- Docs and agent rules: the tier profile and gate table in
  `docs/modules/ROOT/pages/development.adoc`; *Make targets* and *Release authority* in
  `AGENTS.md` (the release checklist becomes `make check-release`).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `developer-tooling`: the single quality gate holds every self-contained test and runs them in
  parallel (Requirement: Single quality gate); CI runs it on every PR and the release checks on PRs
  into `master` (Requirement: CI runs the gate); the release gate runs the e2e tests and the
  randomised properties (Requirement: Local end-to-end tests; possibly a new requirement for the
  release gate — settled in the PLAN).

## Impact

- `tests/unit/service_layer/` (most files shrink), `tests/unit/domain/test_patterns.py`,
  `tests/bdd/steps/pitfalls.py`, `tests/unit/service_layer/test_representations_golden.py`,
  `pytest.ini`, `Makefile`, `pyproject.toml` / `poetry.lock`.
- `.github/workflows/ci.yml`, `deep.yml` (removed), `mutation.yml`, a release job.
- `AGENTS.md`, `docs/modules/ROOT/pages/development.adoc`, `CHANGELOG.md` (the removed targets).
- `tests/guards/mutation_score.txt` may rise; it must not fall.
