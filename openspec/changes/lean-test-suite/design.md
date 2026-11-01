> Derives from: EPIC lean-test-suite (proposal.md)

## Context

The current state is recorded in `inputs/seeds-2026-11-01.md`: unit tests grouped by module, spec
and feature scenarios linked by count only, duplicated behaviour and step definitions, three ways of
building sample data, byte-exact golden files, and an 80% line-coverage gate. Two things already
exist and are reused: `tests/e2e/test_collection.py::test_a_live_collection_equals_the_sample_profile`
(the drift guard of DEC-4) and the SHACL-validates-source check in
`tests/unit/test_representations_golden.py`. Implementation starts after the namespace-prefixes
work is merged (DEC-10; met by PR #42), and the counts are taken again at the start (task 1.1).

## Goals / Non-Goals

**Goals:**
- Every scenario in `openspec/specs/` proven by exactly one test, checked by a guard (DEC-1).
- Each check owned by one tier; duplicates removed (DEC-2).
- Tiers fenced by import contracts and a no-network rule (DEC-3).
- One canonical, generated sample dataset with named facts; edge cases as derivations (DEC-4, DEC-5).
- Branch coverage 100% `domain/`, 90% elsewhere; a mutation score that only goes up (DEC-6).

**Non-Goals:** the EPIC's No-gos apply unchanged.

## Decisions

- **P-1 Layout.**

  ```
  tests/
    conftest.py          # sample-data fixtures, the no-network fixture
    sample_data.py       # FACTS: named facts about the canonical dataset
    builders.py          # derivations: canonical data with one change; returns model objects
    fakes.py             # FakeSparql and other test doubles (moved from tests/unit/fakes.py)
    unit/domain/  unit/adapters/  unit/service_layer/  unit/entrypoints/
    bdd/                 # conftest.py = the shared step library; test_<capability>.py binds scenarios()
    features/            # <capability>.feature, one per spec capability (file name = capability, - → _)
    e2e/                 # real SPARQL store; RDF_FINGERPRINTER_TEST_ENDPOINT
    guards/              # the suite's own checks: traceability, composed dicts, fences smoke
    test_data/           # RDF sources, generated sample profile, golden outputs
  ```
  `tests/unit/steps/` moves to `tests/bdd/`; `tests/unit/test_no_composed_dicts.py` and its allow-list
  move to `tests/guards/`; `tests/unit/test_package.py` moves to `tests/guards/` (it checks packaging).

- **P-2 Ownership rule (DEC-2), applied per check:**

  | The check is about… | Owning tier | Example |
  |---|---|---|
  | what a user of a capability sees (a spec scenario) | `tests/bdd/` | "No queries during rendering" |
  | a rule that holds for all inputs | `tests/unit/domain/` as a Hypothesis property | prefix compaction round-trips |
  | a branch or error path no scenario reaches | `tests/unit/<layer that decides>/` | HTTPS→HTTP prefix-fetch fallback |
  | talking to a real store | `tests/e2e/` | first-N reads at most N instances |
  | the repository itself (packaging, dicts, traceability) | `tests/guards/` | wheel contains templates |

  A unit test that repeats a Gherkin scenario's assertion is deleted. When in doubt, the removal test
  of P-6 decides.

- **P-3 Traceability guard (DEC-1).** `tests/guards/test_traceability.py` reads every
  `#### Scenario: <title>` from `openspec/specs/<cap>/spec.md` and every `Scenario:` / `Scenario
  Outline:` title from `tests/features/<cap_with_underscores>.feature`, and fails when:
  1. a spec scenario has no feature scenario with the identical title and is not allow-listed;
  2. a feature scenario has no spec scenario with that title (orphan);
  3. an allow-list entry names a spec scenario that does not exist, or a test node id that pytest
     cannot collect (checked with `pytest --collect-only -q <node id>`, run once per entry).

  The allow-list `tests/guards/untraced_scenarios.txt` holds one line per entry:
  `<capability> | <scenario title> | <pytest node id> | <reason>`. Capability `developer-tooling` is
  expected to live mostly there, each entry naming the guard test or make target check that proves it.

- **P-4 Fences (DEC-3).** `.importlinter` changes `root_package = fingerprint` to
  `root_packages = fingerprint tests` (existing contracts unchanged) and adds forbidden contracts:

  | Source | May not import |
  |---|---|
  | `tests.unit.domain` | `fingerprint.adapters`, `fingerprint.service_layer`, `fingerprint.entrypoints` |
  | `tests.unit.adapters` | `fingerprint.service_layer`, `fingerprint.entrypoints` |
  | `tests.unit.service_layer` | `fingerprint.entrypoints` |
  | `tests.unit`, `tests.bdd`, `tests.e2e`, `tests.guards` | each other (independence contract) |
  | `tests.conftest`, `tests.sample_data`, `tests.builders`, `tests.fakes` | `tests.unit`, `tests.bdd`, `tests.e2e`, `tests.guards` |

  No-network: an autouse fixture in `tests/conftest.py` monkeypatches `socket.socket.connect` to raise
  `RuntimeError("network access in a unit/bdd test")` unless the test path is under `tests/e2e/`.
  `FakeSparql` works on an in-memory rdflib store and needs no socket.

- **P-5 Canonical data (DEC-4, DEC-5).**
  - `make refresh-sample-profile` runs the collector (the `fingerprint` CLI with `--profile-out`, or the
    service function the CLI uses) against `RDF_FINGERPRINTER_TEST_ENDPOINT` and writes
    `tests/test_data/profiles/sample-profile.json`; `make refresh-golden` then rewrites the golden
    outputs from it (replacing the `UPDATE_GOLDEN=1` switch). Both print `git diff --stat` of what changed.
  - `tests/sample_data.py` holds frozen dataclass constants, one per dataset (`CONTINENTS`,
    `TREATIES`), each with the facts tests assert: graph IRIs, class IRIs and instance counts, the
    properties per class with min/max cardinality, the expected prefixes. Facts are typed in, not
    read from the profile — they are the independent expectation the profile is checked against.
  - `tests/conftest.py` gives session-scoped fixtures `sample_run` (the loaded `ProfileRun`),
    `sample_analytics` and `sample_outputs` (the generated representation files).
  - `tests/builders.py` holds the derivation functions (moved from `tests/unit/fakes.py`: `klass`,
    `prop`, `profile_run`, `literals`, `resources`) changed to return domain model objects; edge
    cases use these or `sample_run.model_copy(update=…)`. The nine files with inline raw profiles
    switch to them.

- **P-6 Redundancy removal procedure (DEC-2, DEC-6).** Per module, after the migration:
  1. record branch coverage of the module and its `mutmut` result (killed/survived mutants);
  2. delete a candidate test (one that P-2 says another tier owns, or that repeats an example a
     property now covers);
  3. re-run; if branch coverage and the killed-mutant set are unchanged, the deletion stays,
     otherwise it is reverted and the test's unique contribution noted in its name.
  Surviving mutants either get a test (in the tier P-2 names) or prove dead code, which is deleted
  and listed in tasks.md.

- **P-7 Gate (DEC-6).**
  - `make test` adds `--cov-branch`, keeps `--cov-fail-under=90` overall, then runs
    `coverage report --include='fingerprint/domain/*' --omit='fingerprint/domain/profile.py,fingerprint/domain/views.py' --fail-under=100`.
    The generated model modules are excluded (they are checked by `check-models`).
  - `make check-mutation` runs `mutmut run` on `fingerprint/domain` and `fingerprint/service_layer`
    with the unit and bdd tiers, computes `killed / (killed + survived)` and compares it with
    `tests/guards/mutation_score.txt` (one number, three decimals). Lower → exit 1. Higher → it
    rewrites the file, and the developer commits it (the ratchet). Not part of `check-all` until its
    run time is known (Open Questions).

- **P-8 Golden outputs (DEC-8).** Turtle files compare with `rdflib.compare.isomorphic`; on failure
  the test prints `graph_diff` (in-golden-only / in-output-only triples). PlantUML and HTML golden
  files stay text-compared.

- **P-9 Properties (DEC-7).** First set, in `tests/unit/domain/`:
  - for any IRI and prefix table, expanding the compacted form gives the IRI back;
  - when several namespaces match an IRI, the longest one is chosen;
  - `cardinality_statistics` of any non-empty histogram gives min ≤ avg ≤ max and min ≥ 0;
  - every ratio in the analytics (completeness, coverage, confidence) lies in [0, 1];
  - `to_iriref` either returns a valid IRIREF or raises `IriRefError`, never anything else.

  Strategies live in `tests/unit/domain/strategies.py`. Hypothesis settings: the `ci` profile
  (`derandomize=True`, `max_examples=100`) is used by `make test`, so runs are repeatable.

## Algorithm / approach

Worked example — "No queries during rendering" (fingerprint-report):

- Before: `tests/unit/test_service_layer_report.py::test_renders_without_querying_an_endpoint`, plus the
  scenario in `fingerprint_report.feature` and again in `profile_representations.feature`, with the
  steps defined in two step files; the profile built inline in the unit file.
- After: one scenario titled exactly as the spec scenario, in `tests/features/fingerprint_report.feature`;
  the `profile_representations` variant stays only if its spec has its own scenario with that title;
  the steps once, in `tests/bdd/conftest.py`; the profile from `sample_analytics`; the unit test deleted
  after P-6 shows no coverage or mutant loss.

Idempotency: every make target here is re-runnable. `refresh-sample-profile` and `refresh-golden`
overwrite with the same content when nothing changed; `check-mutation` changes the score file only
upwards.

### Anti-patterns

| Don't | Do instead | Why |
|---|---|---|
| Assert a bare number from the sample data (`== 7`) | Assert `CONTINENTS.instances[CONTINENT]` | the expectation has one home and a name |
| Add an edge case to the canonical dataset | Derive it with a builder or `model_copy` | the shared data stays normal; edge cases stay local |
| Test the same behaviour in Gherkin and a unit test | Keep it in the tier P-2 names | duplication doubles the maintenance |
| Write a contrived test to reach a defensive branch | `# pragma: no cover — <reason>` (outside `domain/`) | coverage must reflect real decisions |
| Edit a golden file or the sample profile by hand | Use `make refresh-golden` / `refresh-sample-profile` | the chain stays derived |
| Rename a spec scenario to match a test | Rename the test's scenario to match the spec | the spec is the truth |
| Lower `mutation_score.txt` | Add the missing test or delete the dead code | the ratchet only moves up |

## Test case specifications

The new guards, each proving a spec scenario of this change (allow-listed per P-3 under `developer-tooling`).

| Id | Component | Input | Expected | Edge cases |
|---|---|---|---|---|
| TC-1 | traceability guard | spec with scenario "X", feature without "X", no allow-list entry | fails naming capability and "X" | Scenario Outline titles; trailing spaces; capability with no feature file |
| TC-2 | traceability guard | feature scenario "Y" in no spec | fails naming feature file and "Y" | same title in two capabilities counts per capability |
| TC-3 | traceability guard | allow-list entry with an uncollectable node id | fails naming the entry | entry for a non-existent scenario; malformed line (not 4 fields) |
| TC-4 | no-network fixture | `socket.create_connection(("localhost", 1))` in a `tests/unit/` test | `RuntimeError` naming the rule | same call under `tests/e2e/` is not blocked; `FakeSparql` still works |
| TC-5 | test fences | temporary module in `tests/unit/domain/` importing `fingerprint.service_layer` | `lint-imports` exits non-zero naming the contract | `tests.builders` importing `tests.bdd` also fails |
| TC-6 | mutation ratchet | score 0.850 stored, run gives 0.840 | exit 1, survivors listed | 0.850 → unchanged file; 0.860 → file rewritten to 0.860 |
| TC-7 | per-layer coverage | domain module with an untaken branch | `make test` exits non-zero listing the branch | generated `profile.py`/`views.py` excluded |
| TC-8 | isomorphic golden | same graph, triples reordered and prefixes renamed | passes | one changed literal → fails with a one-triple diff; blank nodes |

Integration (local, against Oxigraph):

| Id | Flow | Setup | Verification |
|---|---|---|---|
| IT-1 | refresh chain | `make oxigraph-load-test-data` | `refresh-sample-profile` + `refresh-golden` leave `tests/test_data/` unchanged but for timestamps/version |
| IT-2 | drift guard | remove one triple from the continents RDF, reload, no refresh | `make test-e2e` fails naming the class or property; restore the file afterwards |
| IT-3 | full gate | clean checkout after the change | `make check-all`, `make test-e2e`, `make check-mutation` all exit 0 |

## Error matrix

| Failure mode | How it is detected | Expected handling |
|---|---|---|
| Spec scenario without a test | traceability guard, case 1 | add the Gherkin scenario, or an allow-list entry with a node id and reason |
| Orphan feature scenario | traceability guard, case 2 | delete it, or add the missing spec scenario through an OpenSpec change |
| Stale allow-list entry | traceability guard, case 3 | remove or correct the entry |
| Unit test imports a higher layer | `make check-architecture` names the contract | move the test to the right layer, or test through the right seam |
| Unit/bdd test opens a socket | `RuntimeError` from the no-network fixture | use `FakeSparql`, or move the test to `tests/e2e/` |
| Stored profile drifts from the RDF | `test_a_live_collection_equals_the_sample_profile` in `make test-e2e` | `make refresh-sample-profile`, review the diff, update `sample_data.py` facts if the data changed on purpose |
| Golden Turtle differs | isomorphism test prints the triple diff | fix the code, or `make refresh-golden` for an intended change |
| Branch coverage below threshold | `make test` exits non-zero, `show_missing` lists lines | add a test in the owning tier |
| Mutation score drops | `make check-mutation` exits 1 and lists survivors | add a test or delete dead code |
| Hypothesis finds a counterexample | the property test fails with the shrunk example | fix the code; keep the example with `@example` only if it documents a rule |
| Oxigraph not running for refresh | the collector's connection error | `make oxigraph-load-test-data` first; the target says so in its help text |

## Risks / Trade-offs

- [The mutation run is slow] → scoped to two packages, coverage-guided; measured before deciding
  whether it joins `check-all` or a CI job (Open Questions).
- [Aligning titles touches the durable specs] → titles change through this change's delta only where
  the spec title is the less clear one; otherwise the feature file changes.
- [`root_packages` change affects the existing contracts] → existing contracts name full module paths,
  so they keep their meaning; `make check-architecture` before and after must report the same contracts kept.
- [Deleting tests feels risky] → each deletion is confirmed by P-6's unchanged coverage and
  killed-mutant set, and lands in its own commit per module.
- [Hypothesis flakiness] → `derandomize=True` in the `ci` profile.

## Open Questions

- Where does `make check-mutation` run? Default: locally before every PR, plus a CI job on pull
  requests if the first full run (task 6.1) takes under 10 minutes; otherwise a weekly scheduled CI
  job. The developer confirms after 6.1.
