## MODIFIED Requirements

### Requirement: Depth and switches select the queries
The collector SHALL run only the queries that the configured depth and switches require, as tabled
in `design.md`; graph totals, predicate partitions and untyped subjects (full scans) SHALL run only
when `graph_statistics` is on, and pitfall check queries only when `pitfall_scan` is on
(pitfall-scans "The pitfall scan stage").

#### Scenario: Default depth
- **WHEN** the collector runs with default settings
- **THEN** it issues the graph list, class counts, hierarchy, co-type, vote, value and object-class queries and no graph-total, top-value, incoming-link or pitfall query

#### Scenario: Graph statistics on
- **WHEN** `graph_statistics` is on
- **THEN** each graph profile records triples, distinct subjects, distinct objects, predicate partitions and untyped subjects

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
