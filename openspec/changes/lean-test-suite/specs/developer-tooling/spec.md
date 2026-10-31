## ADDED Requirements

### Requirement: Requirement-traced tests
Every scenario in `openspec/specs/<capability>/spec.md` SHALL be proven by exactly one Gherkin
scenario with the identical title in `tests/features/<capability>.feature` (hyphens as underscores),
or by a test named in `tests/guards/untraced_scenarios.txt` with a reason. `make check-all` SHALL fail
when a spec scenario is unproven, when a feature scenario has no spec scenario of that title, or when
an allow-list entry names a missing scenario or a test that cannot be collected.

#### Scenario: A spec scenario without a test
- **WHEN** a scenario is added to `openspec/specs/fingerprint-report/spec.md` and no feature scenario or allow-list entry has its title
- **THEN** `make check-all` exits non-zero and names the capability and the scenario title

#### Scenario: An orphan feature scenario
- **WHEN** `tests/features/fingerprint_report.feature` holds a scenario whose title is in no spec scenario
- **THEN** `make check-all` exits non-zero and names the feature file and the scenario title

#### Scenario: A stale allow-list entry
- **WHEN** an entry in `tests/guards/untraced_scenarios.txt` names a test node id that pytest cannot collect
- **THEN** `make check-all` exits non-zero and names the entry

### Requirement: Fenced test tiers
The tests SHALL be organised in tiers — `tests/unit/<layer>/` per package layer, `tests/bdd/`,
`tests/e2e/` and `tests/guards/` — and `make check-architecture` SHALL fail when a layer's unit tests
import a higher package layer, when one tier imports another, or when shared test support imports a
tier. Tests outside `tests/e2e/` SHALL NOT open a network connection.

#### Scenario: A domain test imports the service layer
- **WHEN** a module in `tests/unit/domain/` imports `fingerprint.service_layer`
- **THEN** `make check-architecture` exits non-zero and names the broken contract

#### Scenario: A unit test reaches the network
- **WHEN** a test under `tests/unit/` opens a socket connection
- **THEN** the test fails with an error saying network access is not allowed outside `tests/e2e/`

### Requirement: Canonical sample data
The sample profile `tests/test_data/profiles/sample-profile.json` SHALL be produced by
`make refresh-sample-profile` from the RDF in `tests/test_data/` loaded into the store at
`RDF_FINGERPRINTER_TEST_ENDPOINT`, and the golden outputs by `make refresh-golden` from that profile.
The known facts of the sample datasets SHALL be named once in `tests/sample_data.py`, and `make test-e2e`
SHALL fail when a fresh collection differs from the stored profile other than in timestamps and tool version.

#### Scenario: Regenerating without a data change
- **WHEN** a contributor runs `make oxigraph-load-test-data`, then `make refresh-sample-profile` and `make refresh-golden` on a clean checkout
- **THEN** `git status` shows no change under `tests/test_data/` other than timestamps and tool version

#### Scenario: The stored profile drifts
- **WHEN** a triple is removed from `tests/test_data/continents-source-ap.rdf`, the store is reloaded and the sample profile is not regenerated
- **THEN** `make test-e2e` fails and names the differing class or property

### Requirement: Coverage and mutation gate
`make test` SHALL fail when branch coverage is below 100% for `fingerprint/domain/` (excluding the
generated model modules) or below 90% for `fingerprint/` as a whole. `make check-mutation` SHALL
compute the mutation score of `fingerprint/domain/` and `fingerprint/service_layer/` and SHALL fail
when it is lower than the score stored in `tests/guards/mutation_score.txt`.

#### Scenario: An untested domain branch
- **WHEN** a branch is added to a module in `fingerprint/domain/` with no test reaching it
- **THEN** `make test` exits non-zero and lists the missing branch

#### Scenario: The mutation score drops
- **WHEN** a test that alone kills a mutant in `fingerprint/service_layer/` is deleted
- **THEN** `make check-mutation` exits non-zero and lists the surviving mutant
