# EPIC: Batched precision mode for big classes

## Appetite

TBD (proposed: MEDIUM). Pitch only. Depends on `harden-fingerprinter` (collection algorithm,
profile model) and is informed by `benchmark-fingerprinter` (how many classes need it). Split out
of `harden-fingerprinter` by the developer, 2026-10-31 (its DEC-14).

**Status: PITCH — not shaped.** Seeds: `../harden-fingerprinter/inputs/stats-design.md`
(precision modes, trade-off T2), the batched sections of the first two clarity-gate rounds
(summarised below).

## Why

`harden-fingerprinter` reads each class exactly, and when that times out, reads the first N
instances and labels the result. For classes too big for one exact query but small enough to read
in chunks, a third mode could stay exact: list every instance once, query them in `VALUES`
batches, and merge the partial results client-side. It was cut from 2.0 because it carries most of
the collection's complexity.

## Solution outline (draft)

- Escalation becomes exact → batched → first N → failure; policy `batched` forceable.
- Subject source: `VALUES ?s { … }` per batch from one full instance listing.
- Merge: histogram bins, triples, lengths and co-type counts add; min/max lengths and typed
  min/max values (numeric as `Decimal`, temporal via ISO parsing, else code point) combine.
- Distinct objects: per-batch `COUNT(DISTINCT)` overlaps, so extra queries return the distinct
  values and a client-side set per partition counts them, up to a memory limit, after which the
  count is a flagged lower bound. Blank-node objects cannot be matched across batches: their
  distinct counts are always lower bounds.
- Skip batched when the listing is truncated by an endpoint result cap or contains blank-node
  instances; a skipped mode counts as one attempt of kind `subject_stream`.

## Key decisions

- **DEC-1**: Batched results must equal exact results wherever both succeed (except flagged
  lower bounds); proven by an e2e comparison on Oxigraph.

## Open questions

- Q1: Is batched worth it? Decide after `benchmark-fingerprinter` reports how many classes fall
  to first N on real graphs.
- Q2: Defaults for batch size and the distinct-set memory limit (draft: 2 000 and 1 000 000).
- Q3: Approximate distinct counting (HyperLogLog) instead of exact sets above the limit?

## Rabbit-holes

- Parallel batches within one class on top of the class pool.
- Paging the instance listing with `OFFSET` (unstable without `ORDER BY`).

## No-gos

- No change to exact or first-N behaviour.
- No new representations.
