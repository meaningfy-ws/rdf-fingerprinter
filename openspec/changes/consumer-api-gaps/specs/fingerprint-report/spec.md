## ADDED Requirements

### Requirement: Bounded endpoint calls
The SPARQL client SHALL end every attempt within `timeout_seconds` of its start plus one blocked
socket read, raising `QueryTimeout`, and SHALL refuse an answer larger than
`RDF_FINGERPRINTER_MAX_ANSWER_BYTES` (default 268435456) with `AnswerTooLarge`, a `PermanentError`,
without reading the rest (consumer-api-gaps C-1).

#### Scenario: A slow answer times out at the deadline
- **GIVEN** an endpoint that sends one byte per second
- **WHEN** a query runs with a timeout of 2 seconds
- **THEN** "QueryTimeout" is raised within 4 seconds

#### Scenario: An oversized answer is refused
- **GIVEN** an endpoint whose answer is larger than the answer size limit
- **WHEN** a query runs
- **THEN** "AnswerTooLarge" is raised and no more than the limit plus one buffer was read

### Requirement: Listing error contract
`list_named_graphs` SHALL raise `PermanentError` for an answer without the `g` variable, and
`ConfigurationError`, a `UsageError` that is not raised for an invalid URL, for an invalid
`RDF_FINGERPRINTER_*` setting (consumer-api-gaps C-2).

#### Scenario: A listing answer without the graph column is refused
- **GIVEN** an endpoint whose graph listing has no graph column
- **WHEN** a caller tries to list its named graphs
- **THEN** "PermanentError" is raised

#### Scenario: A bad setting is not a bad URL
- **GIVEN** the setting RDF_FINGERPRINTER_ERROR_EXCERPT_LENGTH is "zero"
- **WHEN** a caller tries to list its named graphs
- **THEN** "ConfigurationError" is raised
