## ADDED Requirements

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
