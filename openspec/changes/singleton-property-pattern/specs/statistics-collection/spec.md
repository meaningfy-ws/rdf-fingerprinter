# statistics-collection — delta for singleton-property-pattern

## ADDED Requirements

### Requirement: Reification probes
When `reifications` is on (the default), the collector SHALL ask each packaged reification probe
once per graph, and SHALL run a kind's capture query only when its probe answers true. With
`reifications` off it SHALL issue no probe or capture query and the profile SHALL equal today's.

#### Scenario: Kind absent
- **GIVEN** a graph with no `rdf:Statement` node
- **WHEN** the graph is profiled
- **THEN** the collector issues the `rdf:Statement` probe and not its capture query

#### Scenario: Switch off
- **GIVEN** `reifications` is off
- **WHEN** a graph with singleton properties is profiled
- **THEN** no probe is issued and every singleton predicate IRI is an ordinary property, as before

### Requirement: Reified relations are grouped by what they stand for
Each kind found SHALL be captured as reified relations, one per (subject class, generic predicate,
object class), each with its kind, statement count and the reifier properties with their counts. The
generic predicate SHALL come from what the data states, never from IRI strings: the kind's standard
marker (`rdf:predicate`, `owl:annotatedProperty`, `owl:assertionProperty`), else the predicate
resource's type other than `rdf:Property` and the OWL property types, else none (an unnamed
relation). Non-standard vocabulary, such as `rdf:singletonPropertyOf`, SHALL NOT name a relation:
it is reported as a reifier property only (DEC-12).

#### Scenario: Singleton properties are resources used as predicates
- **GIVEN** 50 distinct predicate IRIs typed `ex:Link`, each linking a subject of class A to an object
  of class B, each with `rdf:singletonPropertyOf ex:isRelatedTo` and `prov:wasAttributedTo`
- **WHEN** the graph is profiled
- **THEN** class A has one reified relation of kind resource as predicate, named `ex:Link`, to B, 50
  statements, reifier properties `rdf:singletonPropertyOf` on 50 and `prov:wasAttributedTo` on 50,
  and no relation named `ex:isRelatedTo`

#### Scenario: RDF reification
- **GIVEN** 30 `rdf:Statement` nodes whose `rdf:subject` is of class A, `rdf:predicate` is `ex:p`
  and `rdf:object` is of class B
- **WHEN** the graph is profiled
- **THEN** class A has one reified relation of kind RDF statement, `ex:p` to B, 30 statements

#### Scenario: Resource used as predicate
- **GIVEN** predicate IRIs typed `ex:Procedure` (not a property type), linking class A to class B,
  one of them used 25 times
- **WHEN** the graph is profiled
- **THEN** class A has one reified relation of kind resource as predicate, named `ex:Procedure`, to
  B, counting every use

#### Scenario: A predicate typed only as a property is ordinary
- **GIVEN** predicate IRIs typed only `rdf:Property`, used once each, one of them with
  `rdf:singletonPropertyOf ex:isRelatedTo`
- **WHEN** the graph is profiled
- **THEN** each stays an ordinary property and no reified relation is reported for them

#### Scenario: Relation through a blank node
- **GIVEN** subjects of class A each pointing with `ex:role` to a blank node that carries
  `ex:agent` and `ex:since`, the blank node not being a list or an OWL construct
- **WHEN** the graph is profiled
- **THEN** class A has one reified relation of kind blank n-ary, `ex:role`, with reifier properties
  `ex:agent` and `ex:since`

#### Scenario: RDF-star is counted only
- **GIVEN** a graph with 12 `rdf:reifies` triples
- **WHEN** the graph is profiled
- **THEN** the graph profile records 12 triple-term reifications (`rdf:reifies` triples) and no class has a
  relation for them

### Requirement: Reification machinery is not an ordinary class or property
When a kind is found, the predicates and reifier classes that implement it SHALL be absent from the
profile's ordinary classes and properties.

#### Scenario: Singleton predicates leave the property rows
- **GIVEN** the singleton graph of "Singleton properties are resources used as predicates"
- **WHEN** the graph is profiled
- **THEN** class A has no ordinary property for any of the 50 predicate IRIs

#### Scenario: A class with reifiers and ordinary instances stays whole
- **GIVEN** 3 singleton predicate IRIs typed `rdf:Property` and `ex:Link`, and 2 ordinary predicates
  typed `rdf:Property` only
- **WHEN** the graph is profiled
- **THEN** class `ex:Link` is absent, and class `rdf:Property` is present with 5 instances

#### Scenario: rdf:Statement leaves the classes
- **GIVEN** the graph of "RDF reification"
- **WHEN** the graph is profiled
- **THEN** the profile has no class `rdf:Statement` and no property `rdf:subject`, `rdf:predicate` or
  `rdf:object`
