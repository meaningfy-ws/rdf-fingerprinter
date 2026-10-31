# EPIC: LLM-friendly schema discovery and representation

## Appetite

TBD (proposed: BIG, likely split). Depends on `harden-fingerprinter`: its single-pass aggregate
queries and machine-readable profile are what these tools serve.

**Status: DRAFT — shaping.** Seed: `inputs/llm-schema-research.md`; prior art in
`../harden-fingerprinter/inputs/prior-art.md`. The open questions below must close before the
PLAN (`design.md` + `tasks.md`) is derived and gated.

## Why

LLMs write SPARQL, Cypher and Gremlin badly unless they are told the graph's schema, and the
studies agree on what helps: a compact schema **derived from the data** (classes, the
predicates each class actually uses, target types, cardinality, labels), pruned to the
question, delivered with example queries, with a validate-and-repair loop. The fingerprinter
already computes most of that per-class shape, but only as an HTML page a person reads. No
lightweight `pip install` tool profiles any SPARQL endpoint and serves the result to an agent.
`sparql-llm` consumes VoID but does not produce it; `void-generator` produces VoID but is Java
and has no agent interface.

## Solution outline (draft)

1. **Schema profile model.** One in-memory profile per graph: classes (count, label, comment),
   class × property statistics (today's columns), object/datatype targets, and endpoint metadata.
   The HTML report and every new output render from it.
2. **Representations.** Serialise the profile in the formats the research favours: per-class
   compact shapes (ShEx-like or a plain text/Markdown card), VoID partitions, and possibly SHACL
   and JSON. Every format is a function of the profile; none queries the endpoint again.
3. **MCP server.** A `fingerprint mcp` entry point exposing schema discovery as tools and
   resources (candidate list below), over stdio first.
4. **Query support.** Validate a generated SPARQL query against the profile (unknown class or
   predicate, domain/range mismatch) and run it with a limit and timeout — the repair loop the
   studies credit with the largest cheap gains.

### Candidate MCP surface (to decide, see Q2)

| Kind | Name | Returns |
|---|---|---|
| tool | `list_graphs` | named graphs with triple/instance counts |
| tool | `list_classes(graph, filter?)` | classes with instance counts and labels, sorted by size |
| tool | `describe_class(graph, class, format?)` | the class's shape: predicates, cardinality, target types |
| tool | `search_schema(text)` | classes/properties matching a question (schema linking) |
| tool | `get_profile(graph, format)` | the whole profile as VoID / shapes / JSON |
| tool | `validate_query(sparql)` | schema violations in a query, before it runs |
| tool | `run_query(sparql, limit)` | results, with a cap and timeout |
| tool | `sample_instances(class, n)` | a few example subjects with their triples |
| resource | `schema://{graph}` | cached profile, so clients can attach it as context |
| prompt | `write_sparql` | a template that wires schema, examples and validation together |

## Key decisions

- **DEC-1**: Schema is derived from the data the endpoint holds, not from a declared ontology.
  An ontology, when present, only enriches labels and comments.
- **DEC-2**: Every representation renders from one profile model; adding a format never adds
  endpoint queries.
- **DEC-3**: Read-only. No tool writes to the endpoint.

## Open questions

- Q1: Scope and split — profile model + formats in one EPIC and the MCP server in a second, or
  one EPIC?
- Q2: Which MCP tools ship first? Is the table above the right granularity (few coarse tools
  vs. many fine ones), and do tools compute live or serve a cached profile?
- Q3: Which representation is the default for LLMs — ShEx-like shapes, a Markdown class card,
  SHACL, or JSON? Pick one, then measure it against the others (Q6).
- Q4: Token budget — how is a large schema pruned: by question (embedding/string match), by
  size thresholds, or left to the agent through `list_classes` → `describe_class`?
- Q5: Sources of labels/comments: the data graph only, a supplied ontology, or both?
- Q6: Evaluation — which benchmark proves a format helps (TEXT2SPARQL corpus, own competency
  questions over the test data, Cellar)? Without it, Q3 is a guess.
- Q7: Cypher and Gremlin are in the research. Are they in scope (property-graph adapters) or
  only SPARQL/RDF for now?
- Q8: Packaging — optional extra (`rdf-fingerprinter[mcp]`) or a separate package? Which MCP SDK?
- Q9: Persistence — compute once and save the profile to a file the server loads, or query on
  every call?

## Rabbit holes

- Building a full text-to-SPARQL agent: we serve schema and validation to the client's LLM; we
  do not generate queries ourselves.
- Embedding/vector search infrastructure for schema linking — start with string matching.
- A full SHACL/ShEx inference engine (sheXer, QSE already exist).

## No-gos

- No LLM calls from inside the library.
- No write tools, no endpoint credentials management beyond what the CLI already accepts.
- No breaking change to `generate_endpoint_fingerprint_report` or the HTML report.
