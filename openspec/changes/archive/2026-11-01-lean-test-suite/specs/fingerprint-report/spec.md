## MODIFIED Requirements

### Requirement: Report content
The report SHALL show:
- an overview with provenance (endpoint, dates, tool version);
- the namespace table (prefix, namespace, source);
- a collection section: the settings used, and every recorded failure with its graph, class,
  property, query kind, attempts and message;
- per graph and class: the class, its instance count, its precision mode ("exact" or "first N of
  M", followed by "(sample may differ between queries)" when the sample was not shared) and its
  parents;
- per property, as today: property, subjects, min, max, avg, kind, distinct values, value types,
  confidence, cardinality (the label; `present` for a presence-only property), inheritance and
  language coverage. Numbers are rounded to 2 decimals, and an absent value is `—`;
- the caveats: first-N classes, the untyped subjects per graph (when graph statistics were
  collected), the IRIs that could not be written, and the namespaces the filters hid, with their
  class counts.

Every IRI SHALL be shown as `prefix:local`, graph names included, with the full IRI as its
`title` and link target. A hidden namespace's count is its number of distinct class IRIs. An
unknown filter name is warned about once per run. The
report SHALL NOT embed diagram sources.

#### Scenario: First N class is labelled
- **WHEN** a class with 50 000 instances was read with first N = 10 000
- **THEN** its section shows "first 10000 of 50000"

#### Scenario: The property columns
- **WHEN** the report is generated for the e2e test data
- **THEN** every class table has the columns property, subjects, min, max, avg, kind, distinct values and value types

#### Scenario: Failure listed
- **WHEN** the profile contains one failure for class `ex:Big`
- **THEN** the collection section lists `ex:Big` with the query kind and the error message

#### Scenario: Short names only
- **WHEN** the report is generated for the readability test profile
- **THEN** no text node outside the namespace table, the provenance endpoint, the setting values, the failure messages and the unwritable-IRI caveats holds `http://` or `https://`

#### Scenario: Hidden namespaces are listed
- **WHEN** the report is generated with the default filters for a profile holding 2 `owl:` classes
- **THEN** the caveats list `owl` as hidden with 2 classes, and no `owl:` class section exists

#### Scenario: Exact class is labelled
- **WHEN** a class with 120 instances was read exactly
- **THEN** its section shows "exact"

#### Scenario: Absent value is a dash
- **WHEN** a property's language coverage is absent
- **THEN** its language coverage cell shows `—`

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

#### Scenario: Clean run
- **WHEN** every class is profiled
- **THEN** the CLI exits 0 and the report is written

#### Scenario: Usage error
- **WHEN** the output folder does not exist, a setting is invalid, or the prefix file is malformed
- **THEN** the CLI exits 2 and writes no report

#### Scenario: Unexpected error
- **WHEN** an unexpected error occurs during collection
- **THEN** the CLI exits 4 and writes no report

### Requirement: Formats rendered after collecting
The `fingerprint` command SHALL accept the representations to render after collecting (any of
SHACL, PlantUML and the document); without them, it SHALL write only the report and the profile file.
Selecting the document SHALL write no second page and SHALL log that `main.html` is the document. The
command and every `fingerprint-gen-*` command SHALL accept `--prefixes FILE`, and the repeatable
`--exclude-namespace` and `--include-namespace`. The other options:
- `--no-prefix-lookup`: `fingerprint` only;
- `--module-size N` (an integer ≥ 1): `fingerprint` and `fingerprint-gen-puml`;
- `--shapes-namespace IRI`: `fingerprint` and `fingerprint-gen-shacl`.

These SHALL be usage errors (exit 2), before any query: an unknown format, an unreadable or malformed
prefix file, a module size below 1, and an unwritable shapes namespace.

#### Scenario: Report plus SHACL in one run
- **WHEN** the fingerprint command runs with the SHACL format selected
- **THEN** the output folder holds `main.html`, `profile.json` and one shapes file per non-empty profiled graph

#### Scenario: The document is the report
- **WHEN** the fingerprint command runs with the document format selected
- **THEN** the output folder holds `main.html` and no `profile.html`

#### Scenario: Unknown format
- **WHEN** the fingerprint command runs with a format that does not exist
- **THEN** it exits 2, names the known formats and queries nothing

#### Scenario: A failing representation keeps the report
- **WHEN** a selected representation fails to render
- **THEN** the output folder holds `main.html` and `profile.json`, and the command exits 4
