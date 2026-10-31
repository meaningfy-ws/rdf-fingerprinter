> Derives from: EPIC `domain-object-model` (`proposal.md`, DEC-1..DEC-8)

## Context

State at PR #40 (2.1.0, unreleased), counted in the code:

- **Dicts as values**: `domain/analytics.py` (helpers return `dict[str, Any]`, `analyse` validates
  once), `service_layer/collection.py` (raw profile dicts, `Row` dicts, `"_:"`-prefixed blank nodes),
  `service_layer/generators/*` (view dicts; `serialize()`/`render_graphs()` return `dict[str, str]`),
  `service_layer/settings.py` (a merged `values` dict), `adapters/sparql.py` (`rows_from_json`),
  `domain/iri.py` (`Mapping` prefix tables), `handlers.py` (`additional_config: dict`, 1.x API).
  An AST scan by the clarity-gate reviewer finds 183 dict constructions or annotations today.
- **Generated code** in `fingerprint/domain/generated/profile.py` (+ `profile_run.schema.json`).
- **Configuration**: `adapters/settings_sources.py`; `resolve_settings` (CLI > env > `selected_graphs`
  > config > default; env booleans `1/true/yes/on`·`0/false/no/off`, `selected_graphs` comma-split,
  an empty `selected_graphs` ignored); operational module constants.
- **SPARQL**: `SparqlWrapperClient` POSTs form-encoded `query=…` and asks for JSON; `classify`
  maps SPARQLWrapper and urllib errors, incl. "500 whose message has a timeout marker → timeout".
  rdflib 7.6.0's `SPARQLConnector` has no timeout (verified twice).
- **Rendering**: `adapters/template_renderer.py` renders through `ReportBuilder.template_env`; the
  four templates unpack tuples (`for prefix, namespace in …`, `for predicate, value in …`,
  `for name, value in …`) and PlantUML reads `cls.links`.

## Goals / Non-Goals

**Goals:** DEC-1..DEC-7 with no behaviour change (DEC-8): 2.1 scenarios, golden files and
`make test-e2e` unchanged and green after every group.

**Non-Goals:** the EPIC's no-gos; no eds4jinja2 change beyond P-6.

## Decisions

- **P-1 The rule and its check (DEC-1).** AGENTS.md *Working conventions*: "Values are LinkML-generated
  Pydantic objects and enums, never composed dicts." `tests/unit/test_no_composed_dicts.py` walks the
  AST of `fingerprint/**/*.py` (the generated `domain/profile.py`, `domain/views.py` excluded) and
  reports `file:line` for:
  1. a `dict`, `dict[...]`, `Dict[...]` or `Mapping[...]` parameter or return annotation (bare `dict`
     included);
  2. a dict display, dict comprehension or `dict(...)` call inside a function body;
  
  except when (a) the dict is the direct value of a keyword argument named `update` (to `model_copy`)
  or is unpacked with `**` into a call (construction syntax, DEC-1), (b) it is assigned at module level
  to an UPPER_CASE name (a table), or (c) the line carries `# dict-ok: <reason>`. Expected marks after
  this change, each with its reason: eds4jinja2's configuration and `make_documents` outputs (adapter
  boundary), JSON being parsed into a model (`additional_config["collection"]`, the config file), the
  prefix table (`dict[str, str]` loaded once from `prefixes.json`, a lookup table), local lookup
  indexes built and consumed inside one function (`{c.class_iri: c for c in …}`), and the 1.x
  `additional_config: dict` parameter (public API). A temporary allow-list file
  (`tests/unit/composed_dicts_allowlist.txt`, `file:line` per entry) holds today's offenders; each
  task group removes its own; 8.1 requires it empty.
- **P-2 Generated modules (DEC-2, DEC-3).** `make generate-models` writes `fingerprint/domain/profile.py`
  and `fingerprint/domain/profile_run.schema.json` (task 1.3) and, from task 6.1, also
  `fingerprint/domain/views.py`; `check-models` diffs each module that exists. Ruff excludes the
  generated modules; the `generated` import-linter contract covers them.
- **P-3 The views schema** `model/fingerprint_views.yaml` (namespace `fp:views/`, no import of the
  profile schemas; values are already written for the target format):
  - enums `RepresentationFormat` (`shacl`, `puml`, `doc`), `ShapeSeverity` (`info`, `warning`,
    `violation`), `DiagramMemberKind` (`attribute`, `association`);
  - shared: `PrefixDeclaration {prefix, namespace}`, `Annotation {predicate, value}`,
    `RenderedDocument {file_name, text}` (what `serialize()` returns, as a list);
  - SHACL: `ShapesGraph {graph_label, prefixes*, node_shapes*}`, `NodeShape {shape, target,
    annotations*, property_shapes*}`, `PropertyShape {path, constraints*, severity?, annotations*}`;
  - PlantUML: `DiagramGraph {graph_label, classes*, parent_boxes*}`, `DiagramClass {alias, label,
    members*, generalisations*}`, `DiagramMember {kind, text}`, `DiagramBox {alias, label}`;
  - document: `ProfileDocument {overview, namespaces*, graphs*, caveats}`, `Overview {endpoint?,
    started_at?, finished_at?, tool_version?, settings*}`, `SettingValue {name, value}`, `DocumentGraph
    {slug, label, diagram, classes*}`, `DocumentClass {iri, label, anchor, instances, precision, sampled,
    parents*, properties*}`, `ParentReference {label, source}`, `DocumentProperty {iri, label, types*,
    cardinality, usage, inheritance}`, `Caveats {sampled*, failures*, skipped*}`, `SampledClass {graph,
    class_label, precision}`, `FailureNote {graph, class_label, measurement, message}`.
  
  Frozen, `extra=forbid`. **Template edits** (a Pydantic object iterates as `(field, value)` pairs, so
  every tuple unpacking must go; the rendered text stays the same):
  - `shacl_shapes/shapes.ttl`: `for p in view.graph.prefixes` → `@prefix {{ p.prefix }}: {{ p.namespace | turtle_iri }}`;
    `for a in ns.annotations` / `for a in ps.annotations` → `{{ a.predicate }} {{ a.value }}`; the
    severity line from `ps.severity` (`sh:Info`/`sh:Warning`, none for `violation`); `cls`→`ns`, `p`→`ps`.
  - `plantuml_diagram/diagram.puml`: attributes = `members` with kind `attribute` (`m.text`); the link
    lines = `{{ c.alias }} --> {{ m.text }}` for kind `association`; generalisations unchanged.
  - `profile_document/profile.html`: `for s in view.overview.settings` → `s.name`/`s.value`;
    `for n in view.namespaces` → `n.prefix`/`n.namespace`; caveat rows `s.class_label`, `f.class_label`.
  - `fingerprint_report` (the statistics report): unchanged; it reads `conf.profile`, not a view.
- **P-4 Generator hooks (LinkML's begin/visit/end shape).** `begin_graph(graph) -> None` (pre-order:
  SHACL resets used prefixes and finds classes with declared subclasses; PlantUML assigns aliases),
  then `visit_property(graph, cls, prop) -> P | None`, `visit_class(graph, cls, properties: list[P]) ->
  C | None`, `visit_graph(graph, classes: list[C]) -> G | None` (post-order: frozen objects are built
  after their children). `serialize() -> list[RenderedDocument]`, `render_graphs() ->
  list[tuple[slug, text]]` becomes `list[RenderedDocument]` keyed by slug in `file_name`. `GENERATORS`
  is a module-level table keyed by `RepresentationFormat`.
- **P-5 SPARQL (DEC-5 as amended).** The adapter sends each query as today on the wire —
  `POST`, `Content-Type: application/x-www-form-urlencoded`, body `query=<urlencoded>`, `Accept:
  application/sparql-results+json` — with `urllib.request.urlopen(request, timeout=timeout_seconds)`,
  and parses the body with `rdflib.query.Result.parse(BytesIO(body), format="json")`. `SparqlPort.select`
  returns `list[ResultRow]` (`URIRef`, `BNode`, typed `Literal`; unbound → `None`); `ask` returns
  `Result.askAnswer`. `classify` keeps today's table on the urllib/socket side and **keeps the 500 rule**:
  an `HTTPError` 500 whose body excerpt holds a timeout marker is a `QueryTimeout`, else permanent; a
  body `Result.parse` cannot read (`ValueError`, e.g. `JSONDecodeError`) is permanent. The
  SPARQLWrapper branches and `rows_from_json` go.
- **P-6 eds4jinja2 2.1 (DEC-7)**, a change in `../eds4jinja2` with its own spec and tests:
  `ReportBuilder.make_documents(outputs: Mapping[str, Mapping[str, Any]], *, check: Callable[[str, str],
  None] | None = None, autoescape: bool | None = None) -> list[Path]`:
  - each key is an output file name under the builder's existing `output_path`; each value holds the
    template variables of that output (passed to `render(**variables)`; `conf` stays the global);
  - `autoescape`, when given, is set on the environment before the first render (as `render_report`
    does today);
  - each output is rendered through the same path as `make_document()` (sequential, or the parallel
    pre-fetch when `parallelism > 1`, record pass per output);
  - every text is passed to `check(name, text)`; only if all pass are the files written;
  - the before-rendering listeners run once before the batch, the after-rendering listeners once after
    the files are written;
  - `make_document()` keeps its behaviour.
  The template renderer adapter calls `make_documents` (one output for the report and the document, one
  per graph for SHACL and PlantUML) with the Turtle check and the autoescape of the format;
  `JinjaTemplateRenderer.render`/`write` and the `template_env` guard test go. Released as eds4jinja2
  2.1.0 **with the developer's go-ahead** (that repository grants agents no release authority);
  rdf-fingerprinter then requires `eds4jinja2>=2.1,<3`. If the release is refused, task 7.1 is dropped
  and the current adapter stays.
- **P-7 Configuration (DEC-6).** `fingerprint/adapters/config_resolver.py`: `ConfigResolverABC`,
  `EnvConfigResolver`, `DefaultConfigResolver` (Meaningfy settings pattern), and `env_property(name,
  default)` whose property reads through the **instance's** resolver (`self.resolver`), so tests pass
  `FingerprintConfig(DefaultConfigResolver())`. `fingerprint/__init__.py`: `class FingerprintConfig`
  and `config = FingerprintConfig(EnvConfigResolver())`; nothing resolves at import.
  `config.validate()` reads every property once and raises `UsageError` naming the first variable
  that does not coerce; it runs at the start of every entry point (the `fingerprint` and
  `fingerprint-gen-*` commands, `generate_endpoint_fingerprint_report`, `fingerprint_report`,
  `generate_from_profile_file`), before any query or write. Variables:

  | Variable | Type, default | Replaces |
  |---|---|---|
  | `RDF_FINGERPRINTER_PROFILE_FILE` | text, `profile.json` | `PROFILE_FILE` |
  | `RDF_FINGERPRINTER_RETRY_BACKOFF_SECONDS` | comma-separated numbers, `1,4` | `BACKOFF_SECONDS` |
  | `RDF_FINGERPRINTER_TIMEOUT_MARKERS` | comma-separated texts, `timeout,time limit,timed out,estimated execution time` | `TIMEOUT_MARKERS` |
  | `RDF_FINGERPRINTER_ERROR_EXCERPT_LENGTH` | integer, `200` | `EXCERPT` |
  | `RDF_FINGERPRINTER_SHAPES_NAMESPACE` | IRI text, `urn:fingerprint:shape:` | `DEFAULT_SHAPES_NAMESPACE` |
  | `RDF_FINGERPRINTER_DEFAULT_GRAPH_LABEL` | text, `default graph` | `DEFAULT_GRAPH_LABEL` |
  | `RDF_FINGERPRINTER_PREFIXES_FILE` | path, the packaged `prefixes.json` | `PREFIXES_FILE` |
  | `RDF_FINGERPRINTER_<SETTING>` per collection setting | as today, unset by default | the env branch of `resolve_settings` |

  **Collection settings.** `model/fingerprint_stats.yaml` gains `SettingsOverride` (every `Settings`
  slot, optional, no default; a test asserts both classes have the same field names). Sources, in
  precedence order, each an override: CLI options (`SettingsOverride(**options)` with `None` for
  unset), the environment (`config.settings_override()`: per slot, booleans from `1/true/yes/on` /
  `0/false/no/off`, `selected_graphs` split on commas and stripped, other values passed to Pydantic;
  a bad value raises `UsageError` naming `RDF_FINGERPRINTER_<NAME>`), the `selected_graphs` parameter,
  the configuration (`--config` file or `additional_config["collection"]`, both through
  `SettingsOverride.model_validate`; unknown keys → `UsageError` "unknown collection settings: …").
  An empty `selected_graphs` list counts as unset, as today. `resolve_settings(*overrides)` builds
  `Settings(**{slot: first non-None})` (construction syntax), maps `ValidationError` to `UsageError`,
  then applies the `(0, 1]` threshold rule. `settings_sources.py` goes. Stays constant (standards and
  protocol tables): `vocabulary.py`, `RDF_TYPE`, `QUERY_FILES`, `QUERY_KIND`, `MODES`, `NODE_KINDS`,
  `TOO_LARGE`, `LABEL_PREDICATES`.
- **P-8 Collection and analytics build objects.** Collection builds `ValuePartition(node_kind=…,
  datatype=…, triples=row.n.toPython())` etc. straight from `ResultRow`s; a blank node is recognised by
  `isinstance(term, BNode)` and written to the profile as `_:<id>` exactly as today (the `"_:"` prefix
  test goes). Analytics helpers return `PropertyAnalytics`, `ClassAnalytics`, `GraphAnalytics`,
  `ParentClass` objects; `drop_none` goes. `profile.json`, the analytics and the report are unchanged.

## Algorithm / approach

### Order of work

Groups 1, 2, 3, 4, 5 run in order, each green; group 0 (eds4jinja2) runs alongside; 6 needs 1.3; 7
needs 0.2. The SPARQL adapter and collection change together (task group 3), because the row type
changes under collection.

### Safety net (DEC-8)

Golden files byte-equal after every group; a live collection after group 3 equals `sample-profile.json`
but for timestamps and version; `make test-e2e` after groups 3 and 7.

### Example — a property shape, before and after

```python
# before (dict)                                   # after (view object)
{"path": self.term(p), "constraints": [...],       PropertyShape(path=self.term(p), constraints=[...],
 "annotations": [("fp:confidence", "1.0")]}                      severity=ShapeSeverity.warning,
                                                                 annotations=[Annotation(predicate="fp:confidence", value="1.0")])
```

### Anti-patterns

| Don't | Do instead | Why |
|---|---|---|
| Return or pass a `dict` | a generated model object | DEC-1 |
| Unpack a model in a template (`for a, b in obj`) | read attributes (`obj.a`) | a model iterates as fields: wrong text, no error |
| Compare an enum field to a string literal | the enum member | free strings drift |
| Read `os.environ` outside the resolver | `config.X` | DEC-6 |
| Resolve config at import | on access, validated at entry | import has no side effects; exit 2 before queries |
| Subclass rdflib's `SPARQLConnector` | `urlopen` + `Result.parse` | no timeout, private API |
| Edit a golden file to make a group pass | find the behaviour change | DEC-8 |

## Error matrix

| Failure mode | How it is detected | Expected handling |
|---|---|---|
| a body that is not SPARQL results JSON | `Result.parse` raises `ValueError` | `PermanentError` "unreadable response" |
| HTTP 500 with a timeout marker in the body | `HTTPError` 500 + marker check | `QueryTimeout` (unchanged rule) |
| HTTP 429/502/503, connection reset | `urllib.error` | transient → retried per `RDF_FINGERPRINTER_RETRY_BACKOFF_SECONDS` |
| per-query timeout | `socket.timeout` / `TimeoutError` | `QueryTimeout` |
| a variable that does not coerce (`RETRY_BACKOFF_SECONDS=x`) | `config.validate()` at entry | `UsageError`, exit 2, naming the variable, before any query |
| an unknown key in the configuration | `SettingsOverride.model_validate` | `UsageError` "unknown collection settings: …" |
| a view object with a wrong field | Pydantic `ValidationError` | a bug; unit tests per generator |
| eds4jinja2 < 2.1 | dependency bound | not installable; nothing at runtime |
| one `check` fails in a batch | `make_documents` raises before writing | none of that format's files is written (unchanged) |

## Risks / Trade-offs

- [Large diff] → one commit per group, each green, goldens per group.
- [eds4jinja2 release needs a person] → group 7 waits; refused → dropped, current adapter stays.
- [`Result.parse` cost on big results] → measured by the benchmark EPIC.
- [`SettingsOverride` drifting from `Settings`] → the field-name test.

## Open Questions

- DEC-5 as amended awaits the developer's confirmation (P-5 proceeds unless told otherwise).
