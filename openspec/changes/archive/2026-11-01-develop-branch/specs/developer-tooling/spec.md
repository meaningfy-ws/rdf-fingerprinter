## MODIFIED Requirements

### Requirement: CI runs the gate
CI SHALL run `make check-all` on every push and pull request to `master` and to `develop`.

#### Scenario: Failing gate blocks the PR
- **WHEN** a pull request into `master` or `develop` introduces a Ruff error
- **THEN** the CI check for that pull request fails
