## ADDED Requirements

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

### Requirement: Depth and switches select the queries
The collector SHALL run only the queries that the configured depth and switches require, as tabled
in `design.md`; graph totals, predicate partitions and untyped subjects (full scans) SHALL run only
when `graph_statistics` is on.

#### Scenario: Default depth
- **WHEN** the collector runs with default settings
- **THEN** it issues the graph list, class counts, hierarchy, co-type, vote, value and object-class queries and no graph-total, top-value or incoming-link query

#### Scenario: Graph statistics on
- **WHEN** `graph_statistics` is on
- **THEN** each graph profile records triples, distinct subjects, distinct objects, predicate partitions and untyped subjects

### Requirement: rdf:type is not a property row
Per-class property statistics SHALL exclude `rdf:type`; type information SHALL be recorded as
co-types.

#### Scenario: Type triples excluded
- **WHEN** instances of `ex:Student` are also typed `ex:Person`
- **THEN** no property profile of `ex:Student` has property `rdf:type`, and its co-types list `ex:Person`

### Requirement: Per-class queries are scoped to the class
Every per-class query SHALL select its subjects through the class's own subject source (all
instances, a VALUES batch, or the first N); no query SHALL aggregate over the whole graph and filter
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
times out, retry the class in `batched` mode, then in `first_n` mode, then record a failure.
Partial results of a failed attempt MUST be discarded. The mode used SHALL be stored per class.
A forced policy (`exact`, `batched`, `first_n`) SHALL use only that mode.

#### Scenario: Exact succeeds
- **WHEN** every query for a class answers within the timeout
- **THEN** the class's `precision_mode` is `exact` and `observed_instances` equals `instances`

#### Scenario: First N uses one sample
- **WHEN** a class is read in first_n mode
- **THEN** the vote, value, object-class and co-type queries all use the same instance IRIs from a single listing query

#### Scenario: Escalation to first N
- **WHEN** the exact and batched attempts for a class with 50 000 instances time out and first N = 10 000 succeeds
- **THEN** `precision_mode` is `first_n`, `observed_instances` is 10 000 and `instances` is 50 000

#### Scenario: Batched equals exact
- **WHEN** the same class on the e2e store is collected once with policy `exact` and once with policy `batched` and batch size 1
- **THEN** the histograms, value partitions and distinct counts are equal

#### Scenario: Truncated instance listing
- **WHEN** the instance listing for batched mode returns fewer rows than the class's instance count
- **THEN** batched mode is skipped for that class and the next mode is tried

### Requirement: Failures are recorded and fail the run
A query that still fails after retries and fallbacks SHALL be recorded as a `Failure` (query kind,
graph, class, property, message, attempts); the other classes SHALL still be collected.

#### Scenario: Named graphs cannot be listed
- **WHEN** the endpoint rejects the named-graph listing query with HTTP 400
- **THEN** only the default graph is profiled and a failure of kind `graphs` is recorded

#### Scenario: One class fails
- **WHEN** every attempt for one class fails and all other classes succeed
- **THEN** the profile contains the other classes and one failure naming that class

### Requirement: Settings
Every collection parameter SHALL be settable by CLI option, environment variable
`RDF_FINGERPRINTER_<NAME>` or the library's `additional_config["collection"]`, in that precedence,
with the defaults of DEC-12, and SHALL be recorded in the profile. The completeness check SHALL be
switchable by configuration property or environment variable.

#### Scenario: Environment variable overrides default
- **WHEN** `RDF_FINGERPRINTER_TIMEOUT_SECONDS=10` is set and no CLI option is given
- **THEN** the recorded settings have `timeout_seconds` 10

#### Scenario: CLI overrides environment
- **WHEN** the environment sets concurrency 2 and the CLI passes `--concurrency 8`
- **THEN** the recorded settings have `concurrency` 8

### Requirement: Completeness check for first-N classes
When the completeness check is on and a class was read in `first_n` mode, the collector SHALL ask,
for every predicate of the graph not seen in the class's sample, whether any instance uses it, and
record each one found as a property with `presence_only` true.

#### Scenario: Rare property found
- **WHEN** a class is read in first_n mode, the completeness check is on, and only instance 20 000 uses `ex:rare`
- **THEN** the class profile lists `ex:rare` with `presence_only` true and no histogram
