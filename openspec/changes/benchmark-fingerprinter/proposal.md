# EPIC: Benchmark fingerprint collection on a large graph

## Appetite

TBD (proposed: SMALL). Pitch only. Depends on `harden-fingerprinter` (the new collection must
exist to be compared). Split out of that EPIC by the developer, 2026-10-31.

**Status: PITCH — not shaped.** Seeds: `../harden-fingerprinter/inputs/exploration.md`
(performance findings), `../harden-fingerprinter/inputs/stats-design.md` (cost bound, precision
modes). Open questions below must close before shaping.

## Why

`harden-fingerprinter` argues from reading the queries that the new collection costs
Σ classes min(|C|, read) × out-degree instead of classes × full-graph scans. Nobody has measured
it. Before telling users "it works on large graphs" we need numbers: how long, how many queries,
which classes fall back to batched or first-N, and where the old template gives up.

## Solution outline (draft)

- A **reproducible local benchmark**: a large public RDF dump loaded into Oxigraph (developer
  choice, 2026-10-31) by a `make` target, so anyone can rerun it offline.
- Run the **old** report (1.0.x template) and the **new** collection on the same graph and
  settings; record wall time, query count, per-query time, timeouts, precision mode per class,
  peak memory.
- Repeat across precision policies (`exact`, `auto`, `first_n`) and concurrency levels.
- Publish the results as a page in the docs, plus a short table in the CHANGELOG of the release
  that ships the new collection.

## Key decisions

- **DEC-1**: Local dump in Oxigraph, not a public endpoint — reproducible, no load or quota noise
  (developer, 2026-10-31).

## Open questions

- Q1: Which dump? Target size (≥ 10 M triples? ≥ 100 classes? some classes ≥ 1 M instances so the
  fallbacks trigger).
- Q2: Is the benchmark a one-off report or a repeatable `make benchmark` kept in the repo (not in CI)?
- Q3: Success criterion — a fixed speed-up, "completes where the old one times out", or only
  published numbers?
- Q4: Also compare against a prior-art tool (void-generator) on the same dump?

## Rabbit-holes

- Tuning Oxigraph itself; comparing stores.
- Micro-benchmarking individual queries before the end-to-end numbers exist.

## No-gos

- No benchmark in CI (time and data size).
- No changes to the collection algorithm here — findings feed back into `harden-fingerprinter`
  or a follow-up EPIC.
