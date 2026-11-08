---
kind: seed (secondary; superseded by proposal.md, never groomed)
---

# Seeds

Two issues filed by a consumer (rdf-fingerprinter-ws, 2026-11-08); the developer asked for both to
be addressed the same day.

- meaningfy-ws/rdf-fingerprinter#63 — *Public call to list an endpoint's named graphs.* The library
  lists them internally (`_Collection.named_graphs`, query Q0) but offers no public call; a consumer
  that lets people choose `selected_graphs` would otherwise copy Q0.
- meaningfy-ws/rdf-fingerprinter#64 — *Ship a py.typed marker so type checkers use the
  annotations.* mypy reports `import-untyped` on `fingerprint`, so consumers lose the annotations.
