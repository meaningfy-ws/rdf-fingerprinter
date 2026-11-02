# Q&A record, round 1: llm-schema-tools — 2026-11-01 (seed input, not groomed)

This file records the questions put to the developer while shaping the EPIC, and the answers they
gave. A **Decided** answer is the developer's and overrides the planner's recommendation. A
**Proposed** answer is the planner's recommendation, **not yet confirmed**.

The draft's questions map to these as follows: draft Q1 → Q1–Q2, Q3 → Q3–Q5, Q4 → Q6–Q7,
Q5 → Q8, Q2/Q9 → Q9–Q10, solution point 4 → Q11, Q6 → Q12, Q7 → Q13, Q8 → Q14.

## Already answered by shipped work (3.0.0)

- **One profile model:** `ProfileRun`, generated from `model/*.yaml` and saved and loaded as
  `profile.json` by `fingerprint/adapters/profile_file.py`. Spec:
  `openspec/specs/profile-representations/spec.md`, requirement "Profile file round-trip".
- **Formats render from the profile only (draft DEC-2):** the requirements "Representations derive
  from the saved profile only" and "Generators share one framework". SHACL, PlantUML and the HTML
  document already ship this way.
- **Labels (partly):** the profile records `label_coverage`, the share of instances that have a
  label. It does not store the labels or comments of classes and properties.

## Questions and answers

| # | Question | Status | Answer |
|---|---|---|---|
| Q1 | Split: one EPIC or several? | **Decided** | **One EPIC, staged.** Formats, MCP and query validation all stay in `llm-schema-tools`. Appetite: **VERY LARGE**. |
| Q2 | Which EPIC does this change id carry? | Settled by Q1 | `llm-schema-tools` carries all of it; no new ids. |
| Q3 | Default LLM format | **Decided** | **Both ShEx-compact and the Markdown class card ship; the evaluation picks the default.** |
| Q4 | VoID output in scope? | Proposed, not yet confirmed | Yes: a VoID Turtle generator. The model is already VoID-aligned. |
| Q5 | Prefixed names in the formats? | Proposed, not yet confirmed | Yes, from the profile's `namespaces`. |
| Q6 | Pruning a large schema | Proposed, not yet confirmed | Size thresholds in the generators, reusing the shown/hidden class rule. In MCP, the agent drives it (`list_classes` → `describe_class`) and `search_schema` does string matching. No embeddings. |
| Q7 | A size budget per output? | Proposed, not yet confirmed | No. Pruning flags only; the evaluation records the sizes. |
| Q8 | Source of labels and comments | **Decided** | **Both sources, now:** an `--ontology` file read at render time **and** a query on the data graph for labels and comments, stored in the profile. |
| Q9 | MCP data: cached or live | **Decided** | **Cached only.** The server serves a saved `profile.json` and never touches an endpoint. `run_query` and `sample_instances` are out of this EPIC. |
| Q10 | First MCP tools | Proposed, not yet confirmed | `list_graphs`, `list_classes`, `describe_class(format)`, `get_profile(format)`, `search_schema`, `validate_query`, and the resource `schema://{graph}`. The prompt `write_sparql` is left out. |
| Q11 | What `validate_query` checks | Proposed, not yet confirmed | Parse errors, unknown classes and predicates, and a predicate used on a variable whose class's profile lacks it. Cardinality and datatype checks are out. |
| Q12 | Evaluation | Proposed, not yet confirmed | Checks that need no LLM: the size of each format and validator coverage on our own queries. Plus our own competency questions, put to an external LLM by hand, with the results recorded in `inputs/`. No public benchmark. |
| Q13 | Cypher and Gremlin | Proposed, not yet confirmed | No-go: SPARQL and RDF only. Cypher-style patterns could be an *RDF representation* format; they are listed in `schema-representation-options.md` §8, but no property-graph adapters. |
| Q14 | Packaging and MCP SDK | Proposed, not yet confirmed | An optional extra `rdf-fingerprinter[mcp]` using the official `mcp` Python SDK, a `fingerprint-mcp` script, and stdio. Check the SDK's current version first. |

## Scenarios the EPIC must prove (adjusted to the decisions)

| # | Scenario | Change from round 1 |
|---|---|---|
| T1 | The canonical sample profile renders as ShEx-compact, as a Markdown card and as VoID with no endpoint; a store that fails every request does not stop it. | Markdown card added (Q3). |
| T2 | The ShEx-compact output parses. The VoID output parses as Turtle, and its class and property partition counts equal the profile's. Every shown class in a Markdown card has a heading and one row per property. | Markdown card added. |
| T3 | Every class shown in the HTML document has exactly one shape and one card. Classes the pruning flags hide are absent, and the output states how many were hidden. | — |
| T4 | Labels from `--ontology` appear on the matching classes and properties. A class with no label falls back to its prefixed name. An unreadable ontology file is a usage error (exit 2). | — |
| T4a | Labels and comments the data graph holds for classes and properties are collected and stored in the profile. A profile saved before this change loads with no labels and renders the same as before. | New (Q8). |
| T4b | When the ontology and the data both give a label for the same class, one source wins, and which one is stated (the precedence is not decided yet; see follow-up F1). | New (Q8). |
| T5 | The size of every format on the sample data is recorded, and the compact formats are smaller than SHACL. | — |
| T5a | Both ShEx-compact and the Markdown card are measured on the same competency questions, and the recorded results name the default. | New (Q3). |
| T6 | With a profile file and no endpoint, `list_classes` returns the profile's classes sorted by size. `describe_class` for an unknown class returns a tool error, not a crash. `describe_class` serves both formats. | Both formats added. |
| T7 | `validate_query` flags an unknown predicate, an unknown class, and a predicate used on a class whose profile lacks it. It passes a correct query built from the sample facts and returns a parse-error result for broken SPARQL. | — |
| T8 | The MCP server opens no network connection to any SPARQL endpoint. It has no tool that runs or updates a query; a query given to `validate_query` is parsed, never executed. | Replaces the old T8 (`run_query`'s limit and timeout); `run_query` is out (Q9). |

Edge cases: IRIs with odd characters (reuse the "Unusual IRIs stay valid" outline); a profile with
no `namespaces` (saved before 3.0); sampled first-N classes marked in both compact formats; an empty
graph.

The canonical sample data has **no** labels or comments on its classes or properties (only the
`owl:Ontology` instance has an `rdfs:comment`). T4, T4a and T4b therefore need a fixture built with
`tests/builders.py`, or an ontology file under `tests/test_data/`.

## Follow-up questions the decisions raise (round 2)

- F1 (Q8): When both sources label the same term, which wins: the ontology or the data? And do
  they merge per language tag?
- F2 (Q8): Which properties count as a label or comment in the data query (`rdfs:label`,
  `skos:prefLabel`, `skosxl:prefLabel/literalForm`, `rdfs:comment`, `skos:definition`)? Which
  depth or switch turns the query on, and is it per graph or across graphs?
- F3 (Q3, Q12): Is a hand-run evaluation with one external LLM enough to choose the default? How
  many questions, which model(s), what counts as a correct answer, and what happens on a tie?
- F4 (Q3): Until the evaluation picks one, what does `describe_class` return when no format is
  given?
- F5 (Q9): With the server cached-only, is `validate_query` the last MCP tool in this EPIC, so that
  the stages are formats → MCP discovery → validation?
- F6 (Q9): Does the server serve one profile file or several (one per endpoint)? Does it reload the
  file when it changes?
- F7 (Q1): Under VERY LARGE, which stage boundaries are releases (separate minor versions)?

## Round 2 answers (developer, 2026-11-01)

| # | Answer | Recorded as |
|---|---|---|
| F1 | **The ontology wins; the data adds to it**, labelling the terms the ontology leaves unlabelled. | Decided |
| F2 | "**The usual suspects from OWL, SKOS and DCT.**" The planner turned this into the list below, marked **proposed list, not yet confirmed**. | Intent decided; list proposed |
| F3 | The developer cannot answer this; the planner proposes an evaluation (below), **not yet confirmed**. | Proposed |
| F4 | **The default format is the most compact, most economical encoding.** The planner's measurable definition is below, **not yet confirmed**. | Intent decided; measure proposed |
| F5 | **Yes.** `validate_query` is the last MCP tool. The stages are formats → MCP discovery → validation. | Decided |
| F6 | **One profile (data schema) per server, given as configuration.** | Decided |
| F7 | **No release per stage. One release, when the EPIC is complete.** | Decided |

### F2: label and comment predicates (proposed list)

| Role | Predicates, in priority order |
|---|---|
| Label | `skos:prefLabel`, `skosxl:prefLabel`/`skosxl:literalForm`, `rdfs:label`, `dcterms:title`, then `skos:altLabel` (used only when no other label exists) |
| Comment | `skos:definition`, `rdfs:comment`, `dcterms:description`, `skos:scopeNote` |

"OWL/RDFS annotation properties apply" is read as: these predicates count whether or not they are
declared `owl:AnnotationProperty`. Other declared annotation properties are **not** followed. When a
term has several values, one value is kept per language tag, from the highest-priority predicate.
The same list applies to the `--ontology` file and to the data-graph query.

### F3: evaluation (proposed)

1. **Questions.** 10 competency questions written over the canonical sample data (continents and
   treaties). Each has a reference SPARQL query and its expected result on the local Oxigraph
   (`make oxigraph-load-test-data`). They are stored with the tests' data, so the queries also feed
   `validate_query`'s scenarios.
2. **Runs.** By hand, outside the library and CI: one external LLM chosen by the developer, with its
   name and version recorded. One fixed prompt template, filled with one representation's output
   for the sample profile and one question. Each format is run once per question: 2 formats × 10
   questions = 20 runs.
3. **Scoring.** A run scores 1 when its query, run on the local Oxigraph, returns the same result
   set as the reference query (ignoring order); otherwise 0. A format's score is its total, out
   of 10.
4. **Record.** `inputs/evaluation-<date>.md`: the model, the prompt template, every generated query,
   the scores, and the size of each format (F4).
5. **Use.** See the open conflict below: the evaluation either confirms the default the size rule
   picks, or overrides it.

### F4: what "most compact" means (proposed)

- The measure is the **number of characters** (Unicode code points) of a format's whole output for
  the canonical sample profile `tests/test_data/profiles/sample-profile.json`, with default settings
  and no pruning. Counting characters needs no tokenizer dependency and is deterministic.
- The size check runs once, when the formats stage is complete. It is recorded in
  `inputs/format-sizes.md` together with the PLAN's task. The format with the fewest characters
  becomes the default, set in one place in the code (the default `--format`, and the format
  `describe_class` serves when none is given). Re-measuring is a manual step, and the default changes
  only by a recorded decision.

### Open conflict raised by Q3 + F4

Q3 says "the evaluation picks the default", and F4 says "the default is the most compact". If the
smaller format scores lower in the F3 evaluation, which rule wins? **Proposed:** the size rule picks
the default; the evaluation overrides it only when the other format scores at least 2 more out of
10. Not yet confirmed.

## Round 3 answers (pattern option, developer, 2026-11-01)

Each question is in `pattern-schema-option.md` §8. The answer is the developer's own words; the
reading is the coordinator's. **The developer confirmed the readings of P1–P5 in round 4 ("okay"),
so they are decided.** P6 was settled in round 4.

| # | Answer (verbatim) | Reading (confirmed for P1–P5) |
|---|---|---|
| P1 | "kind of yes" | Part B, with Part A, joins DEC-5 as a **third candidate format** beside ShEx-compact and the Markdown card. The size rule and the evaluation pick the default as before. |
| P2 | "arrow syntax seems to be compact and intuitive, no? (yet labels … not sure, perhaps better to have a glossary below, no?); let's make sure the patterns are as non-redundant as possible" | Variant a (arrows). Part A is rendered as a **glossary below** the patterns, referenced by prefixed name, not inline. The patterns are de-duplicated (rules N1–N9 in `pattern-schema-option.md`, "Refined format"). |
| P3 | "as compact and as compressed as possible" | **No increase of the default depth.** Derive what can be derived (e.g. incoming links reversed from outgoing patterns), emit nothing the profile lacks, and prefer the most compressed rendering. |
| P4 | "one hop" | Paths go **one hop** beyond the class, marked as class-level statistics. |
| P5 | "possibly in short IRI representation and a prefix definition" | Value IRIs appear as **prefixed names, with one prefix block at the top**. No labels for value IRIs in this EPIC. |
| P6 | "not sure what it means, whatever works best" | Delegated to the planner. **Proposed:** merge `definition` and `comment` into one description field, filled by the first of `skos:definition`, `rdfs:comment`, `dcterms:description`, `skos:scopeNote`, one value per language. Why: the model needs one sentence of meaning per term, and a second field adds tokens while rarely saying anything different. Not yet confirmed. |

## Round 4 answers (developer, 2026-11-01)

| # | Question | Answer (verbatim) | Reading | Status |
|---|---|---|---|---|
| R4-1 | Are the readings of P1–P5 right? | "okay" | Yes: P1–P5 are decided as read (DEC-5, DEC-13 to DEC-16). | Decided |
| R4-2 | P6: merge definition and comment? | "sure" | One description field, filled by the first of `skos:definition`, `rdfs:comment`, `dcterms:description`, `skos:scopeNote`, one value per language (DEC-17). | Decided |
| R4-3 | Is `bn via` enough for "one hop"? | "we shall know from class to class (incoming and outgoing), I guess a blank node would count as … intermediary so exceptionally we could include 2–3 hops" | Every class block shows its class-to-class links in both directions: outgoing edges, and incoming `via` links for named classes too. Blank nodes are see-through: a chain through them is followed until a named class, an IRI or a literal, up to 3 hops. Otherwise one hop (DEC-15 revised; rules N6 and N7 revised). | Reading by the coordinator, applied |
| R4-4 | Do prefixed names apply to every format? | "yes" | DEC-16 applies to every format. That answers Q5. | Decided |
| R4-5 | The remaining open items (Q4, Q6/Q7, Q10, Q11, Q12/F3, Q3 × F4, F2, F2a, Q14) | "..." | Unanswered. The coordinator will ask separately; they stay open. | Open |

**Planner's choice for R4-3 (to avoid printing every link twice).** An incoming link is the
reverse of an outgoing edge. So the whole-graph view prints the `via` list with **names only**,
and the link's count stays on the source's outgoing edge. The one-class view adds the counts,
because the source block is absent there. Why: you asked to see both directions in every class
block, and this costs only the names, never a second copy of a number. The other option, showing
incoming links only in `describe_class`, would hide them from the whole-graph view you asked for.

### R4-6: Re-shape to one format (developer, 2026-11-01)

| # | Question | Answer (verbatim) | Reading | Status |
|---|---|---|---|---|
| R4-6 | How should the remaining open items be settled (VoID, pruning, tool set, validation depth, evaluation, tie-break, F2/F2a, packaging)? | "focus only on the latest concise and comprehensive form we described before" | **Interpretation, awaiting confirmation:** the pattern schema with its glossary (DEC-13 to DEC-17) is the only LLM representation. ShEx-compact, the Markdown card and VoID (Q4) are dropped, and with them the size-versus-evaluation default (DEC-8 as written, the Q3 × F4 tie-break) and the format-comparison evaluation (Q12/F3). DEC-8 becomes a size check that records the pattern output's size. | Logged as the re-shape DEC-18 |

**Effect on the open items.** These no longer apply: Q3, Q4, Q12/F3, Q3 × F4 and F4a's
comparison. Q5 was answered by R4-4. These still apply to the pattern form, with the planner's
recommendations adjusted in `proposal.md`, "Open questions": F2, F2a, Q6, Q7, Q10, Q11, Q13 and
Q14.

**Q10 adjustment.** `describe_class` returns the pattern block plus glossary. The whole-schema tool
loses its format argument, and the planner proposes renaming it `get_schema(graph)`.

**Q11 adjustment.** `validate_query` checks against the pattern edges, including sequence paths
along blank-node chains.

**Superseded.** The scenarios T1, T2, T5 and T5a in "Scenarios the EPIC must prove" above name the
dropped formats. When the PLAN is derived, they are re-cut for the pattern schema: it renders with
no endpoint; it follows N1–N9; its golden output matches; its size is recorded. This record is not
edited.

## Round 5 answers (developer, 2026-11-01)

| # | Question | Answer (verbatim) | Recorded as |
|---|---|---|---|
| R5-1 | Is the re-shape reading of R4-6 right? | "yes, pattern mainly, with compact and enriched shex as a secondary form" | **Confirmed, with an amendment.** The pattern schema with its glossary is the primary form and the default. An enriched ShEx-compact is the secondary form, rendered from the same profile and glossary. The Markdown card, VoID and the default-choosing evaluation stay dropped. Logged as the amendment to DEC-18. |
| R5-2 | The remaining open items (appetite, F2, F2a, Q6/Q7, Q10, Q11, Q13, Q14) | "Take all recommendations" | Every planner recommendation in `proposal.md`, "Open questions" (as of R4-6), is decided. They are DEC-19 to DEC-26. DEC-23 gains an optional `format` (`pattern` \| `shex`, default `pattern`) for the amendment. |

The planner added one further decision for the amendment: DEC-27, how the ShEx output is checked.
PyShExC, already in `poetry.lock`, parses it in the tests; the details are in
`pattern-schema-option.md`, "Secondary form".

## Round 6 answers (developer, 2026-11-01)

| # | Question | Answer (verbatim) | Recorded as |
|---|---|---|---|
| R6-1 | (Unprompted, while the PLAN was being revised after the clarity gate) | "wait, only stage 1, the other stages are part of another epic change" | **Decided: re-shape.** `llm-schema-tools` keeps stage 1 only: the pattern-schema and enriched-ShExC generators, the glossary and term model, the label sources (`--ontology`, the data query and its model change), the golden files and the two `fingerprint-gen-*` commands. Stages 2–3 (the MCP server, cached only, and `validate_query`) become the new change `llm-schema-server`, a DRAFT that depends on this one. DEC-4 is superseded; DEC-9, DEC-10, DEC-11, DEC-23, DEC-24 and DEC-26 move there with their text; DEC-19 becomes MEDIUM. Logged as DEC-28. The stage-2/3 PLAN parts already written are kept as seed inputs of `llm-schema-server`, marked "carried over, not gated". |
| R6-2 | Does DEC-12 (one release when the EPIC is complete) now mean that this change releases 3.2.0 when stage 1 is done? (asked through the coordinator) | "yes, release 3.2.0 when stage 1 is done" | **Decided.** This change releases 3.2.0 (MINOR; 3.1.0 was `pitfall-scans`) when its work is done; `llm-schema-server` gets its own release. Recorded in DEC-12 and DEC-28. |

