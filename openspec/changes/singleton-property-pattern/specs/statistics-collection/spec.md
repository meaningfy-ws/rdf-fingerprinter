# statistics-collection — delta for singleton-property-pattern

> Outcome only; the detection and grouping rules are decided when the EPIC is shaped.

## ADDED Requirements

### Requirement: Resources used as predicates are recognised
The profile SHALL recognise predicates that are themselves resources of the graph (the singleton
property pattern and its variants) and report them as relations grouped by what they stand for,
instead of as one ordinary property per predicate IRI.

#### Scenario: Singleton properties of one generic property
- **GIVEN** a graph where 500 distinct predicate IRIs each link a subject of class A to an object of
  class B, and each predicate IRI has `rdf:singletonPropertyOf ex:isRelatedTo`
- **WHEN** the graph is profiled
- **THEN** the profile reports one relation `ex:isRelatedTo` from A to B, built from 500 singleton
  predicates, and no ordinary property for any of those 500 predicate IRIs
