# Design: graph-listing-and-typing

> Derives from: EPIC graph-listing-and-typing (`proposal.md`, DEC-1 to DEC-3).

## Decisions

- **G-1** `collection.py` gains `_Collection.listed_graphs()`, the Q0 call that raises:
  `EndpointUnreachable` and `RetriesExhausted` become `EndpointUnreachable` (as today), any other
  `SparqlError` propagates. `_Collection.named_graphs()` keeps its behaviour by calling it and
  recording `QueryTimeout`/`PermanentError` as before. A module function
  `list_named_graphs(endpoint, settings, sparql)` returns `sorted(listed_graphs())`.
- **G-2** `handlers.list_named_graphs(sparql_endpoint_url, settings, *, sparql=None)` runs
  `validate_config()` and `validate_endpoint()` first, builds `SparqlHttpClient(url,
  settings.timeout_seconds)` when no port is given, and delegates to G-1.
- **G-3** `py.typed` files are empty; Poetry's `packages` include ships every file of a package, so
  no `pyproject.toml` change is needed. `make check-wheel` requires both in the built wheel.

## Test case specifications

| Spec scenario | Where | Double |
|---|---|---|
| Named graphs are listed | `fingerprint_report.feature` | `store` + two named graphs |
| No named graphs | `fingerprint_report.feature` | `store` |
| Listing an unreachable endpoint | `fingerprint_report.feature` | `FakeSparql.on("Q0", EndpointUnreachable)` |
| The listing times out | `fingerprint_report.feature` | `FakeSparql.on("Q0", QueryTimeout)` |
| Both packages are typed | `tests/guards/test_package.py::test_both_packages_are_typed` (allow-listed); `make check-wheel` | the source tree; the built wheel |
