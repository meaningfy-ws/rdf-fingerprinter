## MODIFIED Requirements

### Requirement: Single quality gate
The repository SHALL provide `make check-all`, the gate CI runs, which SHALL be
`make check-all-fast`: it MUST fail if any of lint, type check, architecture contracts, model
drift, OpenSpec validation or the test suite without the Hypothesis property tests fails, and it
SHALL NOT run the Hypothesis property tests or the coverage gates (developer, 2026-11-02: run
them only on exception). The repository SHALL also provide `make check-all-deep`, which runs the
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
