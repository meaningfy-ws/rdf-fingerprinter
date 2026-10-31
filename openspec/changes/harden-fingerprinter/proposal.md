# EPIC: Harden the fingerprinter

## Appetite

**LARGE** (developer, 2026-10-31). New `domain` and `adapters` layers, two LinkML models, a new
collection algorithm, hierarchy analytics, and the report migrated onto the profile. Follows
`adopt-meaningfy-tooling` (released 1.0.0), which named hardening as the next EPIC.
`profile-representations` builds on the profile introduced here.

Seeds (secondary, never groomed): `inputs/exploration.md` (code, query and repo review),
`inputs/prior-art.md` (seven comparable tools, read from source), `inputs/stats-design.md`
(statistics catalogue, query templates, trade-offs), `inputs/qa-record.md` (developer answers).

## Why

The fingerprinter must profile **large** knowledge graphs, and today it cannot:

- **Cost ≈ classes × full-graph scans.** One query per class binds the class with `VALUES`
  *outside* four `GROUP BY` subqueries, so every per-class query aggregates the whole graph; the
  same pattern is scanned three times; object types come from an `OPTIONAL` join over every object.
- **Sequential, unbounded, silent.** No timeout, no retry; a failed query renders as an inline
  error box and the CLI still exits 0. eds4jinja2's `parallelism` cannot help: its record pass
  returns empty tables, so the data-dependent per-class queries are never pre-warmed.
- **Flat and thin.** Every asserted type is profiled alone (a materialised superclass repeats its
  subclasses); no confidence, cardinality label, languages, lengths or diversity.
- **Statistics live in Jinja.** The logic cannot be unit-tested, cannot recover from failure and
  cannot feed another output without querying again.

A single global class × property aggregate is no answer: on a large graph that query times out.

## Solution outline

Statistics collection becomes a **Python algorithm** that fills a **raw statistics model**; pure
domain functions compute an **analytics model** from it; the HTML report renders the analytics
through eds4jinja2. Outcome: profiling cost grows with the number of instances read, not with
classes × graph size; every number states how precise it is; failures are visible and fail the run.

Collection, per graph (queries and trade-offs in `inputs/stats-design.md`):

1. **Discover cheaply** (void-generator): graphs; instance counts per class in one `GROUP BY ?c`
   (fallback: per-class counts); declared `rdfs:subClassOf` edges; optional predicate partitions
   and untyped subjects.
2. **Per class, four independent queries**, run concurrently, biggest classes first:
   cardinality **votes** (subjects with exactly *n* values per property — sheXer/QSE); value
   partitions (kind, datatype, language, distinct objects, lexical lengths, value ranges); object
   classes (inner join, untyped counted, same or any graph); co-types.
3. **Second wave, only where the first wave says so**: top-K values; property-presence `ASK`
   for classes read in `first_n` mode; incoming links.
4. **Precision escalates per class on timeout**: exact → batched → first N → recorded failure.
5. **Analytics**: min/max/mean/median, confidence, cardinality label with alternatives,
   property kind, type purity, language coverage, diversity, declared and implied parents,
   own/inherited properties, and more — an open catalogue.

## Key decisions

- **DEC-1**: Collection is a Python algorithm, not template logic — timeouts, retries, concurrency,
  fallbacks and store-free unit tests are control flow Jinja cannot express; rejected: a cleverer
  template (eds4jinja2 cannot parallelise data-dependent fetches).
- **DEC-2**: Staged discovery + per-class queries scoped to the class's instances; rejected: one
  global class × property aggregate (times out on large graphs, developer 2026-10-31).
- **DEC-3**: Precise by default; sampling only as a fallback. Per class: exact → batched (VALUES
  batches merged client-side) → first N (`LIMIT` without `ORDER BY`, labelled "first N of M",
  developer 2026-10-31) → recorded failure. The mode used is stored per class; rejected: random
  sampling (needs every instance IRI first).
- **DEC-4**: Property statistics derive from per-instance cardinality votes; min/max/avg keep
  today's meaning (min 0 when some instances lack the property; avg over all instances read).
- **DEC-5**: Portable SPARQL 1.1 only; rejected: store-specific query variants (Virtuoso, QLever).
- **DEC-6**: eds4jinja2 stays and renders the report; the analytics are passed into the
  `ReportBuilder` context, so custom templates keep working (developer 2026-10-31); rejected:
  dropping eds4jinja2 for plain Jinja2.
- **DEC-7**: Meaningfy standard in full: cosmic-python onion layers (`domain`, `adapters`,
  `service_layer`, `entrypoints`) enforced by `.importlinter`; TDD; unit tests with a fake SPARQL
  adapter; e2e on Oxigraph; BDD features for the collection rules (developer 2026-10-31).
- **DEC-8**: The profile model is **LinkML**, in two schemas under namespace
  `fp: https://data.meaningfy.ws/fingerprint/` (developer 2026-10-31): `fingerprint_stats` (raw
  observations, settings, precision mode used) and `fingerprint_analytics` (extends it with
  computed indicators). Generated into Pydantic in `fingerprint/domain`; LinkML is dev-time only.
  Drafts: `model/` in this change; rejected: hand-written dataclasses (no contract for
  `profile-representations`).
- **DEC-9**: Object types may be looked up across graphs (`object_type_scope`); the completeness
  check is a configuration property / environment variable (developer 2026-10-31).
- **DEC-10**: One collection algorithm: the precision mode only swaps the subject source; every
  statistic is a mergeable partial result; rejected: parallel implementations per mode.
- **DEC-11**: The default graph is always profiled, then every named graph (developer
  2026-10-31), documented for union-default-graph stores; rejected: skipping the default graph.
  Note (corrected 2026-10-31): 1.x, called with no graph selected, profiled the default graph
  only, so profiling the named graphs too is a BREAKING change listed in the CHANGELOG.
- **DEC-12**: Defaults (developer 2026-10-31): timeout 60 s, concurrency 4, batch 2 000,
  first_n 10 000, distinct_limit 1 000 000, top_k 20, acceptance threshold 0.95, depth `values`,
  policy `auto`, object types `same_graph`, completeness check off. Each is overridable by CLI
  option, config file or environment variable.

## Rabbit-holes

- Engine-specific tuning (Virtuoso JDBC, QLever variants) — void-generator shows the cost.
- Full supertype pruning with an `ASK` per class pair — quadratic in classes.
- Approximate-distinct sketches (HyperLogLog) — a dependency for a bound we can state instead.
- Report layout redesign — new columns only.

## No-gos

- No SHACL, PlantUML, ReSpec, VoID or other representations — `profile-representations`.
- No MCP server or LLM tooling — `llm-schema-tools`.
- No breaking change to `generate_endpoint_fingerprint_report`'s signature (new keyword arguments
  with defaults only).
- No deletion of repo files without explicit developer go-ahead (cleanup is recorded only).
- No random sampling; no store-specific SPARQL.
- No performance benchmark — the `benchmark-fingerprinter` EPIC (developer, 2026-10-31); this
  EPIC proves correctness and bounded per-query work, not speed-ups.

---

## What Changes

- New `fingerprint/domain` (generated profile models + pure analytics), `fingerprint/adapters`
  (SPARQL client with timeout/retry, query templates), collection service in
  `fingerprint/service_layer`; `.importlinter` enforces the four layers.
- New `model/` with the two LinkML schemas and `make generate-models` (+ a sync check in the gate).
- The packaged report template renders the analytics instead of running SPARQL; it shows
  confidence, cardinality label, value types, own/inherited, and the precision mode per class.
- CLI gains collection options (depth, policy, timeout, concurrency, …) and exits non-zero when a
  query fails after all fallbacks. **BREAKING** for scripts relying on exit 0 with error boxes.
- New dependency: Pydantic (runtime); LinkML (dev group).

## Capabilities

### New Capabilities
- `statistics-collection`: collecting raw statistics from a SPARQL endpoint — discovery, per-class
  queries, precision modes, settings, failures.
- `profile-analytics`: computing the analytical indicators (cardinality, confidence, value
  profile, diversity, hierarchy) from raw statistics.
- `fingerprint-report`: the HTML report rendered from the analytics.

### Modified Capabilities
- `developer-tooling`: generated models are kept in sync by the gate.

## Impact

`fingerprint/` gains two packages; `fingerprint_report_templates` macros no longer query; the
public function keeps its signature; CLI exit code changes on failure; Pydantic added at runtime.
