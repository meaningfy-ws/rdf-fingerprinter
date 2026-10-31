> Derives from: EPIC `profile-representations` (`proposal.md`, DEC-1..DEC-9)

## Context

2.0.0 collects a `ProfileRun` (raw statistics, `fingerprint/domain/generated/profile.py`), derives a
`ProfileAnalytics` with `analyse(run)` (`fingerprint/domain/analytics.py`) and renders one HTML report
through eds4jinja2's `ReportBuilder` (`fingerprint/service_layer/report.py`). Nothing is saved; every
view needs a new collection.

Constraints found while planning:

- `ReportBuilder.make_document()` renders **one** template (`config["template"]`) to
  `output_folder / template` and writes it straight to disk. It cannot write one file per graph, and
  it writes before we could check the output. Its public attributes `template_env` (a Jinja
  environment with the eds4jinja2 helpers, `conf` injected as a global) and `template` (the template
  name from `config.json`) are enough to render ourselves; `external_filters` adds our filters.
  `render_report` already uses `template_env` (it switches autoescape on). eds4jinja2 is a range
  (`>=2.0.0,<3`) in `pyproject.toml`, not a pin.
- `to_iriref` (`fingerprint/domain/iri.py`) rejects the characters SPARQL's IRIREF excludes. Turtle's
  IRIREF excludes the same set, so it is the Turtle IRI guard too.
- `cardinality_label` returns the strictest label whose share reaches the threshold, with its
  `label_support`; `zero_or_more` always has support 1.0. `confidence` is the share of instances that
  have the property. `property_partitions` of a class hold every property its instances use, inherited
  ones included, each with `inheritance` = own / inherited / refined.
- The `fingerprint` script is one click command (`fingerprint.entrypoints.cli.main:fingerprint_endpoint`);
  LinkML (dev only here, but often installed by users) ships `gen-shacl`, `gen-plantuml`, `gen-doc`.
- Layers (`.importlinter`): entrypoints → service_layer → adapters → domain; `domain` imports no
  eds4jinja2/click/SPARQLWrapper; a new `domain` module must be added to the `generated` contract list.
- Runtime dependencies list only what the code imports directly; rdflib arrives through eds4jinja2
  and is a test dependency today.

## Terms and where the complexity is

Terms (confidence, label support, acceptance threshold, precision mode, severity) have one meaning,
defined in `docs/modules/ROOT/pages/glossary.adoc`. The behaviour realised here is
`UC-W2` and its refinements `UC-B2.1` (generator commands) and `UC-B2.2` (`fingerprint --format`) in
`docs/modules/ROOT/pages/use-cases/`; the decisions are AD-7 to AD-10 in `decisions.adoc`.

Where the difficulty sits, so effort and review go there:

| Part | Difficulty | Why |
|---|---|---|
| SHACL mapping (task group 4) | high | statistics → constraints: thresholds, samples, cross-graph types, langString; the "conforms on its own data" rule (AD-10) |
| Turtle and PlantUML escaping (3.2, 3.5) | medium | text templates emit RDF (AD-9); safe local names, unwritable IRIs |
| Template renderer and generator (2.2, 3.3) | medium | per-graph files through `template_env`, check-then-write, shared with the report |
| Layer clean-up of 2.0 (2.0–2.3) | low–medium | moves only; existing tests must stay green |
| Profile file, threshold override (3.0, 3.4) | low | Pydantic JSON round-trip; `model_copy` |
| PlantUML, document (5, 6) | low | layout over a prepared view |
| Commands (7) | low | click wiring, exit codes as 2.0 |

## Goals / Non-Goals

**Goals:** `profile.json` written beside the report and loadable; a LinkML-shaped generator framework;
SHACL, PlantUML and profile-document generators rendered by eds4jinja2; one command per format;
`fingerprint --format`; docs and CHANGELOG 2.1.0.

**Non-Goals:** the EPIC's no-gos (no queries from generators, no VoID/ShEx/OWL/LLM formats, no
diagram rendering, no change to the report or the 1.x function, no new RDF test data). No change to
eds4jinja2 itself.

## Decisions

- **P-1 Render through `template_env`, write ourselves — in one adapter.** The *template renderer*
  (`fingerprint/adapters/template_renderer.py`) builds a `ReportBuilder` for a template package
  (config + filters + `conf`), renders `builder.template_env.get_template(builder.template)` with a
  `view` variable, checks texts (Turtle parse) and writes files, check-then-write. `conf.profile` (the
  analytics) is also set, as for the report, so custom templates may read the whole profile. The
  report's `render_report` delegates to the same adapter, which takes eds4jinja2 out of the service
  layer (AD-4 gap). Generators receive the renderer through a `TemplateRenderer` protocol (as
  collection receives `SparqlPort`), so their tests need no files. Rejected: `make_document()` (one file, written before the check, DEC-4);
  patching eds4jinja2 (EPIC rabbit-hole).
- **P-2 LinkML shape, adapted to many files.** `Generator.serialize() -> dict[str, str]` maps a file
  name to its text (LinkML returns one `str`; a per-graph format needs several). The base class walks
  the analytics and calls `visit_graph(graph)`, `visit_class(graph, cls)`, `visit_property(graph, cls, prop)`;
  each returns the dict a template sees at that level (`None` drops the element). All mapping logic
  (counts, severities, value constraints, aliases, prefixes) lives in these Python hooks, unit-tested;
  templates only lay text out.
- **P-3 Command names** `fingerprint-gen-shacl`, `fingerprint-gen-puml`, `fingerprint-gen-doc` —
  LinkML's `gen-*` pattern, prefixed so they never shadow LinkML's scripts. `fingerprint` gains a
  repeatable `--format {shacl,puml,doc}`.
- **P-4 Shared arguments** (LinkML `shared_arguments`): `PROFILE` (path to `profile.json`),
  `-o/--output` (existing folder, default `./output`, as `fingerprint`), `--threshold` (overrides the
  run's acceptance threshold; same (0, 1] check as collection), `--template` (a template package
  folder). SHACL adds `--shapes-namespace`.
- **P-5 The profile file is an adapter.** `fingerprint/adapters/profile_file.py`: `save_profile(run, folder) -> Path`
  writes `run.model_dump_json(indent=2, exclude_none=True)` to `folder/profile.json`;
  `load_profile(path) -> ProfileRun` uses `ProfileRun.model_validate_json` and raises
  `ProfileFileError(ValueError)` naming the path on a missing file, invalid JSON or a model mismatch.
  The CLI maps it to exit 2.
- **P-6 Threshold override.** `with_threshold(run, t)` returns
  `run.model_copy(update={"settings": run.settings.model_copy(update={"acceptance_threshold": t})})`;
  `analyse` then derives labels at `t` (DEC-2). Checked with the existing `(0, 1]` rule, reused from
  `resolve_settings` by validating through it (`resolve_settings(cli={"acceptance_threshold": t}, env={})`).
- **P-7 Prefixes.** One source: the packaged `fingerprint_report/templates/prefixes.json`, loaded once
  in Python. Two filters: `curie(iri)` for display (PlantUML labels, the document) shortens with the
  first matching namespace (same rule as the report macro); `turtle_term(iri)` for SHACL writes
  `prefix:local` only when the local part is a safe Turtle local name (ASCII
  `[A-Za-z0-9_]([A-Za-z0-9_.-]*[A-Za-z0-9_-])?`), else `to_iriref(iri)` — so `http://ex.org/q?a=1&b='x'`
  and `http://ex.org/ș/ü` are written as full IRIs. SHACL declares `@prefix` only for namespaces it
  used (collected by the hooks), plus `sh:`, `xsd:`, `rdf:`, `rdfs:`, `fp:`.
- **P-8 Unwritable IRIs are skipped, not broken.** A class or property IRI that `to_iriref` rejects is
  left out of SHACL and PlantUML (its hook returns `None`), logged at WARNING and listed in the
  document's caveats. The document shows it, autoescaped.
- **P-9 Annotation vocabulary** `fp:` = `https://data.meaningfy.ws/fingerprint/` (the profile model's
  namespace root): `fp:confidence`, `fp:labelSupport`, `fp:instances`, `fp:observedInstances`,
  `fp:precisionMode` (`"exact"`/`"first_n"`), plus a human `rdfs:comment`. Numbers are typed literals
  (`xsd:decimal` rounded to 4 places, `xsd:integer`).
- **P-10 Shape IRIs.** Node shape = `<namespace><percent-encoded class IRI>` (`urllib.parse.quote(iri, safe="")`),
  unique and deterministic; property shapes are blank nodes inline, as LinkML's `gen-shacl` writes them.
  Default namespace `urn:fingerprint:shape:`.
- **P-11 File names per graph.** `shapes-<slug>.ttl`, `diagram-<slug>.puml`; slug = `default` for the
  default graph, else the graph IRI's last non-empty part (split on `/`, `#`, `:`) lower-cased to
  `[a-z0-9-]` (max 40 chars, `graph` if nothing is left) + `-` + the first 8 hex of its SHA-1 (as built). The document gives each graph's file-name suffix (it cannot know which formats were generated). One document:
  `profile.html`.
- **P-12 Where code lives** (cosmic-python: I/O at the edges, services orchestrate, CLI only parses).
  | Module | Holds |
  |---|---|
  | `fingerprint/domain/iri.py` | `to_iriref` (existing), `to_turtle_term(iri, prefixes)`, `turtle_string` — pure rules |
  | `fingerprint/domain/exceptions.py` | `IriRefError` (moved) |
  | `fingerprint/adapters/template_renderer.py` | `JinjaTemplateRenderer`: eds4jinja2 rendering, prefixes file loading, Turtle check (rdflib), check-then-write |
  | `fingerprint/adapters/profile_file.py` | `save_profile`, `load_profile` |
  | `fingerprint/adapters/settings_sources.py` | `load_config_file` (moved; raises `ConfigFileError`, which the settings resolver turns into `UsageError`, since adapters may not import the service layer), `environment()` |
  | `fingerprint/adapters/exceptions.py` | the SPARQL error classes (moved), `ProfileFileError`, `GeneratedOutputError`, `ConfigFileError`, `TemplatePackageError` |
  | `fingerprint/service_layer/generators/generator.py` | `Generator` (hooks, view, `serialize(renderer)`), `TemplateRenderer` protocol |
  | `fingerprint/service_layer/generators/{shacl,plantuml,document}.py` + `__init__.py` | the three generators, `GENERATORS = {"shacl": …, "puml": …, "doc": …}` |
  | `fingerprint/service_layer/representations.py` | `generate_representations(run, output, formats, *, threshold=None, template=None, renderer=None) -> list[Path]` and `generate_from_profile_file(path, …)` |
  | `fingerprint/service_layer/exceptions.py` | `UsageError` (moved) |
  | `fingerprint/entrypoints/cli/generate.py` | the three commands: parse, call `generate_from_profile_file`, map exceptions to exit codes |

  Moved names stay importable from their old modules (they import them), so callers and tests keep
  working. `.importlinter` gains a forbidden contract: `fingerprint.service_layer` imports no `jinja2`,
  `eds4jinja2`, `rdflib` or `SPARQLWrapper` itself, with `allow_indirect_imports = True` (the default
  `SparqlWrapperClient` that `handlers` builds reaches SPARQLWrapper through `adapters`, which is the
  intent); `fingerprint.domain.exceptions` joins the `generated` contract list. template packages `fingerprint_report_templates/{shacl_shapes,plantuml_diagram,profile_document}/`
  (each `config.json` + `templates/`). rdflib becomes a declared runtime dependency (already installed
  via eds4jinja2) for the Turtle check; pySHACL joins the `test` group.
- **P-13 Exit codes.** Generator commands: 0 written; 2 usage (profile file, threshold, output folder,
  template folder without `config.json`); 4 unexpected, including generated Turtle that does not parse
  (`GeneratedOutputError`). A profile that records failures still renders with exit 0 — the failures are
  shown as caveats. `fingerprint --format`: a generator error after the report is written exits 4;
  otherwise the 2.0 exit codes stand.
- **P-14 Template syntax.** No packaged `config.json` sets `template_flavour_syntax`: eds4jinja2's
  default syntax has no `#` line statements, so Turtle comments and CSS selectors survive (as built:
  the `html` syntax was dropped for the document, whose CSS has lines starting with `#`). A custom package's choice is its own; the Turtle parse
  check still guards SHACL.
- **P-15 Service signature.** `fingerprint_report(…, formats: Sequence[str] = (), sparql: SparqlPort | None = None)`
  keyword-only and appended; `sparql` defaults to `SparqlWrapperClient` (DIP; the 1.x function is
  unchanged); it still returns `(report_path, run)`. `generate_endpoint_fingerprint_report` passes no
  formats.

- **P-16 The profile file is a published format** (AD-7). `make generate-models` also runs
  `gen-json-schema` on `model/fingerprint_stats.yaml` into `fingerprint/domain/generated/profile_run.schema.json`
  (shipped in the wheel; `make check-models` diffs it too). Compatibility rule (AD-7): 2.x minor releases only
  add optional fields, so newer readers load older files; an older reader rejects a newer file
  (`extra="forbid"`); `load_profile` then names the file and the `tool_version` it carries.
- **P-17 Gates that back the method.** `make test` gains `--cov-fail-under=80` (today 97 %). Every
  feature scenario, 2.0 ones included, is tagged with its use case (`@uc_w1`, `@uc_b1_1`, …,
  `@uc_b2_2`; pytest-bdd turns tags into markers, registered in `pytest.ini` because of
  `--strict-markers`).

## Algorithm / approach

### Flow

```
fingerprint -e URL -o out --format shacl          fingerprint-gen-shacl out/profile.json -o out2 --threshold 0.9
  fingerprint_report(…, formats=["shacl"])          generate_from_profile_file(path, out2, ["shacl"], threshold=0.9)
    collect → run                                     load_profile → run
    save_profile(run) → out/profile.json              generate_representations(run, out2, ["shacl"], threshold=0.9)
    render_report(analyse(run)) → out/main.html         with_threshold → analyse → ShaclGenerator(analytics)
    generate_representations(run, out, ["shacl"])       .serialize(renderer) → renderer.write(out2, texts)
```

The CLI only parses and maps exceptions to exit codes; every step is a service call. Formats run in
the order given; each generator's texts are all checked before any of its files is written, so a
failure leaves that format's files unwritten and keeps those of formats finished before it.

### Generator (P-1, P-2)

```python
class TemplateRenderer(Protocol):                 # implemented by adapters.template_renderer
    prefixes: dict[str, str]                      # from the packaged prefixes.json, for the hooks' terms
    def render(self, package, *, view=None, config=None, autoescape=None) -> str: ...
    def write(self, folder, texts: dict[str, str], check: str | None = None) -> list[Path]: ...  # check="turtle"

class Generator:                                  # service_layer/generators/generator.py
    template_package: ClassVar[Path]              # packaged default
    per_graph: ClassVar[bool]
    file_name: ClassVar[str]                      # "shapes-{slug}.ttl" | "profile.html"
    autoescape: ClassVar[bool] = False            # True only for the document
    check: ClassVar[str | None] = None            # "turtle" for SHACL

    def __init__(self, analytics, renderer, template_location=None): ...  # as built: renderer here
    def end_graph(self, graph, view) -> None: ...  # LinkML's end_* hook, e.g. used prefixes
    def visit_graph(self, graph) -> dict | None: ...
    def visit_class(self, graph, cls) -> dict | None: ...
    def visit_property(self, graph, cls, prop) -> dict | None: ...
    def view(self) -> list[dict]: ...             # graph dicts, each with "classes", each with "properties"
    def serialize(self) -> dict[str, str]: ...    # file name → text
    def write(self, folder) -> list[Path]: ...    # renderer.write(folder, serialize(), check)
```

`renderer.write` checks every text before writing any, so a failure leaves no partial output of that format. Rendering is
pure; running a generator twice over the same profile overwrites with identical bytes (idempotent).
Order is deterministic: graphs as in the profile, classes and properties sorted by IRI.

### SHACL mapping (DEC-5)

Counts from the accepted label: `exactly_one` → min 1, max 1; `zero_or_one` → max 1; `one_or_more` →
min 1; `zero_or_more` → none; `exactly_n` → min n, max n.

Value constraint, read from the property's `value_partitions` (literal partitions carry a
`datatype`, resource partitions an `object_class` or none when untyped). A literal partition without
a datatype (stores that leave `datatype()` unbound for tagged literals) counts as `rdf:langString`
when it has a language, as `analyse` does (`RDF_LANG_STRING`), else as plain `sh:nodeKind sh:Literal`.
The alternatives are every distinct datatype (`sh:datatype`), every distinct `object_class` (`sh:class`) when `untyped_object_ratio` is 0, and
the observed resource node kind (`sh:IRI`, `sh:BlankNode` or `sh:BlankNodeOrIRI`) when some resource
objects are untyped. One alternative → inline; several → `sh:or ( [ … ] [ … ] )`. A property whose
values are all of one kind group also gets that observed node kind (`sh:Literal`, `sh:IRI`, …; as
built, more precise than always `sh:BlankNodeOrIRI`). An object typed with two classes satisfies the
`sh:or` of both, so the constraint holds on the source data.

Severity, from the threshold:

First matching row wins:

| Situation | Severity |
|---|---|
| no cardinality label (`presence_only` property; no counts, no value constraint emitted) | `sh:Info` |
| `confidence` < threshold (most instances lack the property) | `sh:Info` |
| accepted label has `label_support` < 1 (accepted, with exceptions) | `sh:Warning` |
| the class was read in first-N mode (unread instances may differ) | `sh:Warning` |
| the class has declared subclasses (`sh:targetClass` reaches their instances, not counted here) | `sh:Warning` |
| the run used `object_type_scope = any_graph` and the shape has `sh:class` (types may sit in other graphs) | `sh:Warning` |
| otherwise (holds for every instance) | default (`sh:Violation`) |

So shapes generated from a dataset conform to it at `sh:Violation`. A class with no observed
instances gets a node shape with `sh:targetClass`, its annotations and no property shapes.

Worked example — `ex:Person`, 3 of 3 instances, `ex:name` on all 3, one value each, `xsd:string`:

```turtle
<urn:fingerprint:shape:http%3A%2F%2Fexample.org%2FPerson> a sh:NodeShape ;
    sh:targetClass ex:Person ;
    fp:instances 3 ; fp:observedInstances 3 ; fp:precisionMode "exact" ;
    sh:property [
        sh:path ex:name ;
        sh:minCount 1 ; sh:maxCount 1 ;
        sh:datatype xsd:string ; sh:nodeKind sh:Literal ;
        fp:confidence 1.0 ; fp:labelSupport 1.0
    ] .
```

### PlantUML mapping (DEC-6)

Per graph: `@startuml`, `hide empty members`, then for each class an alias `C<n>` (order of the
sorted class list): `class "ex:Person" as C1 { ex:name : xsd:string [1] }` for own and refined datatype
properties; an object property `ex:knows` (own/refined) with one target class in the graph is
`C1 --> "0..*" C3 : ex:knows`; to several or untyped targets it stays an attribute typed by its
targets. Parents: `C1 --|> C2` declared, `C1 ..|> C2` implied; a parent class not profiled in the
graph gets a plain `class "…" as P<n>` box. Multiplicities from the label: `1`, `0..1`, `1..*`,
`0..*`, `n`. Aliases make quoting safe: labels are CURIEs of IRIs already accepted by `to_iriref`,
which contain no `"`.

### Profile document (DEC-7, SEMIC / SHACL Play style)

One static HTML file, inline CSS, no JavaScript, numbered sections: 1 Overview (endpoint, started /
finished, tool version, settings table) · 2 Namespaces (prefix, IRI) · 3..n one chapter per graph:
graph IRI, output files, diagram source in `<details><pre>`, then a section per class (CURIE + full
IRI, instances and precision "first N of M", parents with source, a table property | value type(s) |
cardinality (`1`, `0..1`, …) | usage (confidence %) | own/inherited/refined) · last: Caveats (first-N
classes, recorded failures, skipped IRIs). Autoescape on (DEC-4).

Look, taken from SHACL Play's `doc2html.xsl` and SEMIC profiles: a table of contents at the top
linking every numbered section; each class section headed by its CURIE with the full IRI in small
monospace below; tables with a header row, zebra rows and IRIs as links to themselves; the diagram
source in monospace; a print stylesheet (`@media print`) that drops the contents' links and avoids
breaking a class table across pages. Every date and value comes from the profile, never from the
render time, so the golden file is stable.

### Anti-patterns

| Don't | Do instead | Why |
|---|---|---|
| Decide counts, severities or types inside Jinja | compute them in `visit_*` hooks, test them in Python | templates stay layout only; logic is testable (P-2) |
| `make_document()` for SHACL/PlantUML | render via `template_env`, check, then write | one file per graph; no unchecked file on disk (P-1) |
| Concatenate raw IRIs into Turtle | the `turtle_iri` filter (`to_iriref`) and `turtle_string` | hostile data must not break the file (DEC-4) |
| HTML autoescape for Turtle/PlantUML | autoescape only for the document | `&lt;` in Turtle is a broken IRI |
| Query anything from a generator | read `view` (and `conf.profile`) only | DEC-1 |
| Copy `prefixes.json` into each package | load the report's one file in Python | one prefix source (P-7) |

## Error matrix

| Failure mode | How it is detected | Expected handling |
|---|---|---|
| `profile.json` missing / not JSON / not the model | `load_profile` raises `ProfileFileError` | exit 2, message names the file, nothing written |
| `--threshold` outside (0, 1] | `resolve_settings` raises `UsageError` | exit 2 |
| output folder missing | `NotADirectoryError` check, as `fingerprint` | exit 2 |
| `--template` folder without `config.json` | `FileNotFoundError` from `ReportBuilder` | exit 2, names the folder |
| custom `config.json` without `template` or `conf` | `KeyError` while the template renderer builds its `ReportBuilder`, raised as `TemplatePackageError` (adapters) | the service turns it into a usage error, exit 2, "config.json must have `template` and `conf`" |
| custom template has a Jinja error | `jinja2.TemplateError` | exit 4, message shows template and line |
| class/property IRI not writable as IRIREF | `to_iriref` raises `IriRefError` in a hook | element skipped from SHACL/PlantUML, WARNING logged, listed in caveats; exit 0 |
| generated Turtle does not parse | `rdflib.Graph().parse(data=…, format="turtle")` raises in `check` | `GeneratedOutputError`, exit 4, none of that format's files written; formats finished before it kept |
| profile records collection failures | `run.failures` non-empty | rendered, listed in caveats, exit 0 |
| `fingerprint --format` generator fails after the report | exception from `write` | report and `profile.json` stay, exit 4 |
| the report cannot be rendered or written after collection | exception from the template renderer | `profile.json` (saved first) stays, exit 4; regenerate with the generator commands |
| unknown `--format` | click `Choice` | exit 2 before collecting |
| rerun over the same output folder | — | identical bytes overwritten (idempotent) |

## Risks / Trade-offs

- [Turtle from text templates is fragile] → filters for every IRI and string, a parse check on every
  output, golden files, hostile-value scenarios.
- [`template_env`/`template` are attributes, not a documented eds4jinja2 contract, and eds4jinja2 is
  a range `>=2.0.0,<3`] → one wrapper in `adapters/template_renderer.py`; the guard test
  `test_report_builder_exposes_template_env` fails loudly if a 2.x release renames them.
- [`sh:class` fails when the data graph lacks the objects' types] → classes only when no object is
  untyped; the `any_graph` comment; conformance is tested on the source data.
- [Large graphs → huge diagrams] → per-graph files only (EPIC rabbit-hole); no pruning in 2.1.
- [`profile.json` size] → `exclude_none`; top values bounded by `top_k`.

## Deferred after the pre-PR review (recorded, not built)

- Typed view models per format (frozen dataclasses) instead of view dicts — worth it once custom
  templates rely on the view shape; the shapes are documented in the representations page.
- A `TurtleGenerator` base (prefix bookkeeping, Turtle check) and generator commands built in a loop
  over `GENERATORS` — when the next format (VoID, an LLM schema card) arrives.
- Moving `prefixes.json` to the package root and the report's Jinja `curie` macro onto the filter;
  porting the analytics steps onto the `tests/unit/fakes.py` builders.

## Open Questions

None blocking. The developer may later override P-3 (names), P-9 (`fp:` vocabulary) and P-10
(default shape namespace).
