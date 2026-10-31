> Derives from: EPIC `domain-object-model` (`proposal.md`, DEC-1..DEC-8)

## Context

State at PR #40 (2.1.0, unreleased), counted in the code:

- **Dicts as values**: `domain/analytics.py` (≈18 dict constructions: helpers return `dict[str, Any]`,
  `analyse` validates once), `service_layer/collection.py` (≈24: raw profile dicts, `Row` dicts),
  `service_layer/generators/*` (≈34: view dicts read by the templates), `service_layer/settings.py`
  (merged `values` dict), `adapters/sparql.py` (`rows_from_json` → `dict[str, str | None]`).
- **Generated code** in `fingerprint/domain/generated/profile.py` (+ `profile_run.schema.json`) from
  `model/fingerprint_stats.yaml` and `model/fingerprint_analytics.yaml`; the `generated` import-linter
  contract and the Ruff exclude point there.
- **Configuration**: `adapters/settings_sources.py` (environment, config file), `resolve_settings`
  (CLI > env > `selected_graphs` > config > default); operational constants scattered as module
  constants (`PROFILE_FILE`, `BACKOFF_SECONDS`, `TIMEOUT_MARKERS`, `EXCERPT`, `DEFAULT_SHAPES_NAMESPACE`,
  `DEFAULT_GRAPH_LABEL`, `PREFIXES_FILE`).
- **SPARQL**: `SparqlWrapperClient` (SPARQLWrapper, POST, JSON, per-query timeout, retries 1 s / 4 s,
  `classify`). rdflib's `SPARQLConnector` calls `urlopen` **without a timeout** (checked in rdflib
  7.6.0: only headers are forwarded), so it cannot replace the client on its own.
- **Rendering**: `adapters/template_renderer.py` renders through `ReportBuilder.template_env` because
  `make_document()` writes one file named after the template, unchecked. eds4jinja2 2.0.0
  (`../eds4jinja2`, own spine, no release authority for agents in its AGENTS.md).

## Goals / Non-Goals

**Goals:** DEC-1..DEC-7 realised with no behaviour change (DEC-8): the 2.1 scenarios, the golden files
and `make test-e2e` unchanged and green.

**Non-Goals:** the EPIC's no-gos. No new LinkML semantics for the profile; no new configuration file
format; no eds4jinja2 change beyond P-6.

## Decisions

- **P-1 The rule and its check (DEC-1).** AGENTS.md *Working conventions* gains: "Values are
  LinkML-generated Pydantic objects and enums, never composed dicts." A unit test
  `tests/unit/test_no_composed_dicts.py` walks the AST of `fingerprint/**/*.py` (generated modules
  excluded) and fails on: dict displays and dict comprehensions inside a function body; calls to
  `dict(...)`; `dict[...]`, `Dict[...]` or `Mapping[...]` in a parameter or return annotation — unless
  the line carries `# dict-ok: <reason>`. Module-level constants (UPPER_CASE names) are tables, not
  values, and pass. The test prints each offending `file:line`.
- **P-2 Generated modules (DEC-2, DEC-3).** `make generate-models` writes
  `fingerprint/domain/profile.py` (both profile schemas, as today) and `fingerprint/domain/views.py`
  (from the new `model/fingerprint_views.yaml`), and `fingerprint/domain/profile_run.schema.json`;
  `check-models` diffs all three. Ruff excludes the two generated modules; the `generated` contract
  becomes "generated modules import no project code" over `fingerprint.domain.profile` and
  `fingerprint.domain.views`. `fingerprint/domain/generated/` is removed.
- **P-3 The views schema** `model/fingerprint_views.yaml` (namespace `fp:views/`, imports nothing from
  the profile schemas; values are strings and numbers already written for the target format):
  - enums `RepresentationFormat` (`shacl`, `puml`, `doc`) and `ShapeSeverity` (`info`, `warning`, `violation`);
  - shared: `PrefixDeclaration {prefix, namespace}`, `Annotation {predicate, value}`;
  - SHACL: `ShapesGraph {graph_label, prefixes*, node_shapes*}`, `NodeShape {shape, target,
    annotations*, property_shapes*}`, `PropertyShape {path, constraints*, severity?, annotations*}`;
  - PlantUML: `DiagramGraph {graph_label, classes*, parent_boxes*}`, `DiagramClass {alias, label,
    attributes*, generalisations*, associations*}`, `DiagramBox {alias, label}`;
  - document: `ProfileDocument {overview, namespaces*, graphs*, caveats}`, `Overview {endpoint?,
    started_at?, finished_at?, tool_version?, settings*}`, `SettingValue {name, value}`, `DocumentGraph
    {slug, label, diagram, classes*}`, `DocumentClass {iri, label, anchor, instances, precision,
    sampled, parents*, properties*}`, `ParentReference {label, source}`, `DocumentProperty {iri, label,
    types*, cardinality, usage, inheritance}`, `Caveats {sampled*, failures*, skipped*}`, `SampledClass
    {graph, class_label, precision}`, `FailureNote {graph, class_label, measurement, message}`.
  Frozen, `extra=forbid`, like the profile model. Templates read the same names as today except where
  a key becomes an attribute (`f["class"]` → `f.class_label`); the golden files must not change.
- **P-4 Generators build bottom-up.** The visit hooks return view objects and receive their children:
  `visit_property(graph, cls, prop) -> P | None`, `visit_class(graph, cls, properties: list[P]) -> C |
  None`, `visit_graph(graph, classes: list[C]) -> G | None` (frozen objects are built once, so a parent
  is made after its children; `end_graph` disappears). `serialize()` / `render_graphs()` keep their
  contracts. `GENERATORS` is keyed by `RepresentationFormat`.
- **P-5 SPARQL through the standard library and rdflib (DEC-5, adjusted).** Because rdflib's
  `SPARQLConnector` cannot time a query out, the adapter sends the query itself with
  `urllib.request.urlopen(Request(endpoint, data=query, method="POST", headers={Content-Type:
  application/sparql-query, Accept: application/sparql-results+json}), timeout=…)` and parses the body
  with `rdflib.query.Result.parse(..., format="json")`. `SparqlPort.select` returns `list[ResultRow]`
  (rdflib terms: `URIRef`, `BNode`, typed `Literal`); `ask` returns `bool` (`Result.askAnswer`).
  SPARQLWrapper leaves the dependencies; `classify` keeps its table on urllib/socket errors only (the
  SPARQLWrapper branches go). Rejected: subclassing `SPARQLConnector` to add a timeout (private API);
  keeping SPARQLWrapper.
- **P-6 eds4jinja2 2.1 (DEC-7)**, a change in `../eds4jinja2` with its own spec and tests:
  `ReportBuilder.make_documents(outputs: Mapping[str, Mapping[str, Any]], check: Callable[[str, str],
  None] | None = None) -> list[Path]` renders the configured template once per output name with that
  output's variables, calls `check(name, text)` for each, and writes all files only if every check
  passed; `make_document()` keeps its behaviour. The template renderer adapter then calls
  `make_documents` (one output for the report and the document, one per graph for SHACL and PlantUML);
  `JinjaTemplateRenderer.render` / `write` and the `template_env` guard test go. Released as eds4jinja2
  2.1.0 **with the developer's go-ahead** (that repository grants agents no release authority);
  rdf-fingerprinter requires `eds4jinja2>=2.1,<3`.
- **P-7 Configuration (DEC-6).** `fingerprint/adapters/config_resolver.py`: `ConfigResolverABC`,
  `EnvConfigResolver`, `DefaultConfigResolver`, `env_property(default_value=None)` as in the Meaningfy
  settings pattern. `fingerprint/__init__.py`: `class FingerprintConfig` and `config =
  FingerprintConfig()`; values resolve on access (no import-time side effects). Variables and defaults:

  | Variable | Default | Replaces |
  |---|---|---|
  | `RDF_FINGERPRINTER_PROFILE_FILE` | `profile.json` | `PROFILE_FILE` |
  | `RDF_FINGERPRINTER_RETRY_BACKOFF_SECONDS` | `1,4` | `BACKOFF_SECONDS` |
  | `RDF_FINGERPRINTER_TIMEOUT_MARKERS` | `timeout,time limit,timed out,estimated execution time` | `TIMEOUT_MARKERS` |
  | `RDF_FINGERPRINTER_ERROR_EXCERPT_LENGTH` | `200` | `EXCERPT` |
  | `RDF_FINGERPRINTER_SHAPES_NAMESPACE` | `urn:fingerprint:shape:` | `DEFAULT_SHAPES_NAMESPACE` |
  | `RDF_FINGERPRINTER_DEFAULT_GRAPH_LABEL` | `default graph` | `DEFAULT_GRAPH_LABEL` |
  | `RDF_FINGERPRINTER_PREFIXES_FILE` | the packaged `prefixes.json` | `PREFIXES_FILE` |
  | `RDF_FINGERPRINTER_<SETTING>` (each collection setting) | the LinkML default | the env branch of `resolve_settings` |

  The collection settings get a generated `SettingsOverride` class (every `Settings` slot, optional, no
  defaults) in `model/fingerprint_stats.yaml`; each source becomes one: CLI options →
  `SettingsOverride(**options)`, the environment → `config.settings_override()`, the config file →
  `SettingsOverride.model_validate_json` (adapter), the `selected_graphs` parameter → an override with
  that slot. `resolve_settings(*overrides)` builds `Settings` from the first non-None value per slot in
  precedence order, then applies the existing `(0, 1]` threshold rule. `settings_sources.py` goes.
  Stays constant (standards and protocol tables, not operations): `vocabulary.py` IRIs, `RDF_TYPE`,
  `QUERY_FILES`, `QUERY_KIND`, `MODES`, `NODE_KINDS`, `TOO_LARGE`, `LABEL_PREDICATES`.
- **P-8 Collection and analytics build objects.** Collection turns each `ResultRow` into model
  objects at once (`ValuePartition(node_kind=…, datatype=…, triples=int(row.n))`); analytics helpers
  return `PropertyAnalytics` / `ClassAnalytics` / `GraphAnalytics` / `ParentClass` objects (built with
  keyword arguments), and `drop_none` goes. `profile.json`, the analytics values and the report are
  unchanged.

## Algorithm / approach

### Order of work

eds4jinja2 2.1 can be built in parallel (task group 0), but group 7 needs its release. Every other
group is independent of it and keeps the suite green: config (2) → SPARQL (3) → collection (4) →
analytics (5) → views and generators (6) → renderer on eds4jinja2 (7). The dict check (1.2) starts with
today's offenders on an allow-list file, and each group removes its own entries; group 8 ends with an
empty allow-list.

### Safety net (DEC-8)

- Golden files (`tests/test_data/golden/`) byte-equal before and after every group.
- `sample-profile.json` is the 2.1 format; a live collection after group 4 must give an equal profile
  apart from timestamps and version.
- `make test-e2e` after groups 3, 4 and 7.

### Example — a property shape, before and after

```python
# before (dict)                                  # after (view object)
{"path": self.term(p), "constraints": [...],      PropertyShape(path=self.term(p), constraints=[...],
 "annotations": [("fp:confidence", "1.0")]}                     severity=ShapeSeverity.warning,
                                                                annotations=[Annotation(predicate="fp:confidence", value="1.0")])
```

### Anti-patterns

| Don't | Do instead | Why |
|---|---|---|
| Return or pass a `dict` | return a generated model object | DEC-1 |
| Compare an enum field to a string literal | compare to the enum member | free strings drift |
| Read `os.environ` outside the config resolver | `config.X` | DEC-6, testable with `DefaultConfigResolver` |
| Resolve config at import time | resolve on property access | "import has no side effects" |
| Subclass rdflib's `SPARQLConnector` | own `urlopen` + `Result.parse` | private API, no timeout |
| Change a golden file to make a group pass | find the behaviour change | DEC-8 |

## Error matrix

| Failure mode | How it is detected | Expected handling |
|---|---|---|
| a SPARQL response is not SPARQL results JSON | `Result.parse` raises | `PermanentError` ("unreadable response"), as today |
| HTTP 429/502/503, connection reset | `urllib.error` | transient → retries `RDF_FINGERPRINTER_RETRY_BACKOFF_SECONDS` |
| per-query timeout | `socket.timeout` / `TimeoutError` from `urlopen(timeout=…)` | `QueryTimeout`, as today |
| an environment variable with a wrong type (`RETRY_BACKOFF_SECONDS=x`) | the config property's coercion raises `ValueError` | usage error (exit 2) naming the variable |
| a view object built with a wrong field | Pydantic `ValidationError` | a bug: unit tests per generator catch it |
| eds4jinja2 older than 2.1 installed | import of `make_documents` fails | prevented by the dependency bound; the CLI exits 4 |
| a `check` fails for one output of a batch | `make_documents` raises before writing | none of that format's files is written (unchanged) |

## Risks / Trade-offs

- [A large diff in one change] → groups land as separate commits, each green; goldens per group.
- [eds4jinja2 release needs a person] → group 7 waits for it; the rest proceeds; if the release is
  refused, group 7 is dropped and the current adapter stays (the PLAN records it).
- [`Result.parse` performance on large results] → the same JSON decoding plus term objects; the
  benchmark EPIC will measure it.
- [`SettingsOverride` duplicates `Settings` slots] → generated from the same slots (`is_a`/mixins in
  LinkML or a slot list in one place); a test asserts the two have the same field names.

## Open Questions

- P-5 replaces the developer's literal choice (rdflib `SPARQLConnector`) with the standard library plus
  rdflib's parser, because the connector has no timeout. The developer may prefer to contribute a
  timeout to rdflib instead; the PLAN proceeds with P-5 unless told otherwise.
