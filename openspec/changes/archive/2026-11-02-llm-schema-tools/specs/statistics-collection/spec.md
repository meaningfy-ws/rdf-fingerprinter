## ADDED Requirements

### Requirement: Term labels and descriptions are collected
At every depth from `classes` on, the collector SHALL send one term-annotation query per profiled
graph, after the graph's classes are profiled (EPIC DEC-21). The query SHALL ask for the labels
and descriptions of the graph's class IRIs, and, from depth `properties` on, of its property
IRIs. It SHALL match them in the default graph and in every named graph, as the declared-hierarchy
query does. IRIs that cannot be put in a query SHALL be left out of it.

The predicates SHALL be those of EPIC DEC-20 and DEC-17. They count whether or not they are
declared `owl:AnnotationProperty`; no other annotation property is followed.
- **Label**, in priority order: `skos:prefLabel`, `skosxl:prefLabel`/`skosxl:literalForm`,
  `rdfs:label`, `dcterms:title`. `skos:altLabel` is used only when the term has none of these.
- **Description**, in priority order: `skos:definition`, `rdfs:comment`, `dcterms:description`,
  `skos:scopeNote`.

Only literal values count. Per term, per field and per language tag (untagged counts as one
language), the value SHALL come from the highest-priority predicate that has a value in that
language. Among several such values, the smallest lexical form wins. The selected values SHALL be
stored in the graph profile's `term_annotations`: one entry per term with at least one value,
holding its labels and its descriptions, each with its language. A graph whose terms have no
annotation SHALL store an empty list. When the query fails, a failure of kind `term_annotations`
SHALL be recorded, and the graph SHALL be kept, without annotations.

#### Scenario: Labels and descriptions of a class are stored
- **WHEN** `ex:Person` is profiled and the store holds `ex:Person rdfs:label "Person"@en`, `ex:Person skos:prefLabel "Personne"@fr` and `ex:Person rdfs:comment "A human being"@en`
- **THEN** the graph's term annotations give `ex:Person` the labels `"Person"@en` and `"Personne"@fr` and the description `"A human being"@en`

#### Scenario Outline: Label predicate priority
- **WHEN** the store holds, for the class `ex:Person`, only <values>
- **THEN** its stored labels are <labels>

  Examples:
    | values                                                                  | labels                 |
    | `skos:prefLabel "Human"@en`, `rdfs:label "Person"@en`                   | `"Human"@en`           |
    | `skosxl:prefLabel [ skosxl:literalForm "Human"@en ]`, `rdfs:label "Person"@en` | `"Human"@en`    |
    | `skos:altLabel "Body"@en`                                               | `"Body"@en`            |
    | `skos:altLabel "Body"@en`, `dcterms:title "Person"@de`                  | `"Person"@de`          |
    | `rdfs:label "B"`, `rdfs:label "A"`                                      | `"A"`                  |

#### Scenario: Annotations from another graph
- **WHEN** `ex:Person` is profiled in graph `http://ex.org/data` and its `rdfs:label` is asserted only in graph `http://ex.org/ontology`
- **THEN** the term annotations of `http://ex.org/data` hold that label

#### Scenario: Property annotations need depth properties
- **WHEN** the store labels the class `ex:Person` and the property `ex:name`, and the collector runs once at depth `classes` and once at depth `properties`
- **THEN** at `classes` only `ex:Person` has annotations, and at `properties` both have

#### Scenario: A failed annotation query keeps the graph
- **WHEN** the endpoint rejects the term-annotation query of a graph with HTTP 400
- **THEN** the graph's classes are in the profile, it has no term annotations, and one failure of kind `term_annotations` is recorded

## MODIFIED Requirements

### Requirement: Depth and switches select the queries
The collector SHALL run only the queries that the configured depth and switches require, as tabled
in `openspec/changes/archive/2026-10-31-harden-fingerprinter/design.md` ("Query templates"), plus
the term-annotation query at every depth from `classes` on ("Term labels and descriptions are
collected"); graph totals, predicate partitions and untyped subjects (full scans) SHALL run only
when `graph_statistics` is on, and pitfall check queries only when `pitfall_scan` is on
(pitfall-scans "The pitfall scan stage").

#### Scenario: Default depth
- **WHEN** the collector runs with default settings
- **THEN** it issues the graph list, class counts, hierarchy, co-type, vote, value, object-class and term-annotation queries and no graph-total, top-value or incoming-link query

#### Scenario: Graph statistics on
- **WHEN** `graph_statistics` is on
- **THEN** each graph profile records triples, distinct subjects, distinct objects, predicate partitions and untyped subjects

#### Scenario: Measurements per depth
- **WHEN** the depth is `classes`, `properties`, `values`, `rich_values` or `links`
- **THEN** each depth adds its measurements to those of the shallower ones (instance counts, hierarchy, co-types and class annotations; property histograms and property annotations; value partitions and object classes; top values; incoming links) and the profile holds nothing of the deeper ones
