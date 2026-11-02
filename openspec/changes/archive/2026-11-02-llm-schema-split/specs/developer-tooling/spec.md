## MODIFIED Requirements

### Requirement: Single quality gate
The repository SHALL provide `make check-all`, the gate CI runs, which SHALL be
`make check-all-fast`: it MUST fail if any of lint, type check, architecture contracts, model
drift, OpenSpec validation or the test suite without the Hypothesis property tests fails. It
SHALL NOT run the Hypothesis property tests and SHALL NOT fail on a coverage floor, but it SHALL
write `coverage.xml` for the coverage report (developer, 2026-11-02: the per-PR gate stays quick). The repository SHALL also provide `make check-all-deep`, which runs the
same static checks and `make test` (every test, the Hypothesis property tests included, with the
coverage gates of "Coverage and mutation gate").

#### Scenario: Clean tree passes
- **WHEN** a contributor runs `make install` then `make check-all` on a clean checkout, with no SPARQL store running
- **THEN** the command exits 0

#### Scenario: The fast gate skips the property tests
- **WHEN** a contributor runs `make check-all`
- **THEN** no test marked `hypothesis` runs, and `make check-all-deep` runs them

#### Scenario: Layer violation fails
- **WHEN** a module in `fingerprint.service_layer` imports `fingerprint.entrypoints`
- **THEN** `make check-architecture` exits non-zero and names the broken contract

### Requirement: CI runs the gate
CI SHALL run `make check-all` on every push and pull request to `master` and to `develop`, and
SHALL upload its coverage report to Codecov. A separate workflow SHALL run `make check-all-deep`
every week and on manual dispatch (developer, 2026-11-02).

#### Scenario: Failing gate blocks the PR
- **WHEN** a pull request into `master` or `develop` introduces a Ruff error
- **THEN** the CI check for that pull request fails

#### Scenario: The deep gate runs weekly
- **WHEN** the weekly schedule fires, or a maintainer dispatches the deep workflow by hand
- **THEN** it runs `make check-all-deep`
