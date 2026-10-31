## ADDED Requirements

### Requirement: The profile is saved with the report
The `fingerprint` command and `fingerprint_report` SHALL write the raw profile run as
`profile.json` in the output folder as soon as collection ends, before the report is rendered, so a
rendering failure loses nothing collected (EPIC DEC-2).
The library function `generate_endpoint_fingerprint_report` SHALL keep its return value (DEC-8).

#### Scenario: Profile file beside the report
- **WHEN** the fingerprint command runs and the report is written
- **THEN** the output folder also holds `profile.json`

#### Scenario: Profile kept when the report fails
- **WHEN** collection succeeds and the report template raises an error
- **THEN** `profile.json` is in the output folder and the command exits 4

#### Scenario: Partial failures are saved too
- **WHEN** one class fails and the report is written
- **THEN** `profile.json` lists that failure and the command exits 1

### Requirement: Formats rendered after collecting
The `fingerprint` command SHALL accept the representations to render after collecting (any of
SHACL, PlantUML and the profile document); without it, it SHALL write only the report and the
profile file, as before. An unknown format SHALL be a usage error (exit 2).

#### Scenario: Report plus SHACL in one run
- **WHEN** the fingerprint command runs with the SHACL format selected
- **THEN** the output folder holds the report, `profile.json` and one shapes file per profiled graph

#### Scenario: Unknown format
- **WHEN** the fingerprint command runs with a format that does not exist
- **THEN** it exits 2, names the known formats and queries nothing

### Requirement: Read-only and credential-safe
Collection SHALL send only SPARQL `SELECT` and `ASK` queries. Credentials in the endpoint URL (user
info, query string) SHALL NOT appear in any output or log line.

#### Scenario: Credentials are redacted
- **WHEN** the endpoint is `https://user:pw@host:8890/sparql?key=abc`
- **THEN** outputs and logs show `https://host:8890/sparql`

### Requirement: Library outcomes
`generate_endpoint_fingerprint_report` SHALL raise `NotADirectoryError` for a missing output folder,
`UsageError` (a `ValueError`) for an invalid setting, and `EndpointUnreachable` when the endpoint is
unreachable at the start, all before writing; other exceptions SHALL propagate unchanged. A custom
template folder SHALL render the report with the caller's constants in its configuration.

#### Scenario: Custom template constants
- **WHEN** the library is called with a custom template that reads a constant passed in `additional_config`
- **THEN** the report shows the constant

## MODIFIED Requirements

### Requirement: Exit status
The `fingerprint` CLI SHALL exit 0 when the profile has no failures, 1 when the outputs were written
but failures were recorded, 2 on a usage error before any query, 3 when the endpoint is unreachable
when the run starts (the graph listing meets an authorisation refusal or a persistent transient
error), and 4 on an unexpected error. A refusal or timeout after the start SHALL be a recorded
failure (exit 1), not exit 3. **BREAKING** (1.x always exited 0).

#### Scenario: Partial failure
- **WHEN** one class fails and the report is written
- **THEN** the CLI exits 1 and logs the number of failures

#### Scenario: Endpoint unreachable
- **WHEN** the endpoint URL refuses connections
- **THEN** the CLI exits 3, writes no report and logs `cannot reach endpoint <url>`
