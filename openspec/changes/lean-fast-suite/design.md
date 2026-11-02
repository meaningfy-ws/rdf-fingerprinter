> Derives from: EPIC lean-fast-suite (`proposal.md`, DEC-1 to DEC-9). Parent change:
> `../archive/2026-11-01-lean-test-suite/` (DEC-2, P-2, P-6). Replaces the fast/deep split that
> `../archive/2026-11-02-llm-schema-split/` introduced (released in 3.4.0).

## Context

Measured 2026-11-02 (`inputs/seeds-2026-11-02.md`): the self-contained suite is 1,518 tests plus
18 Hypothesis properties; 152 s serial without coverage, 318 s with branch coverage. Unit
`service_layer` (396 tests) and `tests/bdd` (314) each take ~2.5 min under coverage and each cover
93–94% of the package alone; the service unit tier reaches only 75 lines / 26 branches of
`fingerprint/service_layer/` that BDD does not. The make targets today (`develop` at c105d79): `check-all` = `check-all-fast` = `check-quality` +
`test-fast` (no Hypothesis, coverage reported, no floor); `check-all-deep` = `check-quality` +
`test` (Hypothesis `ci`, floors 90% / 100% domain). `ci.yml` runs `check-all` on 3.12–3.14 and
uploads `coverage.xml` to Codecov from 3.14; `deep.yml` runs `check-all-deep` weekly;
`mutation.yml` runs `check-mutation` weekly.

## Goals / Non-Goals

**Goals:** one feature gate (`make check-all`) holding every self-contained test with the coverage
floors, run in parallel; a release gate, local (`make check-release`) and in CI (PRs into `master`);
the service unit tier pruned to its residue; the feature gate's wall time and test count lower than
the seed's, with coverage and the mutation score not lower.

**Non-Goals:** the EPIC's No-gos apply unchanged.

## P-1 Targets (DEC-4, DEC-5, DEC-7, DEC-8)

| Target | Recipe | Replaces |
|---|---|---|
| `test` | `pytest tests --ignore=tests/e2e -m "not release" -n auto --hypothesis-profile=ci --cov=fingerprint --cov-branch --cov-report=term:skip-covered --cov-report=xml:coverage.xml --cov-fail-under=90 --junitxml=junit_report.xml`, then the domain report `--fail-under=100` (unchanged) | `test`, `test-fast` |
| `check-all` | `check-quality test` | `check-all-fast`, `check-all-deep` |
| `test-release` | `pytest tests --ignore=tests/e2e -m release -n auto --hypothesis-profile=ci` (no coverage) | — |
| `test-properties` | `pytest tests --ignore=tests/e2e -m hypothesis -n auto --hypothesis-profile=dev` (no coverage) | — |
| `check-release` | `check-all test-release test-properties test-e2e` | — |
| `test-e2e`, `check-mutation` | unchanged, serial | — |

`check-all-fast`, `check-all-deep` and `test-fast` are deleted, not aliased (DEC-4: one gate; an
alias would keep the old vocabulary alive). `pytest.ini` registers `release: runs only in the release
gate (make check-release); deep extra depth of a check the feature gate already proves`.
`pytest-xdist` joins the dev group in `pyproject.toml`; `-n auto` uses every core.

**Checkpoint (DEC-4).** Task 2.4 measures `make test` (with coverage) after the parallel run lands,
and again at 5.2 after pruning. If the final `make test` is clearly slower than the seed's 152 s (more than 10%, i.e. over 167 s), the
developer is asked whether a no-coverage local variant returns; the PLAN does not pre-build it.

## P-2 The release marker (DEC-5)

First and only use in this change: `test_shapes_report_no_violation_on_their_own_data` in
`tests/unit/service_layer/test_representations_golden.py` gets `@pytest.mark.release`. The BDD
scenario "Shapes report no violation on their own data" stays in the feature gate. The marker is for
*extra depth of a check the gate already proves*, never for a check proven nowhere else — the
traceability guard keeps the spec scenario bound to its Gherkin, which `release` never marks.

## P-3 Pruning procedure for `tests/unit/service_layer` (DEC-1, DEC-2)

Per module `M` of `fingerprint/service_layer/` (the order of task group 4):

1. **Baseline** (once, task 4.1): a full `make check-mutation` on a clean tree; save
   `mutmut results --all true` as `temp/mutation-baseline.txt` (killed / survived per mutant name),
   and the per-file branch coverage of `make test` as `temp/coverage-baseline.json`.
2. **Candidates:** every test in `tests/unit/service_layer/test_<M>.py` (and the files that test `M`
   indirectly, by the GitNexus `context` of `M`'s public functions) that is *not* one of:
   (a) a test named in `tests/guards/untraced_scenarios.txt` as the proof of a spec scenario —
   never deleted; (b) a test that alone reaches a line or branch of `M` the BDD tier does not:
   derived by running `pytest tests/unit/service_layer tests/bdd --cov=fingerprint --cov-branch
   --cov-context=test` and keeping every unit test whose context covers a line or arc of `M` no `tests/bdd`
   context covers; (c) a golden-file test (`test_representations_golden.py`
   compares outputs as a whole — it stays, P-2 aside).
3. **Delete the batch**, then `make test` (coverage), then `rm -rf mutants` and
   `poetry run mutmut run "fingerprint.service_layer.<M>*"` (the mutants of `M` only; mutmut 3.8
   filters mutant names with `fnmatch`). Removing `mutants/` is mandatory: `also_copy` includes
   `tests/`, copied with `copytree(dirs_exist_ok=True)`, so a deleted test file would survive in
   `mutants/tests/` and keep killing mutants; it also rebuilds `mutmut-stats.json`.
4. **Compare:** branch coverage of every file equal to the baseline, and the killed set of `M`'s
   mutants (names starting `fingerprint.service_layer.<M>`) equal to the baseline's, compared on those names only. Any loss → restore candidates one at a time (bisect the batch)
   until both are equal; each restored test is renamed to say what it alone proves (P-6 step 3).
5. **Record** in the task's commit body: tests before/after, restored tests and why.

`M` with no unit test of its own but covered through another file's tests is pruned with the file
that tests it. Hypothesis-marked tests are never candidates.

## P-4 Pitfall-scan scenarios (EPIC outline 3)

Each scenario in `tests/features/pitfall_scans.feature` drives the CLI over `FakeSparql`, and the
packaged catalogue runs every check as rdflib SPARQL (~2 s per scenario). The `Given` store fixture
in `tests/bdd/steps/pitfalls.py` gains a narrowed catalogue: `fingerprint.adapters.pitfall_catalogue.packaged_checks` monkeypatched (`load_catalogue` calls it;
neither `handlers.py` nor `cli/main.py` imports it directly) to return the checks the scenario's `Then` steps name, plus one check per scope
(`data`, `schema`) so scope routing still runs. Scenarios whose assertion is about the whole
catalogue keep it unnarrowed: "Catalogue size", "Schema checks run once, on the schema graph",
"Checks run on the worker pool", "Offline". A scenario's assertions and titles do not change.

**Go/no-go:** task 3.1 first measures the 18 pitfall scenarios under `-n auto`; if their summed time
is under 10% of the parallel `make test`, the narrowing is skipped and recorded as such (the EPIC's
outcome is met by DEC-7 alone for this tier).

## P-5 `patterns.py` unit tests (DEC-9)

`tests/unit/domain/test_patterns.py` gains plain example tests (no `@given`) until
`pytest tests/unit/domain -m "not hypothesis" --cov=fingerprint.domain.patterns --cov-branch`
reports 100% branch coverage of `fingerprint/domain/patterns.py`. Inputs come from
`tests/builders.py` and `sample_run.model_copy` (canonical data rule). Each test asserts a named
fact, not a re-computation.

## P-6 CI (DEC-6)

- `ci.yml`: unchanged trigger (push and PR to `master`, `develop`), runs `make check-all` (now with
  Hypothesis and floors), Codecov upload unchanged.
- New `release-check.yml` (named apart from `publish.yml`, which the "Tokenless release" requirement already calls the release workflow): `on: pull_request: branches: [master]` and `workflow_dispatch`. Job `release`
  (Python 3.12, one version): service container `ghcr.io/oxigraph/oxigraph:0.5.13` (the image
  `docker/docker-compose.yml` pins) on port 7878, started in memory as compose does; the Makefile's
  curl recipe moves from `oxigraph-load-test-data` into a new `load-test-data` target (no
  `start-oxigraph` prerequisite), and `oxigraph-load-test-data: start-oxigraph load-test-data`
  keeps the local behaviour. CI: wait for the endpoint (`curl` loop, ≤ 60 s), `make load-test-data`,
  `make test-release test-e2e` (`test-release` carries DEC-5's release-only depth, so the CI release
  check proves what the local release gate does, randomised properties apart; endpoint default `http://localhost:7878/query`), then
  `make build`, a fresh venv under `$RUNNER_TEMP`, `pip install dist/*.whl`, `fingerprint --help`.
  `test-properties` is local only (DEC-8: no randomness in CI); `check-all` already ran in `ci.yml`.
- `deep.yml`: deleted.
- `mutation.yml`: `on: release: types: [published]` and `workflow_dispatch`; the `schedule` goes.

## P-7 Spec, guards and allow-list

The delta (`specs/developer-tooling/spec.md`) MODIFIES "Single quality gate", "CI runs the gate",
"Local end-to-end tests", "Coverage and mutation gate", and ADDS "Release gate". Each MODIFIED
requirement is restated in full, so the traceability guard (which applies MODIFIED as a
replacement) and the archiver both drop what it leaves out. The scenarios "The fast gate skips the property
tests" and "The deep gate runs weekly" disappear with the MODIFIED requirement text; their entries
in `tests/guards/untraced_scenarios.txt` and their tests in `tests/guards/test_repository_wiring.py`
are replaced by the new scenarios' (scenario → test map below). The traceability guard counts this
change's delta from the moment `tasks.md` exists, so task 1.1 binds every new scenario.

### Scenario → test map (all `developer-tooling`, proven by guard tests, listed in the allow-list)

| Requirement › Scenario | Test (`tests/guards/test_repository_wiring.py`) |
|---|---|
| Requirement › Scenario | Test | Asserts |
|---|---|---|
| Single quality gate › Clean tree passes | `test_check_all_runs_every_static_check_and_the_tests` (updated) | `check-all`'s prerequisites are `check-quality` and `test`; `check-quality` runs lint, typecheck, architecture, models, spec |
| Single quality gate › The gate runs every self-contained test | `test_the_gate_runs_the_properties_in_parallel_with_the_floors` | the `test` recipe has `-n auto`, `--hypothesis-profile=ci`, `-m "not release"`, `--ignore=tests/e2e`, `--cov-fail-under=90`, and the domain report `--fail-under=100` |
| Release gate › The release gate runs what the feature gate leaves out | `test_check_release_runs_the_release_tests_the_random_properties_and_e2e` | `check-release`'s prerequisites are `check-all test-release test-properties test-e2e`; `test-release` selects `-m release`; `test-properties` selects `-m hypothesis` with `--hypothesis-profile=dev` |
| CI runs the gate › A release PR runs the release checks | `test_the_release_check_runs_e2e_on_a_store_and_installs_the_wheel` | `release-check.yml` triggers on `pull_request` to `master` (and `workflow_dispatch`), declares an `oxigraph` service, runs `make load-test-data`, `make test-release`, `make test-e2e`, installs `dist/*.whl` with pip and runs `fingerprint --help` |
| Coverage and mutation gate › Mutation testing runs after a release | `test_mutation_runs_after_a_release_and_on_demand` | `mutation.yml` triggers on `release` `published` and `workflow_dispatch`, has no `schedule`, runs `make check-mutation` |

These are wiring tests (they read the Makefile / workflow YAML), the same kind as the scenarios they
replace; running the gate, GitHub execution and branch protection are not tested.

## Error matrix

| Situation | Outcome |
|---|---|
| A test is not safe in parallel (shared file, global state) under `-n auto` | the test is fixed to use `tmp_path`/fixtures; never `-n 0` for the suite. Recorded in task 2.2 |
| Hypothesis `ci` examples differ per worker | the `ci` profile is derandomised per test (seeded from the test's id), so placement does not matter; 2.2 runs `make test` twice and compares the Hypothesis statistics |
| Coverage under xdist misses the domain report | pytest-cov combines worker data before `coverage report`; 2.2 checks the domain report still lists `fingerprint/domain/*` |
| A pruned batch loses coverage or a kill | bisect and restore (P-3 step 4) |
| A deleted test still kills mutants | `mutants/` was not removed before the run; remove it and rerun (P-3 step 3) |
| The Oxigraph service container is not reachable in CI | `release-check.yml` waits on `curl` to the endpoint (≤ 60 s) and fails naming the endpoint |

## Verification

- Before/after table in the 5.2 commit and in `docs/modules/ROOT/pages/development.adoc`
  (`#test-profile`): test counts per tier, `make test` wall time, branch coverage (package, domain),
  mutation score.
- `make check-all` green; `make check-release` green against `make oxigraph-load-test-data`.
- `release-check.yml` is exercised once by `workflow_dispatch` on the branch before the PR (needs the
  developer: pushing is outward-facing).
- The mutation score in `tests/guards/mutation_score.txt` is ≥ the baseline.

## Risks / Trade-offs

- **Coverage in the gate keeps a cost.** Accepted (DEC-4); the checkpoint in P-1 is the escape.
- **Wiring tests prove wiring, not execution** — same trade-off the replaced scenarios made.
- **Pruning relies on mutmut runs of ~10–40 min per module group.** Run them in the background;
  the per-module glob keeps each under the full hour.
