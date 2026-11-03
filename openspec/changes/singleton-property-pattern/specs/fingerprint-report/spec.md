# fingerprint-report — delta for singleton-property-pattern

## ADDED Requirements

### Requirement: Reified relations in the report
The report SHALL show each class's reified relations in a separate section under the class, after
its properties, and SHALL state in the graph summary which reification kinds were found and the
triple-term count when not zero.

#### Scenario: Kinds found are named
- **GIVEN** a profile with singleton properties and `rdf:Statement` reifications
- **WHEN** the report is rendered
- **THEN** the graph summary names both kinds and each subject class shows its reified relations
