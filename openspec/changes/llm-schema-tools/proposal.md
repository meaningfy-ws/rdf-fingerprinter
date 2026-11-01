# EPIC: An LLM-friendly pattern schema and a schema server for agents

## Appetite

**LARGE** (DEC-19; developer, Round 5: "take all recommendations"). It was VERY LARGE until the
re-shape (DEC-18) cut the formats. The work comes in three stages: the schema outputs and labels,
then MCP schema discovery, then query validation. There is **one release, when the EPIC is
complete** (DEC-12).

**Golden-thread parents:**
- Archived change `2026-10-31-profile-representations`. Its DEC-1 says every representation is a
  function of the saved profile. Its generator framework is the extension point for both outputs.
- Archived change `2026-10-31-harden-fingerprinter`: DEC-5 (portable SPARQL 1.1 only), DEC-7
  (layers) and DEC-8 (the LinkML profile model, which the labels extend).
- Living specs:
  - `openspec/specs/profile-representations/spec.md`: requirements "Representations derive from the
    saved profile only", "Generators share one framework" and "Text outputs are escaped".
  - `openspec/specs/statistics-collection/spec.md`: requirements "Depth and switches select the
    queries" and "Settings".
  - `openspec/specs/namespace-prefixes/spec.md`.

**Seeds** (secondary, never groomed), all under `inputs/`:
- `llm-schema-research.md`: the evidence.
- `schema-representation-options.md`: nine candidate formats, compared on one sample class.
- `pattern-schema-option.md`: the pattern schema. Its "Refined format" section is the primary
  output; its "Secondary form" section is the enriched ShExC.
- `qa-round-1.md`: the questions and answers, rounds 1 to 5, including the re-shape and its
  amendment.
- Prior art: `../archive/2026-10-31-harden-fingerprinter/inputs/prior-art.md`.

## Why

LLMs write SPARQL badly unless they are given the graph's schema. The research seed agrees on what
helps most:
- a compact schema derived from the data, with readable names and labels;
- delivered to the agent as tools;
- with the generated query checked against that schema.

The fingerprinter already saves such a schema as `profile.json`, but publishes it only in formats
built for people (HTML, PlantUML) or for validating data (SHACL). Today no `pip install` tool turns
an endpoint's real content into an LLM-sized schema and serves it to an agent. `void-generator`
produces VoID, but it is Java and has no agent interface.

## Solution outline

**One saved profile; one pattern view of it, rendered two ways; a read-only schema server over
that profile.**

1. **Stage 1: the schema outputs and labels.**
   - **The pattern schema** is the primary output and the default (DEC-13 to DEC-18). It has three
     parts, in this order:
     - a prefix block;
     - one block per class, with arrow edges that carry the statistics, incoming `via` links, and
       blank-node chains up to 3 hops;
     - a glossary of labels and descriptions.
   - **The enriched ShEx-compact** is the secondary output (DEC-18 amendment). It carries the same
     facts where ShExC can, and it parses (DEC-27).
   - Both are rendered from one pattern view of the profile and one term glossary, by generators on
     the existing framework.
   - Classes and properties get **labels and one description** from two sources: an `--ontology`
     file read at render time, and a new collection query on the data graph whose results are
     stored in the profile (DEC-6, DEC-7, DEC-17, DEC-20, DEC-21).
   - At the end of the stage, the sizes of both outputs on the canonical sample profile are
     recorded (DEC-8).
2. **Stage 2: MCP schema discovery.**
   - A server is started with **one** saved profile, given as configuration (DEC-10). It answers the
     discovery tools of DEC-23 from that profile.
   - It **never** contacts an endpoint (DEC-9).
3. **Stage 3: query validation.**
   - `validate_query` is the last MCP tool (DEC-11). It checks a query's triple patterns against
     the pattern view's edges, at the depth DEC-24 fixes.
   - The query is parsed, never run. This is the check-and-repair loop the research credits with
     the largest cheap gains, with the repair left to the client's LLM.

**Outcome:** an agent connected to the server finds the classes and predicates a question needs,
in a compact form that reads like the triple patterns it must write, and learns which of its
query's terms do not exist in the data. No SPARQL endpoint is involved after the profile is saved.

## Key decisions

Superseded decisions keep their ids and are marked; they are not deleted.

- **DEC-1**: The schema is derived from the data the endpoint holds, not from a declared ontology.
  An ontology only adds labels and descriptions (DEC-7). Reason: the research seed found that a
  schema derived from the data grounds queries better. Rejected: generating the schema from the
  ontology.
- **DEC-2**: Both outputs render from the saved profile only, so rendering adds no endpoint query.
  This continues profile-representations DEC-1. Rejected: generators that query the endpoint.
- **DEC-3**: Read-only. No part of this EPIC writes to an endpoint. Rejected: update tools.
- **DEC-4**: One EPIC in three stages: schema outputs → MCP discovery → validation (Q1). Reason: the
  stages share one profile and one release (DEC-12). Rejected: splitting it into several EPICs.
- **DEC-5**: *Superseded by DEC-18.* It said three candidate LLM formats would ship (ShEx-compact,
  the Markdown class card and the pattern schema), with the default chosen by size and evaluation.
- **DEC-6**: Labels and descriptions come from both sources (Q8): an `--ontology` file read at
  render time, and a data-graph query stored in the profile. Rejected: either source alone.
- **DEC-7**: Label precedence (F1): **the ontology wins; the data fills in only the terms the
  ontology does not label.** Rejected: data first, or merging the two.
- **DEC-8** (rewritten by DEC-18): **A size check, not a format choice.** At the end of stage 1, the
  character counts of both outputs for the canonical sample profile
  (`tests/test_data/profiles/sample-profile.json`, whole-graph view, default settings) are recorded
  in `inputs/format-sizes.md`. They are a reference for keeping the outputs compact, not a gate.
  Rejected: choosing a default by measurement; DEC-18 fixes the default.
- **DEC-9**: The MCP server is **cached only** (Q9). It serves a saved `profile.json` and never
  contacts an endpoint. Reason: collection takes minutes, and a server that cannot reach an
  endpoint can neither leak its credentials nor load it. Rejected: live or on-demand collection,
  and `run_query`.
- **DEC-10**: **One profile per server**, given as configuration (F6). Rejected: several profiles
  per server.
- **DEC-11**: `validate_query` is the **last MCP tool** of this EPIC (F5). Rejected: tools that
  generate or run queries.
- **DEC-12**: **One release, when the EPIC is complete** (F7), with the SemVer bump and the
  `CHANGELOG.md` entry required by the release authority in `AGENTS.md`. Rejected: one release per
  stage.
- **DEC-13**: The pattern schema uses the **arrow notation** `(:C)-p->(:T)`. Labels go in a
  **glossary below the patterns**, referenced by prefixed name, never inline. The patterns follow
  the non-redundancy rules N1–N9 of `inputs/pattern-schema-option.md`, "Refined format" (P2). The
  arrows are a notation for RDF triple patterns, not a query language (DEC-25). Rejected:
  SPARQL-pattern and inline-label variants.
- **DEC-14**: **The default collection depth does not rise for this EPIC** (P3). The outputs emit
  only what the profile holds, or what can be derived from it: incoming links are reversed from
  outgoing edges, and chains are joined from class profiles. Rejected: collecting top-K values or
  incoming links by default.
- **DEC-15** (revised in round 4): **Links between classes are shown in both directions, one hop
  at a time, and blank nodes are see-through** (P4, R4-3).
  - Every named-class block lists its outgoing edges and its incoming `via` links.
  - Each link's count is printed once, on the outgoing edge. The whole-graph view names incoming
    links only; `describe_class` adds their counts.
  - Chains through blank-node objects are followed until a named class, an IRI or a literal is
    reached, up to **3 hops**. Their statistics are those of the blank-node class over all its
    instances, and are marked as such.
  - Edges to named classes stop after one hop.
  - The rules are N6 and N7. Rejected: outgoing links only; unbounded paths; path-level statistics.
- **DEC-16**: **IRIs, including value IRIs, are written as prefixed names in both outputs**, with
  one prefix block at the top of each output (P5, R4-4). Value IRIs get no labels in this EPIC.
  Rejected: full IRIs.
- **DEC-17**: **Each term has one description field** (P6, R4-2). It holds the first of
  `skos:definition`, `rdfs:comment`, `dcterms:description` and `skos:scopeNote` that the term has,
  one value per language, from either source. Reason: the model needs one sentence of meaning, and
  a second field costs tokens. Rejected: separate definition and comment fields.
- **DEC-18** (re-shape, 2026-11-01, **amended in round 5**): **The pattern schema with its
  glossary is the primary LLM representation and the default; an enriched ShEx-compact is the
  secondary form.**
  - *Re-shape (R4-6).* Asked how to settle the open items, the developer said "focus only on the
    latest concise and comprehensive form we described before". This was read as one format only.
    That supersedes DEC-5 and rewrites DEC-8. It drops ShEx-compact, the Markdown class card, VoID
    (Q4), the size-versus-evaluation default (the Q3 × F4 tie-break) and the format-comparison
    evaluation (Q12/F3).
  - *Amendment (R5-1).* The developer answered "yes, pattern mainly, with compact and enriched shex
    as a secondary form". This brings ShEx-compact back as the secondary form only.
  - *What "enriched" means.* The ShExC carries the pattern schema's facts where ShExC can:
    statistics and labels as `#` comments; cardinality as ShEx cardinality; blank-node chains as
    nested `BNODE { … }` shapes, up to 3 hops (DEC-15); prefixes as in DEC-16; descriptions as in
    DEC-17. The mapping is in `inputs/pattern-schema-option.md`, "Secondary form".
  - *What both forms share.* They render from the same profile, through the same pattern view and
    term glossary. `validate_query` uses the same view.
  - *Still dropped:* the Markdown class card, VoID, and any evaluation that picks the default.
  - Reason: one view, rendered twice, keeps the facts in one place. ShExC gives a standard,
    parseable form for pipelines that expect shapes.
- **DEC-19** (Round 5: take all recommendations): **Appetite LARGE.** Two outputs of one view, a
  label query, a server and a validator are several related capabilities, with no system-wide
  migration. Rejected: keeping VERY LARGE after the cut.
- **DEC-20** (Round 5; F2): **The label predicates**, in priority order, are `skos:prefLabel`,
  `skosxl:prefLabel`/`skosxl:literalForm`, `rdfs:label` and `dcterms:title`, then `skos:altLabel`
  only when no other label exists. One value per language. They count whether or not they are
  declared `owl:AnnotationProperty`; other annotation properties are not followed. The description
  predicates are those of DEC-17. Both sources use the same list.
- **DEC-21** (Round 5; F2a): **The label query runs at every depth that finds classes.** It is one
  query per graph, over the classes found and, from depth `properties` on, over the predicates
  found. Profiles saved before this change load with no labels. Rejected: a separate switch.
- **DEC-22** (Round 5; Q6, Q7): **Pruning.** The generators prune with size-threshold flags that
  reuse the shown/hidden class rule of the existing generators (profile-representations spec,
  "PlantUML class diagram"). In MCP, the agent narrows down with `list_classes`, then
  `describe_class`, and with `search_schema`'s string matching over names and the glossary.
  There is no size budget per output. Rejected: question-driven pruning inside the server, and
  token budgets.
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
- **DEC-25** (Round 5; Q13): **SPARQL and RDF only.** There are no Cypher or Gremlin adapters, and
  no query language other than SPARQL. The pattern schema's arrows are a notation only.
- **DEC-26** (Round 5; Q14): **Packaging.** The server ships as an optional extra
  `rdf-fingerprinter[mcp]`, using the official `mcp` Python SDK, with a `fingerprint-mcp` console
  script and stdio transport. The core dependencies are unchanged. Checked on PyPI on 2026-11-01:
  `mcp` 2.3.0 (released 2026-10-02) requires Python ≥3.10 and `pydantic>=2.12`, which fits the
  project's `pydantic>=2.10,<3`. The PLAN pins the version and confirms the 2.x server API.
  Rejected: a separate package, or adding the SDK to the core dependencies.
- **DEC-27** (for the DEC-18 amendment): **The ShEx output is checked with a parser.** The tests
  parse every ShExC output with **PyShExC** (`pyshexc`). It is already in `poetry.lock` as a
  dependency of `linkml`; it is declared in the test group so the check does not rest on a
  transitive dependency. PyShExC 0.10.3.post1 requires Python ≥3.10 and lists 3.11–3.14. Its
  `parse` returns `None` on a syntax error, so the test asserts a `Schema` result. It is a test-only
  dependency, never a runtime one. Rejected: a grammar check of our own.

## Open questions

None. Every question from rounds 1 to 5 is decided above or listed as dropped in DEC-18.

## Rabbit-holes

- **A text-to-SPARQL agent.** The server provides schema and validation; the client's LLM writes
  and repairs the query.
- **Shape inference.** sheXer and QSE exist. Both outputs render the profile; they infer nothing
  new, and the ShExC is not meant for validating data.
- **Type tracking in `validate_query`.** Keep to DEC-24's scope; do not grow it into a SPARQL type
  checker.
- **Token counting.** Sizes are recorded in characters (DEC-8), not with one vendor's tokenizer.
- **Labels in many languages.** Keep one value per language tag. The outputs show the untagged
  value or `en`; the PLAN fixes the rule.

## No-gos

- **No endpoint access from the MCP server**: no connection, no collection, no fallback to the live
  endpoint (DEC-9).
- **No `run_query`** and no `sample_instances`: no tool runs a query (DEC-9, DEC-11).
- **No Cypher or Gremlin** (DEC-25).
- **No embeddings** or vector search for schema linking: string matching only (DEC-22).
- **No Markdown class card and no VoID output** (DEC-18). VoID stays possible as a later EPIC for
  pipelines such as `sparql-llm`.
- **No evaluation that picks a format.** The pattern schema is the default by decision (DEC-18).
- **No LLM calls from inside the library or its CI.**
- No write tools, and no endpoint credential management beyond what the `fingerprint` CLI already
  accepts.
- No breaking change to `fingerprint_report` (`fingerprint/service_layer/handlers.py`), the
  `fingerprint` CLI, the existing `fingerprint-gen-*` commands, or reading a `profile.json` saved by
  3.0. A profile without labels still loads and renders.

---

## What Changes

- A pattern view of the profile: classes, merged co-typed groups, edges, incoming links,
  blank-node chains and the term glossary. Two outputs are rendered from it.
- Two new generators, following profile-representations "Generators share one framework", each
  with its own `fingerprint-gen-*` command:
  - the pattern schema (primary): prefix block, class blocks, glossary;
  - the enriched ShEx-compact (secondary).
- An `--ontology` option on both generators, supplying labels and descriptions at render time
  (DEC-6, DEC-7).
- A data-graph label/description query in collection (DEC-20, DEC-21). The profile model
  (`model/fingerprint_stats.yaml`) gains optional label and description fields, and the sample
  profile and golden files are regenerated with `make refresh-sample-profile` and
  `make refresh-golden`.
- The outputs' sizes on the sample profile, recorded in `inputs/format-sizes.md` (DEC-8).
- A new MCP entry point serving one saved profile: the discovery tools, then `validate_query`
  (DEC-9 to DEC-11, DEC-23, DEC-24), shipped as the `[mcp]` extra (DEC-26).

## Capabilities

### New Capabilities
- `schema-server`: the MCP server over one saved profile. It covers configuration, the discovery
  tools and their `format` argument, the schema resource, and `validate_query`.

### Modified Capabilities
- `profile-representations`: adds the pattern view, the pattern schema and enriched ShExC
  generators, the `--ontology` label source, the label precedence (DEC-7), the description field
  (DEC-17) and the pruning flags (DEC-22).
- `statistics-collection`: adds the label/description query (DEC-20, DEC-21) and records its
  results in the profile.

## Impact

- **Code:**
  - `fingerprint/domain/`: the pattern view as domain objects (LinkML-generated where it is a
    value, per the "values are domain objects" convention in `AGENTS.md`).
  - `fingerprint/service_layer/generators/`: two new generators.
  - `fingerprint/domain/views.py`: two new `RepresentationFormat` members.
  - `fingerprint/adapters/queries/`: one new query.
  - `fingerprint/entrypoints/`: a new MCP entry point, and two new commands in `generate.py`.
  - `model/*.yaml`: optional label and description slots, followed by `make generate-models`.
- **Dependencies:**
  - the `mcp` SDK as an optional extra (DEC-26);
  - PyShExC declared in the test group (DEC-27).
  The core dependencies are unchanged.
- **Tests:**
  - A label fixture, because the canonical sample data labels none of its classes or properties.
  - Golden outputs of both forms on the sample profile.
  - A ShExC parse check.
  - Scenarios for rules N1–N9, the server tools and the validator.
- **Docs:** a new page on the pattern schema, the ShExC form and the server, under
  `docs/modules/ROOT/pages/`.
- **Release:** one SemVer MINOR release at the end, unless a breaking change appears (DEC-12).
