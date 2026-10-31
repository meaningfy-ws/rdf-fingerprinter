> Derives from: EPIC harden-fingerprinter (proposal.md)

## 1. Model and layers

- [x] 1.1 Move `model/*.yaml` from this change to the repo's `model/`; add LinkML (pinned) to a new `model` dependency group, Pydantic and SPARQLWrapper as direct runtime dependencies (DEC-8, P-2, P-10)
- [x] 1.2 gen-pydantic project template (banner, frozen, `extra="forbid"`); `make generate-models` → `fingerprint/domain/generated/profile.py`; `make check-models` in `check-all`; Ruff excludes `domain/generated/` (P-10; Requirements: Generated models stay in sync; Generated code is read-only)
- [x] 1.3 Create `fingerprint/domain` and `fingerprint/adapters`; `.importlinter`: four layers + the two forbidden contracts (DEC-7, P-10; Requirement: Onion layers are enforced)
- [x] 1.0 Gherkin features written from the spec scenarios and error matrix: `tests/features/statistics_collection.feature`, `profile_analytics.feature`, `fingerprint_report.feature` (P-8)
- [x] 1.4 Add `pytest-bdd` to the test group; `tests/unit/steps/` skeleton bound to `tests/features/` (P-8)

## 2. Domain (pure, TDD)

- [x] 2.1 `domain/iri.py` `to_iriref` with its rejection rules (P-3)
- [x] 2.3 `domain/analytics.py`: cardinality statistics and confidence (Requirement: Cardinality statistics keep today's meaning)
- [x] 2.4 Cardinality label, support, alternatives (Requirement: Cardinality label)
- [x] 2.5 Value profile indicators (Requirement: Value profile indicators)
- [x] 2.6 Hierarchy: declared + implied parents, own/inherited/refined, depth with cycles (Requirement: Hierarchy)
- [x] 2.7 Exactness flags; analytics from a JSON-loaded raw profile (Requirements: Exactness is visible; Analytics are derived, never collected)
- [x] 2.8 Remaining class and graph indicators, median/mode/stddev, top-K share, entropy (Requirement: Further indicators)
- [x] 2.9 Step definitions for `profile_analytics.feature`, green

## 3. Adapters

- [x] 3.1 `adapters/sparql.py`: `SparqlPort`, `SparqlWrapperClient`, error classes, timeout, classification markers and retry/backoff (P-2, P-5)
- [x] 3.2 `adapters/queries/*.rq` (Q0–Q11, Q2a, Q3a, Q3b, QS, QU as in `design.md`) + template filling with subject sources and type lookup per setting (P-3, DEC-10; Requirements: Per-class queries are scoped to the class; rdf:type is not a property row)
- [x] 3.3 Unit tests of the rendered query texts per mode; e2e test of each query on Oxigraph

## 4. Collection service

- [x] 4.1 `service_layer/settings.py`: the P-6 table, precedence, `--config FILE`, boolean parsing, into `Settings` (P-6, DEC-12; Requirement: Settings)
- [x] 4.2 Discovery: graphs (default first, `selected_graphs`), Q0 rejection, class counts with fallback, subclass edges, graph statistics switch (Requirements: Staged discovery; Depth and switches select the queries)
- [x] 4.3 First-wave per-class queries Q5–Q8 → raw `ClassProfile` (Requirement: Raw statistics per class; Object types across graphs)
- [x] 4.4 Precision escalation exact → first_n (one QS per class, blank-node fallback, oversized-query failure), failure recording and logging per the error matrix (Requirements: Precision escalation; Failures are recorded and fail the run)
- [x] 4.5 Thread pool, biggest classes first (P-4)
- [x] 4.6 Second wave: top-K, completeness check, incoming links (Requirement: Completeness check for first-N classes)
- [x] 4.7 Step definitions for `statistics_collection.feature` with `FakeSparql` (e2e-only rows on Oxigraph), green

## 5. Report and CLI

- [x] 5.1 `service_layer/report.py` `render_report`; `handlers` composes collect → analyse → render, signature unchanged (P-7; Requirement: Public function keeps its signature)
- [x] 5.2 Rewrite `main.html`/macros to render the analytics; remove the SPARQL macros (Requirements: Report renders from the analytics; Report content; Failures and settings are reported)
- [x] 5.3 CLI options per the P-6 table; calls collect/analyse/render; exit codes 0/1/3/4 (Requirement: Exit status)
- [x] 5.4 e2e on Oxigraph: report on the test data; CLI exit codes; step definitions for `fingerprint_report.feature`

## 6. Docs and release

- [ ] 6.1 Antora pages: statistics catalogue, precision modes, settings, default-graph note (DEC-11); update `architecture.adoc` from target to current
- [ ] 6.2 CHANGELOG 2.0.0 with the BREAKING changes (exit codes, `rdf:type` rows, named graphs profiled by default); version bump (P-9)

## Roadmap

- [x] 1.0 · [x] 1.1 · [x] 1.2 · [x] 1.3 · [x] 1.4 · [x] 2.1 · [x] 2.3 · [x] 2.4 · [x] 2.5 · [x] 2.6 · [x] 2.7 · [x] 2.8 · [x] 2.9 · [x] 3.1 · [x] 3.2 · [x] 3.3 · [x] 4.1 · [x] 4.2 · [x] 4.3 · [x] 4.4 · [x] 4.5 · [x] 4.6 · [x] 4.7 · [x] 5.1 · [x] 5.2 · [x] 5.3 · [x] 5.4 · [ ] 6.1 · [ ] 6.2

## Verification

`make check-all` (lint, types, layers, models in sync, OpenSpec strict, unit + BDD) and
`make test-e2e` on `make oxigraph-load-test-data`; clarity gate ≥ 9/10 on this PLAN.
