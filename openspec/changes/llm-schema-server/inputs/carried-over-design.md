# Carried over from the llm-schema-tools PLAN (stages 2–3) — 2026-11-01 (seed input, not gated)

**Carried over from `../../llm-schema-tools/design.md`, not gated.** The developer split the EPIC
(`../../llm-schema-tools/inputs/qa-round-1.md`, Round 6; `llm-schema-tools` DEC-28). These are the
stage-2/3 parts of that PLAN, moved here unchanged so nothing is lost. The stage-1 parts they refer to
(the pattern view, `§B`–`§D`, P-1 to P-10, TC-A*/TC-P*/TC-S1) stay in `llm-schema-tools/design.md`,
which is their only source. Numbers (P-n, TC-n, §E–§G) keep their original ids. The clarity gate
scored the whole PLAN 8.7/10 before the gap fixes; this extract has not been gated on its own.

## Verified dependencies (server and validator)

| Package | Version | How verified | What the design relies on |
|---|---|---|---|
| `mcp` (official Python SDK) | **2.3.0** (PyPI, 2026-10-02), pinned `mcp>=2.3,<3` as the extra `mcp` | Installed in a scratch venv, outside the worktree; a minimal server was run through `MCPServer.call_tool`, `read_resource` and the in-memory `mcp.client.Client(server)` | `from mcp.server.mcpserver import MCPServer`. **FastMCP no longer exists in 2.x**: `mcp.server.fastmcp` raises `ModuleNotFoundError` saying "FastMCP was renamed to MCPServer". `MCPServer(name=, version=, instructions=)`; `@server.tool()` takes the name from the function, the description from the docstring, and the input schema from the type hints. A `Literal["pattern", "shex"]` parameter becomes a JSON-schema `enum`, and a wrong value is rejected by the SDK. A return annotated with a pydantic model (or a list of them) becomes the output schema plus `structured_content`. `@server.resource("schema://{graph}", mime_type="text/plain")` registers a template. `server.run("stdio")` serves stdio. Raise `mcp.server.mcpserver.exceptions.ToolError` (or `ResourceError`) for an expected failure: the client gets `is_error=True` and the message. Any other exception becomes `UnexpectedToolError`: the client sees only "Error executing tool <name>", and the traceback is logged. Tests: `async with Client(server) as c: await c.call_tool(...)` runs in-process, with no socket. Requirements: Python ≥3.10, `pydantic>=2.12` (the lock has 2.14.2). Its 2.3.0 metadata requires `anyio>=4.9`, `httpx2>=2.10.0`, `jsonschema>=4.20.0`, `mcp-types==2.3.0`, `opentelemetry-api>=1.28.0`, `pydantic>=2.12.0`, `pyjwt[crypto]>=2.10.1`, `python-multipart>=0.0.9`, `sse-starlette>=3.0.0`, `starlette>=0.27`, `typing-extensions>=4.13.0`, `typing-inspection>=0.4.1`, `uvicorn>=0.31.1` (and `pywin32>=311` on Windows), all through the extra only. |
| `rdflib` | 7.6.0 (locked) | Tried in the worktree venv (§F) | `rdflib.plugins.sparql.prepareQuery(text)` parses and translates **without evaluating**. Its algebra has `BGP` nodes whose triples hold `Variable`, `URIRef`, `BNode`, `Literal` or `rdflib.paths.Path` predicates, with prefixes already expanded. `SequencePath.args` lists the steps. The other paths are `AlternativePath`, `InvPath` and `MulPath`. `OPTIONAL` is `LeftJoin.p2`, `UNION` is `Union`, `MINUS` is `Minus.p2`, a subquery or `VALUES` is `ToMultiSet`, `GRAPH` is `Graph.p`, and `FILTER EXISTS` is a `Builtin_EXISTS` inside `Filter.expr`. A syntax error raises `pyparsing.ParseException` with `lineno`/`col`. An undeclared prefix raises a bare `Exception("Unknown namespace prefix : ex")`. An update raises `ParseException` from the query parser and parses with `rdflib.plugins.sparql.parser.parseUpdate`. **The triples of one group are split into several `BGP` nodes at each `OPTIONAL`/`VALUES`/`MINUS`/`GRAPH`, joined by `Join`, and are sorted, not in source order.** |

## Decisions (server and validator)

| Id | Decision | Why | Rejected |
|---|---|---|---|
| P-11 | Server: package `fingerprint/entrypoints/schema_server/` (`server.py` registers the tools on `MCPServer`; `main.py` is the click command). The `mcp` import is inside `main()`, so a missing extra gives exit 2 with a message. Graphs are named by slug or IRI, and the resource uses the slug. Services live in `fingerprint/service_layer/schema_service.py` (`SchemaService`), which raises `SchemaLookupError`. | Entry points only parse and map errors (layering); the console script is installed even without the extra. Slugs are URI-safe; graph IRIs hold `/`, which the `{graph}` template cannot match. | A package named `fingerprint/entrypoints/mcp` (shadows the SDK's name in reading); IRIs in the resource URI. |
| P-12 | `validate_query` scope: the query's top-level group, meaning every `BGP` reached through `Join`, `Filter.p`, `Extend`, `Graph`, `LeftJoin.p1`, `Minus.p1`, `Project`, `Distinct`, `Reduced`, `Slice`, `OrderBy`, `Group` and `AggregateJoin`. DEC-24's "same basic graph pattern" is read as this group. Typing by an edge target needs every target alternative to be a class. A sequence path is checked step by step against the classes each step reaches, through blank-node chains **and** named targets. Checks use every class of every graph, unfiltered. | rdflib splits one group into several BGPs (finding above), so a literal reading of "same BGP" would miss `?c a C` before an `OPTIONAL`. Untyped alternatives would give false positives. A sequence through a named class (`dcterms:replaces/euvoc:status`) holds in the data and must not be reported. | Per-BGP typing; a full SPARQL type checker (rabbit-hole). |
| P-14 | `.importlinter`: add the five new domain modules to the `generated` contract's forbidden list; add `mcp` to `pure-domain` and `service-io`; add a contract `schema server never collects`, which forbids `fingerprint.entrypoints.schema_server` from importing `fingerprint.service_layer.collection` and `fingerprint.service_layer.handlers` (indirect imports count). | DEC-9 is checked statically as well as by the no-network fixture. `adapters.sparql` cannot be forbidden: `service_layer.settings` imports its `redact`. | No static fence. |
| P-15 | Search covers the filtered views (shown and nested groups and the properties of their edges) across graphs, with words ANDed and compared case-insensitively. It returns at most 25 hits plus the total. | Consistent with `list_classes`; a cap keeps one answer LLM-sized. | Ranking by fuzzy score (DEC-22 says string matching). |

P-14 also adds the stage-1 domain modules to the `generated` contract; that part is done in `llm-schema-tools`.

## Modules (server and validator)

| Layer | Module | Responsibility |
|---|---|---|
| domain | `search.py` | `search(views, text) -> SearchResult` (§G). |
| domain | `validation.py` | `validate(parsed: ParsedQuery, views, table) -> ValidationReport` (§F). |
| adapters | `sparql_query.py` | `parse_query(text, table) -> ParsedQuery`: rdflib parse, algebra walk, no evaluation. |
| service_layer | `schema_service.py` | `SchemaService.load(profile, *, ontology, prefixes, options)`; `graphs()`, `classes(graph)`, `describe(graph, cls, fmt)`, `schema(graph, fmt)`, `search(text)`, `validate(sparql)`; `SchemaLookupError` in `service_layer/exceptions.py`. |
| entrypoints | `schema_server/__init__.py`, `server.py`, `main.py` | `build_server(service) -> MCPServer`; `serve` click command (`fingerprint-mcp`). |

`pyproject.toml`: `[project.optional-dependencies] mcp = ["mcp>=2.3,<3"]`; script
`fingerprint-mcp = "fingerprint.entrypoints.schema_server.main:serve"`. `Makefile`: `install` runs
`poetry install --with test,lint,model --extras mcp`. `pytest.ini` registers the marker `uc_w3`.
`.importlinter`: `mcp` forbidden in `pure-domain` and `service-io`; the contract `schema server never
collects` (P-14).

## Model additions (server results)

| Class / enum | Fields |
|---|---|
| `GraphSummary` | `slug`, `iri`, `blocks` (int), `hidden_classes` (int) |
| `ClassSummary` | `name`, `classes` (text*), `instances`, `nested` (bool) |
| `TermKind`, `MatchedField` (enums) | `class`, `property`; `name`, `iri`, `label`, `description`, `mixed` |
| `SearchHit`, `SearchResult` | `name`, `iri`, `kind`, `graphs` (text*), `label`, `matched`; `hits` (SearchHit*), `total` |
| `QueryTermKind` (enum), `QueryTerm`, `QueryTriple`, `ParsedQuery` | `variable`, `iri`, `literal`; `kind`, `value`; `subject`, `steps` (uriorcurie*, ≥1: a predicate or an IRI sequence path), `object`; `triples` (QueryTriple*), `unchecked` (text*), `parse_error` |
| `ValidationIssueKind` (enum), `ValidationIssue`, `ValidationReport` | `unknown_class`, `unknown_predicate`, `predicate_not_on_class`, `path_step_not_on_class`; `kind`, `term` (prefixed name), `variable`, `message`; `valid`, `parse_error`, `issues`, `unchecked` |

The one-class view (`PatternGraph.kind = one_class`, `pattern_view(..., focus=)`, `via` with counts,
`expand_name`) was planned for `describe_class` and is **not built** in `llm-schema-tools`; it belongs here.

### E. Schema server

**Start** (`fingerprint-mcp PROFILE [--ontology F] [--prefixes F] [--exclude-namespace X]…
[--include-namespace X]… [--min-instances N] [--max-classes K]`):
1. `configure_logging()`; the root handler writes to stderr (stdout is the protocol).
2. `import mcp` inside `serve()`; on `ImportError`, `click.echo("error: fingerprint-mcp needs
   the mcp extra: pip install 'rdf-fingerprinter[mcp]'", err=True)` and `sys.exit(2)`.
3. `SchemaService.load(...)`:
   - `load_profile`, then `resolve_namespaces(run, user_prefixes)` with no fetch;
   - `with_ontology`, then `analyse`;
   - per graph: `pattern_view(graph, table, options)` for the filtered views, and
     `pattern_view(graph, table, GeneratorOptions(include_namespaces=[every namespace]))` for
     validation; both kept immutable.
   A `UsageError` → `click.UsageError` (exit 2).
4. `build_server(service).run("stdio")`.

**Tools** (`@server.tool()` closures over `service`; the docstrings are the tool descriptions an
agent reads; `format` is `Literal["pattern", "shex"] = "pattern"`):

| Tool | Returns | Description (docstring, first line) |
|---|---|---|
| `list_graphs()` | `list[GraphSummary]` | "The profiled graphs: slug, IRI, blocks and hidden classes." |
| `list_classes(graph: str)` | `list[ClassSummary]` | "Class groups of a graph with instance counts, largest first; nested = only reached as blank nodes." |
| `describe_class(graph: str, class_name: str, format)` | `str` | "One class's block: its edges with statistics, incoming links with counts, blank-node chains, and glossary." |
| `get_schema(graph: str, format)` | `str` | "The whole graph's schema, as the generator writes it." |
| `search_schema(text: str)` | `SearchResult` | "Find classes and properties whose name, IRI, label or description holds every word." |
| `validate_query(sparql: str)` | `ValidationReport` | "Check a SPARQL query's terms and triple patterns against the profile. The query is parsed, never run." |
| resource `schema://{graph}` | `str`, `text/plain` | "The whole graph's pattern schema." |

`instructions` = "Schema of one saved fingerprint of a knowledge graph. Start with list_graphs
and list_classes, find terms with search_schema, read blocks with describe_class, then check your
SPARQL with validate_query. Arrows are notation for triple patterns: (:C)-p->(:T) is
?x a C ; p ?y . ?y a T." `name="rdf-fingerprinter"`, `version=fingerprint.__version__`.

The parameter is named `class_name`, because `class` is a Python keyword. Each tool function
only calls the service and maps `SchemaLookupError` to `ToolError(str(error))`; the resource maps
it to `ResourceError`. The service methods hold the lookups:
- **graph.** A slug or an IRI. Unknown: "unknown graph 'x'; known: default, continents-214e8f67, …".
- **class.** No helper in the repo expands a CURIE (`PrefixTable.resolve`,
  `fingerprint/domain/prefixes.py`, returns a `NamespacePrefix` for the namespace filters). A new
  pure function `expand_name(name, table) -> str` in `fingerprint/domain/patterns.py` does it:
  - `<iri>` → the IRI without brackets;
  - otherwise split at the first `:`; when `table.by_prefix(prefix)` has an entry, the result is
    `entry.namespace + local`;
  - anything else (no `:`, or an unknown prefix such as `http`) is taken as a full IRI.
  Messages (exact text; `{…}` are filled in):
  - unknown: `unknown class '{name}' in graph {slug}; did you mean {m1}, {m2}?`, with up to 3
    `difflib.get_close_matches` over the graph's names, cutoff 0.6, and without the `; did you
    mean …?` part when there is no match;
  - hidden by namespace: `class {name} is hidden by the server's namespace filters; start
    fingerprint-mcp with --include-namespace {prefix}`;
  - hidden by size: `class {name} is hidden by the server's size filters; start fingerprint-mcp
    with a lower --min-instances or a higher --max-classes`.
- **format.** Validated by the SDK from the `Literal`. The service also checks it, for library
  callers, and names `pattern` and `shex`.
- **text.** Empty after `split()`: "search text is empty".

The service is read-only and immutable after `load`, so concurrent tool calls are safe and every
call can be repeated with the same result.

### F. `validate_query`

1. `len(sparql) > 100_000` → `parse_error = "query longer than 100000 characters"` (a guard at a
   trust boundary).
2. `adapters.sparql_query.parse_query(text, table)`:
   - `prepareQuery(text)` raises `ParseException` → if `parseUpdate(text)` succeeds,
     "only SPARQL queries are validated, not updates"; else `f"line {e.lineno}, column {e.col}:
     {e.msg}"`.
   - Message `Unknown namespace prefix : p` → "undeclared prefix p:", plus
     " — add PREFIX p: <ns>" when the table has `p`.
   - Otherwise walk the algebra with the scope of P-12, collecting `QueryTriple`s. Variables and
     blank nodes are `variable`; IRIs are `iri`; literals are `literal`. A `URIRef` predicate is
     one step; a `SequencePath` whose args are all `URIRef` gives its steps. Any other path is
     listed as unchecked (`"property path " + path.n3()`) and its triple is dropped.
   - Each `LeftJoin.p2`, `Union`, `Minus.p2`, `ToMultiSet` holding a `Project`, `Builtin_EXISTS`
     or `Builtin_NOTEXISTS` in a `Filter.expr`, and `ServiceGraphPattern` is listed once, as
     `OPTIONAL`, `UNION`, `MINUS`, `subquery`, `FILTER EXISTS`, `FILTER NOT EXISTS` or
     `SERVICE`.
3. `domain.validation.validate(parsed, views, table)`, over the unfiltered views of every graph:
   - `classes` = every member IRI. `edges[C]` = for each class, the union over graphs of its
     group's edges: property IRI → the set of target member classes, plus the flag
     `all_classes` (every alternative is a group). `predicates` = every edge property in any
     group, plus `rdf:type`.
   - **Seed types.** For `(?x, [rdf:type], <C>)`: `C ∈ classes` → `types[?x] ∪= {C}`; else issue
     `unknown_class`, once per IRI.
   - **Propagate** until nothing changes (at most one pass per triple): for `(?s, steps, ?o)` with
     `?s` typed, follow the steps. `reached` = the union over `C ∈ reached` of `edges[C][step]`
     targets, and the walk stops (adding nothing) when any `edges[C][step]` is missing or not
     `all_classes`. At the end, `types[?o] ∪= reached`.
   - **Check** each triple:
     - every step IRI ∉ `predicates` → `unknown_predicate`, once per IRI;
     - a single known step on a typed `?s`, no `C ∈ types[?s]` with it → `predicate_not_on_class`;
     - a sequence on a typed `?s`: at the first step no reached class has →
       `path_step_not_on_class`; a step whose targets are not all classes ends the check.
   - Messages name the term, the variable and the typing group. They add "classes with it:" and
     up to 3 groups that do have the predicate, which is the repair hint the client's LLM uses.
   - `valid` = no parse error and no issue.

**Worked examples** (sample profile; `P` = the PREFIX lines for `euvoc`, `skos`, `skosxl`, `rdf`):

| Query (after `P`) | Report |
|---|---|
| `SELECT ?c ?name { ?c a euvoc:Continent ; skosxl:prefLabel/skosxl:literalForm ?name }` | valid; `types[?c]` = {Continent, Concept}, `prefLabel` → {skosxl:Label} (all classes), `literalForm` is on Label |
| `SELECT * { ?c a euvoc:Continent ; skos:inScheme ?s . ?s rdf:value ?v }` | `predicate_not_on_class rdf:value` on `?s` typed `owl:Ontology&skos:ConceptScheme`; "classes with it: euvoc:XlNotation, …" |
| `SELECT * { ?c a euvoc:Continent ; euvoc:status ?st . ?st rdf:value ?v }` | valid: `euvoc:status` → `IRI` is not all classes, so `?st` stays untyped and is not checked |
| `SELECT * { ?t a euvoc:Treaty ; dcterms:replaces/euvoc:status ?s }` | valid: the sequence goes through the named group `euvoc:Treaty&skos:Concept` (P-12) |
| `SELECT * { ?c a euvoc:Continent OPTIONAL { ?c euvoc:nope ?x } }` | valid; `unchecked = ["OPTIONAL"]` |
| `SELECT * { ?c euvoc:xlNotation/(rdf:value\|dcterms:type) ?v }` | valid; `unchecked = ["property path …"]` |

### G. Search (`domain.search.search`)

- Index the filtered views of every graph: each shown or nested group member and each edge
  property, keyed by IRI. Each entry holds its graphs (slugs), its prefixed name, and its
  annotation's labels and descriptions in every language.
- The words are `text.casefold().split()`. A term matches when each word is a substring of at
  least one of its fields.
- `matched` is the first of name, IRI, label (any language) and description that holds every
  word, else `mixed`.
- Sort by (matched order, name). Return the first 25 and the total.
- The shown label is chosen by P-8.

### Worked example: the one-class view

**One-class view, `describe_class(continents-214e8f67, skos:ConceptScheme)`** (after the prefixes
and legend): the header carries counts, and `skosxl:Label` is expanded here, because no other
edge in this view reaches it:
```text
(:owl:Ontology&skos:ConceptScheme) 1 via (:euvoc:Continent&skos:Concept)-skos:inScheme 6, (:euvoc:Continent&skos:Concept)-skos:topConceptOf 6
  …
  -skosxl:prefLabel-> (:skosxl:Label) bn
    -dcterms:created-> xsd:date =2014-10-10
    …
    -skosxl:literalForm-> rdf:langString @24
# glossary: none
```

## Test case specifications (server and validator)

| Test ID | Tier / file | Input | Expected | Edge cases |
|---|---|---|---|---|
| TC-P7 | `tests/unit/domain/test_patterns.py` | `expand_name` | `<iri>` → IRI; `skos:Concept` → namespace + local; unknown prefix and `http://ex.org/a` → taken as full IRIs | `ex:` with an empty local part |
| TC-V1 | `tests/unit/domain/test_validation.py` | hand-built `ParsedQuery` + views | fixpoint over out-of-order triples; multi-typed variable; IRI subject untyped; issue messages list ≤3 classes | path through a named group valid; `rdf:type` with variable object ignored |
| TC-R1 | `tests/unit/domain/test_search.py` | words over names, IRIs, labels, descriptions | `mixed`; cap at 25 with `total`; casefold (`ß`, `İ`) | term in two graphs → both slugs |
| TC-Q2 | `tests/unit/adapters/test_sparql_query.py` | the rdflib findings above | scope per P-12; unchecked labels; parse error line/column; unknown-prefix hint; update detected; 100 001 chars refused | blank node `[ ]` as variable; `GRAPH ?g {}` checked |
| TC-SV1 | `tests/unit/service_layer/test_schema_service.py` | sample profile | graph by slug and by IRI; class lookup by CURIE and by IRI; suggestions ≤3, none → no `did you mean`; the two hidden-class messages verbatim (§E). **Task 3.3 adds:** `validate` uses the unfiltered views (a query on the default-hidden `owl:Ontology` is valid); the 100 000-character guard; a parse error comes back as a report, never as `SchemaLookupError` | library call with `fmt="turtle"` → `SchemaLookupError` |
| TC-E2 | `tests/unit/entrypoints/test_schema_server.py` | `Client(build_server(service))` (in-memory, no subprocess); `CliRunner` for `serve` | each tool's `is_error` mapping; output schemas present for structured tools; `UnexpectedToolError` path logs to stderr; `serve` writes nothing to stdout before serving; **assumption, tested:** `serve` with stdin already at EOF (client gone) returns exit 0 — the SDK's stdio loop ends on EOF. **Task 3.3 adds:** `validate_query` returns a structured `ValidationReport` (`structured_content` has `valid`, `issues`, `unchecked`), and a broken query gives `is_error=False` with `parse_error` set | missing extra → exit 2 (import patched to fail) |

Scenario → feature map row:

| Capability | Feature file | Scenarios | Tag | Stage, task |
|---|---|---|---|---|
| schema-server (all 7 requirements) | `tests/features/schema_server.feature` | 21 scenarios, one per spec scenario | `@uc_w3` | 2 (tasks 2.4–2.6), 3 (task 3.3) |

## Error matrix (server and validator)

| Failure mode | How it is detected | Expected handling | Log level | Message (exact; `{…}` filled in) |
|---|---|---|---|---|
| `mcp` not installed | `ImportError` inside `serve()` | exit 2 | none (`click.echo` to stderr) | `error: fingerprint-mcp needs the mcp extra: pip install 'rdf-fingerprinter[mcp]'` |
| Unknown graph | `SchemaLookupError` | `ToolError` → `is_error=True`; resource: `ResourceError` | INFO (the SDK logs a `ToolError` at INFO) | `unknown graph '{graph}'; known: {slug}, {slug}, …` |
| Unknown class | `SchemaLookupError` | `ToolError` | INFO | `unknown class '{name}' in graph {slug}; did you mean {m1}, {m2}?` (no `; did you mean …?` without a match) |
| Class hidden by the server's namespace filters | `SchemaLookupError` | `ToolError` | INFO | `class {name} is hidden by the server's namespace filters; start fingerprint-mcp with --include-namespace {prefix}` |
| Class hidden by the server's size filters | `SchemaLookupError` | `ToolError` | INFO | `class {name} is hidden by the server's size filters; start fingerprint-mcp with a lower --min-instances or a higher --max-classes` |
| Unknown format (library callers; the SDK rejects it for MCP clients) | `SchemaLookupError` / SDK input validation | `ToolError` | INFO | `unknown format '{fmt}'; formats: pattern, shex` (SDK: its validation text naming `'pattern' or 'shex'`) |
| Empty search text | `SchemaLookupError` | `ToolError` | INFO | `search text is empty` |
| Argument of the wrong type or missing | SDK input-schema validation | SDK `ToolError` | INFO | SDK: `Error executing tool {tool}: 1 validation error for {tool}Arguments …` |
| Bug in a tool | any other exception | SDK `UnexpectedToolError`; the client sees only the message | ERROR, with traceback (SDK) | SDK: `Error executing tool {tool}` |
| Query longer than 100 000 characters | length check | `ValidationReport(valid=False, parse_error=…)`: a result, not a tool error, so the agent can repair it | none | `query longer than 100000 characters` |
| Query does not parse | `ParseException` | as above | none | `line {lineno}, column {col}: {msg}` |
| Update given | `ParseException`, then `parseUpdate` succeeds | as above | none | `only SPARQL queries are validated, not updates` |
| Undeclared prefix | `Exception("Unknown namespace prefix : p")` | as above | none | `undeclared prefix {p}:` plus ` — add PREFIX {p}: <{namespace}>` when the table has `p` |
| Concurrent or repeated tool calls | — | safe: the service is immutable after `load`; every call is a pure read, idempotent | — | — |
| Client disconnects (stdio EOF) | SDK stdio loop ends — **an assumption about the SDK, checked by TC-E2** | the process exits 0 | none | — |

## Stage exit criteria (as planned)

| Stage | Done when |
|---|---|
| 2. MCP discovery | The 15 schema-server scenarios bound in task 2.6 pass. The six scenarios bound in task 3.3 — "Server started from a saved profile" (it lists all six tools, `validate_query` included), "A query given for validation is not executed" and the four of "Queries are validated against the pattern view" — stay unbound until then. The P-14 contracts pass and `make check-all` is green. |
| 3. Query validation | Every scenario of this change passes. The docs of task 3.4 are built (`make build-docs`), and `make check-all`, `make test-e2e` and `make check-mutation` (≥ 0.950) are green. Version 3.2.0 is released. |

## Risks (server)

- **[Risk] LinkML-generated models as MCP output schemas.** → TC-E2 asserts that `list_tools`
  shows an output schema for each structured tool. If the generated base model breaks schema
  generation, the tools return `model_dump(mode="json")` text instead (a fallback recorded in the
  task, not the plan).

## Open questions (validation)

| # | Question | Recommended default | What changes otherwise |
|---|---|---|---|
| OQ-2 | DEC-24 types a variable "through `?x a C` in the same basic graph pattern". rdflib splits one group into several BGPs at `OPTIONAL`, `VALUES`, `MINUS` and `GRAPH`. May P-12 read "same basic graph pattern" as the **whole top-level group** (every BGP joined by `Join`, excluding the unchecked constructs)? | **Yes, the top-level group.** Per-BGP typing would miss `?c a C` written before an `OPTIONAL`. | The scope walk in `sparql_query.py`, TC-Q2 and TC-V1. |
| OQ-3 | DEC-24 says "a sequence path `p/q` that does not follow a blank-node chain". P-12 reads it as "a step that is no property of the classes the previous step reaches", which also accepts sequences through named classes (`dcterms:replaces/euvoc:status`). | **The P-12 reading** (the coordinator recommends it too). | TC-V1 and one row of `schema-server › Issues found in a query` (report every sequence that leaves blank nodes). |
