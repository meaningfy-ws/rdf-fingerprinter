# EPIC: List an endpoint's named graphs, and ship the type marker

> Golden thread: capability `fingerprint-report` (Requirement "Library outcomes"). Seeds:
> `inputs/issues.md` (meaningfy-ws/rdf-fingerprinter#63 and #64).

## Appetite

**SMALL**. One public function over the existing Q0 discovery, and one packaging marker.

## Why

A caller that offers people a choice of `selected_graphs` must first know the endpoint's named
graphs. The library already discovers them as the first step of every run, but only inside
`collect`, where a timeout is recorded as a failure and turned into "no named graphs". A caller
has to copy Q0 and its error handling. Separately, the wheel has no `py.typed`, so every consumer's
type checker treats the library as untyped.

## Solution outline

`list_named_graphs(sparql_endpoint_url, settings, *, sparql=None)` next to `fingerprint_report`
returns the endpoint's named graph IRIs, sorted, through the same Q0 query, client, timeout and
retries as a run. It validates the URL and the configuration first, as `fingerprint_report` does,
and it never answers `[]` for an error: an unreachable endpoint raises `EndpointUnreachable`, a
timeout raises `QueryTimeout`, a refusal raises `PermanentError`. Both top-level packages ship an
empty `py.typed`.

## Key decisions

- **DEC-1**: One function in `service_layer/handlers.py` beside `fingerprint_report`, over the run's
  own Q0 path in `collection.py`. Rejected: a new query; a CLI command (no caller asked).
- **DEC-2**: Errors raise; the result is sorted and excludes the default graph. Reason: a caller
  must tell "no named graphs" from "could not list them" (#63). `RetriesExhausted` is reported as
  `EndpointUnreachable`, as a run does.
- **DEC-3**: `fingerprint/py.typed` and `fingerprint_report_templates/py.typed` (PEP 561), included
  by Poetry's package include.

## Rabbit-holes

- Do not change what a run does when Q0 fails: it still records the failure and profiles the
  default graph only.

## No-gos

- No graph sizes, labels or other metadata in the listing.
- No change to `fingerprint_report`.

---

## What Changes

- `fingerprint/service_layer/handlers.py`: `list_named_graphs`.
- `fingerprint/service_layer/collection.py`: Q0 listing shared by the run and the new function.
- `fingerprint/py.typed`, `fingerprint_report_templates/py.typed`.
- `tests/features/fingerprint_report.feature` + steps; `docs/` API reference; `CHANGELOG.md`.

## Capabilities

### New Capabilities

### Modified Capabilities
- `fingerprint-report`: the library also lists an endpoint's named graphs.
- `developer-tooling`: both packages ship `py.typed`.

## Impact

Additive: a new public function and a packaging marker. MINOR release (3.6.0).
