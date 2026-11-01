> Derives from: EPIC lean-test-suite (proposal.md)

## Context

The current state is in `inputs/seeds-2026-11-01.md` and measured in `inputs/baseline.md`: unit
tests grouped by module; 35 of 102 spec scenarios with an identically titled Gherkin scenario;
behaviour tested in two or three tiers; three ways of building sample data; byte-exact golden
files; an 80% line-coverage gate. Two existing pieces are reused:
`tests/e2e/test_collection.py::test_a_live_collection_equals_the_sample_profile` (the drift guard of
DEC-4, already order-insensitive and ignoring `started_at`, `finished_at`, `tool_version`) and the
SHACL-validates-source check in `tests/unit/test_representations_golden.py`. DEC-10's condition is
met (PR #42). Revised 2026-11-01 after an independent clarity-gate review (7.8/10); its findings are
addressed below.

Measured tool facts this plan relies on (2026-11-01, Python 3.12.3):
- coverage 7.17 cannot measure branches with `core = sysmon` on Python 3.12 and falls back to the
  default tracer: the unit tier takes about 74 s with `--cov-branch` against 32 s without. Accepted
  (DEC-6); `.coveragerc` keeps `core = sysmon`, which still applies to non-branch runs and to 3.14+.
- mutmut 3.8.1 is configured only through `[tool.mutmut]` in `pyproject.toml` (keys `source_paths`,
  `do_not_mutate`, `also_copy`, `pytest_add_cli_args`, `pytest_add_cli_args_test_selection`,
  `mutate_only_covered_lines`; `paths_to_mutate` and `tests_dir` are deprecated). It copies
  `also_copy` with `copytree(dirs_exist_ok=True)` on every run, so `also_copy` must not contain the
  mutated paths. Counts come from `mutmut export-cicd-stats` (counts only); survivor names from
  `mutmut results`.
- import-linter 2.15 reads list options one entry per line.
- The `fingerprint` CLI has no option to save the profile elsewhere; the service function
  `fingerprint.service_layer.collection.collect(endpoint, settings, sparql)` returns the `ProfileRun`.

## Goals / Non-Goals

**Goals:**
- Every scenario in `openspec/specs/` proven by exactly one test, checked by a guard (DEC-1).
- Each check owned by one tier; duplicates removed (DEC-2).
- Tiers fenced by import contracts and a no-network rule (DEC-3).
- One canonical, generated sample dataset with named facts; edge cases as derivations (DEC-4, DEC-5).
- Branch coverage 100% `domain/`, 90% `fingerprint/` as a whole; a mutation score that only goes up (DEC-6).

**Non-Goals:** the EPIC's No-gos apply unchanged.

## Decisions

### P-1 Layout

```
tests/
  conftest.py             # sample-data fixtures, Hypothesis profiles, the no-network fixture
  sample_data.py          # facts about the canonical dataset (frozen dataclasses), same_profile()
  builders.py             # derivations; imports only fingerprint.domain; returns model objects
  fakes.py                # FakeSparql and other test doubles (from tests/unit/fakes.py)
  refresh_sample_data.py  # the script behind make refresh-sample-profile (P-5)
  unit/domain/  unit/adapters/  unit/service_layer/  unit/entrypoints/
  bdd/                    # conftest.py = the shared step library; test_<capability>.py binds scenarios()
  features/               # <capability>.feature, one per spec capability (file name = capability, - → _)
  e2e/                    # real SPARQL store; RDF_FINGERPRINTER_TEST_ENDPOINT
  guards/                 # the suite's own checks
  test_data/              # RDF sources, generated sample profile, golden outputs
```

Moves of the files without an obvious layer:

| File today | Moves to | Why |
|---|---|---|
| `tests/unit/test_config.py` | `tests/unit/adapters/` | it tests the config resolvers and `FingerprintConfig` reading the environment |
| `tests/unit/test_representations_golden.py` | `tests/unit/service_layer/` | it tests the generators' outputs (P-2 golden row) |
| `tests/unit/test_no_composed_dicts.py` + `composed_dicts_allowlist.txt` | `tests/guards/` (both, together) | repository check; `ALLOWLIST` uses `Path(__file__).with_name`, so the two move as a pair |
| `tests/unit/test_package.py` | `tests/guards/` | packaging check |
| `tests/unit/steps/*` | `tests/bdd/` | Gherkin tier |
| `tests/unit/fakes.py` | `tests/fakes.py` (doubles) and `tests/builders.py` (builders) | shared support |

Every other `tests/unit/test_<layer>_<module>.py` moves to `tests/unit/<layer>/test_<module>.py`.
Every new test directory gets an `__init__.py`: three modules become `test_prefixes.py` (domain,
adapters, service layer), which pytest's default import mode only accepts in distinct packages, and
import-linter needs each tier to be a package.

### P-2 Ownership rule (DEC-2)

| The check is about… | Owning tier | Example |
|---|---|---|
| what a user of a capability sees (a spec scenario) | `tests/bdd/` | "No queries during rendering" |
| a rule that holds for all inputs | `tests/unit/domain/`, as a Hypothesis property | prefix compaction round-trips |
| a branch or error path no scenario reaches | `tests/unit/<layer that decides>/` | HTTPS→HTTP prefix-fetch fallback |
| the exact text or graph of a generated output | `tests/unit/service_layer/` golden test | `shapes-continents-*.ttl` |
| talking to a real store | `tests/e2e/` | first-N reads at most N instances |
| the repository itself (packaging, dicts, traceability, fences) | `tests/guards/` | wheel contains templates |

A test that repeats an assertion owned by another tier is deleted; P-6 confirms each deletion.

### P-3 Traceability guard (DEC-1)

`tests/guards/traceability.py` holds `trace(specs_root, features_root, allow_list_path) ->
list[Problem]`; `tests/guards/test_traceability.py` calls it on the real tree and asserts no
problems, and its unit tests call it on small trees under `tmp_path` (TC-1..TC-3). Spec titles come
from `#### Scenario: <title>` lines in `<specs_root>/<cap>/spec.md`; feature titles from pytest-bdd's
own parser (`pytest_bdd.feature.get_features`), so `Scenario`, `Scenario Outline`, `Example`,
`Scenario Template` and scenarios inside `Rule` blocks are all handled. Titles compare after
stripping surrounding whitespace. Problems:

1. a spec scenario with no identically titled feature scenario and no allow-list entry;
2. a feature scenario whose title is in no spec scenario of that capability (orphan);
3. a title appearing twice in one spec file or one feature file;
4. an allow-list line that is malformed (not 4 `|`-separated fields), names a missing spec
   scenario, or names a node id whose file does not exist or does not define the named test
   function at module level (checked by parsing the file with `ast`; no subprocess).

A capability with no feature file (today `developer-tooling`) is valid only if every one of its
scenarios is allow-listed. The allow-list `tests/guards/untraced_scenarios.txt` has one entry per
line, `<capability> | <scenario title> | <pytest node id> | <reason>`; `#` starts a comment. Every
entry names a plain module-level test function as `<path>::<function>` — no class, no
parametrisation suffix, no `scenarios()`-generated test (those are traced by title already) and never
a make target; a check that is a make target gets a thin pytest wrapper (e.g. TC-5 runs
`lint-imports` in a subprocess).

### P-4 Fences (DEC-3)

`.importlinter` replaces `root_package = fingerprint` with

```
root_packages =
    fingerprint
    tests
```

Existing contracts are unchanged. New forbidden contracts (import-linter checks indirect imports too):

| Source | May not import |
|---|---|
| `tests.unit.domain` | `fingerprint.adapters`, `fingerprint.service_layer`, `fingerprint.entrypoints`, `tests.fakes` |
| `tests.unit.adapters` | `fingerprint.service_layer`, `fingerprint.entrypoints` |
| `tests.unit.service_layer` | `fingerprint.entrypoints` |
| `tests.builders`, `tests.sample_data` | `fingerprint.adapters`, `fingerprint.service_layer`, `fingerprint.entrypoints` |
| `tests.conftest`, `tests.sample_data`, `tests.builders`, `tests.fakes` | `tests.unit`, `tests.bdd`, `tests.e2e`, `tests.guards` |

plus an `independence` contract over `tests.unit`, `tests.bdd`, `tests.e2e`, `tests.guards`.
Test modules never import `tests.conftest` (pytest injects fixtures by name), so its adapter import
for loading the sample profile does not cross the domain fence. Task 2.2 runs the contracts; if any
fence turns out impossible as written, the smallest change that keeps its intent is recorded here.

No-network: an autouse fixture in `tests/conftest.py` monkeypatches `socket.socket.connect` to raise
`RuntimeError("network access is not allowed outside tests/e2e/")` unless the requesting test's
path is under `tests/e2e/`. `FakeSparql` uses an in-memory rdflib store and opens no socket.

### P-5 Canonical data (DEC-4, DEC-5)

- `tests/refresh_sample_data.py` (run by `make refresh-sample-profile`) loads the stored sample
  profile, collects the store at `RDF_FINGERPRINTER_TEST_ENDPOINT` with
  `collect(endpoint, stored.settings, SparqlHttpClient(endpoint, stored.settings.timeout_seconds))`,
  and compares the two with `same_profile(a, b)` — the drift test's order-insensitive comparison,
  moved to `tests/sample_data.py`, ignoring `started_at`, `finished_at`, `tool_version`. Equal → the
  file is not touched. Different → it writes the new run carrying the stored `started_at`,
  `finished_at` and `tool_version`, so only data differences show in the diff, and prints which
  classes or properties differ.
- `make refresh-golden` rewrites the golden outputs from the sample profile (the `UPDATE_GOLDEN=1`
  logic moved behind a target); it writes only files whose content changed.
- `tests/sample_data.py`: frozen dataclass constants `CONTINENTS` and `TREATIES` with the facts tests
  assert (graph IRIs, class IRIs with instance counts, properties per class with min/max
  cardinality, expected prefixes), typed in by hand as the independent expectation.
- `tests/conftest.py`: session-scoped fixtures `sample_run`, `sample_analytics`, `sample_outputs`.
- `tests/builders.py`: the builders from `tests/unit/fakes.py` (`klass`, `prop`, `profile_run`,
  `literals`, `resources`) returning model objects; edge cases use them or
  `sample_run.model_copy(update=…)`.

### P-6 Redundancy removal procedure (DEC-2, DEC-6)

Per module, after the migration:
1. record the module's branch coverage and its mutmut results (killed and survived mutant names);
2. delete a candidate test (owned by another tier per P-2, or an example row a property covers);
3. re-run; unchanged branch coverage and unchanged killed set → the deletion stays; otherwise revert
   it and rename the test to say what it alone proves.

For `adapters/` and `entrypoints/` (not mutated) the check is branch coverage plus P-2 ownership.
Surviving mutants either get a test in the tier P-2 names or prove dead code, which is deleted and
listed in tasks.md (the EPIC's only production-code exception).

### P-7 Gate (DEC-6)

- `make test` runs `pytest tests --ignore=tests/e2e` (unit, bdd and guards) with `--cov-branch`,
  `--cov-fail-under=90` and `--hypothesis-profile=ci`, then
  `coverage report --include='fingerprint/domain/*' --omit='fingerprint/domain/profile.py,fingerprint/domain/views.py' --fail-under=100`.
- `[tool.mutmut]` in `pyproject.toml`:
  `source_paths = ["fingerprint/domain/", "fingerprint/service_layer/"]`,
  `do_not_mutate = ["fingerprint/domain/profile.py", "fingerprint/domain/views.py"]`,
  `also_copy` = the unmutated rest (`fingerprint/__init__.py`, `fingerprint/adapters/`,
  `fingerprint/entrypoints/`, `fingerprint_report_templates/`, `tests/`, `pytest.ini`),
  `pytest_add_cli_args_test_selection = ["tests/unit", "tests/bdd"]` (guards read the source mutmut
  rewrites, so they are never selected), `mutate_only_covered_lines = false`.
- `make check-mutation` runs `mutmut run`, then `mutmut export-cicd-stats`;
  `tests/guards/mutation_score.py` reads the stats JSON and computes
  score = (killed + timeout) / (killed + timeout + survived + no_tests), three decimals (a mutant no
  test covers counts as not caught). `check_was_interrupted_by_user > 0` or zero mutants → exit 2
  with an error, no score. Score < `tests/guards/mutation_score.txt` → exit 1, and the target prints
  the survivors with `mutmut results`; score > stored → rewrite the file (the ratchet), which the
  implementer commits.

### P-8 Golden outputs (DEC-8)

Turtle golden files compare with `rdflib.compare.isomorphic`; on failure the test prints
`rdflib.compare.graph_diff` (triples only in the golden, only in the output). PlantUML and HTML
golden files stay text-compared.

### P-9 Properties (DEC-7)

`tests/conftest.py` registers Hypothesis profiles `ci` (`derandomize=True`, `deadline=None`) and
`dev` (`deadline=None`) and loads `dev` by default; `make test` passes `--hypothesis-profile=ci`.
Strategies live in `tests/unit/domain/strategies.py`. First properties:
- expanding the compacted form of any IRI gives the IRI back;
- when several namespaces match an IRI, the longest one is chosen;
- `cardinality_statistics` of any non-empty histogram gives 0 ≤ min ≤ avg ≤ max;
- every ratio in the analytics (completeness, coverage, confidence) lies in [0, 1];
- `to_iriref` either returns a valid IRIREF or raises `IriRefError`.

## Algorithm / approach

Worked example — "the output folder does not exist":

- Before: an example row in `tests/features/fingerprint_report.feature:101` (exit 2, no report
  written); `tests/unit/test_service_layer_handlers.py::test_a_missing_output_folder_is_refused_before_any_query`;
  `tests/e2e/test_entrypoints_cli.py::test_missing_output_folder_is_a_usage_error`.
- After (P-2): the Gherkin row owns the user-visible behaviour (exit 2, no report). The unit test
  stays only if it proves something the row cannot — here "no query is sent", a decision of the
  service layer — and is renamed to say so; otherwise P-6 deletes it. The e2e test is deleted: a
  missing folder never reaches the store, so it is not an e2e concern.

Idempotency: every make target is re-runnable. `refresh-sample-profile` does not touch an equal
file; `refresh-golden` writes only changed files; `check-mutation` changes the score file only upwards.

### Anti-patterns

| Don't | Do instead | Why |
|---|---|---|
| Assert a bare number from the sample data (`== 7`) | Assert the named fact from `tests/sample_data.py` | the expectation has one home and a name |
| Add an edge case to the canonical dataset | Derive it with a builder or `model_copy` | the shared data stays normal; edge cases stay local |
| Test the same behaviour in Gherkin and a unit test | Keep it in the tier P-2 names | duplication doubles the maintenance |
| Write a contrived test to reach a defensive branch | `# pragma: no cover — <reason>` (outside `domain/`) | coverage must reflect real decisions |
| Edit a golden file or the sample profile by hand | `make refresh-golden` / `make refresh-sample-profile` | the chain stays derived |
| Rename a spec scenario to match a test | Rename the feature scenario to match the spec | the spec is the truth |
| Lower `mutation_score.txt` | Add the missing test or delete the dead code | the ratchet only moves up |
| Import `tests.fakes` from a domain test | Build domain inputs with `tests.builders` | the domain fence forbids adapters, even indirectly |
| Allow-list a scenario with a make target | Name a pytest test, adding a thin wrapper if needed | the guard can verify a node id, not a target |

## Test case specifications

The new guards; each proves a scenario of this change's spec delta (allow-listed per P-3 under `developer-tooling`).

| Id | Component | Input | Expected | Edge cases |
|---|---|---|---|---|
| TC-1 | `trace()` | spec with scenario "X", feature without "X", empty allow-list | one problem naming the capability and "X" | Scenario Outline / Example keywords; trailing spaces; capability with no feature file |
| TC-2 | `trace()` | feature scenario "Y" in no spec | one problem naming the feature file and "Y" | the same title in two capabilities is checked per capability |
| TC-3 | `trace()` | allow-list entry whose node id names a missing function | one problem naming the entry | missing scenario; 3-field line; duplicate title in one spec |
| TC-4 | no-network fixture | `socket.create_connection(("localhost", 1))` in a `tests/unit/` test | `RuntimeError` naming the rule | not raised under `tests/e2e/`; `FakeSparql` still works |
| TC-5 | test fences | `lint-imports` on a temporary copy of the tree with a domain test importing `fingerprint.service_layer` | non-zero exit naming the contract | a domain test importing `tests.fakes` also fails |
| TC-6 | `mutation_score.py` | stats JSON giving 0.840, stored 0.850 | exit 1 | 0.850 → file unchanged; 0.860 → file rewritten; zero mutants or an interrupted run → exit 2, no division by zero |
| TC-7 | per-layer coverage | a domain module with an untaken branch | `make test` exits non-zero listing the branch | generated `profile.py`/`views.py` excluded |
| TC-8 | isomorphic golden | same graph, triples reordered and prefixes renamed | passes | one changed literal → fails with a one-triple diff; blank nodes |

Integration (local, against Oxigraph):

| Id | Flow | Setup | Verification |
|---|---|---|---|
| IT-1 | refresh chain | `make oxigraph-load-test-data` | `make refresh-sample-profile` and `make refresh-golden` leave `git status` clean |
| IT-2 | drift guard | remove one triple from the continents RDF, reload | `make test-e2e` fails naming the class or property; file restored and store reloaded afterwards |
| IT-3 | full gate | the branch at the end | `make check-all`, `make test-e2e`, `make check-mutation` all exit 0 |

## Error matrix

| Failure mode | How it is detected | Expected handling |
|---|---|---|
| Spec scenario without a test | traceability problem 1 | add the Gherkin scenario, or an allow-list entry naming a pytest test |
| Orphan feature scenario | traceability problem 2 | delete it, or add the spec scenario through a delta of that capability in this change |
| Duplicate title | traceability problem 3 | make the titles distinct (in a spec delta if the spec holds the duplicate) |
| Stale or malformed allow-list entry | traceability problem 4 | correct or remove it |
| Unit test imports a higher layer, or a domain test imports `tests.fakes` | `make check-architecture` names the contract | move the test, or build inputs with `tests.builders` |
| Unit/bdd test opens a socket | `RuntimeError` from the no-network fixture | use `FakeSparql`, or move the test to `tests/e2e/` |
| Stored profile drifts from the RDF | the drift test in `make test-e2e` names the difference | `make refresh-sample-profile`; update `tests/sample_data.py` if the data changed on purpose |
| Golden Turtle differs | isomorphism test prints the triple diff | fix the code, or `make refresh-golden` for an intended change |
| Branch coverage below threshold | `make test` exits non-zero; `show_missing` lists lines | add a test in the owning tier |
| Mutation score drops | `make check-mutation` exits 1 and lists survivors | add a test or delete dead code |
| mutmut cannot import inside `mutants/` | `mutmut run` fails at its clean-tests step | extend `also_copy` |
| Hypothesis finds a counterexample | the property fails with the shrunk example | fix the code; keep it with `@example` only if it documents a rule |
| Oxigraph not running for a refresh | connection error from the collector | `make oxigraph-load-test-data` first (stated in the target's help) |

## Risks / Trade-offs

- [Branch coverage costs ~2.3× unit run time on 3.12] → accepted; about 74 s.
- [The mutation run is slow] → scoped to two packages; measured in task 6.4 before deciding where it runs.
- [Aligning titles touches durable specs] → the feature title changes by default; a spec changes
  only for a duplicate title or a feature-only scenario that proves real behaviour, through a
  MODIFIED delta of that capability in this change (the whole requirement restated; one MODIFIED
  section per delta file).
- [The `root_packages` change affects existing contracts] → `make check-architecture` must report the
  same four existing contracts kept before and after.
- [Deleting tests feels risky] → each deletion is confirmed by P-6 and lands in a per-module commit.
- [Hypothesis flakiness] → `derandomize=True` in the `ci` profile.
- Second review (9.0/10, 2026-11-01): mutmut key names, survivor listing, `__init__.py` per test
  directory, plain-function allow-list entries and the `also_copy` overwrite risk fixed here.

## Open Questions

- Where does `make check-mutation` run? Rule, set by the team lead while the developer is away: a CI
  job on pull requests if the measured full run (task 6.4) is under 10 minutes; otherwise a weekly
  scheduled CI job; locally before every PR in either case.
  **Resolved 2026-11-01:** the full run took 55 minutes, so `.github/workflows/mutation.yml` runs it
  weekly and on demand; baseline score 0.807 (`inputs/baseline.md`).
