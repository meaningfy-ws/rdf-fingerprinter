## ADDED Requirements

### Requirement: Benchmark is reproducible offline
The collection benchmark SHALL run against a local Oxigraph store loaded from a documented public
dump, with no network access to a public endpoint (EPIC DEC-1). Draft: the full requirement set is
written when this EPIC is shaped.

#### Scenario: Rerun on another machine
- **WHEN** a developer loads the documented dump into Oxigraph and runs the benchmark
- **THEN** it completes without contacting any remote SPARQL endpoint and reports wall time, query count and precision mode per class
