# EPIC: A schema server for agents over a saved fingerprint (MCP), with query validation

**Status: DRAFT.** Not shaped against a readiness check; the PLAN is not gated. Split out of
`llm-schema-tools` by the developer on 2026-11-01 (its DEC-28; `../llm-schema-tools/inputs/qa-round-1.md`,
Round 6: "wait, only stage 1, the other stages are part of another epic change").

## Appetite

TBD (proposed: **MEDIUM**). On the `epic-planning` scale, MEDIUM is "one new capability with its
tests and docs; neighbours touched lightly". Here that capability is `schema-server`; the
neighbour `profile-representations` is touched lightly, through the pattern view it serves.

**Golden-thread parents and dependency:**
- **`llm-schema-tools`** (parent and dependency). This change serves its outputs: the pattern
  view, the pattern schema and the enriched ShExC, the glossary and the size filters. It starts
  only after `llm-schema-tools` is merged (released as 3.2.0).
- Living specs: `openspec/specs/profile-representations/spec.md` (as extended by
  `llm-schema-tools`) and the archived change `2026-10-31-profile-representations` DEC-1
  (everything renders from the saved profile).

**Seeds** (secondary, never groomed), under `inputs/`, all **carried over from the llm-schema-tools
PLAN, not gated**:
- `carried-over-design.md`: the server (§E), `validate_query` (§F), search (§G), the verified
  `mcp` 2.3.0 and rdflib 7.6.0 findings, decisions P-11, P-12, P-14 and P-15, tests, error rows and
  risks;
- `carried-over-tasks.md`: the tasks of former stages 2 and 3;
- (the spec delta draft now sits at `specs/schema-server/spec.md`: 7 requirements, 21 scenarios, the drafts convention — no `tasks.md` yet);
- `schema_server.feature`: its Gherkin projection;
- `ucw3.adoc` and `docs-lines.md`: the use case UC-W3 and its index and nav lines.

The parent's research and Q&A seeds stay in `../llm-schema-tools/inputs/`.

## Why

An agent writes better SPARQL when it can look up a graph's schema as tools and have its query
checked against that schema (`../llm-schema-tools/inputs/llm-schema-research.md`). `llm-schema-tools`
produces the schema as files. This change serves it over MCP from one saved profile, without
touching an endpoint, and adds the check-and-repair loop: the query is validated, never run.

## Solution outline

1. **MCP schema discovery.** `fingerprint-mcp <profile.json>` serves one saved profile over stdio
   with `list_graphs`, `list_classes`, `describe_class`, `get_schema`, `search_schema` and the
   resource `schema://{graph}`. It never contacts an endpoint.
2. **Query validation.** `validate_query` parses a query and reports unknown classes and
   predicates, and predicates or path steps that the typed variable's class lacks. It runs nothing.

## Key decisions

Moved from `llm-schema-tools` by its DEC-28, with their ids and text unchanged. In this text,
"this EPIC" meant `llm-schema-tools` before the split, and the DEC ids it cites (DEC-15, DEC-18,
DEC-22) are decisions of that change.

- **DEC-9**: The MCP server is **cached only** (Q9). It serves a saved `profile.json` and never
  contacts an endpoint. Reason: collection takes minutes, and a server that cannot reach an
  endpoint can neither leak its credentials nor load it. Rejected: live or on-demand collection,
  and `run_query`.
- **DEC-10**: **One profile per server**, given as configuration (F6). Rejected: several profiles
  per server.
- **DEC-11**: `validate_query` is the **last MCP tool** of this EPIC (F5). Rejected: tools that
  generate or run queries.
- **DEC-23** (Round 5; Q10, extended by the DEC-18 amendment): **The MCP surface.**
  - `list_graphs`.
  - `list_classes(graph)`: classes with instance counts, largest first.
  - `describe_class(graph, class, format)`: the class's block with counted `via` links, plus the
    glossary entries of the terms it uses.
  - `get_schema(graph, format)`: the whole-graph output.
  - `search_schema(text)`: string matching over prefixed names, IRIs and the glossary.
  - `validate_query(sparql)` (DEC-24).
  - The resource `schema://{graph}`, equal to `get_schema(graph)`.
  - `format` is optional, `pattern` or `shex`, and defaults to `pattern`.
  - Rejected: a `write_sparql` prompt, `sample_instances`, `run_query`.
- **DEC-24** (Round 5; Q11): **Validation depth.** `validate_query` reports:
  - parse errors;
  - unknown classes and predicates;
  - a predicate on a variable typed `C` (through `?x a C` in the same basic graph pattern, or
    through an edge target) that has no edge in `C`'s block;
  - a sequence path `p/q` that does not follow a blank-node chain.
  Out: cardinality and datatype checks, other property paths, and `OPTIONAL`/`UNION` branches and
  subqueries, whose patterns are not checked.
- **DEC-26** (Round 5; Q14): **Packaging.** The server ships as an optional extra
  `rdf-fingerprinter[mcp]`, using the official `mcp` Python SDK, with a `fingerprint-mcp` console
  script and stdio transport. The core dependencies are unchanged. Checked on PyPI on 2026-11-01:
  `mcp` 2.3.0 (released 2026-10-02) requires Python ≥3.10 and `pydantic>=2.12`, which fits the
  project's `pydantic>=2.10,<3`. The PLAN pins the version and confirms the 2.x server API.
  Rejected: a separate package, or adding the SDK to the core dependencies.

## Open questions

From the carried-over PLAN (`inputs/carried-over-design.md`, "Open questions (validation)").
Each has a recommended default; neither has been asked yet.
- **OQ-2:** may DEC-24's "same basic graph pattern" be read as the query's whole top-level group,
  since rdflib splits one group into several BGPs? Recommended: yes.
- **OQ-3:** DEC-24's "a sequence path `p/q` that does not follow a blank-node chain": report only
  a step that is no property of the classes the previous step reaches (sequences through named
  classes allowed)? Recommended: yes (the coordinator agrees).
- To shape: the appetite; the stage split inside this change; the release number.

## Rabbit-holes

- **Type tracking in `validate_query`.** Keep to DEC-24's scope; do not grow it into a SPARQL type
  checker.
- **A text-to-SPARQL agent.** The server provides schema and validation; the client's LLM writes
  and repairs the query.

## No-gos

- **No endpoint access from the MCP server**: no connection, no collection, no fallback to the live
  endpoint (DEC-9).
- **No `run_query`** and no `sample_instances`: no tool runs a query (DEC-9, DEC-11).
- **No embeddings** or vector search: string matching only (`llm-schema-tools` DEC-22).
- **No Cypher or Gremlin** (`llm-schema-tools` DEC-25).
- No write tools; no change to the outputs of `llm-schema-tools`.

---

## What Changes

- A new MCP entry point serving one saved profile: the discovery tools, then `validate_query`
  (DEC-9 to DEC-11, DEC-23, DEC-24), shipped as the `[mcp]` extra (DEC-26).

## Capabilities

### New Capabilities
- `schema-server`: the MCP server over one saved profile. It covers configuration, the discovery
  tools and their `format` argument, the schema resource, and `validate_query`. Draft in
  `specs/schema-server/spec.md` (a draft delta; this change has no `tasks.md` yet, as other drafts
  here). It is gated with the PLAN.

### Modified Capabilities
None planned.

## Impact

- **Code:** `fingerprint/entrypoints/schema_server/`, `fingerprint/service_layer/schema_service.py`,
  `fingerprint/domain/search.py` and `validation.py`, `fingerprint/adapters/sparql_query.py`
  (`inputs/carried-over-design.md`, "Modules").
- **Dependencies:** the `mcp` SDK (`>=2.3,<3`) as an optional extra (DEC-26).
- **Docs:** UC-W3; a server section on the `llm-schema-tools` docs page.
- **Release:** its own SemVer MINOR release, after 3.2.0.
