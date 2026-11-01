> Derives from: EPIC `namespace-filter` (`proposal.md`, DEC-1 to DEC-13). Document type: implementation.

## Context

The generators render a saved profile run (`ProfileRun`, `fingerprint/domain/profile.py`) through
one service, `generate_representations` (`fingerprint/service_layer/representations.py`). It
resolves the namespace table, re-reads the threshold, merges the ontology labels, calls
`analyse()`, then runs each generator on the resulting `ProfileAnalytics`. Every documented entry
point reaches it:
- `fingerprint`, through `fingerprint_report` in `fingerprint/service_layer/handlers.py` (lines 69
  and 72; the second call passes `check_filters=False`);
- every `fingerprint-gen-*` command, through `generate_from_profile_file`.

These four (`fingerprint`, `fingerprint-gen-*`, `fingerprint_report`, `generate_from_profile_file`)
are the documented API (`docs/modules/ROOT/pages/api-reference.adoc`). A `Generator` built directly
is not.

Today the namespace filter is class-level and decided in three places:
- `excluded_namespaces()` and `Generator.shown()` in
  `fingerprint/service_layer/generators/generator.py`;
- `_Builder._shown()` in `fingerprint/domain/patterns.py`;
- PlantUML's link test in `fingerprint/service_layer/generators/plantuml.py` (`overview`).

Names are matched by `PrefixTable.resolve()` (`fingerprint/domain/prefixes.py`): an exact prefix,
then an exact namespace IRI. The table covers every IRI of the run
(`fingerprint/service_layer/prefixes.py`, `used_namespaces`), so every term has a table entry.
Prefixes are unique case-insensitively: `resolve_namespaces` refuses a second holder of a prefix
that differs only in case (`fingerprint/service_layer/prefixes.py`, `holders`).

This change rewrites one requirement and extends another (spec deltas):
- `specs/profile-representations/spec.md`, MODIFIED "Namespace filters";
- `specs/fingerprint-report/spec.md`, MODIFIED "Navigation, search and filters".

They are projected into Gherkin in `tests/features/profile_representations.feature` (Rule
"Namespace filters choose the classes and terms shown") and `tests/features/fingerprint_report.feature`
(Rule "The report is one self-contained page"). The scenarios trace to UC-B2.1 (generate
representations from a saved profile) and UC-W2 (publish a fingerprint).

## Goals / Non-Goals

**Goals:** the matching rule (DEC-6), the two tiers (DEC-7), the term filter (DEC-8) applied once
(DEC-4), the notes and warnings (DEC-9), the report's table, caveats and switches (DEC-10), docs,
and release 3.3.0 (DEC-3).

**Non-Goals:** the EPIC's no-gos (`proposal.md`, "No-gos"). In particular: no change to
`model/fingerprint_stats.yaml` or to collection, no filtering of pitfalls or collection failures,
no config-file filters, no class- or property-level filter, no change to `patterns.py`'s grouping
rules beyond what the filtered analytics give them, and no term-level filtering for a `Generator`
built directly.

## Decisions

The EPIC settles the bet; these are the PLAN's choices.

| Id | Decision | Why | Rejected |
|---|---|---|---|
| P-1 | **Analyse the unfiltered run, then filter the analysed view.** `generate_representations` calls `analyse()` on the run as today (after `with_ontology`), then `exclude_terms(analytics, excluded, table)`, a pure domain function in a new module `fingerprint/domain/namespace_filter.py`. It removes the excluded terms from the `ProfileAnalytics` and leaves every other value as analysed (apart from setting `excluded_terms` and `namespace_uses`), except the four value-type fields of a property that lost an object class (P-2). The full field list is §C. | DEC-4 (one place for the excluded tier). Analysing first keeps every indicator, inheritance included, as on the unfiltered profile: an inherited property stays inherited when its parent is excluded, so PlantUML (`DIAGRAMMED_INHERITANCE`) and the report's property groups do not change. Patching only four fields is less code than making `analyse()` filter-aware. | Filtering the `ProfileRun` before `analyse()`: it re-derives inheritance, class and graph aggregates (`own_property_count`, `mean_out_degree`, `class_count`, `vocabularies`, …) from the reduced run, so inherited properties would become own. Filtering in each generator: today's divergence. |
| P-2 | **An excluded object class is cleared from its value partition** (`object_class` and `object_class_graph` set to `None`); the partition, its triples and its node kind stay. The property's `value_types`, `dominant_value_type`, `type_purity` and `untyped_object_ratio` are then re-derived from its partitions by `value_type_indicators(partitions, total)`, extracted from `_partition_indicators` in `fingerprint/domain/analytics.py`, with `total = prop.total_triples or 0` (the value `property_analytics` passes). | The objects become untyped resources, which every output already writes as `IRI`, `sh:nodeKind sh:IRI` or `resource` (DEC-8). Re-using the analysis function keeps one formula. | Dropping the partition: it loses triples. Leaving `untyped_object_ratio` at 0: `shacl.py` `value_constraints` would then write an empty `sh:or ( )`. |
| P-3 | **Two sets in one value**, `NamespaceFilter` (LinkML, `model/fingerprint_views.yaml`): `hidden` (meta less included), `excluded` (matched by excludes less included), and `matches` (one `FilterMatch` per value: option, name, matched namespaces). DEC-4's "one place" covers the **excluded tier only**: `exclude_terms`. The **hidden tier** stays where it is today: `Generator.shown()`, `_Builder._shown()` and PlantUML's link test, fed with `Generator.excluded = hidden ∪ excluded`. | The meta tier must keep a hidden class's name in merged groups and edge targets (llm-schema-tools P-3), which the class tests already do; moving it would change every golden file. Including `excluded` in `Generator.excluded` gives a `Generator` built directly at least class-level hiding of what it excludes. | Moving the meta tier into `exclude_terms`: it would remove meta classes from names and targets (against llm-schema-tools P-3). |
| P-4 | **Matching lives on `PrefixTable.match(value) -> list[NamespacePrefix]`**, replacing `resolve()`; rule order and syntax as DEC-6. A stem compares with `str.startswith` (case-sensitive). A glob is compiled as `re.fullmatch("".join(".*" if part == "*" else re.escape(part) for part in re.split(r"(\*)", value)), prefix)` (case-sensitive). | The table already owns prefix and namespace lookup; `re.escape` makes `.`, `?`, `[` literal, so `*` is the only wildcard. Case-sensitive globs cannot miss a prefix that differs only in case, because no two prefixes do (Context). | `fnmatch` (it also treats `?` and `[…]` as wildcards, against DEC-6). |
| P-5 | **`exclude_terms` counts what it removes** and sets `GraphAnalytics.excluded_terms` on each graph: one `ExcludedTerms` (namespace, classes, properties, values) per namespace with a non-zero count, sorted by namespace. `ExcludedTerms` and the attribute are LinkML, in `model/fingerprint_analytics.yaml`. | Analytics are not saved, so `profile.json` and its schema do not change (DEC-1, no-go). Counting in the same walk that removes means the counts cannot disagree with what was removed. | A field in `model/fingerprint_stats.yaml`: it would enter the saved profile's schema. A separate counting walk: two walkers to keep in step. |
| P-6 | **The note is one string per graph**, built once by `note_text(terms, table)` in the domain module and carried as `GraphView.excluded_note` (a new optional attribute of the mixin every per-graph view has). Templates print `# excluded namespaces: {{ view.excluded_note }}` (`'` in PlantUML) when it is set. | Five templates print the same text; the rule for the text is in one tested function. | Building the text in each template. |
| P-7 | **The single-value position is exactly the value IRI an output writes:** `top_values[0].value` of a property whose value partitions are all `iri` and whose `distinct_objects` is 1, the condition of `_single_iri` (`patterns.py:195-199`; `_single_iri_value` in `service_layer/prefixes.py` uses the same one to find the namespaces to declare). When that value is excluded it is counted under values and **all** top values of the property are dropped (with one distinct object there is no other); in every other property the top values are left alone and not counted. | `ValueCount` holds no node kind, so a literal top value cannot be told from an IRI otherwise, and no output writes any other top value. | Treating every top value that parses as an IRI as one: it would drop literals that look like IRIs. |
| P-8 | **Warnings are emitted in `generate_representations` when `check_filters` is true**, so `fingerprint` logs each once (its second call passes `False`). Unknown: a `FilterMatch` with no namespaces. Hides nothing: an exclude `FilterMatch` whose namespaces still in `excluded` sum to 0 classes, properties and values over every graph's `excluded_terms`. | Once per run (spec). `warn_unknown_filters` already sits there. | Warning inside each generator: repeated per format. |
| P-9 | **The report** (`DocumentGenerator`): each `DocumentProperty` gets `prefix` (the table prefix of the property, `""` when none); the template gives each row `data-ns="{{ p.prefix }}"`; the switch list is the sorted, non-empty prefixes of shown classes and shown properties, so **`""` gets no switch** and a row with `data-ns=""` is never hidden by a switch; `PrefixDeclaration.excluded` marks table rows, and the table's uses come from `ProfileAnalytics.namespace_uses` (counted on the unfiltered analytics, §B "Namespace uses"), so an excluded namespace shows its real uses and keeps its place in the order; `ProfileDocument.switches` (new, multivalued string; the template's `<fieldset>` reads it instead of computing `totals.prefixes`) holds the switch list; `Caveats.excluded` lists `ExcludedGraphNote(graph, note)`; `DocumentGraph.empty` is true only when the graph had no class partition **and** no excluded class. The sentence for a graph whose shown classes are all gone becomes exactly: `Every class of this graph is in a hidden or excluded namespace (see caveats).` | DEC-10. A prefix-less term cannot be named by a filter value of rule 2 or 3, and the page must read fully without its script (fingerprint-report "One self-contained page"). | Computing the switch list in JavaScript. A switch labelled with an empty name. |
| P-10 | **Goldens:** the golden test runs with default options, where no namespace is excluded, so only `tests/test_data/golden/main.html` and `golden/scanned/main.html` change (rows gain `data-ns`, the switch list gains property-only prefixes). No new golden file: the filter scenarios own the filtered outputs. | One tier per check (lean-test-suite DEC-2). | A filtered golden set: it would duplicate the scenarios. |
| P-11 | Release **3.3.0** (SemVer MINOR): no option, command or saved field is removed. Two reaches change, both under "Changed" (DEC-5): `--exclude-namespace` leaves out every term; a full namespace IRI is now a stem, so it also matches the namespaces under it (`http://example.org/` used to match only that namespace). | Release authority in `AGENTS.md`; DEC-3. | 4.0.0: no existing call fails. |
| P-12 | **Collection failures are not filtered** (`ProfileAnalytics.failures`: `class_iri`, `property`), like pitfall findings (DEC-11): the report's collection section still lists a failure on an excluded term. | A failure says what could not be measured; hiding it hides a gap in the data. | Dropping failures on excluded terms. |

## Layering and modules

| Layer | Module | Change |
|---|---|---|
| domain (model) | `model/fingerprint_views.yaml` → `fingerprint/domain/views.py` | `FilterOption` enum (`exclude`, `include`); `FilterMatch` (option, name, namespaces); `NamespaceFilter` (hidden, excluded, matches); `GraphView.excluded_note`; `Caveats.excluded` → `ExcludedGraphNote` (graph, note); `PrefixDeclaration.excluded` (boolean); `DocumentProperty.prefix`; `ProfileDocument.switches`; new descriptions for `GeneratorOptions.exclude_namespaces`/`include_namespaces` |
| domain (model) | `model/fingerprint_analytics.yaml` → `fingerprint/domain/profile.py` | `ExcludedTerms` (namespace, classes, properties, values; integers required); `GraphAnalytics.excluded_terms`; `NamespaceUse` (namespace, uses); `ProfileAnalytics.namespace_uses` |
| domain | `fingerprint/domain/analytics.py` | `value_type_indicators(partitions, total)` extracted from `_partition_indicators` (P-2); `_partition_indicators` calls it; no other change |
| domain | `fingerprint/domain/prefixes.py` | `PrefixTable.match()` replaces `resolve()` |
| domain | `fingerprint/domain/namespace_filter.py` (new; listed in `.importlinter`'s `generated` contract, as every new domain module must be) | `META_NAMESPACES` (moved from `generator.py`), `namespace_filter(options, table)`, `namespace_uses(analytics, table)` (the uses rule moved from `DocumentGenerator.namespace_table`), `exclude_terms(analytics, excluded, table)`, `note_text(terms, table)` |
| domain | `fingerprint/domain/shex.py` | `schema()` copies `excluded_note` from the `PatternGraph` |
| service_layer | `fingerprint/service_layer/representations.py` | `generate_representations`: filter, warnings (§E); `warn_unknown_filters` folded into the new warning step |
| service_layer | `fingerprint/service_layer/generators/generator.py` | `excluded_namespaces()` removed; `Generator.__init__` takes `namespace_filter()`; `Generator.excluded_note(graph)`; docstring: a `Generator` built directly applies class-level hiding only |
| service_layer | `generators/pattern.py`, `shacl.py`, `plantuml.py` | set `excluded_note` on each per-graph view |
| service_layer | `generators/document.py` | P-9 |
| entrypoints | `fingerprint/entrypoints/cli/main.py`, `generate.py` | help texts (§G) |
| templates | `fingerprint_report_templates/{pattern_schema,shex_schema,shacl_shapes,plantuml_diagram,fingerprint_report}/templates/*` | the note line; the report's rows, switches, table mark, caveats, sentence, script |

`patterns.py` is not edited: it receives the filtered graph and `Generator.excluded` as today.

## Algorithm / approach

### A. Matching (`PrefixTable.match`, `namespace_filter`)

```
match(value):
    if ":" in value:  return [e for e in entries if e.namespace.startswith(value)]      # IRI stem, case-sensitive
    if "*" in value:  return [e for e in entries if glob(value).fullmatch(e.prefix)]   # prefix glob, case-sensitive
    entry = by_prefix(value); return [entry] if entry else []                          # exact prefix

namespace_filter(options, table):
    matches  = [FilterMatch(exclude, v, ns of match(v)) for v in options.exclude_namespaces]
             + [FilterMatch(include, v, ns of match(v)) for v in options.include_namespaces]
    included = ∪ namespaces of include matches
    hidden   = META_NAMESPACES − included
    excluded = (∪ namespaces of exclude matches) − included
```

Results are sorted (namespaces by IRI) so outputs are deterministic. A value is matched once even
if repeated. Worked examples on the table `ex` = `http://example.org/`, `rel` =
`http://example.org/rel/`, `relx` = `http://example.org/relx/`, `org` = `http://org.example/`:

| Value | Rule | Matches |
|---|---|---|
| `rel` | exact prefix | `rel` |
| `rel*` | glob | `rel`, `relx` |
| `*lx` | glob | `relx` (`*x` would also match `ex`) |
| `Rel*` | glob, case-sensitive | none → unknown warning |
| `http://example.org/rel/` | stem | `rel` (`…/relx/` does not start with `…/rel/`) |
| `http://example.org/` | stem | `ex`, `rel`, `relx` (in 3.2.0 this value matched `ex` only) |
| `HTTP://example.org/` | stem, case-sensitive | none → unknown warning |
| `http://example.org/*` | stem (`*` literal) | none → unknown warning |
| `''` | exact prefix | none → unknown warning |
| `*` | glob | every prefixed namespace |

### B. Positions (`exclude_terms`)

`exclude_terms` walks each `GraphAnalytics`; `ns(iri)` is `table.entry_for(iri).namespace`, else
`namespace_of(iri)` (as `Generator.namespace`). It filters exactly the positions an output writes;
every other position is left as analysed.

| Position | Field (on the analytics) | `exclude_terms` does | Counted as |
|---|---|---|---|
| class | `class_partitions[].class_iri` | drops the class, with its properties | classes |
| property | `class_partitions[].property_partitions[].property` | drops the property | properties |
| object class | `…value_partitions[].object_class` | clears `object_class`, `object_class_graph`; re-derives the four value-type fields (P-2) | classes |
| single value | `…top_values[0].value`, when every value partition is `iri` and `distinct_objects` is 1 (P-7) | when excluded, drops all top values of the property | values |
| co-type | `class_partitions[].co_types[].class_iri` | drops the entry | classes |
| parent | `class_partitions[].parents[].parent` | drops the entry | classes |
| annotation | `term_annotations[].term` | drops the entry | not counted (its term is counted where it occurs) |
| datatype | `…value_partitions[].datatype` | **unchanged** (DEC-8) | — |
| pitfall finding | `pitfalls[]` | **unchanged** (DEC-11) | — |
| collection failure | `ProfileAnalytics.failures[]`: `class_iri`, `property` | **unchanged** (P-12) | — |
| incoming link | `class_partitions[].incoming_links[]` | **unchanged**: no output writes it | — |
| graph predicate | `predicate_partitions[]` | **unchanged**: no output writes it | — |
| subclass edge | `declared_subclass_edges[]` | **unchanged**: no output writes it; SHACL's severity rule reads it, so a class keeps `sh:Warning` when its only declared subclass is excluded | — |
| graph IRI | `graph`, `cross_graph_object_types` | **unchanged**: graph names are not terms | — |

**Prefix declarations.** No position above writes a prefix by itself: each output declares the
prefixes of the IRIs it still writes, as today (pattern and ShExC: `used | valued`; SHACL: the
terms it writes plus `FIXED_PREFIXES` = `sh`, `xsd`, `rdf`, `rdfs`, `fp`, always). So an excluded
namespace's prefix stays declared exactly while a kept position uses it: a datatype (excluding
`xsd` keeps `PREFIX xsd:` for `xsd:string`), or a SHACL fixed prefix (excluding `rdfs` keeps
`@prefix rdfs:`). The report's namespace table is the explicit exception: it lists every prefix of
the profile's table, marking the excluded ones (P-9).

**Namespace uses.** Before removing anything, `exclude_terms` sets
`ProfileAnalytics.namespace_uses` to `namespace_uses(analytics, table)`: per table namespace, the
instances of its classes plus the subjects of its properties, over every class and graph
(fingerprint-report "Namespace table order"), on the unfiltered analytics. The report's table reads
it; when it is unset (a `Generator` built directly), `namespace_table` computes it from the
analytics it has, as today.

Counts are **distinct IRIs per graph and namespace** (an IRI seen as a class and as an object
class counts once under classes). The function returns new objects (`model_copy`); the input is
unchanged. With an empty `excluded` it returns the analytics with `excluded_terms = []` on every
graph and `namespace_uses` set, and nothing else changed.

### C. Every analytics field under the filter

"Unchanged" means the value of the unfiltered analysis (P-1). "Follows" means it changes with the
filter.

| Model class | Field | Under the filter |
|---|---|---|
| `ProfileAnalytics` | `endpoint`, `started_at`, `finished_at`, `tool_version`, `settings`, `namespaces`, `failures` | unchanged |
| `ProfileAnalytics` | `graphs` | follows: each graph as below |
| `ProfileAnalytics` | `namespace_uses` (new) | set by the filter from the unfiltered analytics (§B) |
| `GraphAnalytics` | `graph`, `triples`, `distinct_subjects`, `distinct_objects`, `untyped_subjects`, `predicate_partitions`, `declared_subclass_edges`, `pitfalls`, `class_count`, `property_count`, `typed_subject_ratio`, `vocabularies`, `cross_graph_object_types` | unchanged |
| `GraphAnalytics` | `class_partitions` | follows: excluded classes removed |
| `GraphAnalytics` | `term_annotations` | follows: excluded terms removed |
| `GraphAnalytics` | `excluded_terms` (new) | set by the filter (P-5) |
| `ClassAnalytics` | `class_iri`, `instances`, `observed_instances`, `precision_mode`, `sample_shared`, `incoming_links`, `hierarchy_depth`, `own_property_count`, `mandatory_property_count`, `mean_out_degree`, `label_coverage`, `is_exact`, `sample_ratio` | unchanged |
| `ClassAnalytics` | `property_partitions`, `co_types`, `parents` | follows: excluded entries removed |
| `PropertyAnalytics` | `property`, `presence_only`, `distinct_objects`, `distinct_objects_exact`, `cardinality_histogram`, every `CardinalityStatistics` field (`subjects_with_property`, `subjects_without_property`, `total_triples`, `min`, `max`, `mean`, `mean_when_present`, `median`, `mode`, `stddev`, `confidence`, `is_mandatory`, `is_functional`), every `CardinalityChoice` field, `property_kind`, `languages`, `language_coverage`, `mean_length`, `distinct_ratio`, `is_identifier_like`, `is_enumeration_candidate`, `top_k_share`, `entropy_estimate`, `inheritance`, `is_exact`, and the other `PropertyProfile` fields | unchanged |
| `PropertyAnalytics` | `value_partitions` | follows: excluded object classes cleared (P-2) |
| `PropertyAnalytics` | `top_values` | follows: excluded single values removed (P-7) |
| `PropertyAnalytics` | `value_types`, `dominant_value_type`, `type_purity`, `untyped_object_ratio` | follow, **only** when an object class was cleared (P-2); otherwise unchanged |
| `ParentClass` | `parent`, `source`, `co_type_ratio` | unchanged (whole entries are removed, per §B) |

So instance, triple and subject counts never change, and `inheritance` stays as analysed: a
property inherited from an excluded parent is still `inherited` (it is not promoted to `own`), and
the report and PlantUML still treat it as inherited. The overview's "Classes shown" and each class
section's data and object property counts are computed by the report from the classes and rows it
shows, so they follow the filter, as they follow the class-level hiding today.

### D. The note (`note_text`)

`"; ".join(f"{prefix} (classes {c}, properties {p}, values {v})")` over the graph's
`ExcludedTerms`, sorted by prefix (`table.by_namespace(ns).prefix`; the namespace IRI if no entry,
which cannot happen for a matched namespace). `None` for an empty list. The text holds only
prefixes and integers, so no output needs escaping beyond what it has.

### E. Wiring in `generate_representations`

```
run = resolve namespaces (existing) ; run = with_threshold (existing)
analytics = analyse(with_ontology(run, options.ontology))       # as today
table     = PrefixTable(run.namespaces)                         # the resolved table
filters   = namespace_filter(options or GeneratorOptions(), table)
analytics = exclude_terms(analytics, filters.excluded, table)    # P-1, P-5
if check_filters: warn(filters, analytics)                        # P-8
generators as today, each built with options (and so namespace_filter) as today
```

The saved profile is never touched: `handlers.py` saves the collected run before rendering
(fingerprint-report "The profile is saved with the report"), and `generate_from_profile_file` only
reads the file.

### F. What each output then writes (no output-specific filter code)

| Output | Excluded property | Excluded object class of a kept property | Merged group `A&B`, `B` excluded | Note |
|---|---|---|---|---|
| Pattern schema | no edge, no `via`, no glossary line, no `PREFIX` (they derive from the analytics) | alternative `IRI` (`patterns.py` `_alternative`, node kind `iri`, no class) | `B`'s class is gone, so `_groups` merges nothing: `(:A) n` | `# excluded namespaces: …` after the `# hidden:` line |
| ShExC | no triple constraint | `IRI` | shape `A` | `#` line after `# hidden:` |
| SHACL | no property shape, no `@prefix` | `untyped_object_ratio > 0` → `sh:nodeKind sh:IRI`, no `sh:class` (`shacl.py` `value_constraints`) | node shape for `A` only | `#` line after the title comment |
| PlantUML | no attribute, no link, no count | `untyped_object_ratio > 0` → attribute `p : resource [m]` (`plantuml.py` `visit_property`, `types`) | box `A` | `'` line after `@startuml`, in the overview and every module |
| Report | no row; class indicators count shown rows | value types without the class | section `A` | caveats line per graph; table row marked |

**Files for a graph whose classes are all excluded.** The existing rule "No files for empty
graphs" keys on **shown classes**, not on `class_partitions`: `Generator.view()` skips a per-graph
file when no class view was built (`if self.per_graph and not classes`), and `PatternGenerator.views`
(also used by ShExC) keeps only views with blocks. On the filtered analytics such a graph has no
class partition left, so no SHACL, PlantUML, pattern or ShExC file is written. The report keys on
`class_partitions` for its "empty" wording, hence P-9's rule.

### G. Help texts

`--exclude-namespace`: `leave out every term of the matching namespaces: a prefix, a prefix glob
('rel*') or an IRI stem (repeatable)`. `--include-namespace`: `keep the matching namespaces,
over --exclude-namespace and the default hiding of rdf, rdfs, owl, sh classes (repeatable)`.

### H. The report's switches (template script)

In `apply()`: `off` as today; for each row, `row.hidden = !!off[row.dataset.ns] || !(own || match)`
(`off[""]` is never set, P-9); `anyRow` becomes true only for a matching row whose switch is on;
the class rule is unchanged (`!off[cls.dataset.ns] && (own || anyRow)`). The count text stays
`<shown> shown, <hidden> hidden` over class sections. The switch list comes from the
server-rendered `<fieldset>` (P-9). Group header rows (`tr.group`) stay, as with the search today.

### I. Worked example: the filter test profile

`tests/builders.py` gains `filter_profile()`: one default graph, namespaces `ex`
(`http://example.org/`), `org` (`http://org.example/`), `rel` (`http://example.org/rel/`), and a
user prefix `foaf` with no term.
- `ex:Person`, 10 instances: `ex:name` (10 `xsd:string` literals), `rdfs:label` (10 literals
  `@en`), `ex:knows` → `ex:Person`, `ex:memberOf` → `org:Unit`, `rel:r1` and `rel:r2` → `ex:Person`
  (1 triple each).
- `org:Unit`, 2 instances: `ex:name`.

With `--exclude-namespace rel`, the pattern schema loses the lines `-rel:r1-> (:ex:Person) …`,
`-rel:r2-> (:ex:Person) …`, the `via (:ex:Person)-rel:r1, (:ex:Person)-rel:r2` part of the
`ex:Person` header and the `PREFIX rel:` line, and gains
`# excluded namespaces: rel (classes 0, properties 2, values 0)`. With `--exclude-namespace org`,
the `org:Unit` block goes, `-ex:memberOf-> (:org:Unit) …` becomes `-ex:memberOf-> IRI …`, and the
note is `org (classes 1, properties 0, values 0)`: `values 0` holds because `filter_profile()` sets no top values and gives `ex:memberOf` `distinct_objects` 2 (its two objects are the two `org:Unit` instances), so no single-value position exists. (Statistics tokens elided as `…`; the step
definitions assert the parts the scenarios name.)

The brainframe acceptance (`inputs/brainframe-evidence.md`): `fingerprint-gen-pattern
--exclude-namespace relationid` on its `profile.json` is expected to write a workspace pattern file
of at most 100 000 characters with no `relationid:` text and the note
`relationid (classes 0, properties 619, values <v>)`; `<v>` is measured and recorded, not asserted.

### Anti-patterns

| Don't | Do instead | Why |
|---|---|---|
| Test `namespace in excluded` inside a generator or template for the excluded tier | Let `exclude_terms` remove the term from the analytics; the class tests (`shown()`, `_shown()`, PlantUML's link test) serve the meta tier only (P-3) | DEC-4; the old divergence came from per-output tests |
| Filter the `ProfileRun` before `analyse()` | Analyse first, filter the analytics (P-1) | Inheritance and the class and graph aggregates would be re-derived from the reduced run |
| Drop a value partition of an excluded object class, or clear it without re-deriving the four value-type fields | Clear `object_class`, keep the partition, call `value_type_indicators` (P-2) | Triple counts must not change; SHACL needs `untyped_object_ratio` |
| Use `fnmatch` for globs, glob over IRIs, or lower-case before matching | `PrefixTable.match` (P-4) | DEC-6: `*` is the only wildcard, matching is case-sensitive, IRIs may hold `*` |
| Mutate the loaded run or analytics, or write the filtered analytics anywhere | `model_copy`; render only | DEC-1: `profile.json` keeps everything |
| Return per-graph counts as a dict | `ExcludedTerms` objects | `AGENTS.md` "Values are domain objects"; `tests/guards/test_no_composed_dicts.py` |
| Build the note text in templates | `note_text` → `GraphView.excluded_note` | P-6: one tested rule |
| Filter pitfall findings, collection failures or datatypes | Leave them | DEC-11, P-12, DEC-8 |
| Edit golden files by hand | `make refresh-golden` | `development.adoc` "Canonical data" |
| Add the filter profile to `tests/test_data/*-source-ap.rdf` | `tests/builders.py` | lean-test-suite DEC-5: the canonical dataset takes no edge cases |

## Test case specifications

Every spec scenario is a Gherkin scenario with the same title (`tests/guards/test_traceability.py`).
The tables hold only checks no scenario owns, in the tier that decides them (`development.adoc`
"Tiers"). Edge cases come from `tests/builders.py` (`klass`, `prop`, `literals`, `resources`,
`profile_run`, and the new `filter_profile`).

### Scenario → feature map

| Delta requirement | Feature file, Rule | Scenarios | Task |
|---|---|---|---|
| profile-representations "Namespace filters" | `profile_representations.feature`, "Namespace filters choose the classes and terms shown" | Meta vocabularies hidden by default; Included again; Unknown name (unchanged, green) | — |
| same | same | Excluded by option (two steps added); Meta properties kept by default; A meta namespace excluded by name; Properties of an excluded namespace (5); An edge to an excluded class (5); A merged class loses its excluded member; Matching a filter value (6); Include wins over exclude; A name that hides nothing; Datatypes are not filtered; Pitfall findings are not filtered; The saved profile keeps excluded terms | 1.4 |
| same | same | Excluded namespaces are noted (rows pattern schema, ShExC, shapes, diagram) | 1.5 |
| same | same | Excluded namespaces are noted (row report); Every class of a graph excluded | 1.6 |
| fingerprint-report "Navigation, search and filters" | `fingerprint_report.feature`, "The report is one self-contained page" | Search data is present (unchanged); Property rows carry their prefix | 1.6 |
| same | same, `@manual` | Search narrows the classes; Namespace switched off; Property namespace switched off; Search and a property switch combine | 1.6 (by hand, `inputs/manual-checks.md`) |

### Unit tests (the branches the scenarios do not reach)

| Test ID | Tier / file | Input | Expected | Edge cases |
|---|---|---|---|---|
| TC-F1 | `tests/unit/domain/test_prefixes.py` | `PrefixTable.match` on the §A table | the §A table, row by row | glob with `.` and `?` (`a.b*` matches `a.bc`, not `axbc`); repeated `*`; **the 3.2.0 exact-IRI use**: `http://example.org/` now matches `ex`, `rel` and `relx`, and `http://org.example/` still matches `org` alone; `HTTP://example.org/` matches nothing |
| TC-F2 | `tests/unit/domain/test_namespace_filter.py` | `namespace_filter` with excludes/includes | `hidden` = meta − included; `excluded` = matched − included; one `FilterMatch` per value, in order | include of a meta namespace; include with no matching exclude; the same value twice; no options → `hidden` = meta, `excluded` empty |
| TC-F3 | same | `exclude_terms` on analytics of builder runs (`analyse(profile_run(…))`), one per §B row | each filtered position removed or cleared as §B; each **unchanged** row untouched | object class cleared keeps `triples` and re-derives the four fields (a property whose only resource objects were `org:Unit` gets `untyped_object_ratio` 1.0); top values kept when a literal partition exists; datatypes, pitfalls, incoming links, subclass edges unchanged; **a collection failure on `rel:r1` (`failures[].property`) and one on `org:Unit` (`failures[].class_iri`) are still in `failures`**; `namespace_uses` equals `namespace_uses` of the input |
| TC-F4 | same | the counts of `exclude_terms` | distinct counts per §B; zero-count namespaces omitted; sorted | an IRI as class and as object class counts once; a parent counts as a class; **values (P-7):** an excluded `top_values[0]` of an all-`iri` property with `distinct_objects` 1 counts 1 and every top value of the property is dropped; the same with `distinct_objects` 2, or with a literal partition, counts 0 and is kept |
| TC-F5 | same, Hypothesis (`tests/unit/domain/strategies.py`: a `filter_runs()` strategy built from domain models, analysed with `analyse`) | random runs and excluded subsets | no IRI of an excluded namespace at any **filtered** §B position of the result; `exclude_terms` twice = once; the input is unchanged; with nothing excluded only `excluded_terms` and `namespace_uses` differ; **for every kept class and kept property, every field §C marks unchanged is equal before and after, in particular `instances`, `observed_instances`, `triples`, `subjects_with_property`, `total_triples` and `inheritance`; the graph's `triples`, `distinct_subjects`, `class_count` and `property_count` are equal** | empty run |
| TC-F6 | same | `note_text` | §D format; `None` for `[]` | two namespaces in prefix order |
| TC-F7 | `tests/unit/domain/test_analytics.py` (existing) | `value_type_indicators` | equal to the four fields `_partition_indicators` gives for the same partitions | no resource partition; all untyped |
| TC-R1 | `tests/unit/service_layer/test_representations.py` | `generate_representations` with a recording renderer | unknown and hides-nothing warnings once each; none with `check_filters=False`; none for an exclude fully re-included | ontology label of an excluded term not passed to the renderer |
| TC-R2 | same | `generate_representations` with `exclude=["rel"]` on `filter_profile()` plus `ex:Agent` whose declared parent is `rel:Base` | `GraphAnalytics.excluded_terms` attached per graph, in graph order; `ex:Agent`'s property inherited from `rel:Base` is still `inherited` and still left out of the PlantUML box | a graph with nothing excluded gets `[]` |
| TC-G1 | `tests/unit/service_layer/test_generator.py` (existing) | `Generator(…, options)` built directly | `excluded` = hidden ∪ excluded; `excluded_note` = `note_text` of the graph | graph without `excluded_terms` → `None` |
| TC-D1 | `tests/unit/service_layer/test_document.py` (existing) | document view of the filter profile, through `generate_representations` with `exclude=["rel"]` | `DocumentProperty.prefix`; `PrefixDeclaration.excluded`; `rel`'s uses are 2 (the subjects of `rel:r1` and `rel:r2`), the same as without the filter, and the table order is the same as without it; `Caveats.excluded`; `DocumentGraph.empty` per P-9; `ProfileDocument.switches` is `["ex", "org", "rdfs"]` (no `""`, no `rel`) | property with no table entry → `""`; `namespace_uses` unset → computed as today |

### Integration and output tests

| Test ID | Tier / file | Setup | Verification | Teardown |
|---|---|---|---|---|
| IT-1 | `tests/unit/service_layer/test_representations_golden.py` (existing) | `make refresh-golden` | only `main.html` and `scanned/main.html` differ from 3.2.0 (P-10); text equality afterwards | none |
| IT-2 | `tests/e2e/` (existing, unchanged) | `make oxigraph-load-test-data` | `make test-e2e` green: collection is untouched (DEC-1) | none |
| IT-3 | `make check-mutation` | — | score ≥ `tests/guards/mutation_score.txt` (0.950) | survivors get a test in the owning tier, or the dead code goes |
| IT-4 | brainframe acceptance (by hand, not a test) | the worktree copy `temp/brainframe-llm-schema/profile.json`; commands in `inputs/manual-checks.md` | §I expectations; sizes (`wc -m`) of the pattern, ShExC and report files with and without the option, recorded in `inputs/brainframe-evidence.md` | the `temp/` output folder is git-ignored; leave it or delete it |

## Error matrix

Logging goes to stderr through `configure_logging()`. "Existing" means unchanged from 3.2.0.

| Failure mode | How it is detected | Expected handling | Log level | Message (exact) |
|---|---|---|---|---|
| Value matches no namespace (prefix, glob or stem) | `FilterMatch.namespaces` empty | ignored; outputs as without it | WARNING | existing: `--exclude-namespace {name}: no such namespace; ignored` (or `--include-namespace`) |
| Exclude value hides no term | matched namespaces still excluded sum to 0 over all graphs (P-8) | nothing removed; outputs as without it | WARNING | `--exclude-namespace {name}: no term in this namespace; ignored` |
| Exclude value fully re-included | every matched namespace in `included` | nothing removed | none | — |
| `*`, or a stem covering every namespace | matches all | every class and property removed; no per-graph file (existing "No files for empty graphs"); the report lists each graph with its note | none | — |
| Glob also matches a meta prefix (`r*`) | rule DEC-6 | `rdf`/`rdfs` terms removed; the note names them | none | — |
| Value differs from a prefix or IRI only in case | case-sensitive match (P-4) | unknown warning | WARNING | as the first row |
| Profile saved before 3.0 (no table) | `run.namespaces is None` | resolved without fetching, then matched (existing) | none | — |
| Profile missing, not JSON, newer version | `ProfileFileError` (existing) | exit 2 | none | existing |
| A library caller builds a `Generator` itself | not through `generate_representations` | class-level hiding of `hidden ∪ excluded` only; no note (out of the requirement's scope; `Generator` docstring and `representations.adoc`) | none | — |
| A user template package lacks the note line | — | the note is missing from that output; nothing fails | none | — |
| Pitfall example or collection failure names an excluded IRI | — | shown (DEC-11, P-12); its prefix still resolves in the report | none | — |

Every step is a pure function of the saved profile and the options: re-running a generator with the
same inputs writes the same files (idempotent; the file writer replaces them).

## Exit criteria

| Stage | Done when |
|---|---|
| Implementation | Every scenario of both deltas passes (manual ones checked and recorded in `inputs/manual-checks.md`); `make check-all` and `make test-e2e` green; `make check-mutation` ≥ 0.950; `openspec validate --all --strict` clean; IT-4 recorded; docs build (`make build-docs`). |
| Release | Task 1.11: PR merged with green CI, tag `3.3.0`, GitHub Release published (DEC-3). |

## Risks / Trade-offs

- **[Risk] Gherkin scenarios exist before their steps.** Once `tasks.md` exists, the traceability
  guard counts this change's deltas, so the feature scenarios are written with this PLAN and fail
  with missing steps until bound (`tasks.md`, "Still red until bound"). → The branch is not merged
  before task 1.10.
- **[Risk] The rebase onto `master` after PR #45 (3.2.0).** This PLAN relies only on code already
  on `feature/llm-schema-tools` (the pattern and ShExC generators, `with_ontology`,
  `term_annotations`). → Rebase before task 1.1; if `representations.py`, `generator.py` or
  `analytics.py` moved, re-run GitNexus impact.
- **[Risk] Mutation score.** The position walker has many small branches. → TC-F3 per position,
  TC-F5 as a property.
- **[Trade-off] Four value-type fields change under a filter** (P-2), only for a property that
  lost an object class. Nothing else does (§C). The docs say so.
- **[Trade-off] Class and graph aggregates stay as analysed** (§C): no output writes them today, so
  nothing shows a total that counts excluded terms.
- **[Trade-off] The JavaScript is checked by hand** (DEC-10), as the existing switches are.
- **[Trade-off] A property inherited from an excluded parent appears in no diagram box.** It stays
  `inherited` (§C), so PlantUML leaves it out of the child's box (`DIAGRAMMED_INHERITANCE` =
  own, refined), and the parent's box is gone with the excluded namespace. Accepted (coordinator,
  2026-11-01); the report still lists it under the child's inherited properties, and
  `representations.adoc` says so (task 1.9).

## Open Questions

None. Round 1 settled every EPIC-level question; the matching details are DEC-6 and P-4.

## References

| Topic | Location | Anchor |
|---|---|---|
| EPIC decisions | `openspec/changes/namespace-filter/proposal.md` | "Key decisions" |
| Answers | `openspec/changes/namespace-filter/inputs/qa-round-1.md` | "Round 1 answers" |
| Evidence | `openspec/changes/namespace-filter/inputs/brainframe-evidence.md` | "In the pattern schema" |
| Manual checks | `openspec/changes/namespace-filter/inputs/manual-checks.md` | "Checks" |
| Requirement rewritten | `openspec/specs/profile-representations/spec.md` | "Requirement: Namespace filters" |
| Switches | `openspec/specs/fingerprint-report/spec.md` | "Requirement: Navigation, search and filters" |
| Analysis | `fingerprint/domain/analytics.py` | `_partition_indicators`, `property_analytics`, `graph_analytics` |
| Generator framework | `fingerprint/service_layer/generators/generator.py` | `Generator`, `excluded_namespaces` |
| Pattern grouping and alternatives | `fingerprint/domain/patterns.py` | `_Builder._groups`, `_alternative` |
| SHACL value constraints | `fingerprint/service_layer/generators/shacl.py` | `value_constraints`, `visit_graph` |
| Documented API | `docs/modules/ROOT/pages/api-reference.adoc` | the `fingerprint_report` example |
| Test tiers, canonical data | `docs/modules/ROOT/pages/development.adoc` | "Tests", "Canonical data" |
