> Derives from: EPIC llm-schema-split (`proposal.md`, DEC-1 to DEC-9). Parent change: `../archive/2026-11-02-llm-schema-tools/`.

## Context

3.2 writes the pattern schema as `pattern-<slug>.txt`, rendered by `PatternGenerator`
(`fingerprint/service_layer/generators/pattern.py`) from the `PatternGraph` that
`fingerprint/domain/patterns.py::pattern_view` builds, through the one template
`fingerprint_report_templates/pattern_schema/templates/schema.txt`. The same view feeds the ShExC
(`fingerprint/domain/shex.py`), which reuses the glossary lines (`GlossaryEntry.line`).

Term annotations come from two sources that both yield `AnnotationValue` rows (term, predicate,
text, language) and both go through `select_annotations` (`fingerprint/domain/annotations.py`):
Q12 (`fingerprint/adapters/queries/q12_term_annotations.rq`) at collection time, and
`load_ontology` (`fingerprint/adapters/ontology_file.py`) at render time; `merge_annotations`
applies the ontology-wins rule. The selected values sit in `TermAnnotation(term, labels,
descriptions)` (`model/fingerprint_stats.yaml`).

The renderer (`fingerprint/adapters/template_renderer.py`) renders one template per package (the
package's `config.json` `template`) for every `(file name, view)` output, with the filters of
`filters(prefixes)`. The template loader is a file-system loader over the package's `templates/`,
so `{% include %}` of a sibling template works (the report's `main.html` already extends
`layout.html`).

## Goals / Non-Goals

**Goals:** the five files of DEC-1 from the one view; typed CSV rows (DEC-2, DEC-4, DEC-5); the
annotation model and selection of DEC-5; 3.x profiles load (DEC-9); release 3.4.0 (DEC-1, R4-1).

**Non-Goals:** everything in the EPIC's No-gos; a runtime CSV parse check (the tests parse every
CSV; the cells are quoted by one tested function).

## Decisions

- **P-1 One package, one entry template, five sub-templates.** `pattern_schema/config.json` keeps
  one `template`, now `files.j2`, whose whole body is `{% include view.template %}`. Each output's
  view is a new `PatternFile(template, graph)`: `template` is the sub-template's file name
  (`prefixes.md`, `patterns.md`, `patterns.csv`, `glossary.md`, `glossary.csv`), `graph` the
  `PatternGraph`. The generator emits five `(file name, PatternFile)` pairs per graph. Why: the
  renderer, the `--template` option and "Custom template package" stay as they are. Rejected: five
  packages (the generator would call the renderer five times and `--template` would need five
  folders); building CSV text in Python outside the renderer (a second output path).
- **P-2 CSV cells are quoted by one filter, `csv_cell`.** A pure function in
  `fingerprint/domain/patterns.py`, registered in `filters()`: `None` → empty; `True`/`False` →
  `true`/`false`; an `int` → its digits; a `list` → its items' text joined with ` | ` (DEC-6); then
  any text holding `,`, `"`, `\r`, `\n` or a leading/trailing space is wrapped in `"` with each
  `"` doubled (RFC 4180). The templates join cells with `,` and end each row with `\n`. Why: one
  tested function decides quoting for both CSVs and custom templates. Rejected: Python's `csv`
  module (it writes whole rows, not cells inside a template).
- **P-3 The view carries typed facts; the templates only lay them out.** `PatternEdge` gains the
  typed fields of §B; `PatternBlock` needs nothing new (it has `name`, `instances`, `observed`,
  `via`); `PrefixDeclaration` gains four optional counts (§C); `GlossaryEntry` gains
  `kinds` and `rows` (§D). The 3.2 text fields (`text`, `header`, `line`) stay, so the `.md` lines
  and the ShExC are unchanged except where the specs say.
- **P-4 Annotation model** (DEC-5, DEC-9). `TermAnnotation` keeps `labels` (now: pref labels only)
  and `descriptions` (now: definitions only) under the same names, so a 3.x profile loads with no
  migration, and gains `alt_labels` and `notes` (`LangText`, multivalued, optional).
- **P-5 Order of multi-valued cells.** Alt labels and notes are sorted by text within a language
  and de-duplicated (DEC-6 "values sorted").

## Layering and modules

| Layer | File | Change |
|---|---|---|
| model | `model/fingerprint_stats.yaml` | `TermAnnotation.alt_labels`, `.notes` |
| model | `model/fingerprint_views.yaml` | `PatternFile`; new `PatternEdge`, `PrefixDeclaration`, `GlossaryEntry` slots; `GlossaryRow` |
| domain | `vocabulary.py` | `ALT_LABEL_PREDICATES`, `NOTE_PREDICATES`; `TERM_DESCRIPTION_PREDICATES` loses `skos:scopeNote` |
| domain | `annotations.py` | `select_annotations`, `merge_annotations`, `shown` per §A |
| domain | `patterns.py` | typed edge facts, prefix counts, glossary rows and line, `csv_cell` |
| adapters | `queries/q12_term_annotations.rq`, `ontology_file.py`, `template_renderer.py` (`csv_cell` filter) | §A, P-2 |
| service | `generators/pattern.py` | five outputs per graph (P-1) |
| templates | `fingerprint_report_templates/pattern_schema/templates/` | `files.j2` + five sub-templates; `schema.txt` deleted |

`make generate-models` regenerates `fingerprint/domain/profile.py` and `views.py`. No import
crosses a layer it did not cross before (`make check-architecture`).

## Algorithm / approach

### A. Term annotations (DEC-5; statistics-collection delta)

Predicates (`vocabulary.py`):
- `TERM_LABEL_PREDICATES` = `skos:prefLabel`, `skosxl:prefLabel` (via `skosxl:literalForm`),
  `rdfs:label`, `dcterms:title` (unchanged).
- `ALT_LABEL_PREDICATES` = `skos:altLabel`, `skosxl:altLabel` (via `skosxl:literalForm`).
- `TERM_DESCRIPTION_PREDICATES` = `skos:definition`, `rdfs:comment`, `dcterms:description`.
- `NOTE_PREDICATES` = `skos:scopeNote`, `skos:note`, `skos:example`, `skos:editorialNote`,
  `skos:historyNote`, `skos:changeNote`.

Q12 lists every plain predicate above in its `VALUES ?p`, and gains a second `skosxl` branch for
`skosxl:altLabel/skosxl:literalForm` with `BIND(skosxl:altLabel AS ?p)`. `load_ontology` reads
the same set, resolving `skosxl:altLabel` through `skosxl:literalForm` as it does `prefLabel`.

`select_annotations(values)` per term:
- `labels` = `_per_language(rows, TERM_LABEL_PREDICATES)` — no alt-label fallback any more;
- `alt_labels` = every value of `ALT_LABEL_PREDICATES`, distinct `(language, text)`, sorted by
  language (untagged first) then text;
- `descriptions` = `_per_language(rows, TERM_DESCRIPTION_PREDICATES)`;
- `notes` = every value of `NOTE_PREDICATES`, plus every value of `TERM_DESCRIPTION_PREDICATES`
  that is not the chosen description of its language; distinct, sorted as `alt_labels`;
- the term is kept when any of the four is non-empty.

`merge_annotations` takes, per term and per each of the four fields, the ontology's list when it is
non-empty, else the data's.

Worked example (data, one term `ex:P`): `skos:prefLabel "Person"@en`, `skos:altLabel "Human"@en`,
`skos:altLabel "Body"@en`, `skos:altLabel "Mensch"@de`, `rdfs:comment "A human being"@en`,
`rdfs:comment "Also a legal person"@en`, `skos:scopeNote "Use for people"@en` →
labels `"Person"@en`; alt_labels `"Mensch"@de`, `"Body"@en`, `"Human"@en`; descriptions
`"A human being"@en` (smallest of the two comments); notes `"Also a legal person"@en`,
`"Use for people"@en`.

### B. Patterns: `patterns-<slug>.md` and `patterns-<slug>.csv`

New `PatternEdge` slots, set by `_Builder._spec`/`_edge` from facts the builder already reads:
`owner` (the name of the group whose profile the edge comes from), `path` (the property names of
the edges above it, from the block down), `triples` (`total_triples`), `subjects`
(`subjects_with_property`), `observed` (owner's `observed_instances` or `instances`),
`per_min`/`per_max` (`_values_per_subject`), `blank_nodes`, `languages` (sorted tags),
`min_value`/`max_value` (raw, for the one-literal-datatype case of `_literal_range`),
`single_value` (the raw `=v` value or the `=<name>` name), `distinct` (`distinct_objects`). Raw
means not quoted or cut: the CSV cell quoting does that job.

`patterns-<slug>.md`:

````text
# Patterns of continents

Prefixes: `prefixes-continents-214e8f67.md` · glossary: `glossary-continents-214e8f67.md`

Legend: (:A&B) n: classes with the same n instances · … (the 3.2 legend text, without its `# `)

## euvoc:Continent&skos:Concept

```text
(:euvoc:Continent&skos:Concept) 6
  -dcterms:created-> xsd:date =2014-10-10
  …
```
````

- `Hidden: <n> classes.` and `Excluded namespaces: <note>.` lines follow the legend when they
  apply (3.2: `# hidden:` / `# excluded namespaces:`).
- One `## <group name>` per block, in block order, then a ```` ```text ```` fence holding the
  block's 3.2 header line and edge lines, unchanged.

`patterns-<slug>.csv` header and columns (one row per block, `depth` 0, then one row per edge
line in `.md` order, depth-first):

| column | block row (depth 0) | edge row |
|---|---|---|
| `graph` | graph IRI, empty for the default graph | same |
| `block` | group name | the block it sits in |
| `owner` | group name | group whose profile gives the row |
| `path` | empty | property names above it joined by `/`, empty at depth 1 |
| `depth` | `0` | `1`–`3` |
| `property` | empty | prefixed name |
| `targets` | empty | alternatives in 3.2 order, groups without `(:`/`)`, ` \| `-joined |
| `target_kinds` | empty | `TargetKind` values, same order |
| `ending` | empty | `PatternEdge.ending` without its leading space: empty, `^` or `…` |
| `instances` | `instances` | owner's `observed` |
| `subjects` | empty | `subjects` |
| `triples` | empty | `triples` |
| `per_min`, `per_max` | empty | values per subject |
| `blank_nodes` | empty | `true`/`false` |
| `languages` | empty | tags, ` \| `-joined |
| `min_value`, `max_value`, `single_value` | empty | raw values |
| `distinct` | empty | `distinct` |
| `presence_only` | empty | `true`/`false` |
| `first_n` | `observed` when read first-N | empty |
| `via` | `source-property` pairs, ` \| `-joined | empty |

Worked rows, continents:

```text
graph,block,owner,path,depth,property,targets,target_kinds,ending,instances,subjects,triples,per_min,per_max,blank_nodes,languages,min_value,max_value,single_value,distinct,presence_only,first_n,via
http://…/continents,euvoc:Continent&skos:Concept,euvoc:Continent&skos:Concept,,0,,,,,6,,,,,,,,,,,,,
http://…/continents,euvoc:Continent&skos:Concept,euvoc:Continent&skos:Concept,,1,euvoc:startDate,xsd:date,datatype,,6,6,6,1,1,false,,1952-07-24,1952-07-24,1952-07-24,1,false,,
http://…/continents,euvoc:Continent&skos:Concept,skosxl:Label,skosxl:prefLabel,2,lvont:script,IRI,iri,,145,12,12,1,1,false,,,,,2,false,,
```

The exact numbers come from the sample profile; the golden files fix them (task 1.7).

### C. Prefixes: `prefixes-<slug>.md`

Rows: the view's `prefixes` (3.2 N8: the prefixes of every IRI the view writes), sorted by prefix.
Counts per prefix, over the view only:
- `classes`: distinct class IRIs in the namespace among the members of blocks and expanded nested
  groups;
- `properties`: distinct property IRIs in the namespace among the edges written, at any depth;
- `instances`: sum of those classes' `instances`, each class once;
- `triples`: sum of `triples` over the edge lines whose property is in the namespace (each line is
  one `(owner, property)`, so nothing is counted twice).

```text
# Prefixes of continents

| prefix | namespace | classes | properties | instances | triples |
|---|---|---:|---:|---:|---:|
| dcterms | <http://purl.org/dc/terms/> | 0 | … | 0 | … |
| xsd | <http://www.w3.org/2001/XMLSchema#> | 0 | 0 | 0 | 0 |
```

A `|` in a namespace is written `\|`.

### D. Glossary: `glossary-<slug>.md` and `glossary-<slug>.csv`

`GlossaryEntry` gains `kinds` (DEC-10: `C` for an IRI written as a class, `dP`/`oP`/`P` for one
written as an edge property, by its target kinds — `datatype` → `dP`; `group`, `iri`,
`blank_node` → `oP`; only `unknown` → `P`; both → `dP` and `oP` — and `D` for a datatype target;
the builder records them where it adds to `used`, in the order `C`, `dP`, `oP`, `P`, `D`) and `rows` (`GlossaryRow(language, pref_label,
alt_labels, definition, notes)`, one per language present in any of the four fields, untagged
first, then by tag). Entries: the terms the view writes that have any annotation (notes only
included), sorted by name (3.2 N9).

The `.md` line (`GlossaryEntry.line`, also the ShExC comment) is
`<name> <kinds joined by />[ "<label>"[@<lang>]][ alt: "<a>" | "<b>"][: <description>]`:
- label = `shown(labels)`; when `labels` is empty, `shown(alt_labels)`;
- alt = the `alt_labels` in the label's language, without the one used as the label, JSON-quoted;
- description = `shown(descriptions)`, white space collapsed, cut at 200 characters with `…`;
- `line` is unset when all three parts are empty (a notes-only term). Such an entry gets CSV rows
  only; `glossary.md` and the ShExC write the entries that have a line, and treat "no entry with
  a line" as no glossary (`No term …` / `# glossary: none`).

```text
# Glossary of continents

- skos:Concept C "Concept"@en alt: "Notion": An idea or notion; a unit of thought.
- skosxl:prefLabel oP "preferred label"@en
```

With no entry the body is `No term of this graph has a label or a description.`

`glossary-<slug>.csv`, one row per entry and `GlossaryRow`:
`term,iri,kind,language,pref_label,alt_labels,definition,notes`, where `kind` is `kinds`
` | `-joined, `pref_label` and `definition` the one value in that language (or empty), and
`alt_labels`, `notes` the values in that language, ` | `-joined, full text (no cut, line breaks
kept inside the quoted cell).

### E. The label fixture grows

`tests/test_data/ontology/labels.ttl` gains, for `skos:Concept`: `skos:altLabel "Notion"@en,
"Begriff"@de`; `rdfs:comment "Also a SKOS class."@en` (a second description in `en`, so a note);
`skos:scopeNote "Use for concepts of a scheme."@en`. `skosxl:altLabel` keeps only its
`skos:altLabel`, which now yields no pref label.

### Anti-patterns

| Don't | Do instead | Why |
|---|---|---|
| Format statistics in a template | Read typed `PatternEdge` slots | The templates lay out only (3.2 P-2) |
| Re-parse the 3.2 token text for CSV columns | Set the typed slots where the tokens are made | Two sources of the same fact drift |
| Quote CSV cells by hand in a template | `csv_cell` | One tested rule (P-2) |
| Rename `labels`/`descriptions` | Keep the names, add fields | 3.x profiles must load (DEC-9) |
| Add a profile version field | Optional fields | No migration needed (DEC-9) |

## Test case specifications

### Scenario → feature map

Feature file `tests/features/profile_representations.feature` and
`tests/features/statistics_collection.feature`; titles equal the spec scenario titles.

| Spec scenario (capability › requirement) | Status |
|---|---|
| p-r › Pattern schema output › Five files per graph | new |
| p-r › Pattern schema output › Lines of the continents pattern schema | renamed file, glossary row moved |
| p-r › Pattern schema output › One block per class group and one edge per property | reworded |
| p-r › Pattern schema output › A single IRI value is written as a prefixed name | reworded |
| p-r › Pattern schema output › Values that need quotes, A class read in first-N mode, Unusual IRIs in the LLM outputs | unchanged titles; Unusual IRIs reworded |
| p-r › Prefix file › Prefix counts of the continents graph | new |
| p-r › CSV cells › Cell quoting (5 rows); Every CSV parses | new |
| p-r › Patterns CSV › Rows of the continents patterns CSV (5 rows) | new |
| p-r › Glossary CSV › Rows per language; A description is not cut in the CSV | new |
| p-r › Term labels and descriptions in the outputs › A term with only alt labels; A term with notes only; Alt labels in another language are not shown | new |
| p-r › Term labels and descriptions in the outputs › Labels from an ontology file; A profile saved before term annotations | reworded |
| p-r › Term labels and descriptions in the outputs › The ontology wins for the fields it gives; The label shown; Unreadable ontology file | unchanged |
| p-r › Enriched ShExC output › (2 existing) | unchanged |
| p-r › No files for empty graphs › Empty default graph; p-r › Size filters › Small classes hidden, Only the largest classes | reworded |
| s-c › Term labels and descriptions are collected › Label predicate priority | rows changed, a column added |
| s-c › Term labels and descriptions are collected › Alt labels and notes are stored | new |
| s-c › Term labels and descriptions are collected › the other 4 | unchanged |

### Unit tests (branches the scenarios do not reach)

- `csv_cell`: `None`, `True`, `0`, a list with an item holding `|`, a value with `,`, `"`, `\n`,
  a leading space, an empty list.
- `select_annotations`: a term with only notes is kept; duplicate alt labels collapse; a second
  `skos:definition` in one language becomes a note.
- `merge_annotations`: each of the four fields independently.
- Prefix counts: a prefix used only by a datatype gives zeros; a class in two groups is counted
  once.
- Glossary: a term written both as a class and an object property has `kind` `C | oP` and the
  line token `C/oP`; a property with literal and IRI objects is `dP | oP`; one with no
  collected objects is `P`; a
  notes-only term has CSV rows and no line, and alone gives `# glossary: none` in the ShExC.
- Q12 text holds every predicate of §A (adapter unit test on the query file).

### Integration and output tests

- IT-1 Golden files: the 15 new files (5 × `continents`, `treaties`, `default`) replace the 3
  `pattern-*.txt`; `make refresh-golden`, reviewed against §B–§D.
- IT-2 Every golden `.csv` parses with `csv.DictReader`, its header equals the column list, and
  every row has as many cells as the header.
- IT-3 e2e: `make oxigraph-load-test-data` + `make test-e2e` stay green; no e2e test reads
  `pattern-*.txt`, so none changes.
- IT-4 The ShExC goldens change only in glossary lines (none in the sample profile, so not at
  all); PyShExC parse still green.

## Error matrix

| Failure mode | How it is detected | Expected handling |
|---|---|---|
| Value with `,`, `"`, newline | `csv_cell` | Quoted per RFC 4180 (P-2) |
| Value containing ` \| ` in a multi-valued cell | — | Written as is; splitting is then inexact (DEC-6, accepted) |
| Namespace with `\|` in the prefix table | `prefixes.md` template | Written `\|` |
| Edge value holding three backticks | — | Accepted: values with spaces are JSON-quoted, bare values rarely hold backticks (Risks) |
| 3.x profile without `alt_labels`/`notes` | Pydantic optional fields | Loads; CSV cells empty (DEC-9) |
| Q12 rejected by the endpoint | existing `term_annotations` failure | Unchanged: graph kept, failure recorded |
| `--ontology` unreadable | existing `OntologyFileError` | Unchanged: exit 2, nothing written |
| A custom `--template` package written for 3.x | its own `config.json` template now gets `view` = `PatternFile`, five times per graph | **BREAKING** contract change, in the CHANGELOG (task 1.8): a custom package renders `view.graph` and may branch on `view.template` |
| A cell starting with `=`, `+`, `-` or `@` (endpoint data) | — | Accepted, not escaped: the CSV is data for tools, and escaping would change values; a spreadsheet user imports it as text |

Rendering is a pure function of the saved profile (and the ontology file): re-running writes the
same files byte for byte; it is safe to repeat.

## Stage exit criteria

`make check-all` (the fast gate) green; `make oxigraph-load-test-data` + `make test-e2e` green;
`openspec validate llm-schema-split --strict` green; no mutation run and no `check-all-deep` for
this change (developer, R4-2: a quick implementation and release); every scenario of the feature map bound and green.

## Risks / Trade-offs

- [Alt-label behaviour changes for 3.2 users] → the CHANGELOG `### Changed` names it
  **BREAKING**, in a MINOR release (DEC-1, R4-1).
- [Five files instead of one per graph] → `patterns.md` names the other two files in its second
  line, so an agent given one file finds the rest.
- [Notes make Q12 results and profiles larger] → only class and property IRIs are annotated
  (EPIC rabbit-holes).
- [Fence break by a value holding ```` ``` ````] → accepted; the CSV carries the raw value.

## Open Questions

None. Every column, separator and rule above follows from DEC-1 to DEC-9.

## References

- EPIC `proposal.md`; seeds `inputs/qa-round-1.md`.
- `../archive/2026-11-02-llm-schema-tools/design.md`, sections "B. Building the pattern view" and
  "C. Pattern grammar (final; replaces the seed's sketch)".
- `openspec/specs/profile-representations/spec.md`, requirements "Pattern view" and "Pattern
  schema output" (the living text the delta modifies).
- RFC 4180 (CSV).
