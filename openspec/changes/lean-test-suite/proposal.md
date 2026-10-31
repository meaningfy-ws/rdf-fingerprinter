# EPIC: A lean, traced and fenced test suite

> Parents: capability `developer-tooling` (Requirement: Single quality gate); the use-case catalogue
> (`docs/modules/ROOT/pages/use-cases/`) that the Gherkin features project; seeds in
> `inputs/seeds-2026-11-01.md`.

## Appetite

LARGE — every test file moves or is rewritten, and the test setup gains new guards, but no
production behaviour changes.

## Why

The suite grows by count, not by proof: about 575 unit tests, yet nothing checks that each spec
scenario has a test. The same behaviour is often tested two or three times, and each test file
invents its own sample data. Its 80% line-coverage gate shows the code ran, not that a test would
catch a fault in it. Every new feature makes the suite slower to read and to change. Now is the
time because the domain-object-model work has just stabilised the models the tests build on.

## Solution outline

When this is done, the suite answers three questions mechanically:

1. **Is every requirement proven?** Each scenario in `openspec/specs/` has exactly one Gherkin
   scenario with the same title, or an explicit entry naming the test that proves it. A guard test
   fails on a missing scenario or an orphan one.
2. **Would a fault be caught?** Branch coverage is gated per layer, and a mutation score on the
   domain and service layers may only go up.
3. **Does each test earn its place?** Each check has exactly one owning tier (behaviour in Gherkin,
   decisions and edge cases in unit tests, invariants as properties, the real store in e2e). A test
   whose removal lowers neither branch coverage nor the mutation score is deleted.

All tiers read one canonical sample dataset: source RDF → collected profile → analytics → outputs,
generated and never hand-edited. Its known facts are named once and asserted everywhere. Edge
cases start from the canonical data and change one thing. Tiers are fenced by import contracts and
a no-network rule, so a unit test cannot quietly become an integration test.

## Key decisions

- **DEC-1 Spec scenarios are traced by title.** A spec scenario is proven by the Gherkin scenario
  with the same title in its capability's feature file, or by a test named in an allow-list with a
  reason (for scenarios no Gherkin step can reach, such as CI or docs deployment). Reason: the title
  is already the shared name; no tag vocabulary to maintain. Rejected: per-scenario tags/markers
  (a second name to keep in sync, and `--strict-markers` would need dozens of registrations).
- **DEC-2 One owning tier per check.** Behaviour → Gherkin (through the service layer and entry
  points); decisions and edge cases that the scenarios do not reach → unit tests in the layer that
  makes the decision; domain invariants → Hypothesis properties; the real SPARQL store → e2e. A
  check covered in one tier is not repeated in another. Reason: removes duplication by rule,
  not by taste. Rejected: tests per module with no ownership rule (today's state).
- **DEC-3 Tiers are fenced by layer and enforced.** `tests/unit/<layer>/` mirrors `domain`,
  `adapters`, `service_layer` and `entrypoints`. Import-linter contracts stop a layer's tests from
  importing a higher layer, stop tiers importing each other, and keep test support importing no
  test module. Unit and Gherkin tests cannot open a network connection. Reason: separation that is
  checked, not hoped for. Rejected: a capability-first layout (weaker layer fences); directories
  without contracts.
- **DEC-4 One canonical sample dataset, generated.** `tests/test_data/*-source-ap.rdf` is the
  source; a make target collects it from the local Oxigraph into the sample profile; golden outputs
  derive from the profile. Its known facts are named constants in one module that every tier asserts
  against; an e2e guard fails when the stored profile drifts from a fresh collection. Reason:
  expectations written once, against data whose origin is proven. Rejected: hand-kept profile and
  per-test inline dicts.
- **DEC-5 Edge cases are derivations.** An edge-case fixture is the canonical data with one change,
  built through one builder module that returns domain model objects (never dicts). Edge cases
  (empty graph, timeout, sampled class, credentials) never go into the canonical dataset.
  Reason: each test shows only what differs, and a canonical-data change breaks only normal-case
  tests. Rejected: a growing shared fixture holding every edge case.
- **DEC-6 Gate on branch coverage and a ratcheted mutation score.** Branch coverage: 100% for
  `fingerprint/domain/`, 90% for the rest of `fingerprint/`. `mutmut` scores `domain/` and
  `service_layer/`; the score is stored and may not drop. Reason: line coverage cannot tell a test
  that checks from a test that only runs code. Rejected: 80% line only; branch coverage only.
- **DEC-7 Properties replace example tables for invariants.** `hypothesis` states the domain rules
  (IRI compaction round-trips, the longest namespace wins, cardinality statistics stay ordered,
  ratios stay in [0, 1]). Example rows stay only where a spec example is the documentation, and then
  in Gherkin. Reason: fewer tests, more edge cases found. Rejected: more parametrised rows.
- **DEC-8 Outputs are compared by meaning where the format allows.** Turtle outputs compare as RDF
  graphs (isomorphism); shapes still validate the source data; text golden files stay only for
  PlantUML and HTML, whose text is the product. Reason: a cosmetic serialisation change must not
  break tests. Rejected: byte comparison for everything.
- **DEC-9 Existing guardrails stay as they are.** The no-composed-dicts check, the code import
  contracts, `check-models`, `check-spec`, `make test-e2e` and the release rules are kept unchanged;
  this change adds guards and removes none. Reason: the change must not weaken the gate to make
  itself fit.
- **DEC-10 Runs after the in-flight work.** Implementation starts once the namespace-prefixes work
  and `batched-collection` are merged into `master`; their tests migrate with everything else.
  Reason: avoid restructuring a suite that other sessions are editing in the shared checkout.

## Rabbit-holes

- **Mutation run time.** A full `mutmut` run may take long. Scope it to `domain/` and
  `service_layer/`, use coverage-guided test selection, and measure before deciding where it runs
  (see design Open Questions).
- **Chasing 100% everywhere.** 100% branch coverage is required for `domain/` only; elsewhere
  unreachable defensive branches get `pragma: no cover` with a reason, not contrived tests.
- **Renaming spec scenarios to fit tests.** Titles are aligned towards the spec; a spec title
  changes only when it is unclear, and then through this change's delta.
- **Rewriting steps for style.** Steps are merged where they duplicate; they are not restyled.
- **Golden-file churn.** Regenerating goldens only through the make target, reviewing the diff.

## No-gos

- No production code changes, except deleting code that mutation testing proves dead (each such
  deletion listed in the tasks).
- No new test framework, runner or coverage tool beyond `mutmut` and `hypothesis`; no
  `pytest-socket`.
- No target for the number of tests; the count falls as a result, it is not the goal.
- No change to the use-case catalogue or to what a capability does.
- No extension of the no-composed-dicts check to `tests/` (builders returning models is enough).
- No CI-hosted SPARQL store; e2e stays local.

---

## What Changes

- Test layout: `tests/unit/<layer>/`, a Gherkin tier with one shared step library, `tests/e2e/`,
  and `tests/guards/` for the suite's own checks; `tests/conftest.py`, `tests/sample_data.py` and
  `tests/builders.py` replace the inline dicts and the builders in `tests/unit/fakes.py` (its test
  doubles move to `tests/fakes.py`).
- Spec and feature scenario titles aligned; a traceability guard with an allow-list.
- Duplicate tests removed by the DEC-2 ownership rule and confirmed by coverage and mutation score.
- Parametrised example tables for domain invariants replaced by Hypothesis properties.
- Sample profile generated from the source RDF by a make target; drift guard in e2e.
- Turtle golden comparisons by graph isomorphism.
- Gate: branch coverage per layer; `make check-mutation` with a stored, ratcheted score.
- `.importlinter` gains test-tier contracts; a no-network fixture for unit and Gherkin tests.
- `mutmut` and `hypothesis` added to the dev dependency group.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `developer-tooling`: adds requirements for requirement-traced tests, fenced test tiers, the
  canonical sample data and the coverage-and-mutation gate.

## Impact

- `tests/` (all files), `pytest.ini`, `.coveragerc`, `.importlinter`, `Makefile`, `pyproject.toml`
  (dev group), CI workflow (mutation job), `openspec/specs/*/spec.md` scenario titles where they
  are aligned, `docs/` (the contributor testing page), `AGENTS.md` (*Working conventions*: the
  test-tier rule).
- No public API, CLI or package-content change; no release needed beyond a PATCH if docs ship.
