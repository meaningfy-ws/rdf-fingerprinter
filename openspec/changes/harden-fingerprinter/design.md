> Derives from: EPIC harden-fingerprinter (proposal.md)

## Context

1.0.0 computes every statistic inside Jinja macros (`fingerprint_report_templates/.../macros/
selectors.html`) through eds4jinja2 fetchers: one whole-graph aggregate per class, sequential, no
timeout, errors rendered inline, exit 0. `fingerprint/` has only `service_layer` (60 lines) and
`entrypoints/cli`; `.importlinter` checks those two layers. Runtime dependencies are eds4jinja2 2.x
and click; SPARQLWrapper 2.0 and Pydantic 2.x are installed transitively. eds4jinja2's
`ReportBuilder` merges `additional_config` with `deep_update`, which recurses only into `Mapping`s,
so a Pydantic object placed in `conf` reaches the template as the same object (checked in
`eds4jinja2/models/collections.py`). Unit tests need no store; e2e tests run against Oxigraph
loaded with `tests/test_data/*.rdf` (default graph + two named graphs).

This file is the **single source** for queries, settings and rules. `inputs/stats-design.md` is a
superseded seed (kept, not groomed). Model drafts: `model/fingerprint_stats.yaml`,
`model/fingerprint_analytics.yaml`. Architecture: `docs/modules/ROOT/pages/architecture.adoc`.

## Goals / Non-Goals

**Goals:**
- Collect the raw statistics of `fingerprint_stats` with work bounded per query (DEC-2, DEC-3).
- Compute `fingerprint_analytics` with pure, unit-tested domain functions (DEC-4, DEC-8).
- Render today's report from the analytics through eds4jinja2, with the new columns (DEC-6).
- Make failure visible: recorded in the profile, logged, non-zero exit (DEC-1).
- Onion layers and generated-code rules enforced by tooling; TDD; BDD features (DEC-7).

**Non-Goals:** representations other than the HTML report; benchmarking; store-specific SPARQL;
random sampling; deleting repo files (the EPIC's no-gos).

## Decisions

New choices made while planning (EPIC decisions are cited, not repeated):

- **P-1 Layout.**
  - `model/fingerprint_stats.yaml`, `model/fingerprint_analytics.yaml` — the LinkML sources.
  - `fingerprint/domain/generated/profile.py` — generated from `fingerprint_analytics.yaml` (which
    imports `fingerprint_stats`, so one module holds every class). See P-10.
  - `fingerprint/domain/iri.py` (IRIREF guard), `analytics.py` (raw → analytics).
  - `fingerprint/adapters/sparql.py` — `SparqlPort` protocol, `SparqlWrapperClient`, the error
    classes `QueryTimeout`, `TransientError`, `PermanentError`, `EndpointUnreachable`.
  - `fingerprint/adapters/queries/*.rq` — the query templates below (package data).
  - `fingerprint/service_layer/settings.py` (precedence, P-6), `collection.py` (algorithm),
    `report.py` (`render_report`), `handlers.py` (public function, signature kept).
  - `fingerprint/entrypoints/cli/main.py`.
- **P-2 SPARQL access.** `SparqlWrapperClient` wraps SPARQLWrapper (declared as a direct
  dependency because we import it), JSON results over HTTP POST (first_n queries carry up to `first_n` IRIs in one `VALUES` block), a new wrapper per call (thread-safe), timeout
  from settings. The port is `select(query) -> list[dict[str, str | None]]` and
  `ask(query) -> bool`; unit tests pass a `FakeSparql` answering canned rows per query file name.
- **P-3 Query templates.** `.rq` files filled with `string.Template`. Placeholders: `$graph_open`
  / `$graph_close` (`GRAPH <g> {` / `}`, empty for the default graph, DEC-11), `$cls`, `$prop`
  (IRIREFs), `$subjects` (subject source, below), `$type_lookup` (Q7 scope), `$limit`, `$k`.
  Every IRI goes through `domain.iri.to_iriref()`, which returns `<iri>` or raises `ValueError` when
  the IRI contains a character outside IRIREF (space, `<>"{}|^\``, backslash, U+0000–U+0020).
- **P-4 Concurrency.** `ThreadPoolExecutor(max_workers=concurrency)`; one task per class, submitted
  in descending `instances`; inside a task its queries run sequentially, so at most `concurrency`
  queries are in flight. Graphs are processed one after another.
- **P-5 Failure classification** (by `SparqlWrapperClient`):
  - `QueryTimeout`: socket/client timeout; HTTP 504; HTTP 500 whose body contains, case-
    insensitively, `timeout`, `time limit`, `timed out` or `estimated execution time`. Not retried
    in the same mode — the caller escalates (per class) or falls back (discovery).
  - `TransientError`: connection reset/refused mid-run, HTTP 502, 503, 429. Retried twice, after
    1 s and 4 s; a third failure is raised as `QueryTimeout`.
  - `PermanentError`: HTTP 400, any other 4xx, unparsable response. Never retried.
  - `EndpointUnreachable`: Q0 fails with a connection error (refused, DNS, TLS) or a
    `TransientError` after its two retries, or with HTTP 401, 403 or 407. For Q0 only, an
    exhausted transient error is raised as `EndpointUnreachable`, not `QueryTimeout`.
- **P-6 Settings.** Precedence per setting: CLI option > environment variable > the
  `selected_graphs` function parameter (graphs only) > config file > default. The config file is
  `additional_config["collection"]` for library callers and `--config FILE` (a JSON object with the
  same keys) for the CLI — together they fulfil DEC-12's "config file"; unknown keys are a usage
  error. Values are parsed into the generated `Settings` class (validation from the model).

  | Setting (model slot) | CLI option | Env var `RDF_FINGERPRINTER_…` | Type | Default |
  |---|---|---|---|---|
  | `depth` | `--depth` | `DEPTH` | `Depth` | `values` |
  | `precision_policy` | `--precision` | `PRECISION_POLICY` | `PrecisionPolicy` | `auto` |
  | `first_n` | `--first-n` | `FIRST_N` | int ≥ 1 | 10 000 |
  | `top_k` | `--top-k` | `TOP_K` | int ≥ 1 | 20 |
  | `acceptance_threshold` | `--threshold` | `ACCEPTANCE_THRESHOLD` | float in (0, 1] | 0.95 |
  | `object_type_scope` | `--object-types` | `OBJECT_TYPE_SCOPE` | `ObjectTypeScope` | `same_graph` |
  | `completeness_check` | `--completeness/--no-completeness` | `COMPLETENESS_CHECK` | bool | false |
  | `graph_statistics` | `--graph-stats/--no-graph-stats` | `GRAPH_STATISTICS` | bool | false |
  | `timeout_seconds` | `--timeout` | `TIMEOUT_SECONDS` | int ≥ 1 | 60 |
  | `concurrency` | `--concurrency` | `CONCURRENCY` | int ≥ 1 | 4 |
  | `selected_graphs` | `--graph` (repeatable) | `SELECTED_GRAPHS` (comma-separated) | IRIs | empty |

  Booleans in env vars: `1/true/yes/on` and `0/false/no/off`, case-insensitive; anything else is a
  usage error. `selected_graphs` empty → default graph + every named graph (DEC-11; **changed**
  from 1.x, which profiled only the default graph); non-empty → only those, where `""` means the
  default graph (as in 1.x). `acceptance_threshold` must be in (0, 1]; 0 is rejected by
  `settings.py` as a usage error (the model allows [0, 1]).
- **P-7 Service-layer API and exit codes.** `collect(endpoint, settings, sparql) -> ProfileRun`
  raises `EndpointUnreachable`; `analyse(run) -> ProfileAnalytics` (domain);
  `render_report(analytics, output, template) -> Path`. The public
  `generate_endpoint_fingerprint_report` composes the three and returns the `Path` (1.x signature);
  recorded failures are in the report and logged at WARNING. It checks the output folder
  **before** `collect`, so a bad path fails fast. `conf.default_endpoint` and
  `conf.selected_graphs` are still set (the 1.x keys custom templates read), next to `conf.profile`. The CLI calls the three functions
  itself so it can read `failures`: exit **0** no failures, **1** report written with failures,
  **3** `EndpointUnreachable` (2 stays click's usage error; a missing output folder is reported as
a click usage error, exit 2); any other unexpected exception is logged with its traceback and
exits **4**. The analytics object is passed as
  `conf["profile"]`; eds4jinja2 fetchers stay available to custom templates (DEC-6).
- **P-8 BDD.** `pytest-bdd` (test group). Features in `tests/features/`, step definitions in
  `tests/unit/steps/`, driving domain functions and `collect` with `FakeSparql`.
- **P-9 Versioning.** → **2.0.0**; CHANGELOG lists the BREAKING changes: exit codes; `rdf:type`
  no longer a property row (see Rules); with no graph selected, 1.x profiled the default graph
  only (`selected_graphs=None` → `[""]` in `handlers.py`), 2.0 profiles the default graph and
  every named graph (DEC-11).
- **P-10 Generated code rules** (DEC-8):
  - **Generated, never edited.** `make generate-models` runs `gen-pydantic` (LinkML pinned in a new
    `model` dependency group) and writes `fingerprint/domain/generated/profile.py`. The file starts
    with a banner `# GENERATED by make generate-models from model/*.yaml — DO NOT EDIT`.
    `make check-models` regenerates into a temp file and diffs; it is part of `check-all`.
  - **Read-only objects.** A project template for gen-pydantic sets
    `ConfiguredBaseModel.model_config = ConfigDict(frozen=True, extra="forbid",
    validate_assignment=True)`. The collector builds plain dicts and constructs each model once;
    analytics construct new objects, never mutate raw ones.
  - **Tooling.** Ruff excludes `fingerprint/domain/generated/` (generated style); mypy checks it.
  - **Import contracts** (`.importlinter`):
    1. layers `fingerprint.entrypoints` > `fingerprint.service_layer` > `fingerprint.adapters` >
       `fingerprint.domain` (a layer may import only layers below it);
    2. forbidden: `fingerprint.domain.generated` imports no other `fingerprint` module;
    3. forbidden: `fingerprint.domain` imports none of `SPARQLWrapper`, `eds4jinja2`, `click`
       (external I/O stays outside the domain).

## Algorithm / approach

### Which queries run (depth and switches)

Depth order: `graphs` < `classes` < `properties` < `values` < `rich_values` < `links`; each level
adds to the previous one.

| Level / switch | Queries |
|---|---|
| always | Q0 |
| `graph_statistics` on (any depth) | Q1, Q2, QU |
| `classes` | Q3 (fallback Q3a + Q3b), Q4, Q8 |
| `properties` | + Q5 |
| `values` (default) | + Q6, Q7 |
| `rich_values` | + Q9 |
| `links` | + Q11 |
| `completeness_check` on, depth ≥ `properties`, class read in `first_n` | Q10 per missing predicate (Rules); Q2 runs at discovery when the check is on, recorded in `predicate_partitions` |

### Query → `QueryKind` (for `Failure.query_kind`)

| Query | Kind | Query | Kind |
|---|---|---|---|
| Q0 | `graphs` | Q7 | `object_classes` |
| Q1 | `triples` | Q8 | `co_types` |
| Q2, Q2a | `predicate_partitions` | Q9 | `top_values` |
| Q3, Q3a, Q3b | `class_partitions` | Q10 | `property_presence` |
| Q4 | `declared_hierarchy` | Q11 | `incoming_links` |
| Q5 | `cardinality_votes` | QS | `subject_stream` |
| Q6 | `value_partitions` | QU | `untyped_subjects` |

"All modes failed" records the kind of the last query that failed and `attempts` = number of
modes actually tried. An IRIREF failure records the kind
of the query being built.

### Subject sources (DEC-10)

| Mode | `$subjects` |
|---|---|
| exact | `$graph_open ?s a $cls . $graph_close` |
| first_n | `VALUES ?s { … }` — all IRIs from **one** QS run, in one block |

QS: `SELECT ?s { $graph_open ?s a $cls . $graph_close } LIMIT $limit` (`SELECT DISTINCT ?s` for
the default graph). Running QS once and reusing its IRIs keeps every query of a class on the
**same** instances (a repeated `LIMIT` subquery without `ORDER BY` may return different rows each
time). `observed_instances` = number of QS rows (first_n) or `instances` (exact). Every query
reads its whole subject set in one request, so no partial results are ever merged.
- Blank-node instances cannot be put in `VALUES`. If QS returns any, first_n falls back to the subquery source `{ SELECT ?s { $graph_open ?s a $cls . $graph_close } LIMIT
  $limit }` in every query, and the profile notes that the sample may differ between queries.

### Query templates (final text; prefixes `rdf:`, `rdfs:` declared in every file)

```sparql
# Q0 named graphs
SELECT DISTINCT ?g { GRAPH ?g { } }

# Q1 graph totals                                        (graph_statistics)
SELECT (COUNT(*) AS ?triples) (COUNT(DISTINCT ?s) AS ?distinct_subjects)
       (COUNT(DISTINCT ?o) AS ?distinct_objects) { $graph_open ?s ?p ?o . $graph_close }

# Q2 predicate partitions; fallback Q2a = SELECT DISTINCT ?p {…} (triples left empty)
SELECT ?p (COUNT(*) AS ?triples) { $graph_open ?s ?p ?o . $graph_close } GROUP BY ?p

# QU untyped subjects                                    (graph_statistics)
SELECT (COUNT(DISTINCT ?s) AS ?untyped_subjects)
{ $graph_open ?s ?p ?o . FILTER NOT EXISTS { ?s a ?any } $graph_close }

# Q3 class partitions (named graph: COUNT(?s); default graph: COUNT(DISTINCT ?s), DEC-11)
SELECT ?c (COUNT(?s) AS ?instances) { $graph_open ?s a ?c . $graph_close } GROUP BY ?c
# Q3a fallback: SELECT DISTINCT ?c { $graph_open ?s a ?c . $graph_close }
# Q3b per class: SELECT (COUNT(DISTINCT ?s) AS ?instances) { $graph_open ?s a $cls . $graph_close }

# Q4 declared hierarchy (whole dataset, once per run)
SELECT DISTINCT ?sub ?sup {
  { ?sub rdfs:subClassOf ?sup } UNION { GRAPH ?g { ?sub rdfs:subClassOf ?sup } }
  FILTER(isIRI(?sub) && isIRI(?sup) && ?sub != ?sup) }

# Q5 cardinality votes
SELECT ?p ?n (COUNT(?s) AS ?subjects) {
  { SELECT ?s ?p (COUNT(*) AS ?n) {
      $subjects $graph_open ?s ?p ?o . $graph_close FILTER(?p != rdf:type)
    } GROUP BY ?s ?p }
} GROUP BY ?p ?n

# Q6 value partitions, literals and resources by kind
SELECT ?p ?kind ?dt ?lang (COUNT(*) AS ?triples) (COUNT(DISTINCT ?o) AS ?distinct)
       (MIN(?len) AS ?min_length) (MAX(?len) AS ?max_length) (SUM(?len) AS ?total_length)
       (MIN(?lit) AS ?min_value) (MAX(?lit) AS ?max_value) {
  $subjects $graph_open ?s ?p ?o . $graph_close FILTER(?p != rdf:type)
  BIND(IF(isLiteral(?o), "literal", IF(isBlank(?o), "blank_node", "iri")) AS ?kind)
  BIND(IF(isLiteral(?o), datatype(?o), ?unbound) AS ?dt)
  BIND(IF(isLiteral(?o), lang(?o), ?unbound) AS ?lang)
  BIND(IF(isLiteral(?o), STRLEN(STR(?o)), ?unbound) AS ?len)
  BIND(IF(isLiteral(?o), ?o, ?unbound) AS ?lit)
} GROUP BY ?p ?kind ?dt ?lang

# Q7 object classes; untyped objects have ?t unbound
SELECT ?p ?kind ?t ?tg (COUNT(*) AS ?triples) (COUNT(DISTINCT ?o) AS ?objects) {
  $subjects $graph_open ?s ?p ?o . $graph_close
  FILTER(?p != rdf:type && !isLiteral(?o))
  BIND(IF(isBlank(?o), "blank_node", "iri") AS ?kind)
  $type_lookup
} GROUP BY ?p ?kind ?t ?tg
#   same_graph: OPTIONAL { $graph_open ?o a ?t . $graph_close }
#   any_graph:  OPTIONAL { { ?o a ?t } UNION { GRAPH ?tg { ?o a ?t } } }

# Q8 co-types
SELECT ?d (COUNT(DISTINCT ?s) AS ?subjects)
{ $subjects $graph_open ?s a ?d . $graph_close FILTER(?d != $cls) } GROUP BY ?d

# Q9 top values (subject source of the class's mode)
SELECT ?o (COUNT(*) AS ?triples) { $subjects $graph_open ?s $prop ?o . $graph_close }
GROUP BY ?o ORDER BY DESC(?triples) LIMIT $k

# Q10 property presence (ASK)
ASK { $graph_open ?s a $cls ; $prop ?o . $graph_close }

# Q11 incoming links
SELECT ?sc ?p (COUNT(*) AS ?triples) {
  $subjects $graph_open ?x ?p ?s . ?x a ?sc . $graph_close FILTER(?p != rdf:type)
} GROUP BY ?sc ?p
```

The `OPTIONAL` in Q7 is bounded by `$subjects` (only this class's objects), unlike 1.x where it
ran over every object of the graph.

### Collection (service layer)

```
collect(endpoint, settings, sparql) -> ProfileRun
  named = Q0                      # PermanentError → default graph only + Failure; unreachable → raise
  graphs = selected_graphs or [default] + named
  edges = Q4 once (if depth ≥ classes); copied into every GraphProfile.declared_subclass_edges
  for graph in graphs:
    graph_stats (if switch): Q1, Q2 (→ Q2a), QU
    Q2 (→ Q2a) also here when completeness_check is on and not yet run
    instances = Q3 (timeout → Q3a + Q3b per class)
    pool.map(profile_class, classes sorted by instances desc)
  return ProfileRun(...)

profile_class(cls):
  for mode in allowed_modes(policy):        # auto: exact, first_n
    try:   partial = run_first_wave(cls, mode)   # first_n: QS once, then Q8 [+Q5] [+Q6, Q7]
           break
    except QueryTimeout: log WARNING, discard partial, continue
    except PermanentError: record Failure, return
  else: record Failure(attempts=len(modes)), return
  second wave: Q9 per property (rich_values), Q10 (completeness), Q11 (links)
               — a failure here records a Failure for that item, keeps the class
```

**Row → model mapping.**
- Q5 rows → `PropertyProfile.cardinality_histogram` (`values_per_subject` = `?n`, `subjects`).
- Q6 rows with `kind = literal` → `ValuePartition` (`node_kind literal`, `datatype`, `language`,
  `triples`, `distinct_objects`, lengths, values).
- Q6 rows of all kinds → `PropertyProfile.distinct_objects` = Σ `?distinct` (the groups hold
  disjoint values, so the sum is exact) — the report's "distinct values" column.
- Q7 rows → `ValuePartition` (`node_kind` iri/blank_node, `object_class` = `?t` or absent for
  untyped, `object_class_graph` = `?tg`, `triples`, `distinct_objects` = `?objects`).
- Q8 → `CoTypeCount`; Q9 → `top_values` with `top_values_exact` = (class mode is exact);
  Q10 true → `PropertyProfile(presence_only=true)`; Q11 → `IncomingLink`.

**Idempotency.** Collection only reads. A retried or escalated attempt discards its partial result
before the next attempt, so nothing is counted twice; the profile is built once per class from the
successful attempt. Re-running the CLI overwrites the output folder's report.

### Analytics (domain, pure)

For one property of one class with `O` = `observed_instances` and bins `{n: subjects}`:

- `with = Σ subjects`, `without = O − with`, `total = Σ n·subjects`
- `min = 0 if without > 0 else min(n)`; `max = max(n)`; `mean = total / O`;
  `mean_when_present = total / with`; median, mode and stddev over the bins with the n = 0 bin
  added — population stddev (`statistics.pstdev` semantics), a mode tie takes the smallest n
- `confidence = with / O`; `is_mandatory = confidence == 1`; `is_functional = max ≤ 1`
- **Cardinality label** at `t = acceptance_threshold`, share(x) = subjects satisfying x ÷ O:
  1. if share(n ≥ 1) ≥ t: `exactly_one` if share(n = 1) ≥ t; else `exactly_n` (with
     `exact_count = k`) if some k > 1 has share(n = k) ≥ t (if several qualify, which needs
     t ≤ 0.5, the smallest k); else `one_or_more`;
  2. else `zero_or_one` if share(n ≤ 1) ≥ t; else `zero_or_more`.
  `label_support` = share of the chosen label's condition (`zero_or_more`: 1.0).
  `alternative_labels` = the rejected labels one level stricter: `zero_or_more` → [`one_or_more`,
  `zero_or_one`]; `zero_or_one`, `one_or_more`, `exactly_n` → [`exactly_one`]; `exactly_one` → [].
- `property_kind`: all partitions literal → `datatype_property`; none literal →
  `object_property`; else `mixed`.
- `value_types` = datatypes and object classes ordered by `triples` desc; `dominant_value_type` =
  first; `type_purity` = its triples ÷ `total` (multi-typed objects count once per type, so purity
  can exceed what a single type explains — documented); `untyped_object_ratio` = triples of the untyped
  partitions ÷ resource triples, where resource triples = `total` − Σ literal-partition triples
  (Q7 counts a multi-typed object once per type, so Q7 triples are not summed); `languages` ordered by triples; `language_coverage` = tagged literal
  triples ÷ literal triples; `mean_length` = Σ total_length ÷ literal triples.
- Diversity: `distinct_ratio` = `distinct_objects` ÷ `total`; `is_identifier_like` = label
  `exactly_one` ∧ `distinct_objects == with`; `is_enumeration_candidate` = `distinct_objects ≤
  top_k`; `top_k_share` = Σ top-value triples ÷ `total`; `entropy_estimate` = −Σ pᵢ log₂ pᵢ over the
  top values plus one bucket for the remainder (`total − Σ top`), 0 when `total = 0`.
- `is_exact` = class mode ≠ `first_n` (and not `presence_only`).
- **`presence_only` properties**: only `inheritance` and `is_exact = false` are set; every
  statistic is absent. Inheritance: `inherited` if any compared parent has the property, else `own`.
- **Inputs not collected** (depth below `values`: no Q6/Q7; below `rich_values`: no Q9): every
  indicator derived from the missing query is absent — `property_kind`, `value_types`,
  `dominant_value_type`, `type_purity`, `untyped_object_ratio`, `languages`,
  `language_coverage`, `mean_length`, `distinct_ratio`, `is_identifier_like`,
  `is_enumeration_candidate` (no Q6/Q7); `top_k_share`, `entropy_estimate` (no Q9). Inheritance
  then compares labels only. The report shows "—" for absent values.
- **Class**: `parents` = declared edges ∪ implied (a co-type with `subjects == O` and `O > 0`,
  source `implied`; declared wins if both). Two classes implied by each other are recorded as each
  other's parent and treated as **equivalent**: excluded from inheritance comparison and depth.
  `hierarchy_depth` = longest path to a class without parents over the remaining edges, cycles cut
  by a visited set. `own_property_count`, `mandatory_property_count`; `mean_out_degree` = Σ property
  totals ÷ O; `label_coverage` = max confidence among
  `http://www.w3.org/2000/01/rdf-schema#label`, `http://www.w3.org/2004/02/skos/core#prefLabel`,
  `http://purl.org/dc/terms/title`, `http://schema.org/name`, `https://schema.org/name`,
  `http://xmlns.com/foaf/0.1/name` (0 if none); `sample_ratio` = O ÷ instances;
  `is_exact` = mode ≠ `first_n` ∧ all its properties exact.
- **Inheritance** of property p on class C: look at C's parents that have a profile in the same
  graph (parents without a profile are listed but not compared). `inherited` if any such parent has
  p with the same label and dominant type; `refined` if some parent has p but none matches; `own`
  otherwise (also when no parent has a profile).
- **Graph**: `class_count`, `property_count` (distinct properties over all classes);
  `typed_subject_ratio` = (distinct_subjects − untyped_subjects) ÷ distinct_subjects, only when
  `graph_statistics` ran; `vocabularies` = namespaces (IRI up to and including the last `#` or `/`)
  of classes and properties, ordered by triples; `cross_graph_object_types` = distinct
  `object_class_graph` values other than the graph itself.

**Rules.** `rdf:type` is never a property row (Q5–Q7, Q11 filter it); type information lives in
co-types and parents. Q10 checks only the missing predicates = Q2/Q2a predicates − properties
seen in Q5 − `rdf:type`, and runs only at depth ≥ `properties`.

**Worked example.** `ex:Person`, O = 4, `ex:name` bins `{1: 2, 2: 1}` → with 3, without 1, total 4;
min 0, max 2, mean 1.0, mean_when_present 1.33, confidence 0.75; share(n ≥ 1) = 0.75 < 0.95 →
step 2; share(n ≤ 1) = 0.75 < 0.95 → `zero_or_more`, support 1.0, alternatives [`one_or_more`,
`zero_or_one`]. 1.x shows min 0 / max 2 / avg 1.0 for the same data (DEC-4 holds).

### Report

`main.html` iterates `conf.profile.graphs → class_partitions → property_partitions` and renders, per
class: IRI (prefixed with the packaged `prefixes.json`), instances, mode (`exact` or
`first N of M`), parents; per property: property, subjects (`subjects_with_property`), min, max,
avg (`mean`), kind, distinct values, value types — today's columns — plus confidence, cardinality
label, inheritance. A closing "Collection" section lists settings and failures.

### Anti-patterns

| Don't | Do instead | Why |
|---|---|---|
| Bind the class with `VALUES` outside a whole-graph `GROUP BY` | put the class in `$subjects` | the 1.x cost problem |
| `OPTIONAL` over every object of the graph | only inside a class-scoped query (Q7) | row explosion |
| `UNION { FILTER NOT EXISTS {?o …} }` for untyped objects | `OPTIONAL` + unbound `?t` | `?o` is unbound in that branch; the filter never matches |
| Store derived numbers in the raw model | derive in `domain/analytics.py` | one truth; formats never disagree |
| Query from templates or renderers | pass the analytics into the context | DEC-1, DEC-6 |
| Edit `domain/generated/` or mutate a model object | edit YAML + regenerate; build new objects | P-10 |
| Re-run a `LIMIT` subquery in every first_n query | list the first N once (QS), reuse them via `VALUES` | each query could see different instances |
| Swallow a failed query | `Failure` + WARNING + exit 1 | the 1.x silent partial report |

## Error matrix

| Failure mode | How it is detected | Expected handling | Log | Message (log / report) |
|---|---|---|---|---|
| Endpoint unreachable | Q0 connection error, transient after retries, HTTP 401/403/407 | raise `EndpointUnreachable`; CLI exit 3; no report | ERROR | `cannot reach endpoint <url>: <reason>` |
| Q0 rejected (no `GRAPH ?g {}`) | `PermanentError` on Q0 | if `selected_graphs` is set: profile them, no Failure; else default graph only + `Failure(graphs)` | WARNING | `named graphs not listed (<reason>); profiling the default graph only` |
| Q1/Q2/QU timeout | `QueryTimeout` | Q2 → Q2a; Q1/QU → `Failure`, slots left empty | WARNING | `graph <g>: <query> timed out after <t> s` |
| Q3 timeout | `QueryTimeout` | Q3a + Q3b per class; a Q3b timeout → `Failure(class_partitions, class)` | WARNING | `graph <g>: class counts timed out; counting per class` |
| Q3a timeout / error | `QueryTimeout`, `PermanentError` | `Failure(class_partitions, graph)`; graph profiled without classes; next graph | WARNING | `graph <g>: classes not listed: <reason>` |
| Q0 timeout | `QueryTimeout` | if `selected_graphs` is set: profile them, no Failure; else default graph only + `Failure(graphs)` | WARNING | `named graphs not listed (timeout); profiling the default graph only` |
| Q4 timeout / error | `QueryTimeout`, `PermanentError` | `Failure(declared_hierarchy)`; no declared edges | WARNING | `declared hierarchy not read: <reason>` |
| First-wave timeout (Q5–Q8, QS) | `QueryTimeout` | discard partial; next mode | WARNING | `class <c>: <mode> timed out after <t> s; trying <next>` |
| Blank-node instances in first_n | bnode in QS | subquery source for that class; profile notes the sample may vary | INFO | `class <c>: blank-node instances; first-N sample may differ between queries` |
| first_n query too large | HTTP 400/413 on a `VALUES` query | `Failure(kind, class)`, message suggests lowering `first_n` | WARNING | `class <c>: endpoint rejected <n>-IRI query; lower --first-n` |
| All modes failed | loop exhausted | `Failure(query_kind, class, attempts)`; class omitted | WARNING | `class <c>: not profiled after <n> attempts` |
| Transient error | 502/503/429, reset | retry ×2 (1 s, 4 s), then `QueryTimeout` | INFO per retry | `retrying <query> (<n>/2): <reason>` |
| Malformed query / unsupported feature | `PermanentError` | `Failure`, no retry, no escalation | WARNING | `<query> rejected by endpoint: <status> <body excerpt>` |
| Second-wave failure (Q9, Q10, Q11) | any error after retries | `Failure` for that item; class kept | WARNING | `class <c>, property <p>: <query> failed` |
| IRI not an IRIREF | `to_iriref` raises | `Failure` for that class/graph | WARNING | `skipping <iri>: not usable in a SPARQL query` |
| Output folder missing | existing check | `NotADirectoryError` (unchanged) | — | unchanged |
| Run finished with failures | `failures` non-empty | report written with Failures section; CLI exit 1 | WARNING | `report written to <path> with <n> failures` |

Progress is logged at INFO: one line per graph and per class (`class <c>: <mode>, <O> of <N>
instances, <q> queries`).

## Risks / Trade-offs

- [Q3 `GROUP BY ?c` times out on the largest stores] → Q3a/Q3b fallback.
- [first_n bias toward store row order] → labelled per class; Q10 optional.
- [Union-default-graph stores double count; `any_graph` lookups can return the same type from the
  default and a named graph] → documented (DEC-11); distinct counts unaffected.
- [Large `VALUES` blocks rejected by some stores] → POST; clear failure message; `first_n` adjustable.
- [Classes too big for exact but readable in chunks get only a first-N sample] → batched mode is the follow-up EPIC `batched-collection`.
- [Generated Pydantic shape changes with LinkML versions] → LinkML pinned in the `model` group;
  `check-models` catches drift.
- [Report rows change for custom-template users] → eds4jinja2 fetchers kept; CHANGELOG notes.

## Open Questions

None blocking. Calls made while planning (developer may override): P-2 SPARQLWrapper; P-5 retry
counts, backoff and timeout markers; P-7 exit code 3; P-8 pytest-bdd; P-9 2.0.0; P-10 frozen
models; `rdf:type` excluded from property rows; label predicates for `label_coverage`.
