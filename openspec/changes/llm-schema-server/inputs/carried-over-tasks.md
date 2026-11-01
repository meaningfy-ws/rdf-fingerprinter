# Carried over from the llm-schema-tools PLAN (tasks of stages 2–3) — 2026-11-01 (seed input, not gated)

**Carried over from `../../llm-schema-tools/tasks.md`, not gated.** Moved unchanged when the developer
split the EPIC (`llm-schema-tools` DEC-28). Task ids keep their original numbers; dependencies on
`1.x` tasks are tasks of `llm-schema-tools` (stage 1), which must be merged first. The docs task 3.4
here covers only the server and validator parts; the stage-1 docs are done in `llm-schema-tools`.
Test ids (TC-*, IT-*) refer to `carried-over-design.md`. The release task is not carried over: this
change gets its own release when it is planned.

## 2. Stage 2: MCP schema discovery

- [ ] 2.1 `pyproject.toml`: `[project.optional-dependencies] mcp = ["mcp>=2.3,<3"]` and script `fingerprint-mcp`; `poetry lock`; `Makefile` `install` with `--extras mcp`; `.importlinter`: `mcp` in `pure-domain` and `service-io`, and the contract `schema server never collects` (P-14); marker `uc_w3` in `pytest.ini`
  - Layer: build, guards. Depends on: 1.13.
  - Tests: `make check-architecture` green; `make install` in a clean in-project `.venv` installs `mcp` 2.3.x.
- [ ] 2.2 `fingerprint/domain/search.py` (design §G)
  - Layer: domain. Depends on: 1.7.
  - Tests: TC-R1; 100% branch coverage.
- [ ] 2.3 `fingerprint/service_layer/schema_service.py` (`SchemaService.load`, `graphs`, `classes`, `describe`, `schema`, `search`) and `SchemaLookupError`
  - Layer: service_layer. Depends on: 1.10, 2.2.
  - Tests: TC-SV1.
- [ ] 2.4 `fingerprint/entrypoints/schema_server/server.py` (`build_server`): five tools, the resource, `instructions`, and the mapping of `SchemaLookupError` to `ToolError`/`ResourceError` (design §E)
  - Layer: entrypoints. Depends on: 2.1, 2.3.
  - Tests: TC-E2 (in-memory `mcp.client.Client`).
- [ ] 2.5 `fingerprint/entrypoints/schema_server/main.py` (`serve`): click options, the lazy `mcp` import, exit 2 paths, logging to stderr, `run("stdio")`
  - Layer: entrypoints. Depends on: 2.4.
  - Tests: TC-E2 (stdout stays empty before serving; exit 2 when `mcp` is missing; exit 0 on stdin EOF). The stdio path end to end is proven by `› Server started from a saved profile`, bound in 3.3.
- [ ] 2.6 `tests/bdd/test_schema_server.py` binding `schema_server.feature`; step definitions for 15 of the 21 schema-server scenarios; the other six (`› Server started from a saved profile`, which lists all six tools, `› A query given for validation is not executed`, and the four of `› Queries are validated against the pattern view`) are bound in 3.3, so until then bind per title with `scenario()`, not `scenarios()`
  - Layer: tests. Depends on: 2.5.
  - Tests: Gherkin `schema-server › One saved profile per server` (2: `Unusable start-up file`, `Server without the mcp extra`), `› The server never contacts an endpoint` (1: `Every tool answers without a network`), `› Graphs and classes are listed` (3), `› A class is described with its links` (5), `› The whole-graph schema and its resource` (1), `› Schema search by string matching` (3).
- [ ] 2.7 Stage-2 gate: `make check-all` green (the six schema-server scenarios of 3.3 are not bound yet, so they do not run); P-14 contracts pass
  - Layer: all. Depends on: 2.1–2.6.
  - Tests: the stage-2 exit criteria.

## 3. Stage 3: query validation, docs and release

- [ ] 3.1 `fingerprint/adapters/sparql_query.py` (`parse_query`): parse without evaluating, the P-12 scope walk, unchecked labels, and parse errors (design §F steps 1–2)
  - Layer: adapters. Depends on: 1.1.
  - Tests: TC-Q2.
- [ ] 3.2 `fingerprint/domain/validation.py` (`validate`): seed, fixpoint, checks and messages (design §F step 3)
  - Layer: domain. Depends on: 1.7, 3.1.
  - Tests: TC-V1; 100% branch coverage.
- [ ] 3.3 `SchemaService.validate` and the `validate_query` tool; bind the whole `schema_server.feature` with `scenarios()`
  - Layer: service_layer, entrypoints, tests. Depends on: 2.6, 3.2.
  - Tests: TC-SV1 extended (`validate` uses the unfiltered views; the 100 000-character guard; a parse error is a report, not `SchemaLookupError`); TC-E2 extended (`validate_query` returns a structured `ValidationReport`; a broken query gives `is_error=False` with `parse_error`); Gherkin `schema-server › Queries are validated against the pattern view` (4), `› The server never contacts an endpoint › A query given for validation is not executed` and `› One saved profile per server › Server started from a saved profile` (all six tools, over stdio).
- [ ] 3.4 Docs:
  - a new page `docs/modules/ROOT/pages/llm-schema.adoc` (the pattern schema and its grammar, the ShExC form, labels and `--ontology`, size filters, `fingerprint-mcp` with an MCP client configuration example, `validate_query`'s scope), in `nav.adoc`;
  - pointers from `representations.adoc` and `getting-started.adoc` (`pip install 'rdf-fingerprinter[mcp]'`);
  - glossary terms: Agent, Pattern schema, Pattern view, Merged group, Nested group, Term annotation;
  - `architecture.adoc`: the new entry point;
  - `use-cases/ucw2.adoc` "Out of Scope" no longer lists ShEx and LLM formats;
  - a README section;
  - `statistics.adoc`: Q12 and the depth table.
  - Layer: docs. Depends on: 3.3.
  - Tests: `make build-docs` green; links resolve.
- [ ] 3.5 Final gate: `make check-all`, `make oxigraph-load-test-data` + `make test-e2e`, `make check-mutation` (≥ 0.950, `mutation_score.txt` raised if higher), `openspec validate llm-schema-tools --strict`
  - Layer: all. Depends on: 3.1–3.4.
  - Tests: IT-1 to IT-5; the stage-3 exit criteria.
