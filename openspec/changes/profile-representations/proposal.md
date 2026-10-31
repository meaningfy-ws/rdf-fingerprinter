# EPIC: Represent the fingerprint profile in many forms

## Appetite

TBD (proposed: MEDIUM). Depends on `harden-fingerprinter`: it renders the **profile model** that
EPIC introduces (DEC-7/DEC-8 there). Feeds `llm-schema-tools` (see Q1 on the overlap).

**Status: DRAFT — shaping.** Seeds: `../harden-fingerprinter/inputs/prior-art.md`. Open questions
below must close before the PLAN (`design.md` + `tasks.md`) is derived and gated.

## Why

A fingerprint is an inferred application profile of a knowledge graph, but today it exists only
as one HTML statistics page. People and tools need it in the forms they already use: shapes to
validate data against, a diagram to grasp the model, a readable specification document to
publish and discuss, and standard metadata for catalogues. Each of those is a pure function of
the profile; none should cost another query against the endpoint.

## Solution outline (draft)

One profile (from `harden-fingerprinter`) → many **renderers**, each a function of the profile only.

| Representation | Content | Prior art |
|---|---|---|
| Statistics report (today's HTML) | per class: properties, votes, min/max/avg, confidence, cardinality label, types, own/inherited | — |
| **Simple SHACL** (Turtle) | `sh:NodeShape` per class (`sh:targetClass`); `sh:PropertyShape` per property with `sh:path`, `sh:minCount`/`sh:maxCount` from the accepted cardinality label, `sh:datatype` / `sh:class` / `sh:nodeKind`, `sh:or` for mixed types; statistics as annotations (confidence, sample size, "first N of M") | SHACL Play generate, QSE |
| **PlantUML** class diagram | classes with datatype properties as attributes, object properties as associations with multiplicities, generalisation from the (declared or implied) hierarchy | sheXer, SHACL Play shacl-doc |
| **ReSpec-style HTML** application-profile document | W3C-spec look: overview, diagram, one section per class with its property table, value types and cardinalities, namespaces, provenance (endpoint, graph, date, caps) | SHACL Play shacl-doc (XSLT → ReSpec) |
| **VoID** (Turtle) | `void:classPartition`, `void:propertyPartition`, `void:entities`, `void:triples`, `void:distinctObjects` | void-generator |
| Profile as JSON / YAML | the profile model serialised as is (free from the generated Pydantic classes) | — |

Mechanism: renderers are eds4jinja2 templates fed the profile (harden DEC-6); RDF outputs
(SHACL, VoID) are built as graphs and serialised, so IRIs and literals are escaped correctly.
The CLI selects formats (`--format shacl,puml,respec,...`, default: today's report).

### An idea to weigh (Q2): the KG's profile as a LinkML schema

Emit the profiled KG as a **LinkML schema** (classes, slots with ranges and cardinalities,
`is_a` from the hierarchy, statistics as annotations). The LinkML generator suite then yields
SHACL, ShEx, OWL, JSON Schema, PlantUML/Mermaid, ER diagrams and Markdown docs deterministically,
instead of hand-writing one renderer per format. Cost: LinkML's generators decide the output
shape (statistics survive only as annotations); the ReSpec document and the statistics report
stay custom.

## Key decisions

- **DEC-1**: Every representation is a function of the profile; no renderer queries the endpoint.
- **DEC-2**: Rendering goes through eds4jinja2 (developer, 2026-10-31); RDF outputs are
  serialised from graphs, not string templates.
- **DEC-3**: Meaningfy standard throughout: cosmic-python layers (renderers are adapters or
  service-layer functions over the domain profile; no rendering logic in `domain`), TDD with
  golden-file tests per format against a fixed profile, SHACL output validated by a SHACL engine
  in tests, PlantUML output checked for syntax.

## Open questions

- Q1: Overlap — `llm-schema-tools` item 2 ("Representations": VoID, shapes, JSON) duplicates this
  EPIC. Move it here and keep `llm-schema-tools` to MCP + query support + LLM schema cards?
- Q2: Hand-written renderers per format, or the KG-as-LinkML route (above) for the formats LinkML
  already generates?
- Q3: SHACL strictness — closed shapes (`sh:closed`)? Emit constraints below the acceptance
  threshold as `sh:severity sh:Info` / `sh:Warning`, or drop them?
- Q4: ReSpec — the real ReSpec JS (CDN, renders client-side) or a static ReSpec-like look
  (offline, printable)?
- Q5: PlantUML — source only, or also rendered SVG/PNG (needs a PlantUML jar or server)?
- Q6: Which order of delivery: SHACL → PlantUML → ReSpec → VoID?

## Rabbit holes

- Full SHACL/ShEx inference (sh:or minimisation, supertype pruning, value enumerations).
- Diagram layout tuning for graphs with hundreds of classes — split per graph or per namespace.

## No-gos

- No endpoint queries in renderers.
- No MCP server or LLM-specific formats — `llm-schema-tools`.
- No editing round-trip (the representations are outputs, not inputs).
