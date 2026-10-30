## ADDED Requirements

### Requirement: Single quality gate
The repository SHALL provide `make check-all`, which MUST fail if any of lint, type check,
architecture contracts, OpenSpec validation or the test suite fails.

#### Scenario: Clean tree passes
- **WHEN** a contributor runs `make install` then `make check-all` on a clean checkout with Fuseki running
- **THEN** the command exits 0

#### Scenario: Layer violation fails
- **WHEN** a module in `fingerprint.service_layer` imports `fingerprint.entrypoints`
- **THEN** `make check-architecture` exits non-zero and names the broken contract

### Requirement: CI runs the gate
CI SHALL run `make check-all` on every push and pull request to `master`.

#### Scenario: Failing gate blocks the PR
- **WHEN** a pull request introduces a Ruff error
- **THEN** the CI check for that pull request fails

### Requirement: Tokenless release
Publishing to PyPI SHALL use Trusted Publishing (OIDC); the repository MUST NOT need a PyPI token secret.

#### Scenario: Release publishes the package
- **WHEN** a release is published on GitHub
- **THEN** the workflow builds the sdist and wheel with Poetry and uploads them to PyPI via OIDC
- **AND** the wheel contains `fingerprint_report_templates` with its templates and queries
