# developer-tooling Specification

## Purpose
The quality gate, test setup, documentation and release path that every contributor, agent and
CI run use for rdf-fingerprinter: `make check-all` as the single gate, local end-to-end tests
against a SPARQL store, Antora docs on GitHub Pages, and tokenless PyPI releases. Established by
`adopt-meaningfy-tooling` (released as 1.0.0).
## Requirements
### Requirement: Single quality gate
The repository SHALL provide `make check-all`, which MUST fail if any of lint, type check,
architecture contracts, OpenSpec validation or the test suite fails.

#### Scenario: Clean tree passes
- **WHEN** a contributor runs `make install` then `make check-all` on a clean checkout, with no SPARQL store running
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

### Requirement: Import has no side effects
Importing any `fingerprint` module SHALL NOT configure logging or read files relative to the
current working directory.

#### Scenario: Import from another directory
- **WHEN** the installed package is imported with a working directory that has no `logging.conf`
- **THEN** the import succeeds and the root logger's handlers are unchanged

### Requirement: Reports on strict SPARQL stores
The packaged report templates SHALL use SPARQL 1.1 that strict stores evaluate without errors.

#### Scenario: Oxigraph renders the type columns
- **WHEN** the default report is generated against Oxigraph loaded with the test data
- **THEN** no table cell of the report renders as `nan`

### Requirement: Local end-to-end tests
The repository SHALL provide `make test-e2e`, which runs the tests that generate reports against
the SPARQL store at `RDF_FINGERPRINTER_TEST_ENDPOINT` (default: the local Oxigraph loaded by
`make oxigraph-load-test-data`). CI MUST NOT need a SPARQL store.

#### Scenario: e2e against the local Oxigraph
- **WHEN** a contributor runs `make oxigraph-load-test-data` then `make test-e2e`
- **THEN** the report-generation and CLI tests run against `http://localhost:7878/query` and pass

### Requirement: Published documentation
The documentation SHALL be AsciiDoc built by Antora and published to GitHub Pages from `master`.

#### Scenario: Docs deploy on merge
- **WHEN** a change under `docs/` is merged to `master`
- **THEN** the `docs` workflow builds the site and deploys it to `https://meaningfy-ws.github.io/rdf-fingerprinter/`

#### Scenario: Broken docs block the PR
- **WHEN** a pull request makes the Antora build fail
- **THEN** the `docs` workflow check for that pull request fails

### Requirement: Generated models stay in sync
The domain model module SHALL be generated from the LinkML schemas in `model/` by
`make generate-models`, and `make check-all` SHALL fail when the committed module differs from a
fresh generation.

#### Scenario: Schema edited without regeneration
- **WHEN** a slot is added to `model/fingerprint_stats.yaml` and `fingerprint/domain/generated/profile.py` is not regenerated
- **THEN** `make check-all` exits non-zero and names the out-of-date file

### Requirement: Generated code is read-only
The generated module SHALL carry a do-not-edit banner, SHALL be excluded from Ruff, and its model
classes SHALL be immutable (frozen) and reject unknown fields.

#### Scenario: Mutating a profile object
- **WHEN** code assigns a new value to a field of a generated profile object
- **THEN** a validation error is raised

#### Scenario: Banner present
- **WHEN** `make generate-models` runs
- **THEN** the first line of `fingerprint/domain/generated/profile.py` states it is generated and must not be edited

### Requirement: Onion layers are enforced
`.importlinter` SHALL enforce the layers `entrypoints` > `service_layer` > `adapters` > `domain`
(each importing only layers below it), SHALL forbid `fingerprint.domain.generated` from importing
any other `fingerprint` module, and SHALL forbid `fingerprint.domain` from importing
`SPARQLWrapper`, `eds4jinja2` or `click`.

#### Scenario: Generated module imports project code
- **WHEN** `fingerprint/domain/generated/profile.py` imports `fingerprint.domain.analytics`
- **THEN** `make check-architecture` exits non-zero

#### Scenario: Domain imports an adapter
- **WHEN** a module in `fingerprint.domain` imports `fingerprint.adapters`
- **THEN** `make check-architecture` exits non-zero and names the broken contract

