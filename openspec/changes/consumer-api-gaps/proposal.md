# EPIC: Close four gaps found by the first service consumer

> Golden thread: capabilities `fingerprint-report` (Requirements "Library outcomes", "Named graph
> listing") and `profile-representations`. Seeds: `inputs/issues.md`
> (meaningfy-ws/rdf-fingerprinter#76, #77, #75, #69), raised by rdf-fingerprinter-ws.

## Appetite

**SMALL**. Four independent, additive fixes; no behaviour a caller relies on changes.

## Why

A web service that calls the library on user-given endpoints needs (1) a bounded call, (2) an error
contract it can map to messages, (3) to label the diagram files without parsing their names, and (4)
the list of formats in the reference it reads.

## Solution outline

- **#76** `SparqlHttpClient` gets a whole-request deadline per attempt (`timeout_seconds`, raising
  `QueryTimeout`) and a maximum answer size (`RDF_FINGERPRINTER_MAX_ANSWER_BYTES`, raising the new
  `AnswerTooLarge`, a `PermanentError`). The worst case is documented.
- **#77** An answer to the graph listing without `?g` raises `PermanentError`. A bad
  `RDF_FINGERPRINTER_*` value raises the new `ConfigurationError`, a `UsageError` subclass.
- **#75** `describe_diagrams(run, output_location, ...)` returns one `DiagramFile` per PlantUML file
  `generate_representations` writes: path, format, graph, kind, module, part.
- **#69** The API reference lists all five generators with their files.

## Key decisions

See `design.md` (C-1 to C-4).

## Rabbit-holes

- Do not move the HTTP client to `http.client`: it would lose urllib's proxy support.
- Do not add a manifest file to the output folder: it would change every format's file list.

## No-gos

- No version bump and no release: the lead releases.
