## MODIFIED Requirements

### Requirement: Generated models stay in sync
The model modules SHALL be generated from the LinkML schemas in `model/` by `make generate-models`
into `fingerprint/domain/` (`profile.py`, `views.py`, `profile_run.schema.json`), and `make check-all`
SHALL fail when a committed module differs from a fresh generation.

#### Scenario: Schema edited without regeneration
- **WHEN** a slot is added to `model/fingerprint_stats.yaml` and `fingerprint/domain/profile.py` is not regenerated
- **THEN** `make check-all` exits non-zero and names the out-of-date file

### Requirement: Generated code is read-only
The generated modules SHALL carry a do-not-edit banner, SHALL be excluded from Ruff, and their model
classes SHALL be immutable (frozen) and reject unknown fields.

#### Scenario: Mutating a profile object
- **WHEN** code assigns a new value to a field of a generated profile object
- **THEN** a validation error is raised

#### Scenario: Banner present
- **WHEN** `make generate-models` runs
- **THEN** the first line of `fingerprint/domain/profile.py` and of `fingerprint/domain/views.py` states it is generated and must not be edited

## ADDED Requirements

### Requirement: Values are domain objects
Code in `fingerprint/` SHALL pass, return and store LinkML-generated Pydantic objects and enums, never
composed dicts. `make check-all` SHALL fail on a dict display, a dict comprehension or a call to
`dict`, `dict.fromkeys`, `defaultdict`, `OrderedDict` or `Counter` inside a function, or a `dict`,
`Mapping` or `defaultdict` parameter, return or attribute annotation, unless the line is marked
`# dict-ok: <reason>`; module-level constant tables, keyword arguments to `model_copy(update=…)` and
dicts unpacked with `**` into a constructor are allowed.

#### Scenario: A new dict value is refused
- **WHEN** a function in `fingerprint/service_layer/` returns `{"path": p}`
- **THEN** the gate fails and names the file and line

#### Scenario: A marked library boundary passes
- **WHEN** the template renderer adapter builds eds4jinja2's configuration dict on a line marked `# dict-ok: eds4jinja2 configuration`
- **THEN** the gate passes

### Requirement: Configuration through one typed config
Every operational value SHALL be read through the typed config object in `fingerprint/__init__.py`,
each backed by an `RDF_FINGERPRINTER_*` environment variable with a default; no other module SHALL
read `os.environ`. Importing the package SHALL resolve no value.

#### Scenario: A variable changes a default
- **WHEN** `RDF_FINGERPRINTER_PROFILE_FILE=run.json` is set and the fingerprint command runs
- **THEN** the profile is saved as `run.json`

#### Scenario: A badly typed variable
- **WHEN** `RDF_FINGERPRINTER_RETRY_BACKOFF_SECONDS=x` is set
- **THEN** the command exits 2 naming the variable, before any query is sent
