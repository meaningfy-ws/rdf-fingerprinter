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
it is reported as a reifier property only (DEC-12). A relation through a qualifying node SHALL be
named by the predicate the data uses to reach that node, never translated into another
vocabulary's term (DEC-13).

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
- **GIVEN** subjects of class A each pointing with `ex:role` to an untyped blank node that carries
  `ex:agent` and `ex:since`, the blank node not being a list or an OWL construct
- **WHEN** the graph is profiled
- **THEN** class A has one reified relation of kind blank n-ary, `ex:role`, with reifier properties
  `ex:agent` and `ex:since`

#### Scenario: A typed blank node stays ordinary
- **GIVEN** subjects of class A each pointing with `ex:address` to a blank node typed `ex:Address`
  that carries `ex:street`
- **WHEN** the graph is profiled
- **THEN** class `ex:Address` is profiled with property `ex:street` as before, and class A has no
  reified relation for `ex:address`

#### Scenario: Structured value
- **GIVEN** subjects of class A each with `ex:height` pointing to an untyped node with `rdf:value`
  and `ex:unit`, and subjects of class A each with `ex:code` pointing to a node typed `ex:Notation`
  with `rdf:value`
- **WHEN** the graph is profiled
- **THEN** class A has one reified relation of kind structured value, `ex:height`, with reifier
  property `ex:unit`, no relation for `ex:code`, and class `ex:Notation` is profiled as before

#### Scenario: PROV qualified association
- **GIVEN** 4 subjects of class `ex:Run`, each with a `prov:qualifiedAssociation` node whose
  `prov:agent` is of class `ex:Team` and which carries `prov:hadRole`
- **WHEN** the graph is profiled
- **THEN** class `ex:Run` has one reified relation of kind PROV qualified, `prov:qualifiedAssociation`
  to `ex:Team`, 4 statements, reifier property `prov:hadRole` on 4, no relation named
  `prov:wasAssociatedWith`, and no ordinary property `prov:qualifiedAssociation`

#### Scenario: SKOS-XL labels stay ordinary
- **GIVEN** concepts of class `skos:Concept` with `skos:prefLabel` literals and `skosxl:prefLabel`
  nodes typed `skosxl:Label` carrying `skosxl:literalForm`
- **WHEN** the graph is profiled
- **THEN** class `skos:Concept` has the ordinary properties `skos:prefLabel` and `skosxl:prefLabel`,
  class `skosxl:Label` is profiled with `skosxl:literalForm`, and no reified relation is reported

#### Scenario: Nanopublications are counted
- **GIVEN** a graph holding 3 nanopublication heads with `np:hasAssertion`, `np:hasProvenance` and
  `np:hasPublicationInfo`
- **WHEN** the graph is profiled
- **THEN** the graph profile counts 3 nanopublications, no class has a relation for them, and the
  profile has no class `np:Nanopublication`

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
