# Exploration notes — 2026-10-31 (seed input, not groomed)

Recon of the 1.0.0 code, templates and queries, done before shaping the hardening EPIC.

## What the library does

`fingerprint -e <endpoint>` renders one HTML page: per graph, per class, a table of the
properties its instances use, with subject count, min/max/avg cardinality, property kind
(object/datatype) and value types. The "application profile" is guessed from the data.
All logic lives in Jinja macros (`fingerprint_report_templates/.../macros/selectors.html`)
that run SPARQL through eds4jinja2 and render pandas DataFrames. Python is a ~60-line wrapper.

## Performance findings (selectors.html `fingerprint_pattern`)

1. **N+1 queries, each a full scan.** One `SELECT DISTINCT ?cls` per graph, then one
   fingerprint query per class. Queries run one after another.
2. **`VALUES` sits outside the subqueries.** SPARQL evaluates subqueries bottom-up, so the four
   subqueries aggregate over *every* class and property in the graph and are joined to the
   `VALUES` row afterwards. Unless the engine pushes the binding down (most don't through
   `GROUP BY`), each per-class query costs a full-graph aggregation: total ≈ N_classes × full scan.
3. **Three scans of the same pattern.** Subqueries 1, 2 and 4 each scan `?s a ?c ; ?p ?o`.
   Subqueries 1 and 2 merge into one: group by (c, s, p) → count; then group by (c, p) →
   `COUNT(*)` = subjects using p, `MIN/MAX/SUM` of the per-subject count.
4. **`OPTIONAL { ?object a ?object_class }`** over every object multiplies rows for
   multi-typed objects and is the most expensive join; it feeds only `object_types`.
5. Graph listing `GRAPH ?g { ?s ?p [] }` scans all triples; `GRAPH ?g {}` or a `LIMIT`-free
   `SELECT DISTINCT ?g WHERE { GRAPH ?g { ?s a [] } }` is lighter on most stores.
6. No timeout, no paging, no retry: big public endpoints (Cellar) time out or hit result caps.
7. `render_pandas_table` uses `iterrows()` — fine at report sizes, not a hotspot.

Likely shape of the fix: one or two aggregate queries per graph (all classes at once, grouped
by class and property), split into pieces only when the endpoint times out; optional
concurrency across graphs.

## Correctness findings

- `SELECT DISTINCT` together with `GROUP BY` in subquery 1 is redundant.
- Avg is `avg(per-subject count) × subjects_using / class_instances`, i.e. the mean over all
  instances (zeros included) — correct, but undocumented; min is forced to 0 when some
  instances lack the property — good, keep.
- IRIs (graph, class) are concatenated into query strings unescaped; an IRI with `>` breaks the
  query. Low risk (values come from the endpoint), but trivial to guard.
- "Default graph": on Fuseki/Virtuoso with union default graph, the default-graph fingerprint
  repeats every named graph's content. Behaviour depends on the store and is undocumented.
- `rdf:type` itself appears as a row of every class shape.
- Query errors render inline as an "Error" box; the CLI still exits 0.

## Dead code / unused things

- Macros never called: `select_distinct_property`, `select_distinct_subject_property`,
  `fetch_pattern_stats` (the last hardcodes `skos:Concept skosxl:altLabel` — a debug leftover).
- `render_class_fingerprint` computes `substituted_content` and never uses it (the eds4jinja2
  helper mutates in place, so the prefix substitution still happens — the variable is noise).
- `config.json` ships a dead `srv.meaningfy.ws` endpoint and graph as defaults (always
  overwritten by the handler); `config-cellar.json` is never read.
- `layout.html` has a commented-out duplicate stylesheet link and loads 4+ CDNs (report is not
  viewable offline).

## Repo cleanup candidates (nothing referenced by code, tests, Makefile, CI or docs)

| Path | Size | Why it can go |
|---|---|---|
| `resources/` (whole tree) | 15 MB | Pre-1.0 examples, old `.rq` queries, CSV dumps, generated HTML output, CSS copies; not used by code, tests or docs |
| `docs/rdf-fingerprinter-model.eapx` | 2.9 MB | Enterprise Architect binary model, unreferenced |
| `docs/stats-shape-test.ods` | 36 KB | Spreadsheet scratch, unreferenced |
| `fingerprint_report_templates/fingerprint_report/config-cellar.json` | small | Never loaded |
| 3 unused macros in `selectors.html` | — | Dead |
| empty `""" """` module docstrings + `#!/usr/bin/python3` shebangs on library modules | — | Noise |

Keep: `tests/test_data/*` (used by the Makefile), `package.json` (docs CI), `.coveragerc`,
`mypy.ini` (referenced from `pyproject.toml`).

## Similar tools (prior art)

- **VoID class/property partitions** (`void:classPartition`, `void:propertyPartition`) — the
  W3C vocabulary for exactly these statistics. `sib-swiss/void-generator` computes them over
  SPARQL at UniProt scale.
- **sheXer** (Python) — infers ShEx and SHACL shapes from instance data, with cardinality and
  support thresholds; closest in intent.
- **QSE — Quality Shapes Extraction** (Rabbani et al.) — SHACL extraction with support/confidence
  pruning; runs over files or a SPARQL endpoint, scales to Wikidata.
- **SHACL Play `generate`** (Sparna) — generates SHACL from data via SPARQL plus HTML
  documentation of the shapes; nearest to this report.
- **Loupe**, **ABSTAT**, **LODStats**, **RDF2Graph** — dataset profiling / summarisation.

Gap this library can own: a lightweight `pip install` CLI that profiles any SPARQL endpoint and
emits both a human report and a machine-readable profile (VoID partitions and/or SHACL shapes).

## eds4jinja2 parallelism does not reach the per-class queries (checked 2026-10-31)

`parallelism > 1` makes eds4jinja2 2.x render once in a *record* pass where every fetch returns an
empty DataFrame (`parallel_executor._placeholder`), pre-warm the recorded queries on a thread pool,
then render for real. Our template is data-dependent: classes come from a query, the fingerprint
queries are generated per class. In the record pass the class list is empty, so only the
graph/class listing queries are pre-warmed; every per-class fingerprint query runs live,
sequentially, in the render pass. Net gain for this report: ~nil. A multi-round record (re-record
with the results cached so far until no new queries appear) would fix it generically, upstream.
Also: pre-warm is all-or-nothing (one failed query aborts the report); no timeout in the adapter.
