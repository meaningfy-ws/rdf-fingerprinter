## ADDED Requirements

### Requirement: Report renders from the analytics
The packaged report template SHALL render from the analytics profile passed in its context and
SHALL NOT issue SPARQL queries; it SHALL be rendered by eds4jinja2's `ReportBuilder` (DEC-6).

#### Scenario: No queries during rendering
- **WHEN** the report is rendered from an analytics profile with a SPARQL client that fails on any call
- **THEN** the report is written and the client was never called

### Requirement: Report content
Per graph and class the report SHALL show the class, its instance count, its precision mode
("exact", "batched" or "first N of M") and its parents; per property it SHALL show today's columns
(property, subjects using it, min, max, avg, property kind, distinct values, value types) plus
confidence, cardinality label and own/inherited/refined, with IRIs shortened by the packaged prefixes.

#### Scenario: First N class is labelled
- **WHEN** a class with 50 000 instances was read with first N = 10 000
- **THEN** its section shows "first 10000 of 50000"

#### Scenario: Today's columns survive
- **WHEN** the report is generated for the e2e test data
- **THEN** every class table has the columns property, subjects, min, max, avg, kind, distinct values and value types

### Requirement: Failures and settings are reported
The report SHALL include a collection section listing the settings used and every recorded failure.

#### Scenario: Failure listed
- **WHEN** the profile contains one failure for class `ex:Big`
- **THEN** the collection section lists `ex:Big` with the query kind and the error message

### Requirement: Exit status
The `fingerprint` CLI SHALL exit 0 when the profile has no failures, 1 when the report was written
but failures were recorded, 3 when the endpoint could not be reached, and 4 on an unexpected error (2
remains click's usage error). **BREAKING** (1.x always exited 0).

#### Scenario: Partial failure
- **WHEN** one class fails and the report is written
- **THEN** the CLI exits 1 and logs the number of failures

#### Scenario: Endpoint unreachable
- **WHEN** the endpoint URL refuses connections
- **THEN** the CLI exits 3, writes no report and logs `cannot reach endpoint <url>`

### Requirement: Public function keeps its signature
`generate_endpoint_fingerprint_report` SHALL keep its 1.x parameters and return value; collection
settings SHALL arrive through `additional_config["collection"]`.

#### Scenario: 1.x call still works
- **WHEN** a caller invokes it with only `sparql_endpoint_url` and `output_location`
- **THEN** it returns the path of the main report document
