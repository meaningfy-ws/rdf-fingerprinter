## ADDED Requirements

### Requirement: Scan files locally
`make scan-files ONTOLOGY=<file> [DATA=<file>] OUT=<folder>` SHALL start a separate in-memory scan
Oxigraph (the compose service `oxigraph-scan` on `RDF_FINGERPRINTER_SCAN_PORT`, default 7879), never
the e2e test store, load the
ontology into the graph `urn:fingerprint:scan:schema` and the data (when given) into
`urn:fingerprint:scan:data`, after clearing both, and run `fingerprint --pitfalls --schema-graph
urn:fingerprint:scan:schema --format pitfalls` over those graphs (`--graph` for each loaded graph, so the store's empty default graph is not
profiled) into `OUT`. RDF/XML (`.rdf`, `.owl`) and
Turtle (`.ttl`) files SHALL be accepted.

#### Scenario: Ontology and data
- **WHEN** `make scan-files ONTOLOGY=o.owl DATA=d.rdf OUT=out` runs with Docker available
- **THEN** `out/` holds `main.html` with a Pitfalls section, `profile.json` and a `pitfalls-*.tsv` per graph

#### Scenario: The test store is untouched
- **WHEN** `make scan-files` runs while the e2e store holds the test data
- **THEN** the e2e store's graphs are unchanged
