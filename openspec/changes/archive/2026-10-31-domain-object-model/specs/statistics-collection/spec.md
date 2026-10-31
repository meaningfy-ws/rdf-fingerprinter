## ADDED Requirements

### Requirement: Results are read as typed RDF terms
The SPARQL client SHALL send each query with its per-query timeout and SHALL return the results as
rdflib result rows of typed terms (IRIs, blank nodes, typed literals); collection SHALL build the
profile model objects from those terms directly, without an intermediate string-keyed row. Literals
SHALL keep the lexical form the endpoint sent, and a literal whose language tag rdflib refuses SHALL
keep its text rather than fail the answer.

#### Scenario: A count arrives as a number
- **WHEN** an endpoint answers a class count with `"3"^^xsd:integer`
- **THEN** the class's `instances` is the integer 3

#### Scenario: The timeout still applies
- **WHEN** the endpoint does not answer within `timeout_seconds`
- **THEN** the query fails as a timeout and the class escalates as before

#### Scenario: Values keep the endpoint's text
- **WHEN** the endpoint answers a value `"2020-01-01T00:00:00Z"^^xsd:dateTime` or `"v"@en_US`
- **THEN** the profile records `2020-01-01T00:00:00Z` and `v`, unchanged
