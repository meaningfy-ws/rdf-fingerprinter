# Changelog

All notable changes to this project are documented in this file. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [3.7.1] - 2026-11-08

### Changed
- Docs: the README, which is the PyPI page, is reworked: linked badges, an outputs overview
  image, who the tool is for, why its results can be trusted, a quick start, and absolute links
  (the CHANGELOG link was broken on PyPI).
- Packaging: a clearer description, Changelog and Issues links, and an SPDX license string.

## [3.7.0] - 2026-11-08

OpenSpec change `consumer-api-gaps` (issues #76, #77, #75, #69).

### Added
- `RDF_FINGERPRINTER_MAX_ANSWER_BYTES` (default 256 MiB) and `AnswerTooLarge` (a `PermanentError`):
  a query stops reading an answer longer than the limit.
- `ConfigurationError`, a `UsageError` subclass in `fingerprint.service_layer.exceptions`, raised for
  an invalid `RDF_FINGERPRINTER_*` setting; an invalid endpoint URL stays a plain `UsageError`.
- `describe_diagrams` and `DiagramFile`: for each PlantUML file, its graph, overview or module,
  module name and part number, without parsing the file name.
- Docs: the API reference lists all five formats with their files, and the worst case of a query.

### Changed
- `SparqlHttpClient` enforces `timeout_seconds` as a deadline for the whole attempt (checked
  between reads), not per socket read; a slow answer raises `QueryTimeout`.
- An answer to the graph listing without `?g` raises `PermanentError` instead of `KeyError`; a run
  records it as a failure of the listing and profiles the default graph.
- Docs: the worst case of a query holds once the answer has started; connecting and the response
  headers are bounded per socket operation only.

## [3.6.1] - 2026-11-08

Documentation release; no change to the library's behaviour.

### Added
- Docs: a **Comparison** page, rdf-fingerprinter against SHACL Play, sheXer, void-generator, QSE,
  shaclgen, LODStats and RDF2Graph, feature by feature in collapsible groups, with references.
- Docs: the outputs grouped by who reads them (people, agents, machines) on the Representations
  page; references for OOPS! and ROBOT on the Pitfalls page.
- README: a *What it does* section.

### Changed
- `fingerprint --help` lists exit status 5 (pitfalls at the `--fail-on` level).
- Docs: Architecture, How It Works, Glossary and the home page describe 3.5 (pitfall scans, schemas
  for LLMs, ShExC, reified relations); they make clear that LinkML generates only the tool's own
  model, not the SHACL or diagrams.
- The `namespace-filter` change is archived and its requirements are merged into the specs.

## [3.6.0] - 2026-11-08

Two additions for library callers (OpenSpec change `graph-listing-and-typing`).

### Added
- **`list_named_graphs(url, settings, *, sparql=None)`** in `fingerprint.service_layer.handlers`:
  the endpoint's named graphs, sorted, through the run's own discovery query; errors raise
  (`EndpointUnreachable`, `QueryTimeout`, `PermanentError`), never an empty list (#63, OpenSpec change
  `graph-listing-and-typing`).
- **Typed package.** `fingerprint` and `fingerprint_report_templates` ship `py.typed` (PEP 561), so
  type checkers read the library's annotations (#64).

## [3.5.0] - 2026-11-03

The fingerprint recognises reifications (statements about statements) and shows the links they stand
for as reified relations of their class (OpenSpec change `singleton-property-pattern`).

### Added
- **Reification probes.** Every run asks one SPARQL `ASK` per kind: `rdf_statement`,
  `resource_as_predicate` (which also captures singleton properties: `rdf:singletonPropertyOf` is not
  standard, so it is a reifier property and never names a relation), `owl_axiom`, `negative_property_assertion` and
  `triple_term` (RDF 1.2 `rdf:reifies`, counted only). Only the kinds found are captured.
- **More kinds.** `graph_statement` and `nanopublication` (counted only); `prov_qualified`,
  `dcat_qualified`, `schema_role`, `wikibase_statement` and `cidoc_property_of_property`, each named by
  the predicate or type the data uses; `blank_nary` (an untyped blank node carrying the qualifications)
  and `structured_value` (an untyped `rdf:value` node). Typed blank nodes and value nodes stay ordinary.
  SKOS-XL labels are not a reification.
- **Reified relations per class**: kind, property, object class, statements and reifier properties,
  in the report, the pattern schema (`~>` lines), the PlantUML diagram and `profile.json`
  (`reified_relations`, `reification_kinds`, `reification_counts`); ShExC and SHACL note them
  in comments, without constraints. See the new *Reified Relations* docs page.
- **`--reifications/--no-reifications`** (setting `reifications`, on by default).

### Changed
- **The default fingerprint hides reification machinery.** In a graph with reifications, singleton
  predicates, `rdf:Statement` nodes, `owl:Axiom` and the like leave the ordinary classes and
  properties. `--no-reifications` gives the previous fingerprint.

### Removed
- **BREAKING: the packaged pitfall check `x_individual_as_predicate`** (28 checks remain); the
  pattern it flagged is now a reified relation. `--skip-pitfall x_individual_as_predicate` now fails
  as an unknown check. Supply the query with `--pitfall-checks` to keep it as a defect.

## [3.4.1] - 2026-11-03

No change to the published package: the test suite, the make targets and CI are reorganised
(OpenSpec change `lean-fast-suite`).

### Changed
- **One feature gate: `make check-all`** runs in parallel (pytest-xdist) and includes the Hypothesis
  tests (`ci` profile) and the coverage floors. CI runs it on every PR.
- **Release gate:** `make check-release` (local) runs `check-all`, `make test-release`,
  `make test-properties` (random Hypothesis inputs) and `make test-e2e`. The new `release-check`
  workflow runs the release tests, the e2e tests and a wheel install on PRs into `master`.
- **Mutation testing runs after a release** (and on demand), not weekly.
- The service-layer unit tests are pruned where the BDD scenarios already prove the behaviour;
  coverage and mutation score are unchanged.

### Removed
- **BREAKING for contributors:** `make check-all-fast`, `make check-all-deep`, `make test-fast` and
  the weekly deep workflow (`deep.yml`). Use `make check-all` and `make check-release`.

## [3.4.0] - 2026-11-02

The pattern schema is split into five files per graph (OpenSpec change `llm-schema-split`), so a model
or a script reads only the part it needs.

### Changed
- **BREAKING: five files replace `pattern-<graph>.txt`.** `fingerprint-gen-pattern` and
  `--format pattern` now write `prefixes-<graph>.md`, `patterns-<graph>.md`, `patterns-<graph>.csv`,
  `glossary-<graph>.md` and `glossary-<graph>.csv`. The `PREFIX` lines and the glossary left the
  pattern file; read them from the sibling files. Nothing writes `pattern-<graph>.txt` any more.
- **BREAKING: `skos:altLabel` no longer becomes a label.** Alt labels are stored and shown as alt
  labels; a term with only alt labels has no label in a profile collected with 3.4. A profile saved
  earlier still holds the old labels.
- **BREAKING: `skos:scopeNote` is a note, not a description.** The description is `skos:definition`,
  `rdfs:comment` or `dcterms:description`; notes appear in the glossary CSV only.
- **BREAKING: the notes of filters read `Hidden: <n> classes.` and `Excluded namespaces: <note>.`** in
  the patterns Markdown (they were `# hidden:` and `# excluded namespaces:` comment lines). The ShExC
  keeps its comment lines.
- **BREAKING: a custom `--template` package for the pattern schema** now receives `view` as a
  `PatternFile` (the file's template name and the graph's view), five times per graph, instead of
  the graph's view once.
- **BREAKING: `make check-all` is now the fast gate** (static checks and tests without the Hypothesis
  property tests; coverage is reported to Codecov without a floor). `make check-all-deep` adds the
  Hypothesis tests and the coverage floors; CI runs it weekly and on demand (`deep.yml`).
- Docs: the *Schemas for LLMs* page describes the five files, the CSV columns and a filtering
  example, with sizes re-measured on the new golden files.

### Added
- **Kind codes in the glossary**: `C` class, `dP` datatype property, `oP` object property, `P` property
  with no collected objects, `D` datatype.
- **Alt labels and notes** in the profile (`term_annotations`) and in the glossary CSV, one row per
  term and language; the glossary Markdown shows the alt labels in the language of the label.
- **CSV files**: `patterns-<graph>.csv` (one row per block and edge, 23 columns) and
  `glossary-<graph>.csv` (full, uncut texts), both RFC 4180, with ` | ` between several values.
- **Prefix counts**: `prefixes-<graph>.md` gives, per prefix, its classes, properties, instances and
  triples in the patterns.
- `make check-all-fast` and `make check-all-deep`.

## [3.3.0] - 2026-11-02

Namespace filters that work (OpenSpec change `namespace-filter`). Excluding a namespace now leaves
out every term of it in every output, so a crowd of generated terms (brainframe's 619 singleton
properties `relationid:<uuid>`) no longer swamps the schema, the shapes or the report.

### Changed
- **`--exclude-namespace` now leaves out every term of the matching namespaces in every output**
  (report, SHACL, ShExC, PlantUML, pattern schema), not only their classes: properties, edge
  targets, co-types, subclass parents, single written values and glossary lines. The meta
  vocabularies (rdf, rdfs, owl, sh) are still hidden at class level only, unless you name them.
- **A full namespace IRI is now a stem**: given to `--exclude-namespace` or `--include-namespace`,
  it also matches the namespaces under it, so `http://example.org/` now also catches
  `http://example.org/rel/`.

### Added
- **Prefix globs and IRI stems**: `--exclude-namespace 'relation*'` or
  `--exclude-namespace 'https://my.brainframe.com/#/knowledge/'` cover several namespaces at once.
  Matching is case-sensitive; `--include-namespace` still wins over an exclude.
- **An `excluded namespaces` note** in each text output, e.g.
  `# excluded namespaces: relationid (classes 0, properties 619, values 0)`.
- **A warning when a name hides nothing**:
  `--exclude-namespace <name>: no term in this namespace; ignored`.
- **Report**: a switch per namespace now also hides its property rows; the namespace table lists
  every namespace, marks the excluded ones and keeps their real uses; a caveat lists what was left
  out.
- Docs: combined filters with measured sizes; a *Branches* section for the new `develop`
  integration branch.

On the brainframe workspace graph, `--exclude-namespace relationid` takes the pattern schema from
221,523 to 98,323 characters and the report from 1.34 MB to 0.82 MB.

Nothing breaks: `profile.json` is unchanged, and datatypes, pitfall findings and collection failures
are never filtered.

## [3.2.0] - 2026-11-01

Schemas for LLMs (OpenSpec change `llm-schema-tools`, stage 1). The fingerprinter can now write a
dataset's schema in a form compact enough to hand to a language model as context.

### Added
- **The pattern schema** (`--format pattern`, `fingerprint-gen-pattern`): one `pattern-<graph>.txt`
  per graph in an arrow notation, `(:Class) -prop-> (:Target)`, with counts, cardinalities, value
  ranges and top values. Blank nodes are seen through up to three hops, and each block says where it
  is reached from. A glossary below gives each term one label and one description. Names are
  prefixed everywhere, and only the prefixes in use are declared. On the sample data it is about a
  fifth of the size of the SHACL shapes.
- **Enriched ShExC** (`--format shex`, `fingerprint-gen-shex`): the same view as valid ShExC, with
  nested `BNODE` shapes and the statistics in `#` comments.
- **Term labels and descriptions** (query Q12, at every collection depth): `skos:prefLabel`,
  `skosxl:prefLabel` (through `skosxl:literalForm`), `rdfs:label`, `dcterms:title` (`skos:altLabel`
  when there is no other), and one description by `skos:definition` > `rdfs:comment` >
  `dcterms:description` > `skos:scopeNote`, for every class and property; saved as
  `term_annotations` in `profile.json`.
- **`--ontology FILE`** on `fingerprint-gen-pattern` and `fingerprint-gen-shex`: labels from an
  ontology file (Turtle, RDF/XML, TriG, N-Quads, …) win over those found in the data.
- **`--min-instances N` and `--max-classes N`** on the same commands: leave out rare classes, or
  keep only the largest groups; the output says how many classes it hid.
- Docs: the *Schemas for LLMs* page, glossary terms, and Q12 on the statistics page.

### Changed
- An IRI that is a property's only top value is now written with a prefix, like every other IRI.
- `make check-wheel` no longer fails at random (SIGPIPE under `pipefail`).

Nothing breaks: `profile.json` gains `term_annotations`, and profiles saved by 3.1 still load.

## [3.1.0] - 2026-11-01

Pitfall scans (OpenSpec change `pitfall-scans`). The fingerprinter can report what is wrong with how
a dataset is modelled, next to what it holds.

### Added
- **`--pitfalls`**: after profiling each graph, run a catalogue of 29 SPARQL checks. 25 follow the
  OOPS! pitfall catalogue (P04–P41 where SPARQL can express them); 4 are the fingerprinter's own:
  punning, individuals as predicates, and subjects or objects outside the declared domain or range.
  `--schema-graph` names the ontology graphs: they get the schema checks, and every other graph runs
  the data checks joined with them. Counts and the first `--pitfall-examples` rows are saved in
  `profile.json`.
- **Pitfall findings** in the report's *Caveats and pitfalls* section, with class badges, and the
  **`pitfalls` format**: ROBOT-style TSV per scanned graph (`--format pitfalls`,
  `fingerprint-gen-pitfalls`).
- **A *Taxonomy* section** in the report: the class tree of each graph, with popularity bars.
- **Class indicators**: each class shows its instances and its data and object property counts, in
  the contents and its heading. The namespace table shows each namespace's uses.
- **`--fail-on critical|important|minor`**: exit status 5 when pitfalls reach the level.
- The checks of a graph run `--concurrency` at a time. A default graph scanned with schema graphs
  given (it cannot be joined with them) is a logged warning and a report caveat.
- **`--pitfall-checks DIR`** (your own `.rq` checks, same contract) and `--skip-pitfall ID`.
- **`make scan-files ONTOLOGY=… [DATA=…] OUT=…`**: scan RDF files on a separate in-memory Oxigraph.
- Docs: the Pitfalls page with the catalogue; the settings and exit-status tables.

### Changed
- The report orders by importance: classes by namespace, then instances; properties grouped own,
  refined, inherited, then by use; the namespace table grouped by prefix source, then by uses. SHACL,
  PlantUML and TSV keep their IRI order.
- The *Caveats* section is now *Caveats and pitfalls*.

Nothing breaks: the scan is off by default, and exit 5 only appears with `--fail-on`.

## [3.0.0] - 2026-10-31

Readable representations (OpenSpec change `readable-representations`). Every IRI in every output is
written as `prefix:local`, the report is one usable static page, shapes have readable names, and
diagrams are split into digestible modules.

### Added
- **A prefix for every namespace.** After collection, each namespace in use is named from your prefix
  file (`--prefixes FILE` or `RDF_FINGERPRINTER_PREFIXES_FILE`), the packaged prefixes, prefix.cc's
  prefix list (read once per run; `--no-prefix-lookup` or `RDF_FINGERPRINTER_PREFIX_LOOKUP=false`
  to skip it), or a generated name (`ex-core`, `brainframe`, `graph2`). The table, with each prefix's
  source, is saved in `profile.json`; outputs shorten each IRI by its longest namespace.
- **Namespace filters.** `--exclude-namespace` / `--include-namespace` (prefix or IRI, repeatable) on
  `fingerprint` and the `fingerprint-gen-*` commands; the report lists what it hid.
- **Report page features:** a table of contents by graph, namespace and class, a search box, one
  switch per namespace, light and dark mode, and phone width; readable without JavaScript and with
  no external request.
- **`--module-size N`** (default 15) on `fingerprint` and `fingerprint-gen-puml`;
  **`--shapes-namespace`** now also on `fingerprint`.

### Changed
- **BREAKING** `profile.html` is no longer written: `main.html` is the one HTML page, written by the
  run and by `fingerprint-gen-doc`; `--format doc` on `fingerprint` writes nothing more.
- **BREAKING** The library entry is `fingerprint_report(url, folder, settings, *, formats, options,
  template, user_prefixes, prefix_list, sparql, renderer)`. `generate_endpoint_fingerprint_report`,
  `generate_report_builder_config` and `render_report` are removed; custom report templates render
  the document view model (`view`, a `ProfileDocument`) instead of `conf.profile`. Migration: see the
  API reference.
- **BREAKING** SHACL shapes are named `<class namespace>/shape/<local>` under `<prefix>-shape:`
  (or `shape:<prefix>-<local>` in a given `--shapes-namespace`), and property shapes are named IRIs;
  `RDF_FINGERPRINTER_SHAPES_NAMESPACE` is unset by default (was `urn:fingerprint:shape:`).
- **BREAKING** PlantUML writes, per graph, an overview (`diagram-<graph>.puml`) and one file per
  namespace module (`diagram-<graph>--<module>.puml`) instead of one file per graph; custom PlantUML
  templates receive `DiagramOverview` / `DiagramModule` views.
- **BREAKING** Classes of `rdf`, `rdfs`, `owl` and `sh` are hidden from every output by default
  (`--include-namespace owl` brings one back).
- **BREAKING** `RDF_FINGERPRINTER_PREFIXES_FILE` adds your prefixes over the packaged ones instead of
  replacing them.
- A graph with no shown class produces no shapes or diagram file.
- The report renders much faster (on a 79k-triple store: 1.4 s instead of 10.8 s) and is smaller.

## [2.1.0] - 2026-10-31

Representations release (OpenSpec change `profile-representations`). A fingerprint is saved once
and can be published, without querying the endpoint again, as SHACL shapes, a PlantUML class diagram
and an application-profile document.

### Added
- **`profile.json`.** `fingerprint` (and `generate_endpoint_fingerprint_report`) saves the raw
  profile run beside the report, before the report is rendered, so a template error loses nothing
  collected. Its JSON Schema ships as `fingerprint/domain/profile_run.schema.json`;
  newer 2.x readers load older files.
- **Generators**, modelled on LinkML's: `fingerprint-gen-shacl`, `fingerprint-gen-puml` and
  `fingerprint-gen-doc` read a `profile.json` and write one representation (`--threshold`,
  `--template`, and `--shapes-namespace` for SHACL); exit 0, 2 (usage) or 4 (unexpected).
- **`fingerprint --format shacl|puml|doc`** (repeatable) renders representations in the same run.
- **SHACL shapes**, one Turtle file per graph: open node shapes, counts from the accepted
  cardinality, `sh:datatype` / `sh:class` / `sh:nodeKind` / `sh:or` from the values, annotated with
  confidence and instance counts, and graded by severity so that, validated against the data they
  came from, they report no `sh:Violation`.
- **PlantUML class diagrams**, one source file per graph, and an **application-profile document**
  (`profile.html`) in the style of SEMIC / EU application profiles.
- Template filters for custom packages: `turtle_iri`, `turtle_term`, `turtle_string`,
  `turtle_number`, `curie`.
- Library: `fingerprint_report(..., formats=(), sparql=None)` (any `SparqlPort`), and
  `fingerprint.service_layer.representations.generate_representations` /
  `generate_from_profile_file`.
- Docs: Representations, How It Works, Glossary, Architecture Decisions (AD-1 to AD-12) and a use
  case catalogue (UC-W1, UC-W2 and their realisations).

- **Operational variables** (OpenSpec change `domain-object-model`): `RDF_FINGERPRINTER_PROFILE_FILE`,
  `_RETRY_BACKOFF_SECONDS`, `_TIMEOUT_MARKERS`, `_ERROR_EXCERPT_LENGTH`, `_SHAPES_NAMESPACE`,
  `_DEFAULT_GRAPH_LABEL` and `_PREFIXES_FILE`, each defaulting to the former constant; read through
  `fingerprint.config`, checked before any query (a bad value exits 2 naming the variable).
- `model/fingerprint_views.yaml` → `fingerprint.domain.views`: the objects every representation
  template receives, `GeneratorOptions` and the `RepresentationFormat` enum.

### Changed
- The output folder of `fingerprint` now also holds `profile.json`.
- Report rendering and exceptions moved to their layers (`adapters/template_renderer.py`, an
  `exceptions` module per layer); every 2.0 import path of these still works.
- Values are LinkML-generated objects and enums throughout (collection, analytics, generators);
  `tests/unit/test_no_composed_dicts.py` keeps new dicts out.
- **The SPARQL client** sends a SPARQL 1.1 Protocol form POST through the standard library (with the
  per-query timeout) and reads the answer with rdflib; the request differs from SPARQLWrapper's
  (no `format`/`output`/`results` parameters, `Accept: application/sparql-results+json`,
  `User-Agent: rdf-fingerprinter/<version>`). Failure messages keep the status and a body excerpt but
  lose SPARQLWrapper's wording. Literals keep the endpoint's lexical form. User info in the endpoint
  URL is sent as HTTP Basic authentication, never in the request URL or a message; only `http` and
  `https` endpoints are accepted (exit 2 otherwise).
- A prefixes file given by `RDF_FINGERPRINTER_PREFIXES_FILE` is checked (plain prefix names, writable
  IRIs) before any query or write.
- **Settings sources are checked one by one:** a malformed value in a lower-precedence source (say
  the config file) now fails even when a higher one (the CLI) sets the same setting.
- `make test` fails under 80 % coverage; every Gherkin scenario is tagged with its use case.

### Breaking (2.0 Python API, not used in production yet)
- `fingerprint.domain.generated.profile` is now `fingerprint.domain.profile` (and the JSON Schema
  `fingerprint/domain/profile_run.schema.json`).
- `fingerprint.adapters.sparql.SparqlWrapperClient` is now `SparqlHttpClient`; `SparqlPort.select`
  returns rdflib `ResultRow`s; `rows_from_json` is gone.
- `cardinality_statistics` and `cardinality_label` take a list of `CardinalityBin` and return
  `CardinalityStatistics` / `CardinalityChoice`; `drop_none` is gone.
- Custom representation templates read `view.<field>` of the views model (no more `view.graph.<field>`
  or tuple unpacking); `Generator.serialize()` returns `list[RenderedDocument]`.

### Dependencies
- rdflib is now a declared runtime dependency (it was already installed through eds4jinja2);
  pySHACL 0.40.1 for tests.
- SPARQLWrapper is no longer a direct dependency.
- eds4jinja2 ≥ 2.1: every format and the report are rendered and written through its
  `render_documents` / `make_documents`.

## [2.0.0] - 2026-10-31

Hardening release (OpenSpec change `harden-fingerprinter`). Statistics are collected in Python
with bounded, class-scoped SPARQL 1.1 queries, analysed by pure functions over a LinkML-defined
profile, and rendered without querying. Large graphs no longer time out the report, and failures
are visible instead of silent.

### Breaking
- **Named graphs are profiled by default.** With no graph selected, 1.x profiled only the default
  graph (`selected_graphs=None` → `[""]`); 2.0 profiles the default graph and every named graph.
  Pass `selected_graphs=[""]` / `--graph ""` for the old behaviour.
- **Exit codes.** The CLI exits 1 when the report was written with failed measurements, 2 on a
  usage error (including a missing output folder), 3 when the endpoint is unreachable, 4 on an
  unexpected error. 1.x exited 0 and printed errors into the report.
- **`rdf:type` is no longer a property row** in the class tables; the other types of the
  instances are shown as the class's parents.
- **Report templates render `conf.profile`** (the analysed profile) instead of running SPARQL.
  Custom templates keep `conf.default_endpoint`, `conf.selected_graphs` (now the graphs actually
  profiled) and the eds4jinja2 fetchers. IRIs in the default report are shown with prefixes.

### Added
- Precision per class: `exact`, or `first N of M` when the exact read timed out (policy `auto`);
  policies `exact` and `first_n` force one mode. A completeness check finds properties used only
  outside the first N.
- New report columns: confidence, cardinality label (`exactly_one`, `zero_or_one`, …),
  inheritance (`own` / `inherited` / `refined`) and language coverage; a Collection section with
  the settings used and every failed measurement.
- Collection settings (`--depth`, `--precision`, `--first-n`, `--top-k`, `--threshold`,
  `--object-types`, `--completeness`, `--graph-stats`, `--timeout`, `--concurrency`, `--graph`,
  `--config`), also as `RDF_FINGERPRINTER_*` environment variables and
  `additional_config["collection"]`.
- Per-query timeout (default 60 s), retries of transient errors, and classes profiled concurrently.
- `collect`, `analyse` and `render_report` usable separately; the raw profile serialises to JSON.
- The endpoint URL is logged and recorded without user info or query string, which may carry
  credentials. The packaged report escapes every value that comes from the endpoint.
- LinkML models `model/fingerprint_stats.yaml` and `model/fingerprint_analytics.yaml`, generated
  into read-only Pydantic classes (`make generate-models`, checked by `make check-models`).

### Dependencies
- `pydantic` and `SPARQLWrapper` are direct dependencies again (imported by the code).

### Development
- Onion layers `entrypoints > service_layer > adapters > domain` enforced by import-linter, plus
  contracts keeping the domain free of I/O libraries and the generated code free of project
  imports.
- BDD features in `tests/features/` run with pytest-bdd; `FakeSparql` runs the real client over an
  in-memory rdflib store.

## [1.0.0] - 2026-10-31

Modernisation release (OpenSpec change `adopt-meaningfy-tooling`). The public API is unchanged;
the breaking changes below are bundled into the first stable release.

### Breaking
- **Python 3.12+ required**; tested on 3.12, 3.13 and 3.14.
- **eds4jinja2 2** (pandas 3 / numpy 2) replaces eds4jinja2 0.2. Report output is unchanged.
- **The library no longer configures logging.** `logging.conf` is gone and importing `fingerprint`
  has no side effects; loggers are named after their modules (`fingerprint.service_layer.handlers`,
  …) instead of `fingerprinter`. The `fingerprint` CLI logs at INFO to stderr.
- `rdflib`, `SPARQLWrapper` and `importlib-resources` are no longer direct dependencies.
- `fingerprint.__date__` is removed; `fingerprint.__version__` reads the installed metadata.

### Fixed
- Importing the package from any directory other than the repo root no longer fails with
  `FileNotFoundError: logging.conf doesn't exist`.
- The report works on strict SPARQL 1.1 stores such as Oxigraph: `GROUP_CONCAT` arguments are
  wrapped in `STR()`; before, the object/property type columns came back empty (`nan`).
- The packaged templates are located with `importlib.resources.files()`; the leaked
  `path(...).__enter__()` context is gone.
- `generate_endpoint_fingerprint_report` is annotated as returning a `Path` (what it always returned).

### Development
- Packaging moved from setuptools + pip to **Poetry** (committed `poetry.lock`).
- New gate `make check-all`, run by CI on every pull request: Ruff, mypy, import-linter,
  `openspec validate --strict`, and the tests.
- Unit tests need no SPARQL store and run in CI; end-to-end tests run locally against an in-memory
  **Oxigraph** (`make test-e2e`). The Fuseki test targets are gone.
- Releases publish to PyPI from a GitHub Release via Trusted Publishing (no API token).
- Documentation moved from Sphinx / Read the Docs to AsciiDoc + Antora on GitHub Pages:
  https://meaningfy-ws.github.io/rdf-fingerprinter/
- `SECURITY.md` added.

## [0.3.1] - 2024-02-01

Last release on setuptools; Python 3.8+.
