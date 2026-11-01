> Derives from: EPIC `llm-schema-tools` (`proposal.md`, DEC-1 to DEC-28; stage 1 only since the DEC-28 re-shape). Document type: implementation.

## Context

The fingerprinter saves a profile run (`ProfileRun`, `fingerprint/domain/profile.py`, generated
from `model/*.yaml`) and renders it through one generator framework
(`fingerprint/service_layer/generators/generator.py`; living spec
`openspec/specs/profile-representations/spec.md`, "Generators share one framework"). This change
adds two things:
- one pattern view of the profile per graph, rendered twice: as the pattern schema, the primary
  output (DEC-13 to DEC-18), and as the enriched ShExC, the secondary one (DEC-18 amendment);
- labels and one description per term, from an `--ontology` file and from a new collection
  query (DEC-6, DEC-7, DEC-17, DEC-20, DEC-21).

The MCP server and `validate_query` are the change `llm-schema-server` (DEC-28). The PLAN parts
written for them were moved, unchanged, to `../llm-schema-server/inputs/carried-over-design.md`
and `carried-over-tasks.md`.

Every number in the examples below comes from `tests/test_data/profiles/sample-profile.json`
(tool version 2.1.0, depth `values`, no `namespaces`, so prefixes are resolved at render time).
The renderings were checked by a throw-away prototype of the rules in §B. It was kept in the
session scratchpad, so **this evidence cannot be reproduced from the repository**; the golden
files written in task 1.10 supersede it as the reference output.

**Requirements** are in this change's spec deltas:
- `specs/profile-representations/spec.md` (ADDED: Pattern view, Pattern schema output, Enriched
  ShExC output, Term labels and descriptions in the outputs, Size filters; MODIFIED: Generators
  share one framework, Golden outputs, No files for empty graphs);
- `specs/statistics-collection/spec.md` (ADDED: Term labels and descriptions are collected;
  MODIFIED: Depth and switches select the queries).

They are projected into Gherkin in `tests/features/profile_representations.feature` and
`tests/features/statistics_collection.feature`. The generator scenarios trace to UC-W2 (publish a
fingerprint) and UC-B2.1 (generate representations from a saved profile), the collection
scenarios to UC-W1. UC-W3 (the agent over MCP) moved to `llm-schema-server`.

## Goals / Non-Goals

**Goals:**
- `fingerprint-gen-pattern`, `fingerprint-gen-shex`, `--format pattern|shex`, the `--ontology`
  option, the size filters, the term-annotation query (Q12) and its model change.
- The golden files, the docs page, and release 3.2.0 (DEC-12, confirmed in Round 6).

**Non-Goals:** the EPIC's no-gos and rabbit-holes (`proposal.md`, "No-gos", "Rabbit-holes"). In
particular: no MCP server, no `validate_query`, no `[mcp]` extra (all `llm-schema-server`), no query execution, no Markdown card or VoID, no
token counting, no runtime ShExC parse check (DEC-27 makes PyShExC test-only), and no change to
the existing generators' output.

## Verified dependencies

| Package | Version | How verified | What the design relies on |
|---|---|---|---|
| `pyshexc` | 0.10.3.post1 (locked, from `linkml`; declared in the `test` group, DEC-27) | Parsed candidate outputs | `pyshexc.parser_impl.generate_shexj.parse(text)` returns `Schema`, or `None` after printing the error to stderr. It accepts trailing `;`, `(a OR b)`, `{0,74}`, `?`, `*`, `.`, `BNODE { … } {24}`, a `<label> BNODE { … }` declaration, `BNODE @<label>`, references to undeclared shapes, and IRIs with `?&'#%`, `ș` and `A`. **It rejects `=` in an IRIREF, even written as `=` or `\=`** (all 23 URI sub-delimiters and gen-delimiters were probed; only `=` fails). |

## Decisions

The EPIC settles the bet; these are the PLAN's choices.

| Id | Decision | Why | Rejected |
|---|---|---|---|
| P-1 | The pattern view and the ShExC view are LinkML classes added to `model/fingerprint_views.yaml`, generated into `fingerprint/domain/views.py`. The selected annotations go in `model/fingerprint_stats.yaml`, since they are saved. The raw annotation row goes in `model/fingerprint_analytics.yaml`, beside `SettingsOverride`, so the `profile.json` schema does not list it. | The repo rule "values are domain objects" (`AGENTS.md`, `tests/guards/test_no_composed_dicts.py`); `views.py` is already generated, contract-fenced and excluded from mutation. | A new `model/*.yaml` file: a new Makefile target, contract entry and banner, for no gain. |
| P-2 | The builders are pure domain functions: `fingerprint/domain/patterns.py` (view), `shex.py` (ShExC view), `annotations.py` (selection and merge). The generators only call them. | Domain code gets 100% branch coverage and mutation testing (`development.adoc` "The gate"), and the rules N1–N9 are the risky part. | Logic in Jinja templates: not unit-testable, not mutated. |
| P-3 | A namespace or size filter decides which groups get blocks. A group with any shown member gets a block, and its name lists every member, hidden ones included. Edge targets name hidden groups too; `via` lists leave out sources without a block or nesting. | Hiding `owl:Ontology` (a default meta namespace) must not hide the fact that the scheme's instances are also `owl:Ontology`. This keeps the sample rendering of the seed, and follows the PlantUML precedent of keeping hidden association targets. | Dropping hidden members from names and targets: it loses facts a query needs. |
| P-4 | Nested ("see-through") test: reached only by blank-node objects, at least one, and the reaching distinct objects (summed once per source group and property) ≥ instances. | Without the count guard, a class with unreached IRI instances would lose its block silently. On the sample, the sums equal the instances exactly (145, 6; 4530, 357, 12). | "Reached only as blank nodes" alone. |
| P-5 | A hop is one edge; edges sit at levels 1–3 (level 1 = the block's own edges), so the deepest chain is class → blank node → blank node → target. Expansion is assigned at levels 1 and 2 only: each nested group is expanded under the shallowest reaching edge with the most triples, then by source name, then property name. Other edges into it end ` ^`; a level-3 edge into a nested group expanded nowhere ends ` …`. The cycle guard falls out: a group is assigned once. | Deterministic, and every nested group reached from a block at level 1 or 2 is expanded exactly once (coordinator decision on "up to 3 hops"). | Choosing among all edges at once: a chosen edge could lie under a cut chain, and the group would never be shown. |
| P-6 | The term annotations are stored per `GraphProfile` as the *selected* values (`TermAnnotation`: term, labels, descriptions, each a `LangText`). Q12 matches in the default graph and every named graph, as Q4 does. | The view is per graph, and DEC-21 asks for one query per graph. Ontology triples usually sit in another graph. Selected values keep the profile small; the raw rows are reproducible. | Raw rows in the profile; a run-level list; same-graph lookup only. |
| P-7 | Precedence (DEC-7) works per term **and per field**: the ontology's labels when it has any, else the data's; the same for descriptions; never merged per language. | DEC-7 talks about labels and DEC-17 allows "either source" for the description. Per field satisfies both and is one rule. | Per term (the data loses a description the ontology lacks); per language (rejected by DEC-7). |
| P-8 | Shown language: the untagged value, else `en`, else the smallest tag. Descriptions are collapsed to one line and cut at 200 characters plus `…`. Values in stat tokens are cut at 64. | The EPIC's rabbit-hole "Labels in many languages" leaves the rule to the PLAN. Cut lengths keep outputs LLM-sized while keeping whole IRIs such as `=http://publications.europa.eu/resource/authority/continent` (55 characters). | No cut; per-language glossary lines. |
| P-9 | ShExC: a nested group reached by one edge in the view is written inline; reached by more, it becomes one `<label> BNODE { … }` shape referenced as `BNODE @<label>`. A class with no shape in the file becomes `IRI`. Terms whose IRI holds `=` are skipped (PyShExC finding above). | Follows `inputs/pattern-schema-option.md` "Secondary form". Every file must parse with PyShExC (DEC-27). | Percent-encoding `=` (it changes the IRI). |
| P-10 | Size filters: `--min-instances N` and `--max-classes K` on the two new generators only, in `GeneratorOptions`. **Entry points:** `fingerprint --format pattern\|shex` works with no change, because `fingerprint/entrypoints/cli/main.py:67` builds its `--format` choices from `GENERATORS`; it renders with the default options. `--ontology`, `--min-instances` and `--max-classes` exist only on `fingerprint-gen-pattern` and `fingerprint-gen-shex` (decided: `fingerprint` collects, so its labels come from Q12; library callers can still set the three fields of `GeneratorOptions`). | DEC-22 names "size-threshold flags" reusing the shown/hidden rule; SHACL and PlantUML outputs must not change (no-go). | Applying them to every generator. |
| P-13 | Golden pattern and ShExC files compare as **text**. The PyShExC parse check is a Gherkin scenario ("The ShExC output parses"), not part of the golden test. | ShExC comments carry the statistics, so ShExJ comparison would miss changes (lean-test-suite DEC-8 compares by meaning only "where the format allows"). One tier per check (lean-test-suite DEC-2). | Comparing ShExJ JSON. |
| P-14 | `.importlinter`: add the three new domain modules (`annotations`, `patterns`, `shex`) to the `generated` contract's forbidden list. | Its comment requires every new `fingerprint.domain` module to be listed. The server's contracts moved to `llm-schema-server`. | — |
| P-16 | Release **3.2.0** (SemVer MINOR; 3.1.0 was released by `pitfall-scans`): new commands and an optional profile field. A 3.2 `profile.json` with `term_annotations` is not readable by 3.1 or 3.0 (`extra=forbid`); 3.0 and 3.1 files stay readable (no-go kept). | Release authority in `AGENTS.md`; DEC-12 (the EPIC's "MINOR release" holds; only the number moved with the base). | 4.0.0: nothing existing breaks. |

## Overlap with `pitfall-scans` (merged before this PLAN, PR #44)

Checked against the base `97d6a09`. What exists is reused; nothing is duplicated.

| `pitfall-scans` part | Relation to this change | Decision |
|---|---|---|
| `p08_missing_comment`, `p20_label_longer_than_comment`, `p32_classes_same_label`, `p12_p30_same_name_not_equivalent` (`fingerprint/adapters/queries/pitfalls/`) | They *judge* the labels of `owl:Class`/`owl:*Property` declarations (only `rdfs:label`/`rdfs:comment`), returning `?entity ?property ?value` finding rows. They store no label values. | No reuse possible: Q12 *selects* label and description values of the profiled terms, over the 9 predicates of DEC-17/DEC-20. No change to the checks. |
| `p34_untyped_class`, `p35_untyped_property` | Quality findings about declarations; the pattern view is derived from the data (DEC-1). | Independent. |
| `Settings.schema_graphs` (graphs holding the ontology, joined by `FROM`) | Q12 looks in the default graph and every named graph (P-6), which includes any schema graph. | Q12 does not read `schema_graphs`: it would add a second, narrower rule. |
| `QueryKind.pitfall`, `Failure.check_id`, `_Collection.fail(..., check_id=)` | `term_annotations` is one more `QueryKind` through the same `fail` (query name `"Q12"` in `QUERY_KIND`; `"PITFALL"` is the pitfall entry). Q12's query name is free. | Reused as is; `check_id` stays unset for Q12. |
| `_PitfallScan` (runs in `collect`, after `profile_graph`) | Q12 runs inside `profile_graph`, after the class pool, so a graph's annotations exist before its pitfall scan. | No interaction. |
| `DocumentGraph.taxonomy`, `DocumentClass.data_properties`/`object_properties`, `PrefixDeclaration.uses` (views for the report) | The pattern view does not show the class hierarchy and counts its own edges. | Not reused (report-only views). `PrefixDeclaration` is reused for the pattern prefix block; its new optional `uses` stays unset. |
| `RepresentationFormat.pitfalls`, `GENERATORS[PITFALLS]`, `fingerprint-gen-pitfalls` | `pattern` and `shex` are registered the same way. | Same pattern. |
| `docs/modules/ROOT/pages/pitfalls.adoc` | No name clash with `llm-schema.adoc`. | — |

## Layering and modules

`.importlinter` layers: `entrypoints → service_layer → adapters → domain`.

| Layer | Module (new unless marked) | Responsibility |
|---|---|---|
| domain | `model/fingerprint_stats.yaml`, `fingerprint_analytics.yaml`, `fingerprint_views.yaml` (modified) → `profile.py`, `views.py`, `profile_run.schema.json` (regenerated) | The model additions below. |
| domain | `fingerprint/domain/vocabulary.py` (modified) | `SKOS`, `SKOSXL`, `DCTERMS`, `XSD_STRING`; `TERM_LABEL_PREDICATES`, `ALT_LABEL`, `TERM_DESCRIPTION_PREDICATES` (DEC-20, DEC-17). |
| domain | `annotations.py` | `select_annotations(values) -> list[TermAnnotation]`, `merge_annotations(ontology, data) -> list[TermAnnotation]`, `shown(texts) -> LangText \| None`. |
| domain | `patterns.py` | `pattern_view(graph, table, options) -> PatternGraph`; rules §B. |
| domain | `shex.py` | `shex_view(view: PatternGraph) -> ShexSchema`; mapping §D. |
| adapters | `queries/q12_term_annotations.rq`, `queries/__init__.py` (modified: `"Q12"`, `terms_values()`, `render(..., terms: str = "")`; the default keeps `tests/e2e/test_queries.py:22`, which calls `render` without terms, working) | §A. |
| adapters | `ontology_file.py` | `load_ontology(path) -> list[AnnotationValue]`; raises `OntologyFileError` (new in `adapters/exceptions.py`). |
| service_layer | `collection.py` (modified) | `_Collection.term_annotations(graph, classes)` after the class pool; `QUERY_KIND["Q12"]`. |
| service_layer | `representations.py` (modified) | `with_ontology(run, path)`; `validate_options` checks the size options; ontology errors become `UsageError`. |
| service_layer | `generators/pattern.py`, `generators/shex.py`, `generators/__init__.py` (modified) | `PatternGenerator`, `ShexGenerator`; `GENERATORS[pattern]`, `GENERATORS[shex]`. |
| entrypoints | `cli/generate.py` (modified) | `gen_pattern`, `gen_shex` with `--ontology`, `--min-instances`, `--max-classes`. |
| templates | `fingerprint_report_templates/pattern_schema/`, `shex_schema/` (`config.json`, `templates/schema.txt`, `templates/schema.shex`) | Layout only; every token comes from the view. |

`pyproject.toml`: scripts `fingerprint-gen-pattern = "fingerprint.entrypoints.cli.generate:gen_pattern"`
and `fingerprint-gen-shex = "…:gen_shex"`; test group `"pyshexc==0.10.3.post1"`. `Makefile`:
`check-wheel` also greps for `pattern_schema/templates/schema.txt`, `shex_schema/templates/schema.shex`
and `q12_term_annotations.rq`.

### Model changes (LinkML)

`model/fingerprint_stats.yaml`:
```yaml
QueryKind:           # permissible_values += term_annotations
  term_annotations: { description: "The labels and descriptions of a graph's classes and properties (Q12)." }
LangText:
  description: A literal's text and its language tag; no language for an untagged literal.
  attributes:
    text: { required: true }
    language: {}
TermAnnotation:
  description: The labels and descriptions selected for one class or property (llm-schema-tools DEC-17, DEC-20).
  attributes:
    term: { range: uriorcurie, required: true }
    labels: { range: LangText, multivalued: true, inlined_as_list: true }
    descriptions: { range: LangText, multivalued: true, inlined_as_list: true }
GraphProfile:        # attributes +=
  term_annotations: { range: TermAnnotation, multivalued: true, inlined_as_list: true,
                      description: "Selected labels and descriptions of the graph's terms; absent in profiles saved before 3.2." }
```
`model/fingerprint_analytics.yaml`: `AnnotationValue {term (uriorcurie, required), predicate
(uriorcurie, required), text (required), language}`.

`model/fingerprint_views.yaml`:

| Class / enum | Fields (all generated Pydantic, frozen by the base template) |
|---|---|
| `RepresentationFormat` += | `pattern` ("The pattern schema: one text file per graph."), `shex` ("Enriched ShEx compact: one .shex file per graph.") |
| `GeneratorOptions` += | `ontology` (path text), `min_instances` (int ≥1), `max_classes` (int ≥1) |
| `TargetKind` (enum) | `group`, `datatype`, `iri`, `blank_node`, `unknown` |
| `EdgeTarget` | `kind`, `name` (as written), `classes` (uriorcurie*, for a group), `graph` (uriorcurie, other graph), `has_shape` (bool) |
| `PatternEdge` | `property` (uriorcurie), `name`, `depth` (1–3; 1 = the block's own edge, one hop per level), `targets` (EdgeTarget*), `text` (the line after the indent), `stats` (token text), `ending` (`""`, `" ^"`, `" …"`), `min_count`, `max_count` (int; absent: no histogram), `presence_only` (bool), `edges` (PatternEdge*, nested) |
| `ViaLink` | `source` (group name), `property` (name) |
| `PatternBlock` | `name`, `classes` (uriorcurie*), `shape` (ShExC label), `instances`, `observed` (only first-N), `nested` (bool), `reaching_edges` (int), `co_types` (CoTypeNote*), `via` (ViaLink*), `header` (as written), `edges` (PatternEdge*) |
| `CoTypeNote` | `name`, `subjects` |
| `GlossaryEntry` | `term` (uriorcurie), `name`, `line` |
| `PatternGraph` (mixin `GraphView`) | `graph` (uriorcurie), `prefixes` (PrefixDeclaration*), `hidden_classes` (int), `blocks` (PatternBlock*), `nested_blocks` (PatternBlock*, every nested group's own block, edges from depth 1), `glossary` (GlossaryEntry*) |
| `ShexConstraint` | `predicate`, `value`, `cardinality`, `comment`, `inline` (ShexConstraint*), `depth` |
| `ShexShape` | `comment`, `label`, `blank` (bool), `constraints` (ShexConstraint*) |
| `ShexSchema` (mixin `GraphView`) | `prefixes`, `shapes` (ShexShape*), `glossary` (text*), `skipped_terms` (text*) |

**Backward compatibility:** `term_annotations` is optional. A 3.0 or 3.1 `profile.json` (including `tests/test_data/profiles/scanned-profile.json`, with pitfall results) validates
(`extra=forbid` only rejects unknown keys) and loads with `term_annotations` `None`, which every
reader treats as `[]`. `make generate-models` regenerates `profile_run.schema.json`.
`tests/sample_data.py` `differences()` flattens nested objects and compares lists as sorted JSON,
so the new list needs no change there.

## Algorithm / approach

### A. Term annotations

**Q12** (`fingerprint/adapters/queries/q12_term_annotations.rq`; `$terms` is
`terms_values(iris)`, the IRIs as `<…>` separated by spaces, empty for none):
```sparql
# Q12 term annotations (llm-schema-tools DEC-20, DEC-21)
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX skosxl: <http://www.w3.org/2008/05/skos-xl#>
PREFIX dcterms: <http://purl.org/dc/terms/>
SELECT DISTINCT ?t ?p ?v {
  VALUES ?t { $terms }
  { VALUES ?p { skos:prefLabel rdfs:label dcterms:title skos:altLabel
                skos:definition rdfs:comment dcterms:description skos:scopeNote }
    { ?t ?p ?v } UNION { GRAPH ?g { ?t ?p ?v } } }
  UNION
  { { ?t skosxl:prefLabel/skosxl:literalForm ?v } UNION { GRAPH ?g { ?t skosxl:prefLabel/skosxl:literalForm ?v } }
    BIND(skosxl:prefLabel AS ?p) }
  FILTER(isLiteral(?v))
}
```
- **When.** In `_Collection.profile_graph`, after `pool.map`, when the depth is at least `classes`.
  The terms are the profiled class IRIs, plus, at depth `properties` or deeper, the union of their
  property IRIs, minus `rdf:type`. Each passes `to_iriref`; those that fail are dropped, with no
  failure (they already have one from Q3). Sorted, de-duplicated, one query. With no term left,
  no query is sent and the graph stores `[]`: rdflib, behind `FakeSparql`, cannot evaluate an
  empty `VALUES` block (verified: `AttributeError` in `evalMultiset`).
- **Rows.** Each row becomes `AnnotationValue(term=str(t), predicate=str(p), text=str(v),
  language=v.language or None)` (typed terms; statistics-collection "Results are read as typed RDF
  terms").
- **Errors.** A `SparqlError` records `Failure(query_kind=term_annotations, graph=…,
  message="graph <g>: term annotations not read: <error>")`, and the graph keeps
  `term_annotations` `None`. Otherwise it gets `select_annotations(rows)`, `[]` when there are none.
- **The harden-fingerprinter "Query templates" table** gains one row: `Q12 | term annotations |
  depth ≥ classes | once per graph, after the classes`.

**Selection** (`annotations.select_annotations`), shared by Q12 and `--ontology`:
1. Group the values by term.
2. Labels:
   - for each language `L` (`None` for untagged), take the values in `L` of the first predicate
     of `TERM_LABEL_PREDICATES` = (`skos:prefLabel`, `skosxl:prefLabel`, `rdfs:label`,
     `dcterms:title`) that has a value in `L`, and keep the smallest text;
   - only if the term has no value from any of these, do the same with `skos:altLabel`.
3. Descriptions: the same per-language rule over `TERM_DESCRIPTION_PREDICATES` = (`skos:definition`,
   `rdfs:comment`, `dcterms:description`, `skos:scopeNote`).
4. Emit `TermAnnotation(term, labels, descriptions)`, the texts sorted by language with untagged
   first, terms sorted by IRI, and only terms with at least one text.

The selection is idempotent and order-independent, which a Hypothesis property checks
(TC-A2 below).

**Ontology file** (`ontology_file.load_ontology(path)`):
- Parse with `rdflib.Graph().parse(path, format=rdflib.util.guess_format(path) or "turtle")`.
- Every triple `(s, p, o)` with `s` an IRI, `p` among the nine predicates and `o` a literal is
  one value. `s skosxl:prefLabel ?x . ?x skosxl:literalForm o` gives one value with the predicate
  `skosxl:prefLabel`.
- `OSError` or any parser exception raises `OntologyFileError("ontology file <path> cannot be
  read: <reason>")`.

**Merge** (`annotations.merge_annotations(ontology, data)`): for each term in either list, the
labels come from the ontology entry when it has labels, else from the data; the descriptions the
same way (P-7). `representations.with_ontology(run, path)` applies it to every graph's
`term_annotations` before `analyse`. With no `--ontology`, the run is unchanged. `GraphAnalytics`
copies `term_annotations` through `graph.model_dump()` in `analytics.graph_analytics`.

### B. Building the pattern view

`pattern_view(graph: GraphAnalytics, table: PrefixTable, options: GeneratorOptions) -> PatternGraph`,
the whole-graph view. (The one-class view for `describe_class` is `llm-schema-server`'s.)

1. **Names.** `name(iri)` is `turtle_term(iri, table)[0]` (`prefix:local` when the local part
   matches the safe-local rule, else `<iri>`). It records the prefix used. An IRI failing
   `to_iriref` is added to `skipped` and its class or property is left out (profile-representations
   "An IRI that cannot be written is skipped, not broken").
2. **Groups (N2).** A union-find over `graph.class_partitions`: unite `A` and `B` when `A.co_types`
   has `B` with `subjects == A.instances == B.instances`. A first-N class never qualifies, because
   its co-type counts are over `observed < instances`. The group name is the members' names sorted
   and joined by `&`. The group's properties are each property name once; the profile comes from
   the first member, in name order, that has it.
3. **Nested groups (N7, P-4).** For each group `T`, gather every value partition in the graph
   whose `object_class` is a member of `T`.
   - `T` is nested when every such partition has `node_kind blank_node`, there is at least one,
     and Σ over (source group, property) of the largest `distinct_objects` (else `triples`) among
     those partitions ≥ `T.instances`.
   - Sample: `skosxl:Label` 144 + 1 = 145; `euvoc:XlNotation` 6; treaties `skosxl:Label`
     2489 + 2040 + 1 = 4530; `euvoc:XlNotation` 357; `euvoc:XlNote` 10 + 1 + 1 = 12.
4. **Filters (P-3, P-10).**
   - A member is shown when its namespace is not in `excluded_namespaces(options, table)`.
   - Named groups with a shown member, in (instances desc, name) order, are kept when
     `instances ≥ min_instances`; then only the first `max_classes` are kept.
   - Kept named groups get blocks. `hidden_classes` = members of named groups without a block, plus members of nested groups that no edge of the view reaches (reached only from groups without a block, or only through their own blank-node cycle). Nested groups reached only by level-3 edges are not hidden: their edges show ` …`.
   - Nested groups are never hidden by size. They show only if reached from a block within 3
     levels.
5. **Edges (N3, N4, N5).** For each property of a block's group, in name order, one `PatternEdge`:
   - `targets`, in this order:
     - the groups of the partitions' `object_class`, by name, written together as
       `(:G1|G2)`; a group typed in another graph (`object_class_graph` ≠ `graph.graph`) is
       written `G @<graph name>`;
     - the datatypes of the literal partitions (`datatype`, or `rdf:langString` with a language,
       or `xsd:string`);
     - `IRI` (iri, no class); `BNODE` (blank, no class).
     No partition gives `.` (kind `unknown`).
   - `stats` tokens, each after one space, in this order:

     | Token | Condition | Source field |
     |---|---|---|
     | `k/n` | k < n | k `subjects_with_property`, n the class's `observed_instances` |
     | `×a` / `×a-b` | not both 1 | a, b = min, max of `cardinality_histogram[].values_per_subject` |
     | `bn` | any partition `blank_node` | `ValuePartition.node_kind` |
     | `@tag` / `@n` | ≥1 language | distinct `ValuePartition.language` |
     | `=v` / `lo..hi` | one literal datatype, not `rdf:langString`, `min_value` set | `min_value`, `max_value` of that partition; `=v` when equal |
     | `=name` | every partition `iri`, `distinct_objects` = 1, and `top_values` non-empty (depth `rich_values` or deeper) | `top_values[0].value`, written by step 1's `name` rule (DEC-16), so its prefix is declared. No top values: nothing (DEC-14: no added query) |
     | `dN` | no `=v` or `=name`, and N < `total_triples` | `PropertyAnalytics.distinct_objects`, `total_triples` |
     | `presence` | `presence_only` | no other token |

   - `min_count` = 0 when k < n, else a; `max_count` = b; both absent without a histogram.
   - **Quoting.** A value is bare when it is non-empty, holds no white space and no `"`, has no
     `..` and is at most 64 characters. Otherwise it is `json.dumps(v[:64] + ("…" if len(v) > 64
     else ""), ensure_ascii=False)`.
6. **Chains (N7, P-5).**
   - `frontier` = every (block group, edge) at level 1.
   - For levels 1 and 2: among frontier edges into a nested group not yet assigned, assign each
     such group to its best edge, keyed (−triples into the group, source name, property name).
     Triples into a group are the largest partition `triples` over its members. The assigned
     group's edges form the frontier of the next level (2 or 3). Level-3 edges are never assigned.
   - Rendering: an edge into an assigned group carries the group's edges nested one level deeper
     when the assignment is this edge; ` ^` when it is another edge; ` …` when the group is
     unassigned (every edge reaching it is at level 3). No line lies below level 3.
   - `reaching_edges` = the number of distinct (source group, property) edges in the view into the group, set for assigned (expanded) groups only; 0 for a group expanded nowhere (for ShExC, P-9).
   - `nested_blocks` holds every *assigned* nested group as a block of its own, with
     edges from level 1 (for ShExC named shapes, P-9).
7. **via (N6).** For each block group `G`: the (source, property) pairs over groups with a block
   or nested in the view, whose partitions point at a member of `G`; sorted by source name, then
   property, written `(:S)-p`.
8. **Header.** `(:<name>) <instances>`, then ` ~<observed> first_n` when `precision_mode` is
   `first_n`, then ` co <name> <k>` for co-types outside the group (shown classes only, by k desc,
   then name), joined by `, `, then ` via ` + the via list joined by `, `.
9. **Glossary (N9).** The terms of every rendered name (headers, targets, `co`, `via`, properties),
   intersected with the annotations that have a label or a description, sorted by name. Each line:
   - `name "label"@lang: description`; the `@lang` is omitted for an untagged label, and
     `: description` when there is none;
   - `name: description` when there is no label;
   - label and description each chosen by P-8.
10. **Prefixes (N8).** Every prefix recorded in step 1 (glossary names included), sorted, as
    `PrefixDeclaration` from the table.

The function is pure and deterministic: the same inputs give the same `PatternGraph`. Rendering
twice gives identical files; this is safe to retry and has no side effects.

### C. Pattern grammar (final; replaces the seed's sketch)

```ebnf
output    ::= prefix* legend [hidden] block* glossary
prefix    ::= "PREFIX " PNAME_NS " <" IRI ">" NL
legend    ::= "# " LEGEND NL                         (* the fixed text in the spec, "Pattern schema output" *)
hidden    ::= "# hidden: " INT " classes" NL
block     ::= header NL edge*
header    ::= "(:" group ") " INT [" ~" INT " first_n"] [" co " pair (", " pair)*] [" via " link (", " link)*]
link      ::= "(:" group ")-" name
edge      ::= INDENT "-" name "-> " target (" " stat)* [" ^" | " …"] NL edge*   (* INDENT = 2 × level, level 1..3; a hop is one edge; nested edges follow only an edge at level 1 or 2; a level-3 edge into a nested group ends " …" or " ^" *)
target    ::= alt ("|" alt)* | "."
alt       ::= "(:" gref ("|" gref)* ")" | name | "IRI" | "BNODE"   (* the class part comes first, once *)
gref      ::= group [" @" name]                       (* @graph: typed in another graph *)
group     ::= name ("&" name)*                        (* & binds tighter than | *)
pair      ::= name " " INT
stat      ::= INT "/" INT | "×" INT ["-" INT] | "bn" | "@" (INT | LANG) | "=" VALUE | "=" name | VALUE ".." VALUE | "d" INT | "presence"   (* "=" name: the one IRI value, from top values *)
glossary  ::= "# glossary: none" NL | "# glossary" NL entry*
entry     ::= name (" " STRING ["@" LANG] [": " TEXT] | ": " TEXT) NL
name      ::= PNAME | "<" IRI ">"
VALUE     ::= a lexical form, non-empty, ≤64 chars, without white space, '"' or ".." | a JSON string (cut at 64 + "…")
```

### D. ShExC mapping (`shex.shex_view`)

| Pattern view | ShExC |
|---|---|
| `prefixes` | the same `PREFIX` lines |
| legend | exactly `# comments use the pattern schema's legend: k/n instances having p (omitted: all) · ×a-b values per instance (omitted: 1) · bn blank nodes · @n languages, @tag one language · =v one value · lo..hi range · dN distinct values (omitted: all differ) · presence found, not measured · … deeper than 3 hops` |
| `hidden_classes` > 0 | `# hidden: n classes`. Header order: `PREFIX` lines, legend, hidden line, skipped line, then the shapes |
| block | `# ` + header, then `<shape> {`, the constraints, `}`. The shape is the first shown member's name. |
| edge | `<indent><property> <value>[ <cardinality>] ;`, then `  # <comment>` if and only if the comment is non-empty |
| inline nested group | `<indent><property> BNODE {` + (`  # <comment>` iff non-empty); its constraints at the next level; then `<indent>}` + (` <cardinality>` if any) + ` ;`, e.g. `  } {0,2} ;`. `<indent>` is 2 × level spaces (level 1 = 2 spaces); PyShExC accepts `p BNODE {  # c … } {0,2} ;` |
| value | one alternative: group with a block in this file → `@<shape>`; nested group expanded nowhere → `BNODE` (this wins over the next two); assigned nested group with `reaching_edges` = 1 → `BNODE {` … `}` inline; assigned nested group with `reaching_edges` > 1 → `BNODE @<shape>`; other class → `IRI`; datatype → name; `IRI`/`BNODE`/`.` as is. Several, after de-duplication → `(a OR b …)`. |
| cardinality | from `min_count`, `max_count`: (1,1) → nothing; (0,1) → `?`; a = b > 1 → `{a}`; otherwise `{a,b}`; no histogram → `*` |
| comment | joined by single spaces: the `target` text when a target alternative is a class group; then the `stats` tokens (`=name` included); then `… deeper than 3 hops` for an edge into a group expanded nowhere. Empty when none applies (e.g. `owl:imports IRI ;`), and then no `#` is written |
| assigned nested group with `reaching_edges` > 1 | one shape per group after the block shapes: `# (:G) n`, then `<shape> BNODE {` … `}` |
| an edge at level 3 into a nested group expanded nowhere (pattern ` …`), however many edges reach it | `BNODE`, comment as above; no shape for that group; inline constraints never go below level 3, and a named nested shape's constraints start again at level 1 |
| glossary | each glossary line, with `# ` before it |
| a class or property IRI holding `=` | left out; `# skipped: <iri> <iri> …` once, after the legend and the hidden line |

### E. Worked example: whole-graph pattern schema, graph `continents` (the golden file's body)

The legend line and the trailing glossary are as in the spec. Prefixes resolve from the packaged
table (the sample profile has no `namespaces`). Without the legend line, the text is about 1,700
characters; `inputs/format-sizes.md` records the exact counts (task 1.12).

```text
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX euvoc: <http://publications.europa.eu/ontology/euvoc#>
PREFIX lvont: <http://lexvo.org/ontology#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX skosxl: <http://www.w3.org/2008/05/skos-xl#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
# (:A&B) n: classes with the same n instances · … (legend)
(:euvoc:Continent&skos:Concept) 6
  -dcterms:created-> xsd:date =2014-10-10
  -euvoc:startDate-> xsd:date =1952-07-24
  -euvoc:status-> IRI d1
  -euvoc:xlNotation-> (:euvoc:XlNotation) bn
    -dcterms:created-> xsd:date =2014-10-10
    -dcterms:type-> IRI d1
    -euvoc:startDate-> xsd:date =1952-07-24
    -euvoc:status-> IRI d1
    -rdf:value-> xsd:string AFRICA..OCEANIA
  -skos:inScheme-> (:owl:Ontology&skos:ConceptScheme) d1
  -skos:topConceptOf-> (:owl:Ontology&skos:ConceptScheme) d1
  -skosxl:prefLabel-> (:skosxl:Label) ×24 bn
    -dcterms:created-> xsd:date =2014-10-10
    -dcterms:type-> IRI d1
    -euvoc:startDate-> xsd:date 1952-07-24..2014-10-10 d2
    -euvoc:status-> IRI d1
    -lvont:script-> IRI 12/145 d2
    -skosxl:literalForm-> rdf:langString @24
(:owl:Ontology&skos:ConceptScheme) 1 via (:euvoc:Continent&skos:Concept)-skos:inScheme, (:euvoc:Continent&skos:Concept)-skos:topConceptOf
  -dcterms:created-> xsd:date =2014-10-10
  -dcterms:identifier-> xsd:string =http://publications.europa.eu/resource/authority/continent
  -euvoc:startDate-> xsd:date =2014-10-10
  -euvoc:status-> IRI
  -owl:imports-> IRI
  -rdfs:comment-> rdfs:Literal =Continent
  -skosxl:prefLabel-> (:skosxl:Label) bn ^
# glossary: none
```

How the rules play out here:
- **N2.** 6 = 6 = 6, so `euvoc:Continent` and `skos:Concept` are one block.
- **P-3.** `owl:Ontology` is a meta class, hidden by default, yet it stays in the group name: its
  group has the shown member `skos:ConceptScheme`.
- **N7.** `skosxl:Label` is reached by 144 + 1 blank nodes, so it is nested. It is expanded under
  the 144-triple edge; the scheme's edge ends `^`.
- **N5.** `=2014-10-10` is written instead of `d1 2014-10-10..2014-10-10`.

**Treaties excerpt** (lines of the `euvoc:Treaty&skos:Concept` block: self links in `via`,
coverage, histograms, and a `^` on the 2040-triple `altLabel`, because the 2489-triple
`prefLabel` wins):
```text
(:euvoc:Treaty&skos:Concept) 104 via (:euvoc:Treaty&skos:Concept)-dcterms:isReplacedBy, (:euvoc:Treaty&skos:Concept)-dcterms:replaces
  -dcterms:created-> xsd:date 2011-05-19..2018-05-17 d10
  -dcterms:replaces-> (:euvoc:Treaty&skos:Concept) 22/104
  -eli:date_document-> xsd:date 83/104 1951-04-18..2012-02-02 d30
  -euvoc:officialJournalSeries-> xsd:string 92/104 C..P d3
  -euvoc:signatureLocation-> IRI 74/104 ×1-2 d13
  -euvoc:xlChangeNote-> (:euvoc:XlNote) 1/104 bn ^
  -euvoc:xlDefinition-> (:euvoc:XlNote) 6/104 ×1-2 bn
    -dcterms:source-> rdf:langString 10/12 @2 d3
    -rdf:value-> rdf:langString @2
  -euvoc:xlNotation-> (:euvoc:XlNotation) ×1-6 bn
    -rdf:value-> xsd:string 11951K..UNION d317
  -lemon:context-> IRI ×1-2 d2
  -skosxl:altLabel-> (:skosxl:Label) 56/104 ×1-74 bn ^
  -skosxl:prefLabel-> (:skosxl:Label) ×23-24 bn
    -lvont:script-> IRI 386/4530 d2
    -skosxl:literalForm-> rdf:langString @24 d4176
```

**ShExC, same graph (excerpt)**:
```shex
# (:euvoc:Continent&skos:Concept) 6
euvoc:Continent {
  dcterms:created xsd:date ;  # =2014-10-10
  euvoc:status IRI ;  # d1
  euvoc:xlNotation BNODE {  # (:euvoc:XlNotation) bn
    rdf:value xsd:string ;  # AFRICA..OCEANIA
  } ;
  skos:inScheme @skos:ConceptScheme ;  # (:owl:Ontology&skos:ConceptScheme) d1
  skosxl:prefLabel BNODE @skosxl:Label {24} ;  # (:skosxl:Label) ×24 bn
}
# (:skosxl:Label) 145
skosxl:Label BNODE {
  lvont:script IRI ? ;  # 12/145 d2
  skosxl:literalForm rdf:langString ;  # @24
}
# glossary: none
```

**Glossary with the label fixture** (`tests/test_data/ontology/labels.ttl`, written for the
tests; the texts are fixture data and are not claimed to be the published vocabularies' wording):
```text
# glossary
dcterms:created "Date Created"@en: Date of creation of the resource.
skos:Concept "Concept"@en: An idea or notion; a unit of thought.
skosxl:Label "Label"@en: A special class of lexical entities.
skosxl:prefLabel "preferred label"@en
```
The fixture also holds:
- `euvoc:Treaty` labelled only `"Vertrag"@de` and `"Traité"@fr`, so the smallest-tag rule shows
  `@de`;
- `skosxl:altLabel` with only `skos:altLabel "alternative label"@en`;
- one description longer than 200 characters on `dcterms:type`.

### Anti-patterns

| Don't | Do instead | Why |
|---|---|---|
| Build a dict for a block or an edge | Generated `views.py` classes; `model_copy(update=…)` | `tests/guards/test_no_composed_dicts.py` |
| Compute stat tokens or merges in the Jinja template | `domain/patterns.py`, `domain/shex.py` | Domain is 100% branch-covered and mutation-tested; templates are not |
| Query the endpoint, or call `fingerprint_report`/`collect`, from a generator | Load `profile.json` only | DEC-2 |
| Hard-code `lvont`, `euvoc`, … in code or tests | Names from the prefix table; facts from `tests/sample_data.py` | Prefixes are resolved per profile |
| Add labels to `tests/test_data/*-source-ap.rdf` | `tests/test_data/ontology/labels.ttl` and builders | The canonical dataset never takes edge cases (lean-test-suite DEC-5) |
| Edit `pattern-*.txt`, `shex-*.shex` or `sample-profile.json` by hand | `make refresh-golden`, `make refresh-sample-profile` | `development.adoc` "Canonical data" |
| Parse ShExC at runtime, or add `pyshexc` to the runtime dependencies | Parse in tests only | DEC-27 |

## Test case specifications

Every spec scenario is a Gherkin scenario with the same title (the traceability guard,
`tests/guards/test_traceability.py`, counts this change's deltas once `tasks.md` exists). The
tables below hold only the checks that no scenario owns, in the tier that decides them
(`development.adoc` "Tiers"). Facts come from `tests/sample_data.py` (`CONTINENTS`, `TREATIES`);
edge cases come from `tests/builders.py` (`klass`, `prop`, `literals`, `resources`,
`profile_run`) or `sample_run.model_copy`.

### Scenario → feature map

| Capability (delta) | Feature file | Scenarios | Use case tag | Stage, task |
|---|---|---|---|---|
| statistics-collection, ADDED "Term labels and descriptions are collected" | `tests/features/statistics_collection.feature`, Rule "Labels and descriptions of the profiled terms are collected" | Labels and descriptions of a class are stored; Label predicate priority; Annotations from another graph; Property annotations need depth properties; A failed annotation query keeps the graph | `@uc_w1` (feature) | 1, task 1.3 |
| statistics-collection, MODIFIED "Depth and switches select the queries" | same file, Rule "Depth and switches decide what is measured" | Default depth; Graph statistics on; Measurements per depth | `@uc_w1` | 1, task 1.3 |
| profile-representations, ADDED "Pattern view" | `tests/features/profile_representations.feature`, Rule "The pattern view follows the profile's links…" | A chain deeper than three hops; A blank-node cycle is expanded once; A class with unreached instances keeps its block; An object type from another graph | `@uc_b2_1` | 1, task 1.8 (the steps run the generator) |
| ADDED "Pattern schema output" | same, Rule "The pattern schema is compact…" | Lines of the continents pattern schema; One block per class group and one edge per property; Values that need quotes; A single IRI value is written as a prefixed name; A class read in first-N mode; Unusual IRIs in the LLM outputs | `@uc_b2_1` | 1, tasks 1.6–1.8 |
| ADDED "Enriched ShExC output" | same, Rule "The enriched ShExC says the same…" | The ShExC output parses; Lines of the continents ShExC | `@uc_b2_1` | 1, task 1.9 |
| ADDED "Term labels and descriptions in the outputs" | same, Rule "Terms carry labels…" | Labels from an ontology file; The ontology wins for the fields it gives; The label shown; Unreadable ontology file; A profile saved before term annotations | `@uc_b2_1` | 1, tasks 1.5, 1.8 |
| ADDED "Size filters" | same, Rule "Size filters prune…" | Small classes hidden; Only the largest classes | `@uc_b2_1` | 1, task 1.8 |
| MODIFIED "Generators share one framework", "Golden outputs", "No files for empty graphs" | same file, existing Rules | Custom template package; Golden file per output (+2 rows); Empty default graph | `@uc_b2_1` | 1, task 1.10 |

### Unit tests (the branches the scenarios do not reach)

| Test ID | Tier / file | Input | Expected | Edge cases |
|---|---|---|---|---|
| TC-A1 | `tests/unit/domain/test_annotations.py` | values in 3 languages across 5 predicates | per-language priority, altLabel only as fallback, smallest text | untagged only; description only; no values → no entry |
| TC-A2 | same, Hypothesis (`strategies.py` + `annotation_values()`) | any list of values | `select(select-as-values(x)) == select(x)`; result independent of input order; ≤1 text per language per field | empty list |
| TC-A3 | same | ontology and data entries | P-7 per-field precedence | term only in one source; ontology entry with descriptions only |
| TC-P1 | `tests/unit/domain/test_patterns.py` | builder groups: transitive A=B=C; partial co-type 3 of 6 | one block `(:A&B&C)`; header ` co ex:C 3` | first-N class never merged |
| TC-P2 | same | nested-test inputs | P-4 thresholds: sum < instances → block; one IRI partition → block | `distinct_objects` absent → `triples` used |
| TC-P3 | same | expansion ties | equal triples → source name, then property name decides | same group reached at levels 1 and 2 → level 1 wins |
| TC-P4 | same | stat tokens | each token's omission rule (table §B.5); `@en` versus `@2`; `presence`; `.` target; mixed `(:A)\|xsd:string\|IRI\|BNODE` | `min_value` absent → no range; `rdf:langString` → no range |
| TC-P5 | same | filters | P-3 hidden members still named; `via` drops hidden sources; `hidden_classes` count | max_classes tie broken by name; a nested group reached only from a hidden block, and one reached only through its own cycle, both counted in `hidden_classes` |
| TC-P6 | same, Hypothesis | random small profiles (builders) | every declared prefix is used; no property twice in a block; nesting depth ≤ 3; every nested group expanded at most once | empty graph → no blocks |
| TC-P7 | `tests/unit/domain/test_patterns.py` | `klass`/`prop`/`resources` from `tests/builders.py`, then `model_copy(update={"top_values": [ValueCount(value=…, triples=…)]})` | `=name` only when every partition is `iri`, `distinct_objects` = 1 and `top_values` is set; its prefix is declared; an IRI no prefix covers is `=<iri>` | no top values → `d1`; a literal property keeps `=v` from `min_value`; mixed IRI and literal objects → no `=name` |
| TC-S1 | `tests/unit/domain/test_shex.py` | views with 0, 1, 2 reaching edges; a nested group reached by 2 edges, both at level 3; cardinalities (0,1),(1,1),(3,3),(0,74), none; edges with and without comment parts | inline versus named shape; the group expanded nowhere gets no shape and both edges are `BNODE` with `… deeper than 3 hops`; `?`, none, `{3}`, `{0,74}`, `*`; `(a OR b)` de-duplicated; `owl:imports IRI ;` has no `#`, `skos:inScheme @skos:ConceptScheme ;  # (:owl:Ontology&skos:ConceptScheme) d1` has one | `=` IRI → `# skipped:`; a level-3 `BNODE` edge with no statistics still gets `# … deeper than 3 hops` |
| TC-Q1 | `tests/unit/adapters/test_queries.py` (existing) | `render("Q12", g, terms=terms_values([...]))`; `render("Q12", g)` with the default `terms=""` | VALUES holds `<…>`s; an IRI with a space raises `IriRefError` | `terms_values([])` is `""` (rendered, but collection never sends it) |
| TC-O1 | `tests/unit/adapters/test_ontology_file.py` | `labels.ttl`; the same in RDF/XML; a missing file; a non-RDF file | values incl. the skosxl path; `OntologyFileError` naming the file | unknown extension → Turtle |
| TC-C1 | `tests/unit/service_layer/test_collection.py` (existing) | `FakeSparql` | Q12 sent once per graph after the classes; terms skip unwritable IRIs; not sent at depth `graphs`; not sent for a graph with no class (stores `[]`); `None` after a failure | transient error retried by the client |
| TC-G1 | `tests/unit/service_layer/test_representations.py` (existing) | `GeneratorOptions(ontology=<bad path>)`; `min_instances=0` | `UsageError` before any write | no ontology: the run's annotations pass through unchanged |
| TC-E1 | `tests/unit/entrypoints/test_generate.py` (existing) | `gen_pattern --min-instances 0` | exit 2 | `--ontology` passed through |

### Integration and output tests

| Test ID | Tier / file | Setup | Verification | Teardown |
|---|---|---|---|---|
| IT-1 | `tests/e2e/test_queries.py` (existing parametrised `test_query_runs` gains Q12 automatically) + new `test_term_annotations_of_the_scheme` | `make oxigraph-load-test-data` | Q12 for `<http://publications.europa.eu/resource/authority/continent>` returns `skosxl:prefLabel "Continent"@en` and `rdfs:comment "Continent"`, once each (DISTINCT over the union-default store) | none (read-only) |
| IT-2 | `tests/e2e/test_collection.py` (existing drift test) | the store, after `make refresh-sample-profile` | a live collection equals the sample profile, `term_annotations` included | none |
| IT-3 | `tests/unit/service_layer/test_representations_golden.py::test_golden_output` (existing, parametrised over `set(GENERATORS) - {"pitfalls"}`, so `pattern` and `shex` join it with no change; their files go in `tests/test_data/golden/`, not `golden/scanned/`) | `make refresh-golden` writes `pattern-{default,continents-214e8f67,treaties-3b4301a8}.txt` and `shex-….shex` | text equality; no unmatched golden file | none |
| IT-4 | `make check-mutation` | — | score ≥ `tests/guards/mutation_score.txt` (0.950) with the new domain and service modules | survivors get a test in the owning tier, or the dead code goes (lean-test-suite task 7.5 practice) |

## Error matrix

"Existing" means the message the 3.1 code already prints; it is not changed. Logging goes to
stderr through `configure_logging()`.

| Failure mode | How it is detected | Expected handling | Log level | Message (exact; `{…}` filled in) |
|---|---|---|---|---|
| `--ontology` file missing, unreadable or not RDF | `OntologyFileError` in `load_ontology` | `UsageError` → exit 2; nothing written | none (click prints the usage error) | `ontology file {path} cannot be read: {reason}` |
| `--min-instances`/`--max-classes` < 1 | `click.IntRange(min=1)`; `validate_options` for library callers | exit 2 / `UsageError` before any write | none | click's own range message; library: `--min-instances must be at least 1` / `--max-classes must be at least 1` |
| Profile missing, not JSON, not a profile | `ProfileFileError` (existing) | exit 2 | none | existing |
| Profile saved by 3.0 or 3.1 (no `term_annotations`) or before 3.0 (no `namespaces`) | field is `None` | treated as `[]`; namespaces resolved without fetching (existing) | none | — |
| Profile written by a newer version (unknown field) | `ValidationError` (`extra=forbid`) | exit 2 | none | existing ("… written by rdf-fingerprinter …") |
| Q12 timeout, rejection or unreachable after start | `SparqlError` from `_run` (403 after Q0 counts as permanent, existing) | `Failure(term_annotations)`; graph kept with `term_annotations` `None`; run exits 1 | WARNING (`_Collection.fail`) | `graph {graph or 'default'}: term annotations not read: {error}` |
| Q12 transient (429/502/503) | SPARQL client (existing) | retried 1 s, 4 s; then as a timeout | existing | existing |
| Q12 too large for the endpoint (HTTP 400/413 on a long VALUES) | `PermanentError` | as the Q12 rejection row | WARNING | as the Q12 rejection row |
| Term IRI unusable in a query | `to_iriref` raises | dropped from Q12's VALUES; no extra failure | none | — |
| Class/property IRI fails the IRIREF guard | `Generator.accepts` / builder step 1 | left out, listed in `skipped` | WARNING | existing: `skipping {iri!r}: it cannot be written as an IRI` |
| IRI with `=` in ShExC | `"=" in iri` | left out of the ShExC, `# skipped:` line; the pattern schema keeps it as `<…>` | WARNING | `skipping {iri!r} in ShExC: PyShExC rejects '=' in an IRI` |
| Template package missing or broken | `TemplatePackageError` (existing) | `UsageError` → exit 2 | none | existing |
| Generated ShExC does not parse | Gherkin "The ShExC output parses" and the golden test, in CI | fix the mapping in `domain/shex.py`; no runtime check (DEC-27) | — | PyShExC's own error, in the test output |

## Stage exit criteria

| Stage | Done when |
|---|---|
| 1. Schema outputs and labels | Every profile-representations and statistics-collection scenario of this change passes. Six golden files are checked in. `sample-profile.json` is refreshed (`term_annotations: []` on each graph, unless the refresh finds labels, which then become named facts in `tests/sample_data.py`). `make check-all` and `make test-e2e` are green, and `make check-mutation` is ≥ 0.950. `inputs/format-sizes.md` records the sizes (DEC-8). The docs of task 1.13 build (`make build-docs`). |
| Release | Stage 1 done; task 1.15 merges the PR, tags `3.2.0` and publishes the GitHub Release (DEC-12, confirmed in Round 6). |

## Risks / Trade-offs

- **[Risk] Gherkin scenarios exist before their steps.** Once `tasks.md` exists, the traceability
  guard counts this change's deltas, so the feature scenarios are committed with this PLAN. The
  new scenarios in the two bound feature files (`profile_representations.feature`,
  `statistics_collection.feature`) fail with missing steps until tasks 1.3, 1.8, 1.9 and 1.10
  land (tasks.md, "Still red until bound"). → Mitigation: the first implementation
  commits bind and implement stage-1 steps, and the branch is not merged before the stage-1 exit.
- **[Risk] Mutation score.** `patterns.py` has many small conditions, so it yields many mutants.
  → Mitigation: TC-P4/TC-P6 are written per token rule, and `make check-mutation` runs in task 1.14.
- **[Risk] Arrow notation may lead a model to write Cypher** (`inputs/pattern-schema-option.md`
  §7). → The legend says that arrows are triple-pattern notation;
  this is not measured (no evaluation, DEC-18).
- **[Trade-off] Q12 scans every graph for annotations** (Q4's pattern). On large union stores
  this is one more full lookup per graph, bounded by the VALUES list.
- **[Trade-off] Nested-group statistics are class-level**, over all of the group's instances, not
  per path (DEC-15). The legend states this.

## Open Questions

None blocks the PLAN. The developer is asked the one below. Implementation proceeds on the
recommended default; if the answer differs, only the tests named change.

| # | Question | Recommended default (implemented) | What changes otherwise |
|---|---|---|---|
| OQ-1 | DEC-17 says the description is "the first of `skos:definition`, `rdfs:comment`, `dcterms:description`, `skos:scopeNote` that the term has, one value per language". Is "first" chosen **per language** (§A: for each language, the highest-priority predicate with a value in it), or **per term** (the first predicate the term has at all, then its values per language)? The same applies to the labels of DEC-20. | **Per language.** A term with `skos:prefLabel "Human"@en` and `rdfs:label "Personne"@fr` keeps both, so a French question still finds it. | `select_annotations` and TC-A1/TC-A2; one new row in `statistics-collection › Label predicate priority`. |

OQ-2 and OQ-3 (both about `validate_query`) moved to `llm-schema-server` with DEC-24 (DEC-28).

## References

| Topic | Location | Anchor |
|---|---|---|
| EPIC decisions | `openspec/changes/llm-schema-tools/proposal.md` | "Key decisions" |
| Rules N1–N9, seed grammar, ShExC mapping | `openspec/changes/llm-schema-tools/inputs/pattern-schema-option.md` | "Refined format", "Secondary form" |
| Answers, rounds 1–6 | `openspec/changes/llm-schema-tools/inputs/qa-round-1.md` | "Round 5 answers", "Round 6 answers" (the split) |
| Generator framework | `openspec/specs/profile-representations/spec.md` | "Generators share one framework", "Namespace filters" |
| Depth table, query templates | `openspec/changes/archive/2026-10-31-harden-fingerprinter/design.md` | "Query templates" |
| Test tiers, canonical data, gate | `docs/modules/ROOT/pages/development.adoc` | `#test-tiers`, `#test-data`, `#test-gate` |
| Lean test decisions | `openspec/changes/archive/2026-11-01-lean-test-suite/proposal.md` | DEC-1 to DEC-9 |
| Use cases | `docs/modules/ROOT/pages/use-cases/ucw2.adoc`, `ucb2-1.adoc`, `ucw1.adoc` | `#uc-w2`, `#uc-b2-1`, `#uc-w1` |
| The split-off server change | `openspec/changes/llm-schema-server/proposal.md`, `inputs/carried-over-design.md` | DEC-28 |
| Layer contracts | `.importlinter` | `[importlinter:contract:*]` |
| Release rules | `AGENTS.md` | "Release authority" |
