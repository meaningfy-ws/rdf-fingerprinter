# profile-analytics — delta for singleton-property-pattern

## ADDED Requirements

### Requirement: Class analytics carry reified relations
The class analytics SHALL carry the class's reified relations from the profile, ordered by statement
count descending then generic predicate, apart from its property analytics.

#### Scenario: Relations follow their class
- **GIVEN** a profile where class A has two reified relations
- **WHEN** the analytics are computed
- **THEN** A's class analytics list both relations and its property analytics include neither
