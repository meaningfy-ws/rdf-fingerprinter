## MODIFIED Requirements
### Requirement: Depth and switches select the queries
The collector SHALL run only the queries that the configured depth and switches require, as tabled
in `openspec/changes/archive/2026-10-31-harden-fingerprinter/design.md` ("Query templates"); graph totals, predicate partitions and untyped subjects (full scans) SHALL run only
when `graph_statistics` is on, and pitfall check queries only when `pitfall_scan` is on
(pitfall-scans "The pitfall scan stage").

#### Scenario: Default depth
- **WHEN** the collector runs with default settings
- **THEN** it issues the graph list, class counts, hierarchy, co-type, vote, value and object-class queries and no graph-total, top-value or incoming-link query

#### Scenario: Graph statistics on
- **WHEN** `graph_statistics` is on
- **THEN** each graph profile records triples, distinct subjects, distinct objects, predicate partitions and untyped subjects

#### Scenario: Measurements per depth
- **WHEN** the depth is `classes`, `properties`, `values`, `rich_values` or `links`
- **THEN** each depth adds its measurements to those of the shallower ones (instance counts, hierarchy and co-types; property histograms; value partitions and object classes; top values; incoming links) and the profile holds nothing of the deeper ones

### Requirement: Failures are recorded and fail the run
A query that still fails after retries and fallbacks SHALL be recorded as a `Failure` (query kind,
graph, class, property, check id, message, attempts); the other classes, and the other pitfall checks,
SHALL still be collected.

#### Scenario: Named graphs cannot be listed
- **WHEN** the endpoint rejects the named-graph listing query with HTTP 400
- **THEN** only the default graph is profiled and a failure of kind `graphs` is recorded

#### Scenario: One class fails
- **WHEN** every attempt for one class fails and all other classes succeed
- **THEN** the profile contains the other classes and one failure naming that class

#### Scenario: One pitfall check fails
- **WHEN** one pitfall check's count query times out after its retries
- **THEN** a failure of kind `pitfall` with that check's id is recorded and the other checks' results are in the profile

