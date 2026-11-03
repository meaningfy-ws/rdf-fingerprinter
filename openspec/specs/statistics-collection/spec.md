# statistics-collection Specification

## Purpose
How rdf-fingerprinter collects raw statistics from a SPARQL 1.1 endpoint: staged discovery, class-scoped queries, exact → first-N precision escalation, recorded failures and the collection settings. Formulas and query texts: openspec/changes/archive/2026-10-31-harden-fingerprinter/design.md.
## Requirements
### Requirement: Staged discovery
The collector SHALL profile the default graph and then every named graph (DEC-11), and SHALL obtain
the instance count of every class in a graph with one grouped query, falling back to one count per
class when that query times out.

#### Scenario: Default and named graphs are profiled
- **WHEN** the endpoint holds triples in the default graph and in two named graphs
- **THEN** the profile contains three graph profiles, the default graph first

#### Scenario: Class counts fall back on timeout
- **WHEN** the grouped class-count query times out
- **THEN** the collector lists the distinct classes and counts each one, and the profile has the same instance counts

#### Scenario: Only the selected graphs are profiled
- **WHEN** the endpoint holds triples in the default graph and in two named graphs and only one named graph is selected
- **THEN** the profile contains only that graph

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

### Requirement: rdf:type is not a property row
Per-class property statistics SHALL exclude `rdf:type`; type information SHALL be recorded as
co-types.

#### Scenario: Type triples excluded
- **WHEN** instances of `ex:Student` are also typed `ex:Person`
- **THEN** no property profile of `ex:Student` has property `rdf:type`, and its co-types list `ex:Person`

### Requirement: Per-class queries are scoped to the class
Every per-class query SHALL select its subjects through the class's own subject source (all
instances, or the first N listed once); no query SHALL aggregate over the whole graph and filter
by class afterwards.

#### Scenario: Query text binds the class inside the pattern
- **WHEN** the collector builds the cardinality-vote query for class `ex:Person`
- **THEN** the query contains `?s a <http://example.org/Person>` inside the innermost subquery

### Requirement: Raw statistics per class
For each class the collector SHALL record the instance count, the instances read, the precision
mode used, the co-types, and, per property, the cardinality histogram and the value partitions
(node kind, datatype, language, object class, triples, distinct objects, lexical lengths and value
ranges for literals), as defined by `fingerprint_stats`.

#### Scenario: Cardinality histogram
- **WHEN** class `ex:Person` has four instances and `ex:name` has 1, 1, 2 and 0 values on them
- **THEN** the histogram for `ex:name` is `{1: 2, 2: 1}` and `observed_instances` is 4

#### Scenario: Literal value partition
- **WHEN** the `ex:name` values are `"Ann"@en`, `"Bo"@en` and `"Carl"`
- **THEN** there are two literal partitions, `rdf:langString`/`en` with triples 2, min length 2, max length 3, and `xsd:string` with triples 1

#### Scenario: Untyped objects are counted
- **WHEN** `ex:knows` points to one IRI typed `ex:Person` and one IRI with no type
- **THEN** the object partitions record one object of class `ex:Person` and one untyped object

### Requirement: Object types across graphs
When `object_type_scope` is `any_graph`, the collector SHALL look up object types in every graph
and record the graph that supplied each type; when it is `same_graph` (default), only the profiled
graph is used.

#### Scenario: Same-graph scope ignores other graphs
- **WHEN** an object's type is asserted only in another named graph and the scope is `same_graph`
- **THEN** the object is counted as untyped

#### Scenario: Type asserted in another graph
- **WHEN** an object's type is asserted only in another named graph and the scope is `any_graph`
- **THEN** the object partition records that class and that graph as `object_class_graph`

### Requirement: Precision escalation
Under policy `auto` the collector SHALL read each class exactly first and, when a per-class query
times out, retry the class in `first_n` mode, then record a failure.
Partial results of a failed attempt MUST be discarded. The mode used SHALL be stored per class.
A forced policy (`exact`, `first_n`) SHALL use only that mode. A first_n sample whose listed instances include blank nodes SHALL be recorded with `sample_shared` false.

#### Scenario: Exact succeeds
- **WHEN** every query for a class answers within the timeout
- **THEN** the class's `precision_mode` is `exact` and `observed_instances` equals `instances`

#### Scenario: First N uses one sample
- **WHEN** a class is read in first_n mode
- **THEN** the vote, value, object-class and co-type queries all use the same instance IRIs from a single listing query

#### Scenario: Escalation to first N
- **WHEN** the exact attempt for a class with 50 000 instances times out and first N = 10 000 succeeds
- **THEN** `precision_mode` is `first_n`, `observed_instances` is 10 000 and `instances` is 50 000

#### Scenario: First N on a small class equals exact
- **WHEN** a class with fewer instances than N is collected once with policy `exact` and once with policy `first_n`
- **THEN** the histograms, value partitions and distinct counts are equal

#### Scenario: A forced policy uses only its mode
- **WHEN** the exact read of a class times out under policy `exact`, or under policy `first_n`
- **THEN** under `exact` the class is recorded as a failure, and under `first_n` the class is read in `first_n` mode with no exact attempt

#### Scenario: Blank-node instances weaken the first-N sample
- **WHEN** a class read in first_n mode has blank nodes among its listed instances
- **THEN** its profile records `sample_shared` as false, because blank-node labels may differ between queries

### Requirement: Failures are recorded and fail the run
A query that still fails after retries and fallbacks SHALL be recorded as a `Failure` (query kind,
graph, class, property, check id, message, attempts); the other classes, and the other pitfall checks,
SHALL still be collected.

#### Scenario: Named graphs cannot be listed
- **WHEN** the endpoint rejects the named-graph listing query with HTTP 400
- **THEN** only the default graph is profiled and a failure of kind `graphs` is recorded

#### Scenario: One class fails
- **WHEN** every attempt for one class fails and all other classes succeed
- **THEN** the profile contains the other classes and one failure naming that class

#### Scenario: One pitfall check fails
- **WHEN** one pitfall check's count query times out after its retries
- **THEN** a failure of kind `pitfall` with that check's id is recorded and the other checks' results are in the profile

### Requirement: Settings
Every collection parameter SHALL be settable through `resolve_settings`, in this order of
precedence:
1. a CLI option;
2. the environment variable `RDF_FINGERPRINTER_<NAME>`;
3. its `selected_graphs` argument (graphs only);
4. configuration (`--config FILE` for the CLI, the `config` mapping for library callers);
5. the defaults of DEC-12.

The settings used SHALL be recorded in the profile. An unknown configuration key, an unreadable
configuration file or an invalid value SHALL be a usage error raised before any query. The
completeness check SHALL be switchable by configuration property or environment variable. The 1.x
`additional_config["collection"]` route is removed (readable-representations DEC-9).

#### Scenario: Environment variable overrides default
- **WHEN** `RDF_FINGERPRINTER_TIMEOUT_SECONDS=10` is set and no CLI option is given
- **THEN** the recorded settings have `timeout_seconds` 10

#### Scenario: CLI overrides environment
- **WHEN** the environment sets concurrency 2 and the CLI passes `--concurrency 8`
- **THEN** the recorded settings have `concurrency` 8

#### Scenario: Environment overrides the library configuration
- **WHEN** a library caller passes `config` with `top_k` 5 to `resolve_settings` while `RDF_FINGERPRINTER_TOP_K=7` is set
- **THEN** the recorded settings have `top_k` 7

#### Scenario: Unknown configuration key
- **WHEN** the configuration holds the key `colour`
- **THEN** a usage error names `colour` and no query is sent

#### Scenario: A configuration file sets collection options
- **WHEN** the configuration file sets `concurrency` to 2 and no CLI option or environment variable sets it
- **THEN** the recorded settings have `concurrency` 2

### Requirement: Completeness check for first-N classes
When the completeness check is on and a class was read in `first_n` mode, the collector SHALL ask,
for every predicate of the graph not seen in the class's sample, whether any instance uses it, and
record each one found as a property with `presence_only` true.

#### Scenario: Rare property found
- **WHEN** a class is read in first_n mode, the completeness check is on, and only instance 20 000 uses `ex:rare`
- **THEN** the class profile lists `ex:rare` with `presence_only` true and no histogram

### Requirement: Error classes and retries
The SPARQL client SHALL classify every error into one class with one response: transient (HTTP 429,
502, 503, connection failures) retried after 1 s and then 4 s and, if it persists, treated as a
timeout; timeout (the per-query timeout, HTTP 504, or a 500 whose message mentions a time limit);
permanent (other 4xx and 500s, responses that are not SPARQL results), never retried; unreachable
(HTTP 401, 403, 407), which SHALL stop the run only on the first query — on any later query it
SHALL count as permanent.

#### Scenario: Transient error retried
- **WHEN** a query fails once with HTTP 503 and then succeeds
- **THEN** its result is used and no failure is recorded

#### Scenario: Refusal after the start concerns one query
- **WHEN** a per-class query is refused with HTTP 403 after the graphs were listed
- **THEN** that measurement is recorded as a failure with one attempt and the run goes on

### Requirement: Response per collection stage
A failed query SHALL cost only its stage: the graph listing — unreachable or persistently transient
stops the run, a timeout or rejection profiles the default graph only and records a failure (with
graphs chosen, those are profiled and a WARNING is logged); other discovery queries fall back
(classes counted one by one, predicates listed without counts) or are recorded and skipped; a
failure in a class's first wave (instance listing, histograms, value partitions, co-types) escalates
under `auto` on a timeout and otherwise leaves the class out with a recorded failure; a failure in its
second wave (top values, completeness check, incoming links) is recorded and the class is kept. A
class whose IRI cannot be put in a query SHALL be skipped and recorded. A well-formed response
holding a value the collector cannot interpret SHALL end the run as an unexpected error. A first-N instance query that the endpoint rejects as too large SHALL be recorded as a failure whose message suggests lowering first N.

#### Scenario: Second-wave failure keeps the class
- **WHEN** the top-values query of a class times out
- **THEN** the class is in the profile without top values, and the only failures recorded are top-values failures (one per property queried)

#### Scenario: Permanent first-wave failure does not escalate
- **WHEN** the histogram query of a class is rejected with HTTP 400
- **THEN** the class is left out, one failure is recorded and no first-N attempt is made

#### Scenario: An IRI unusable in a query is skipped
- **WHEN** a class IRI contains a character that cannot be written in a query, such as a space
- **THEN** that class is skipped with a failure naming the IRI and the other classes are still profiled

#### Scenario: A first-N query too large for the endpoint
- **WHEN** the endpoint rejects the first-N instance query of a class as too large
- **THEN** a failure for that class suggests lowering the first N setting

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

### Requirement: Term labels and descriptions are collected
At every depth from `classes` on, the collector SHALL send one term-annotation query per profiled
graph, after the graph's classes are profiled (EPIC DEC-21). The query SHALL ask for the labels
and descriptions of the graph's class IRIs, and, from depth `properties` on, of its property
IRIs. It SHALL match them in the default graph and in every named graph, as the declared-hierarchy
query does. IRIs that cannot be put in a query SHALL be left out of it.

The predicates SHALL be those of llm-schema-split DEC-5. They count whether or not they are
declared `owl:AnnotationProperty`; no other annotation property is followed.
- **Label**, in priority order: `skos:prefLabel`, `skosxl:prefLabel`/`skosxl:literalForm`,
  `rdfs:label`, `dcterms:title`.
- **Alt label**: `skos:altLabel`, `skosxl:altLabel`/`skosxl:literalForm`.
- **Description** (the definition), in priority order: `skos:definition`, `rdfs:comment`,
  `dcterms:description`.
- **Note**: `skos:scopeNote`, `skos:note`, `skos:example`, `skos:editorialNote`,
  `skos:historyNote`, `skos:changeNote`.

Only literal values count. Per term, for labels and for descriptions, and per language tag
(untagged counts as one language), the value SHALL come from the highest-priority predicate that
has a value in that language. Among several such values, the smallest lexical form wins. Alt labels
SHALL be every alt-label value. Notes SHALL be every note value and every description value that
was not selected. Alt labels and notes SHALL be distinct and sorted by language (untagged first),
then by text. An alt label SHALL never be stored as a label. The values SHALL be stored in the
graph profile's `term_annotations`: one entry per term with at least one value, holding its
labels, alt labels, descriptions and notes, each with its language. A graph whose terms have no
annotation SHALL store an empty list. A profile saved before 3.4 SHALL load, with no alt labels
and no notes. When the query fails, a failure of kind `term_annotations` SHALL be recorded, and
the graph SHALL be kept, without annotations.

#### Scenario: Labels and descriptions of a class are stored
- **WHEN** `ex:Person` is profiled and the store holds `ex:Person rdfs:label "Person"@en`, `ex:Person skos:prefLabel "Personne"@fr` and `ex:Person rdfs:comment "A human being"@en`
- **THEN** the graph's term annotations give `ex:Person` the labels `"Person"@en` and `"Personne"@fr` and the description `"A human being"@en`

#### Scenario Outline: Label predicate priority
- **WHEN** the store holds, for the class `ex:Person`, only <values>
- **THEN** its stored labels are <labels> and its stored alt labels are <alt labels>

  Examples:
    | values                                                                          | labels        | alt labels    |
    | `skos:prefLabel "Human"@en`, `rdfs:label "Person"@en`                           | `"Human"@en`  | none          |
    | `skosxl:prefLabel [ skosxl:literalForm "Human"@en ]`, `rdfs:label "Person"@en`  | `"Human"@en`  | none          |
    | `skos:altLabel "Body"@en`                                                       | none          | `"Body"@en`   |
    | `skosxl:altLabel [ skosxl:literalForm "Body"@en ]`, `dcterms:title "Person"@de` | `"Person"@de` | `"Body"@en`   |
    | `rdfs:label "B"`, `rdfs:label "A"`                                              | `"A"`         | none          |

#### Scenario: Alt labels and notes are stored
- **WHEN** the store holds, for the class `ex:Person`, `skos:prefLabel "Person"@en`, `skos:altLabel "Human"@en`, `skos:altLabel "Body"@en`, `skos:altLabel "Mensch"@de`, `rdfs:comment "A human being"@en`, `rdfs:comment "Also a legal person"@en` and `skos:scopeNote "Use for people"@en`
- **THEN** its stored labels are `"Person"@en`, its alt labels `"Mensch"@de`, `"Body"@en`, `"Human"@en`, its descriptions `"A human being"@en`, and its notes `"Also a legal person"@en`, `"Use for people"@en`

#### Scenario: Annotations from another graph
- **WHEN** `ex:Person` is profiled in graph `http://ex.org/data` and its `rdfs:label` is asserted only in graph `http://ex.org/ontology`
- **THEN** the term annotations of `http://ex.org/data` hold that label

#### Scenario: Property annotations need depth properties
- **WHEN** the store labels the class `ex:Person` and the property `ex:name`, and the collector runs once at depth `classes` and once at depth `properties`
- **THEN** at `classes` only `ex:Person` has annotations, and at `properties` both have

#### Scenario: A failed annotation query keeps the graph
- **WHEN** the endpoint rejects the term-annotation query of a graph with HTTP 400
- **THEN** the graph's classes are in the profile, it has no term annotations, and one failure of kind `term_annotations` is recorded

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

