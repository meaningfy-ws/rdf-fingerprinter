## MODIFIED Requirements

### Requirement: Reports on strict SPARQL stores
The packaged report SHALL render from the analytics alone (its templates issue no queries) and SHALL
render the e2e test data collected from a strict store without a `nan` cell.

#### Scenario: Oxigraph renders the type columns
- **WHEN** the default report is generated against Oxigraph loaded with the test data
- **THEN** no table cell of the report renders as `nan`
