## MODIFIED Requirements

### Requirement: Single quality gate
The repository SHALL provide `make check-all`, the feature gate run on every feature and by CI on
every pull request. It MUST fail if any of lint, type check, architecture contracts, model drift,
OpenSpec validation or `make test` fails. `make test` SHALL run every self-contained test (unit,
BDD and guard tests, the Hypothesis property tests on the derandomised `ci` profile included, the
tests marked `release` excluded) in parallel, with the coverage gates of "Coverage and mutation
gate", and SHALL NOT need a SPARQL store.

#### Scenario: Clean tree passes
- **WHEN** a contributor runs `make install` then `make check-all` on a clean checkout, with no SPARQL store running
- **THEN** the command exits 0

#### Scenario: The gate runs every self-contained test
- **WHEN** a contributor runs `make check-all`
- **THEN** `make test` runs the Hypothesis property tests on the `ci` profile across parallel workers, skips the tests marked `release`, and fails on the coverage floors

#### Scenario: Layer violation fails
- **WHEN** a module in `fingerprint.service_layer` imports `fingerprint.entrypoints`
- **THEN** `make check-architecture` exits non-zero and names the broken contract

### Requirement: CI runs the gate
CI SHALL run `make check-all` on every push and pull request to `master` and to `develop`, and
SHALL upload its coverage report to Codecov. On every pull request into `master` (a release PR),
CI SHALL also run the release checks: the tests marked `release`, the e2e tests against an
Oxigraph service loaded with `tests/test_data`, and an install of the built wheel into a clean
environment followed by `fingerprint --help`.

#### Scenario: Failing gate blocks the PR
- **WHEN** a pull request into `master` or `develop` introduces a Ruff error
- **THEN** the CI check for that pull request fails

#### Scenario: A release PR runs the release checks
- **WHEN** a pull request into `master` is opened or updated
- **THEN** the release-check workflow starts an Oxigraph service, loads the test data, runs `make test-release` and `make test-e2e`, and installs the built wheel and runs `fingerprint --help`

### Requirement: Local end-to-end tests
The repository SHALL provide `make test-e2e`, which runs the tests that generate reports against
the SPARQL store at `RDF_FINGERPRINTER_TEST_ENDPOINT` (default: the local Oxigraph loaded by
`make oxigraph-load-test-data`). The feature gate MUST NOT need a SPARQL store; only the release
gate runs the e2e tests.

#### Scenario: e2e against the local Oxigraph
- **WHEN** a contributor runs `make oxigraph-load-test-data` then `make test-e2e`
- **THEN** the report-generation and CLI tests run against `http://localhost:7878/query` and pass

### Requirement: Coverage and mutation gate
`make test` SHALL fail when branch coverage is below 100% for `fingerprint/domain/` (excluding the
generated model modules) or below 90% for `fingerprint/` as a whole. `make check-mutation` SHALL
compute the mutation score of `fingerprint/domain/` and `fingerprint/service_layer/` and SHALL fail
when it is lower than the score stored in `tests/guards/mutation_score.txt`. CI SHALL run
`make check-mutation` after a GitHub Release is published and on manual dispatch; it SHALL NOT
block a merge or a release.

#### Scenario: An untested domain branch
- **WHEN** a branch is added to a module in `fingerprint/domain/` with no test reaching it
- **THEN** `make test` exits non-zero and lists the missing branch

#### Scenario: The mutation score drops
- **WHEN** a test that alone kills a mutant in `fingerprint/service_layer/` is deleted
- **THEN** `make check-mutation` exits non-zero and lists the surviving mutant

#### Scenario: Mutation testing runs after a release
- **WHEN** a GitHub Release is published, or a maintainer dispatches the mutation workflow by hand
- **THEN** it runs `make check-mutation`, and no pull-request or release workflow waits for it

## ADDED Requirements

### Requirement: Release gate
The repository SHALL provide `make check-release`, run locally before every release. It SHALL run
`make check-all`, then the tests marked `release` (extra depth of checks the feature gate already
proves), the Hypothesis property tests on the randomised `dev` profile (`make test-properties`)
and `make test-e2e`, and MUST fail if any of them fails.

#### Scenario: The release gate runs what the feature gate leaves out
- **WHEN** a contributor runs `make oxigraph-load-test-data` then `make check-release`
- **THEN** it runs `make check-all`, `make test-release`, `make test-properties` on the `dev` profile and `make test-e2e`, and exits non-zero if any of them fails
