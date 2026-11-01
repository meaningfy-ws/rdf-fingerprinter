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
- **AND** the wheel contains `fingerprint_report_templates` with its templates and `fingerprint/adapters/queries` with its SPARQL queries

### Requirement: Import has no side effects
Importing any `fingerprint` module SHALL NOT configure logging or read files relative to the
current working directory.

#### Scenario: Import from another directory
- **WHEN** the installed package is imported with a working directory that has no `logging.conf`
- **THEN** the import succeeds and the root logger's handlers are unchanged

### Requirement: Reports on strict SPARQL stores
The packaged report SHALL render from the analytics alone (its templates issue no queries) and SHALL
render the e2e test data collected from a strict store without a `nan` cell.

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

### Requirement: Onion layers are enforced
`.importlinter` SHALL enforce the layers `entrypoints` > `service_layer` > `adapters` > `domain`
(each importing only layers below it), SHALL forbid the generated modules `fingerprint.domain.profile`
and `fingerprint.domain.views` from importing any other `fingerprint` module, and SHALL forbid
`fingerprint.domain` from importing `rdflib`, `jinja2`, `eds4jinja2` or `click`.

#### Scenario: Generated module imports project code
- **WHEN** `fingerprint/domain/profile.py` imports `fingerprint.domain.analytics`
- **THEN** `make check-architecture` exits non-zero

#### Scenario: Domain imports an adapter
- **WHEN** a module in `fingerprint.domain` imports `fingerprint.adapters`
- **THEN** `make check-architecture` exits non-zero and names the broken contract

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

### Requirement: Requirement-traced tests
Every scenario in `openspec/specs/<capability>/spec.md` SHALL be proven by exactly one Gherkin
scenario with the identical title in `tests/features/<capability>.feature` (hyphens as underscores),
or by a module-level test function named in `tests/guards/untraced_scenarios.txt` with a reason. `make check-all` SHALL fail
when a spec scenario is unproven, when a feature scenario has no spec scenario of that title, or when
an allow-list entry names a missing scenario or a test function its file does not define.

#### Scenario: A spec scenario without a test
- **WHEN** a scenario is added to `openspec/specs/fingerprint-report/spec.md` and no feature scenario or allow-list entry has its title
- **THEN** `make check-all` exits non-zero and names the capability and the scenario title

#### Scenario: An orphan feature scenario
- **WHEN** `tests/features/fingerprint_report.feature` holds a scenario whose title is in no spec scenario
- **THEN** `make check-all` exits non-zero and names the feature file and the scenario title

#### Scenario: A stale allow-list entry
- **WHEN** an entry in `tests/guards/untraced_scenarios.txt` names a test function its file does not define
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
`make refresh-sample-profile` SHALL leave the file untouched when a fresh collection equals it other than
in timestamps, tool version and row order. The known facts of the sample datasets SHALL be named once
in `tests/sample_data.py`, and `make test-e2e`
SHALL fail when a fresh collection differs from the stored profile other than in timestamps, tool version
and row order.

#### Scenario: Regenerating without a data change
- **WHEN** a contributor runs `make oxigraph-load-test-data`, then `make refresh-sample-profile` and `make refresh-golden` on a clean checkout
- **THEN** `git status` shows no change under `tests/test_data/`

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

### Requirement: Generated outputs compared by meaning
Golden-file tests of Turtle outputs SHALL compare the produced and the golden file as RDF graphs
(isomorphism), and on a difference SHALL report the triples found in only one of them.

#### Scenario: A reordered Turtle output
- **WHEN** a generator emits the same triples as its golden file in a different order and with different prefix names
- **THEN** the golden test passes

#### Scenario: A changed triple
- **WHEN** a generator emits one literal different from its golden file
- **THEN** the golden test fails and reports that triple as only in the output and the original as only in the golden file

