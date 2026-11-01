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
- when the profile holds scan results, a *Pitfalls* section ("Pitfalls in the report", below);
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
- **THEN** no text node outside the namespace table, the provenance endpoint, the setting values, the failure messages, the unwritable-IRI caveats and the pitfall literal values holds `http://` or `https://`

#### Scenario: Hidden namespaces are listed
- **WHEN** the report is generated with the default filters for a profile holding 2 `owl:` classes
- **THEN** the caveats list `owl` as hidden with 2 classes, and no `owl:` class section exists

#### Scenario: No scan, no section
- **WHEN** the report is generated for a profile without scan results
- **THEN** it has no Pitfalls section and no pitfall badge

### Requirement: Exit status
The `fingerprint` CLI SHALL exit 0 when the profile has no failures, 1 when the outputs were written
but failures were recorded, 2 on a usage error before any query, 3 when the endpoint is unreachable
when the run starts (the graph listing meets an authorisation refusal or a persistent transient
error), 4 on an unexpected error, and 5 when `--fail-on` is given, no failure was recorded and
pitfalls at or above its level were found (pitfall-scans "Fail on findings"). A refusal or timeout
after the start SHALL be a recorded failure (exit 1), not exit 3. **BREAKING** (1.x always exited 0).

#### Scenario: Partial failure
- **WHEN** one class fails and the report is written
- **THEN** the CLI exits 1 and logs the number of failures

#### Scenario: Endpoint unreachable
- **WHEN** the endpoint URL refuses connections
- **THEN** the CLI exits 3, writes no report and logs `cannot reach endpoint <url>`

#### Scenario: Pitfalls found with fail-on
- **WHEN** a run with `--pitfalls --fail-on critical` records no failure and finds a critical pitfall
- **THEN** the CLI exits 5 and logs `<rows> findings in <checks> checks at or above critical`

### Requirement: Read-only and credential-safe
Collection SHALL send only SPARQL `SELECT` and `ASK` queries; every pitfall check, packaged or the
user's, SHALL be parsed before any query and refused unless it is a `SELECT` (pitfall-scans
"Pitfall check contract"). Credentials in the endpoint URL (user info, query string) SHALL NOT appear
in any output or log line.

#### Scenario: Credentials are redacted
- **WHEN** the endpoint is `https://user:pw@host:8890/sparql?key=abc`
- **THEN** outputs and logs show `https://host:8890/sparql`

#### Scenario: An update in a user check is refused
- **WHEN** `--pitfall-checks` holds a file with `DELETE WHERE { ?s ?p ?o }`
- **THEN** the command exits 2 naming the file, and sends no query

### Requirement: Formats rendered after collecting
The `fingerprint` command SHALL accept the representations to render after collecting (any of
SHACL, PlantUML, the document and the pitfalls TSV); without them, it SHALL write only the report and
the profile file. Selecting the document SHALL write no second page and SHALL log that `main.html` is
the document. The command and every `fingerprint-gen-*` command SHALL accept `--prefixes FILE`, and
the repeatable `--exclude-namespace` and `--include-namespace`. The other options:
- `--no-prefix-lookup`: `fingerprint` only;
- `--module-size N` (an integer ≥ 1): `fingerprint` and `fingerprint-gen-puml`;
- `--shapes-namespace IRI`: `fingerprint` and `fingerprint-gen-shacl`;
- the scan options (pitfall-scans "Scan settings and options"): `fingerprint` only.

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

#### Scenario: Pitfalls format in the run
- **WHEN** the fingerprint command runs with `--pitfalls --format pitfalls`
- **THEN** the output folder holds one `pitfalls-<graph>.tsv` per profiled graph with a scan result

## ADDED Requirements

### Requirement: Pitfalls in the report
When the profile holds scan results, the report SHALL have a *Pitfalls* section with:
- a contents entry;
- a summary of the number of distinct checks (by id, over all graphs) with findings, per importance;
- per graph, one entry per check, ordered by importance, then by count descending, then by id,
  showing the title, the description (when given), importance, source, count, whether it is a
  heuristic, and the examples as short names (`prefix:local`, full IRI as title; literal values as escaped text);
- the checks that found nothing, listed by id.

A class section whose class is the entity of an example SHALL show one badge per such check, linking
to that check's entry. The search box SHALL also filter the check entries by id and title (the
report's search, extended to the new section).

#### Scenario: Section and badge
- **WHEN** the report is generated for a profile whose `x_punning_class_and_property` result has the example entity `bf:factActivity`, a profiled class
- **THEN** the Pitfalls section lists that check with its count and example `bf:factActivity`, and the `bf:factActivity` class section shows a badge linking to it

#### Scenario: Values are escaped
- **WHEN** an example value is `<script>alert(1)</script>`
- **THEN** the page shows it as text and contains no `<script>` element with that content
