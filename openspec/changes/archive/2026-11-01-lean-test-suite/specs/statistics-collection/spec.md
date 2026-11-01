## MODIFIED Requirements

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
in `design.md`; graph totals, predicate partitions and untyped subjects (full scans) SHALL run only
when `graph_statistics` is on.

#### Scenario: Default depth
- **WHEN** the collector runs with default settings
- **THEN** it issues the graph list, class counts, hierarchy, co-type, vote, value and object-class queries and no graph-total, top-value or incoming-link query

#### Scenario: Graph statistics on
- **WHEN** `graph_statistics` is on
- **THEN** each graph profile records triples, distinct subjects, distinct objects, predicate partitions and untyped subjects

#### Scenario: Measurements per depth
- **WHEN** the depth is `classes`, `properties`, `values`, `rich_values` or `links`
- **THEN** each depth adds its measurements to those of the shallower ones (instance counts, hierarchy and co-types; property histograms; value partitions and object classes; top values; incoming links) and the profile holds nothing of the deeper ones

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
