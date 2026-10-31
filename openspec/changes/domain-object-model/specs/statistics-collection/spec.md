## ADDED Requirements

### Requirement: Results are read as typed RDF terms
The SPARQL client SHALL send each query with its per-query timeout and SHALL return the results as
rdflib result rows of typed terms (IRIs, blank nodes, typed literals); collection SHALL build the
profile model objects from those terms directly, without an intermediate string-keyed row.

#### Scenario: A count arrives as a number
- **WHEN** an endpoint answers a class count with `"3"^^xsd:integer`
- **THEN** the class's `instances` is the integer 3

#### Scenario: The timeout still applies
- **WHEN** the endpoint does not answer within `timeout_seconds`
- **THEN** the query fails as a timeout and the class escalates as before
