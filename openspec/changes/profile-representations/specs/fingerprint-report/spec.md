## ADDED Requirements

### Requirement: The profile is saved with the report
The `fingerprint` command and `fingerprint_report` SHALL write the raw profile run as
`profile.json` in the output folder, beside the report, whenever the report is written (EPIC DEC-2).
The library function `generate_endpoint_fingerprint_report` SHALL keep its return value (DEC-8).

#### Scenario: Profile file beside the report
- **WHEN** the fingerprint command runs and the report is written
- **THEN** the output folder also holds `profile.json`

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
