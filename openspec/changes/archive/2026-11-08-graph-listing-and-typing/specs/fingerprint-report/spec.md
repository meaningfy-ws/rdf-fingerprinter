## ADDED Requirements

### Requirement: Named graph listing
The library SHALL offer `list_named_graphs(sparql_endpoint_url, settings, *, sparql=None)`, which
SHALL return the endpoint's named graph IRIs, sorted, without the default graph, through the same
query, timeout and retries as a run's graph discovery. It SHALL raise, before any query, a
`UsageError` for an invalid URL or setting; it SHALL raise `EndpointUnreachable` when the endpoint
cannot be reached, `QueryTimeout` when the listing times out and `PermanentError` when the endpoint
refuses it, and SHALL NOT answer an empty list for an error (graph-listing-and-typing DEC-1, DEC-2).

#### Scenario: Named graphs are listed
- **GIVEN** an endpoint with triples in the named graphs `http://example.org/g2` and `http://example.org/g1` and in the default graph
- **WHEN** a caller lists its named graphs
- **THEN** the result is `http://example.org/g1`, `http://example.org/g2`

#### Scenario: No named graphs
- **GIVEN** an endpoint with triples in the default graph only
- **WHEN** a caller lists its named graphs
- **THEN** the result is empty

#### Scenario: Listing an unreachable endpoint
- **GIVEN** an endpoint that cannot be reached
- **WHEN** a caller lists its named graphs
- **THEN** `EndpointUnreachable` is raised

#### Scenario: The listing times out
- **GIVEN** an endpoint whose graph listing times out
- **WHEN** a caller lists its named graphs
- **THEN** `QueryTimeout` is raised
