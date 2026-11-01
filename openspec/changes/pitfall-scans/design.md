> Derives from: the EPIC `pitfall-scans` (proposal.md)

## Context

- **Collection.** Collection is a staged class (`fingerprint/service_layer/collection.py:_Collection`)
  over the `SparqlPort` (`fingerprint/adapters/sparql.py`). It has retries, timeouts and recorded
  `Failure`s.
- **Queries.** Queries are templates in `fingerprint/adapters/queries/*.rq`. Each starts with a
  `# <name>` line that `query_name` reads; `FakeSparql` (`tests/unit/fakes.py`) answers by that name,
  or from an rdflib `Dataset`.
- **The profile.** `ProfileRun` → `GraphProfile` (`model/fingerprint_stats.yaml`) is saved as
  `profile.json` and analysed (`analyse`; `GraphAnalytics` is_a `GraphProfile`, so new fields carry
  through).
- **Settings.** `Settings` and `SettingsOverride` share their slots. The CLI passes collection options
  into `SettingsOverride`, and environment variables are read by name (`RDF_FINGERPRINTER_<NAME>`).
- **Outputs.** The report is `DocumentGenerator` (`generators/document.py`) over
  `fingerprint_report/templates/main.html`. Generators are registered in `generators/__init__.py`
  `GENERATORS` and keyed by `RepresentationFormat` (`model/fingerprint_views.yaml`).
- **Namespaces.** Namespaces are gathered in `service_layer/prefixes.py:_iris` from the
  `IRI_FIELDS` names.
- **Exit codes** live in `fingerprint/entrypoints/cli/__init__.py`, and are mapped in `main.py`.
- **Seed evidence.** The 29 seed queries ran on Oxigraph in under 2 s each, over brainframe
  (79k triples). Two of them (domain and range) had to be written per class, without nested
  property paths, to finish (`inputs/brainframe-modelling-analysis.md`).

## Goals / Non-Goals

**Goals:** the spec deltas of `pitfall-scans`, `fingerprint-report`, `namespace-prefixes` and
`developer-tooling`.
**Non-Goals:** the EPIC's no-gos.

## Decisions

- **D-1 Domain: `fingerprint/domain/pitfalls.py`** (pure):
  - `parse_header(text) -> PitfallCheck` reads the header, the leading `#` lines up to the first
    non-comment line.
    - A line that matches `# <key>: <value>` sets that key.
    - A `#` line without a key is ignored (free prose).
    - An unknown key, a repeated key, a missing required key (`id`, `title`, `importance`, `scope`,
      `source`) or an invalid value raises `PitfallCheckError`.
    - The keys are `id`, `title`, `importance`, `scope`, `source`, `heuristic` (`true`/`false`) and
      `description` (one line).
  - `IMPORTANCE_ORDER = (critical, important, minor)`.
  - `robot_level(importance)` → `ERROR` / `WARN` / `INFO`.
  - `at_or_above(results, level) -> int`.
  - `PitfallCheck` is a LinkML model (D-3) holding the metadata plus `query` (the text) and `origin`
    (`packaged` | the user file path).
- **D-1a The catalogue** (normative for the packaged files; the ids, importance, scope and heuristic
  flag are observable through the TSV levels, `--fail-on`, `--skip-pitfall` and the docs):

  | id | seed file (`inputs/seed-queries/`) | importance | scope | heuristic | source | title |
  |---|---|---|---|---|---|---|
| `p04_unconnected_class` | `oops_p04_unconnected_class` | minor | schema |  | OOPS! P04 | Class connected to nothing |
| `p05_wrong_inverse` | `oops_p05_wrong_inverse` | critical | schema |  | OOPS! P05 | Inverse properties whose domain and range do not mirror each other |
| `p06_class_cycle` | `oops_p06_class_cycle` | critical | schema |  | OOPS! P06 | Cycle in the class hierarchy |
| `p07_merged_concepts` | `oops_p07_merged_concepts` | minor | schema | yes | OOPS! P07 | Class name joins concepts with And/Or |
| `p08_missing_comment` | `oops_p08_missing_label_or_comment` | minor | schema |  | OOPS! P08 | Class or property without a comment |
| `p10_no_disjointness` | `oops_p10_no_disjointness` | important | schema |  | OOPS! P10 | No disjointness axiom at all |
| `p11_missing_domain_or_range` | `oops_p11_missing_domain_or_range` | important | schema |  | OOPS! P11 | Property without a domain or a range |
| `p12_p30_same_name_not_equivalent` | `oops_p12_p30_same_name_not_equivalent` | minor | schema | yes | OOPS! P12/P30 | Same local name in two namespaces, not declared equivalent |
| `p13_missing_inverse` | `oops_p13_missing_inverse` | minor | schema |  | OOPS! P13 | Object property without an inverse |
| `p19_multiple_domains_or_ranges` | `oops_p19_multiple_domains_or_ranges` | critical | schema |  | OOPS! P19 | Several domains or ranges on one property (read as an intersection) |
| `p20_label_longer_than_comment` | `oops_p20_label_longer_than_comment` | minor | schema | yes | OOPS! P20 | Label at least as long as the comment (annotations swapped?) |
| `p21_miscellaneous_class` | `oops_p21_miscellaneous_class` | minor | schema | yes | OOPS! P21 | Catch-all class (Other, Misc, …) |
| `p22_class_naming` | `oops_p22_class_naming` | minor | schema |  | OOPS! P22 | Class name not starting with an upper-case letter |
| `p24_recursive_definition` | `oops_p24_recursive_definition` | important | schema |  | OOPS! P24 | Class or property defined by itself |
| `p25_inverse_of_itself` | `oops_p25_inverse_of_itself` | important | schema |  | OOPS! P25 | Property declared its own inverse |
| `p26_inverse_of_symmetric` | `oops_p26_inverse_of_symmetric` | important | schema |  | OOPS! P26 | Symmetric property that also has an inverse |
| `p27_wrong_equivalent_properties` | `oops_p27_wrong_equivalent_properties` | critical | schema |  | OOPS! P27 | Equivalent properties with different domains or ranges |
| `p28_p29_wrong_symmetric_or_transitive` | `oops_p28_p29_wrong_symmetric_or_transitive` | critical | schema |  | OOPS! P28/P29 | Symmetric or transitive property whose domain and range differ |
| `p32_classes_same_label` | `oops_p32_classes_same_label` | minor | schema |  | OOPS! P32 | Two classes with the same label |
| `p33_single_property_chain` | `oops_p33_single_property_chain` | minor | schema |  | OOPS! P33 | Property chain of one property |
| `p34_untyped_class` | `oops_p34_untyped_class` | minor | data |  | OOPS! P34 | IRI used as a class but never declared |
| `p35_untyped_property` | `oops_p35_untyped_property` | important | data |  | OOPS! P35 | Relation used but never defined |
| `p36_iri_with_file_extension` | `oops_p36_iri_with_file_extension` | minor | schema |  | OOPS! P36 | IRI with a file extension |
| `p38_no_ontology_declaration` | `oops_p38_no_ontology_declaration` | important | schema |  | OOPS! P38 | No owl:Ontology declaration |
| `p41_no_license` | `oops_p41_no_license` | important | schema |  | OOPS! P41 | Ontology without a licence |
| `x_domain_violation` | `data_domain_violation` | important | data |  | rdf-fingerprinter (RDFUnit-style) | Subjects outside a property's declared domain |
| `x_individual_as_predicate` | `extra_individual_as_predicate` | critical | data |  | rdf-fingerprinter | Typed individual used as a predicate |
| `x_punning_class_and_property` | `extra_punning_class_and_property` | important | data |  | rdf-fingerprinter | IRI used as a class and as a property |
| `x_range_violation` | `data_range_violation` | important | data |  | rdf-fingerprinter (RDFUnit-style) | IRI objects outside an object property's declared range |

  - **The id rule:** an OOPS!-derived check is the seed name without `oops_`; the extra checks start
    with `x_`. `p08_missing_comment` is the seed `oops_p08_missing_label_or_comment`, renamed
    because it only checks comments; labels are left to the report's label caveats.
  - **The scope rule:** `schema` checks need only the ontology. `data` checks need the data,
    optionally joined with the schema.
  - **Heuristics** are always `minor`.

- **D-2 Adapter: `fingerprint/adapters/pitfall_catalogue.py`.**
  - `load_catalogue(user_dir=None, skip=()) -> list[PitfallCheck]` reads the packaged files under
    `fingerprint/adapters/queries/pitfalls/`, then the user's.
  - Each file is validated with rdflib's `prepareQuery`. It must parse, its algebra must be a
    `SelectQuery`, and its projected variables, read from `algebra.PV` (not `algebra.p.PV`, which
    fails on `SELECT DISTINCT`), must be exactly `{entity, property, value}`.
  - Its parsed query must have no `datasetClause`, so no `FROM` or `FROM NAMED`: the wrapping adds
    the dataset, and a user `FROM` inside the subquery would not parse.
  - A user id equal to a packaged id replaces it. An unknown `skip` id raises
    `PitfallCheckError`, which the CLI maps to `UsageError` (exit 2).
  - rdflib is an adapter-layer dependency; the domain stays free of it.
- **D-3 Model.** In `fingerprint_stats.yaml`:
  - the enums `PitfallImportance` (`critical`, `important`, `minor`) and `PitfallScope` (`schema`,
    `data`); `QueryKind.pitfall`;
  - the class `PitfallTerm` (`text`, `kind: NodeKind`) and the class `PitfallExample` (`entity`,
    `property`, `value`: `PitfallTerm`);
  - the class `PitfallResult` (`check_id`, `title`, `importance`, `scope`, `source`, `heuristic`,
    `count`, `examples`, `seconds`);
  - `GraphProfile.pitfalls` (multivalued, optional);
  - the slot `check_id`, added to `Failure`;
  - the settings slots `pitfall_scan` (default false), `schema_graphs` (uriorcurie, multivalued) and
    `pitfall_examples` (default 10, minimum 1), on `Settings` and `SettingsOverride`.

  The class `PitfallCheck` is a view-free model in `fingerprint_stats.yaml` too. No `ProfileRun`
  field references it, so `profile.json` never holds it; `gen-json-schema` still lists every class
  under `$defs`, which is harmless and accepted. `PitfallResult` also carries `description`
  (optional). The views are in D-6 and D-7. Run `make generate-models`, and add
  `fingerprint.domain.pitfalls` to the `.importlinter` "generated" contract list.
- **D-4 The scan in collection.** In `collect`, right after `run.profile_graph(graph, edges)` (outside
  `profile_graph`, which returns early below `classes` depth, so the scan runs at any depth), when
  `settings.pitfall_scan` is on, the collector calls `run.scan_pitfalls(graph, checks)`. It sets the
  graph profile's `pitfalls` with `model_copy`:
  - **Empty graph:** first an `ASK { <dataset> ?s ?p ?o }` (the name line `# PITFALL ask`); a graph
    without triples is not scanned.
  - **Which checks:** without schema graphs, all of them. With schema graphs, `schema`-scope checks
    on a schema graph (over itself), and `data`-scope checks on the other graphs (with the
    `FROM <schema>` clauses).
  - The checks run one after the other; concurrency stays per class. The result is
    `list[PitfallResult]`.
  - **Count query:** `pitfall_count_query(check, graph, schema_graphs)`.
  - **Example query:** `pitfall_example_query(…, limit)`.
  - Both builders live in `adapters/queries/__init__.py` (D-5).
  - **A count of 0:** no example query; the result has empty `examples`.
  - **On a count failure:** record a `Failure(query_kind=pitfall, graph, check_id, message,
    attempts)` and skip the examples.
  - **On an example failure:** record a failure; the result keeps its count and has no examples.
  - **Terms:** a term is read from rdflib (`URIRef` → `iri`, `BNode` → `blank_node`, `Literal` →
    `literal`, its lexical form).
  - **Timing:** `seconds` is `time.monotonic` over both queries.

  `collect` receives the checks as a parameter, `collect(endpoint, settings, sparql, checks=())`, so
  the service layer never reads files.
- **D-5 The query wrapping.** A check is split into its prologue (`PREFIX` and `BASE` lines) and its
  body (the `SELECT …`). The builders emit:

  ```sparql
  # PITFALL <id> count
  <prologue>
  SELECT (COUNT(*) AS ?n) <dataset> WHERE { { <body> } }
  ```
  ```sparql
  # PITFALL <id> examples
  <prologue>
  SELECT ?entity ?property ?value <dataset> WHERE { { <body> } } ORDER BY ?entity ?property ?value LIMIT <k>
  ```

  `<dataset>` is `FROM <graph>` followed by `FROM <s>` for each schema graph, for a named graph.
  It is empty for the default graph. The leading name line keeps `query_name`, logs and
  `FakeSparql` rules working. `ORDER BY` makes the examples, and so the golden files, deterministic.
- **D-6 Report views and template.** In `model/fingerprint_views.yaml`:
  - `DocumentPitfalls` (`summary: PitfallLevelCount[importance, checks]`, `graphs`);
  - `DocumentPitfallGraph` (`label`, `slug`, `checks`, `clean: [id]`);
  - `DocumentPitfallCheck` (`id`, `anchor`, `title`, `importance`, `source`, `count`, `heuristic`,
    `q`, `examples`);
  - `DocumentPitfallExample` (`entity`, `property`, `value`: `DocumentValue[label, iri?]`);
  - `ProfileDocument.pitfalls` (optional);
  - `DocumentClass.badges` (`DocumentBadge[check_id, anchor, importance]`).

  `DocumentGenerator.end_profile` builds them:
  - IRIs as short names through `self.label`;
  - literals as text;
  - the order from the spec;
  - badges for classes whose IRI is an example entity of a check in the same graph.

  `main.html` gains a `#pitfalls` section after the class sections, a contents link, badge chips in
  the class summaries, and importance colours in the CSS tokens. The inline script also filters
  `.pitfall[data-q]` entries.
- **D-7 TSV generator.**
  - `PitfallsGenerator` (`generators/pitfalls.py`) has `per_graph`, the file name
    `pitfalls-{slug}.tsv` and the template package `fingerprint_report_templates/pitfalls_tsv`. It
    overrides `outputs()`: one file per graph with results.
  - Its view is `PitfallsTable` (`GraphView` mixin; `lines: PitfallLine[level, rule, subject,
    property, value]`).
  - Values are full IRIs, `_:<id>` for blank nodes, or lexical forms (datatype and language dropped),
    with an empty cell for an unbound variable, and `\t`, `\r` and `\n` replaced by spaces. There
    is no autoescape.
  - `RepresentationFormat.pitfalls` is registered in `GENERATORS`.
- **D-8 Namespaces.** `_iris` also yields the `text` of every `PitfallTerm` whose kind is `iri`
  (DEC-11).
- **D-9 CLI and library.**
  - `fingerprint_report(..., checks=None)`: `None` means the packaged catalogue when the scan is on.
  - `main.py` gains:
    - the settings options `--pitfalls`, `--schema-graph` (repeatable) and `--pitfall-examples`
      (`IntRange(min=1)`);
    - the CLI-only options `--pitfall-checks DIR`, `--skip-pitfall ID` (repeatable) and
      `--fail-on [critical|important|minor]`.
  - Inside the usage `try`, `main.py` loads the catalogue and refuses the CLI-only options when
    `settings.pitfall_scan` is off.
  - After the run, `main.py` exits 1 if there were failures. Otherwise, with `--fail-on`, it exits
    `EXIT_PITFALLS = 5` when `at_or_above(run, level)` (rows, checks), summed over every graph, has
    rows > 0, logging at WARNING `<rows> findings in <checks> checks at or above <level>`.
  - Settings: `schema_graphs` is split on commas in the environment, like `selected_graphs`, in
    `_setting` (`fingerprint/__init__.py`). Each schema graph IRI passes `to_iriref` in
    `resolve_settings`, so a bad one is a `UsageError` before any query.
  - `generate.py` gains `gen_pitfalls`, and `pyproject.toml` the script `fingerprint-gen-pitfalls`.
- **D-10 Dev tooling.**
  - `docker/docker-compose.yml` gains the service `oxigraph-scan`, in memory, on
    `${RDF_FINGERPRINTER_SCAN_PORT}`, with the default `7880` in `docker/.env` (7879 is often used by a
    hand-started store) and the `container_name` `oxigraph-fingerprinter-scan`.
  - The `scan-files` target in the `Makefile` starts it, `DELETE`s and `POST`s the two graphs (the
    content type from the extension), and runs `poetry run fingerprint -e … --graph … --pitfalls
    --schema-graph urn:fingerprint:scan:schema --format pitfalls -o $(OUT)`.
- **D-11 Docs.** A new `docs/modules/ROOT/pages/pitfalls.adoc`: what the scan does, the options, the
  check contract, how to write a check, and the catalogue table (id, importance, scope, source,
  title). It joins the nav. The CLI, settings and exit-status tables are updated.
- **D-12 Release.** Version 3.1.0, with a CHANGELOG entry ("Added"). Nothing breaking: the scan is
  opt-in, and exit 5 only appears with `--fail-on`.

## Algorithm / approach

Worked example (brainframe, from `inputs/`):

```text
fingerprint -e …/query --graph https://my.brainframe.com/graph/workspace --pitfalls \
            --schema-graph https://ontology.brainframe.com/graph/ontology --format pitfalls --fail-on critical
```

For the workspace graph, `p35_untyped_property` sends:

```sparql
# PITFALL p35_untyped_property count
PREFIX owl: … PREFIX rdf: … PREFIX rdfs: …
SELECT (COUNT(*) AS ?n) FROM <…/graph/workspace> FROM <…/graph/ontology>
WHERE { { SELECT ?entity ?property (COUNT(*) AS ?value) WHERE { … } GROUP BY ?entity ?property } }
```

It returns `1100`. The example query returns the first 10 rows by entity order. The profile then
holds `PitfallResult(check_id=p35_untyped_property, importance=important, count=1100, examples=[…10])`.
The page lists it under *important*. The TSV has 10 `WARN p35_untyped_property` lines. Because
`p19_multiple_domains_or_ranges` (critical) found 4, the run exits 5.

The scan is safe to rerun: it is read-only and deterministic, because the examples are ordered.

### Test strategy (initial; the developer will refine it)
| Level | What | Where |
|---|---|---|
| Unit, domain | header parsing, level order and mapping, `at_or_above` | `tests/unit/test_domain_pitfalls.py` |
| Unit, adapter | catalogue loading, validation (each invalid case, including `FROM`, an unknown key and a duplicate user id), replace, skip, and an empty catalogue after skips | `tests/unit/test_adapters_pitfall_catalogue.py` |
| Unit, checks | each packaged check over `tests/test_data/pitfalls/<id>.trig`: a `positive` and a `negative` named graph, run with rdflib on each graph's content; the expected entity per id in a table in the test | `tests/unit/test_pitfall_checks.py` |
| Unit, stage | wrapping (FROM, count, limit, ordering), the schema/data split, empty graphs, count 0 (no example query), blank-node entities, failures, scan off, depth `graphs`, through `FakeSparql` | `tests/unit/test_service_layer_pitfall_scan.py` |
| Gherkin | `tests/features/pitfall_scans.feature` for the spec scenarios; report, exit and format scenarios in the existing features | `tests/unit/steps/` |
| Golden | the page and the TSV for a fixed profile with scan results | `tests/test_data/golden/` |
| e2e | Oxigraph: a schema graph plus data, `--pitfalls --format pitfalls`, and exit 5 with `--fail-on` | `tests/e2e/test_pitfall_scan.py` |

### Anti-patterns
| Don't | Do instead | Why |
|---|---|---|
| Run the user's `.rq` files unparsed | Parse with `prepareQuery`; `SELECT` only | Read-only guarantee (DEC-7) |
| Store every finding row | Count plus `LIMIT k` examples | Unbounded on large data (DEC-4) |
| Join schema and data through `GRAPH` blocks | Use a `FROM` dataset | A triple pattern cannot span two graphs |
| Put check logic in Python | Keep it in the `.rq` | Sharable with ROBOT; user-extensible (DEC-1) |
| Use unordered `LIMIT` | `ORDER BY ?entity ?property ?value` | Deterministic examples and golden files |
| Copy OOPS! descriptions | Write our own words and cite the code | Licence not checked (DEC-12) |
| Hide findings by the namespace filters | Keep them | A finding in a hidden namespace is still a finding (DEC-11) |
| Read check files in the service layer | Pass the checks into `collect` | Layering: I/O in adapters only |

## Error matrix

| Failure mode | How it is detected | Expected handling |
|---|---|---|
| A user check has no or an invalid header, does not parse, is not a `SELECT`, or has the wrong variables | `load_catalogue` raises `PitfallCheckError` | Exit 2 before any query: `--pitfall-checks <file>: <reason>` |
| `--skip-pitfall` names an unknown id | `load_catalogue` | Exit 2, listing the known ids |
| `--pitfall-checks`, `--skip-pitfall` or `--fail-on` without the scan | `main.py` after `resolve_settings` | Exit 2: `<option> needs --pitfalls` |
| `--pitfall-checks` is not a directory | Click `Path(file_okay=False, exists=True)` | Exit 2 |
| A count query times out or is rejected after retries | `SparqlError` in `scan_pitfalls` | `Failure(kind pitfall, check_id)`; the next check runs; exit 1 |
| An example query fails | Same | `Failure`; the result keeps its count, no examples; exit 1 |
| The store ignores `FROM` (union-default stores) | Not detectable | Documented: results then cover the store's default dataset |
| An example term is not a writable IRI | `to_iriref` in the generators | The page shows it as text; the TSV writes it as is (tab and newline stripped) |
| An example value contains markup | Autoescape | Shown as text |
| A profile is saved without `pitfalls` (older or scan off) | The field is absent | No section, no TSV file; nothing breaks |
| `--fail-on` with recorded failures | `main.py` | Exit 1 (failures take precedence) |
| `--format pitfalls` without scan results | `PitfallsGenerator.outputs()` is empty | No file; INFO `no pitfall results in the profile` |

## Risks / Trade-offs

- [Full-scan checks on large endpoints] → Opt-in, with per-query timeouts and recorded failures.
  `--skip-pitfall` drops expensive checks. `seconds` per result shows which ones cost.
- [Closed-world data checks flag OWL-legal data] → Titled as data checks against the declared schema;
  the docs explain the reading.
- [Heuristic false positives (P07, P20, P21, P12/P30)] → Marked `heuristic`, minor importance.
- [rdflib `FROM` in the unit fake] → rdflib's `Dataset` evaluates `FROM <g1> FROM <g2>` over its own
  named graphs, so stage tests can run wrapped queries through `FakeSparql`. It tries an HTTP fetch
  for a `FROM` graph it does not hold, so `tests/unit/fakes.py` sets
  `rdflib.plugins.sparql.SPARQL_LOAD_GRAPHS = False`. The per-check tests run on graph content
  directly; the wrapping is checked again on Oxigraph in e2e.
- [The checks change the profile size] → At most `pitfall_examples` examples per check per graph:
  29 × 10 rows.

## Open Questions

None blocking. The developer will revise the test strategy after implementation (developer, 2026-11-01).
