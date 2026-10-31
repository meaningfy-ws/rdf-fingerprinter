> Derives from: the EPIC `readable-representations` (proposal.md)

## Context

- **Prefixes.** They come from one static file today:
  `fingerprint_report_templates/fingerprint_report/templates/prefixes.json` (2,624 entries).
  `load_prefixes` (`fingerprint/adapters/template_renderer.py:26`) reads it, through
  `config.prefixes_file` (`fingerprint/__init__.py:82`). Setting `RDF_FINGERPRINTER_PREFIXES_FILE`
  *replaces* that file. `split_curie`, `curie` and `turtle_term` (`fingerprint/domain/iri.py:24-60`)
  take the **first** matching namespace. `JinjaTemplateRenderer` loads the prefixes in its
  constructor and closes its `curie`/`turtle_term` filters over them. The generators read
  `renderer.prefixes`, which is a field of the `TemplateRenderer` protocol (`generators/generator.py`).
- **Two render paths.**
  - `fingerprint/service_layer/report.py:render_report` renders `main.html` with
    `conf.profile = analytics` and the 1.x `template_location`/`extra_conf` contract.
    `handlers.py:generate_endpoint_fingerprint_report` uses it.
  - `DocumentGenerator` (`generators/document.py`) renders `profile.html` from view classes. Into
    it, `representations.py:make_generator` composes the PlantUML texts (`diagrams=`, `GraphText`).
- **Error mapping.** `fingerprint/entrypoints/cli/main.py` and `generate.py:generate_one` turn
  `UsageError` into exit 2. Anything unexpected becomes exit 4. `ConfigError` (from
  `load_prefixes`) is not a `UsageError`.
- **Shapes.** The shape IRI is `config.shapes_namespace` (default `urn:fingerprint:shape:`) plus the
  percent-encoded class IRI (`shacl.py:130`). `--shapes-namespace` exists only on
  `fingerprint-gen-shacl`.
- **HTTP** uses the stdlib only (`fingerprint/adapters/sparql.py`, `urllib.request`). No dependency
  is added.
- **prefix.cc** (verified by the clarity gate, 2026-10-31):
  - `http://prefix.cc/popular/all.file.json` answers 200 with one JSON object of prefix →
    namespace: 3,614 entries in popularity order, about 1,000 of them missing from the packaged
    file.
  - The HTTPS certificate expired on 2025-12-31, so a verified HTTPS fetch fails. The developer
    chose: HTTPS first, HTTP only on a certificate failure (`inputs/developer-answers.md`).

## Goals / Non-Goals

**Goals:** the spec deltas of the four capabilities.
**Non-Goals:** the EPIC's no-gos.

## Decisions

- **D-1 Prefix sources.**
  - `fingerprint/service_layer/prefixes.py:resolve_namespaces(run, user, packaged, prefix_list)
    -> ProfileRun`, where:
    - `user` and `packaged` are lists of `NamespacePrefix`, already parsed;
    - `prefix_list` is a `PrefixListSource | None`.
  - It runs in `fingerprint_report` after `collect` and before `save_profile`.
  - The port is `PrefixListSource.fetch() -> list[NamespacePrefix]`. The adapter
    `fingerprint/adapters/prefixes.py:PrefixCcList` tries HTTPS. On `ssl.SSLCertVerificationError`
    (also when it arrives wrapped in `URLError`) it fetches over HTTP and logs the spec's INFO line.
    Every socket operation times out after 10 s; there is no retry. The unit tests use
    `FakePrefixList` (`tests/unit/fakes.py`).
  - The generator commands call `resolve_namespaces(run, user, packaged, None)` for both saved and
    old profiles.
- **D-2 Loading prefix files before any query.**
  - `load_prefixes(path, source)` returns `list[NamespacePrefix]`, in file order. Its error
    messages name the option or variable that gave the path.
  - `config.prefixes_file` defaults to `None` and becomes the user layer only. The packaged file is
    always loaded, as `packaged`.
  - `FingerprintConfig` gains `prefix_lookup` (`RDF_FINGERPRINTER_PREFIX_LOOKUP`, a boolean,
    default true); `validate()` makes a bad value a usage error.
  - Both CLIs load the user file inside their usage `try`, before `collect`, and map `ConfigError`
    to `UsageError` (exit 2). The library takes the parsed list (`user_prefixes`).
- **D-3 Model**, all in task 1.1:
  - `model/fingerprint_stats.yaml` gains the enum `PrefixSource` (`user`, `packaged`, `prefix_cc`,
    `generated`), the class `NamespacePrefix` (`prefix`, `namespace`, `source`) and an optional
    multivalued `ProfileRun.namespaces`.
  - `NamespacePrefix` is not the views' `PrefixDeclaration`: the published profile schema must not
    import the views. `PrefixDeclaration` stays for each output's own declarations.
  - `model/fingerprint_views.yaml`:
    - `GeneratorOptions` gains `exclude_namespaces`, `include_namespaces`, `module_size` (default
      15) and `shapes_namespace` (now without a default).
    - The views stay self-contained, with no import of the stats schema: the `generated`
      import contract forbids it, and pydantic rejects a foreign class instance.
      `PrefixDeclaration` gains an optional `source` (string), and `ProfileDocument.namespaces`
      lists `PrefixDeclaration` with the source filled in by the generator.
    - `DocumentProperty` gains the report's columns, all as display strings formatted by the
      generator (numbers rounded to 2 decimals, `—` when absent): `subjects`, `min`, `max`, `avg`,
      `kind`, `distinct`, `confidence`, `language_coverage`, plus `q` (the search text). The
      existing `cardinality` becomes the label (or `present` for presence-only); `usage` is
      removed.
    - `DocumentClass` gains `prefix`, `q` and `sample_note`.
    - New `CollectionSection` (`settings`, `failures`); `ProfileDocument` gains `collection`.
      `Caveats` loses `failures` and gains `hidden` (`HiddenNamespace`: `prefix`, `classes`) and
      `untyped` (`UntypedSubjects`: `graph`, `count`). `FailureNote` gains `property` and
      `attempts`.
    - `DocumentGraph.diagram` and `GraphText` are removed.
    - PlantUML: `DiagramGraph` is replaced by two per-file views with the `GraphView` mixin.
      `DiagramModule` (`kind = module`, `name`, `classes`, `reference_boxes`) and
      `DiagramOverview` (`kind = overview`, `packages: DiagramPackage(prefix, classes,
      referenced)`, `links: DiagramLink(source, target, count)`). The enum `DiagramKind` is what
      the one `diagram.puml` template branches on.
  - Run `make generate-models`.
- **D-4 Pure domain code.**
  - `fingerprint/domain/prefixes.py`:
    - `namespace_of(iri)`;
    - `path_segments(namespace)`, which counts fragment segments after `#/`;
    - `generate_prefixes(namespaces, table) -> list[NamespacePrefix]` (the spec's rules 1–5);
    - `PrefixTable`, a value object over the list, with `shorten(iri)` (longest namespace,
      DEC-10), `by_prefix`, `by_namespace` and `declarations(used)`.
  - `split_curie`, `curie` and `turtle_term` take a `PrefixTable`.
  - `fingerprint/domain/modules.py`: the clustering (D-8).
  - `fingerprint/domain/shapes.py:shape_iri` (D-10).
  - Add `fingerprint.domain.prefixes`, `.modules` and `.shapes` to the `forbidden_modules` of the
    `generated` contract in `.importlinter`.
  - The port `PrefixListSource` (a Protocol), `PrefixLookupError`, `PrefixCcList` and
    `load_prefixes(path, source, origin)` live in `fingerprint/adapters/prefixes.py`, as
    `SparqlPort` lives in `adapters/sparql.py`.
- **D-5 How outputs get the table.**
  - `Generator.__init__` builds `self.table = PrefixTable(analytics.namespaces)`; `ProfileAnalytics`
    inherits the field through `analyse`.
  - `prefixes` leaves the `TemplateRenderer` protocol. `render` and `make` take `prefixes:
    PrefixTable`, and `JinjaTemplateRenderer` binds its `curie`/`turtle_term` filters to it per
    call, so custom templates' filters use the profile's table too.
  - `JinjaTemplateRenderer.__init__` no longer reads a file.
- **D-6 One render path (DEC-3, DEC-9).**
  - Delete: `report.py`, `generate_endpoint_fingerprint_report`, `generate_report_builder_config`,
    `fingerprint_report_templates/profile_document/`, the `default_endpoint`/`selected_graphs`
    keys in `fingerprint_report/config.json`, the diagram composition in `make_generator`, and
    `GraphText`.
  - `DocumentGenerator`: `template_package = packaged("fingerprint_report")`,
    `file_name = "main.html"`.
  - The flow of `fingerprint_report(sparql_endpoint_url, output_location, settings, *, formats=(),
    options=None, template=None, user_prefixes=None, prefix_list=None, sparql=None, renderer=None)`:
    1. check the folder (`NotADirectoryError`);
    2. `validate_config`, `validate_endpoint`, and the options (`to_iriref` on the shapes namespace, module size ≥ 1), all as `UsageError`;
    3. `collect`;
    4. `resolve_namespaces`;
    5. `save_profile`;
    6. `DocumentGenerator(…, template).write`;
    7. the other `formats`, through `generate_representations`.
  - A `doc` in `formats` logs `main.html is the document` at INFO and is skipped.
  - The CLI builds `PrefixCcList()` unless the lookup is switched off.
- **D-7 Page design** (visuals set in task 4.1 with the `frontend-design` skill):
  - **The one bold element:** each namespace gets a deterministic hue (`(index × 137 + 190) mod 360`
    over the namespace table), shown as the coloured prefix of every short name, the class section's
    left rule and the contents' group labels — a map legend for vocabularies. Everything else is quiet.
  - **Palette:** paper `#f6f7f5`, panel `#ffffff`, ink `#1d2422`, muted `#5c6764`, rule `#d8ddda`,
    accent `#1f6b73`; dark: `#141a19`, `#1b2321`, `#e3e9e6`, `#98a4a0`, `#2d3734`, `#74c4cc`.
  - **Type:** the system UI stack only, 15 px base, tabular figures in number cells; no web font, no
    all-caps labels, no monospace labels.
  - **Applied after measuring (task 6.2):** the page was 1.47 MB with row-level `data-q`, over the
    1.4 MB ceiling, so the fallback below was taken: rows are searched by their visible name plus the
    link's `title` (the full IRI), and `DocumentProperty.q` was dropped. Result on brainframe:
    1.27 MB, rendered in about 1.4 s.
  - **Layout.** A sticky top bar holds the title, the search box and the shown/hidden counts. A
    left `<nav>` holds the table of contents (graph → namespace → class, with counts) and the
    namespace switches; on a phone it collapses above the content. The main column holds the
    overview cards, the namespace table, then per graph one `<details open>` per class with a
    compact `<table>`, then the collection section and the caveats.
  - **Styling.** CSS custom properties on `:root`, with a `prefers-color-scheme: dark` override; a
    system font stack; tabular figures for numbers; no web fonts.
  - **Data attributes.** Each class `<details>` carries `data-ns` and `data-q` (short name and IRI,
    lower case); each property `<tr>` carries `data-q`.
  - **Script.** One inline vanilla `<script>` of at most 150 lines, with an `input` handler and a
    `change` handler that toggle `hidden` and update the counts.
  - **Weight.** Short names are computed once per IRI in the view model; there are no per-cell
    macro calls and no diagram sources.
  - **Size and time.** Task 6.2 runs `/usr/bin/time` on the brainframe test on the developer
    machine, against the 1.4 MB and 10.8 s measured before this change. If either is exceeded:
    drop the row-level `data-q` and search the visible row text and the link title instead (taken).
- **D-8 Diagrams.** Associations follow the spec's rule (one value class, no untyped objects, to any
  class; otherwise an attribute). `PlantumlGenerator` overrides `outputs()`. Per graph it walks the classes
  (hooks as today), clusters them per namespace with `modules.cluster`, and returns one
  `(diagram-<slug>.puml, DiagramOverview)` pair and one `(diagram-<slug>--<module>.puml,
  DiagramModule)` pair per module. The single `diagram.puml` template branches on `view.kind`.
  Names cannot collide:
  - `graph_slug` never holds `--`;
  - a prefix never holds `~` (`_PREFIX_KEY`), so the cluster suffix `~n` cannot clash with a
    prefix like `ex-1`;
  - generated prefixes collapse `-` runs.

  Custom `--template` packages for PlantUML must follow the new views; this is a BREAKING change in
  the CHANGELOG.
- **D-9 Filters.** `Generator.shown(cls)` tests against the excluded set: the meta defaults, plus the
  excludes, minus the includes, with names resolved through `PrefixTable` (prefix first, then the
  IRI). It is applied in the class walk of `generator.py`, so every generator and the page filter
  alike. The hidden prefixes and counts go into `Caveats.hidden`. Unknown names log the spec's
  WARNING once per name.
- **D-10 Shapes.** `shape_iri(class_iri, property_iri | None, table, shapes_namespace | None)`
  returns `(iri, prefix, namespace)`. `ShaclGenerator` de-duplicates the shape IRIs in sorted order
  and declares the shape prefixes it used. `config.shapes_namespace` defaults to `None`, and
  `--shapes-namespace` is added to `fingerprint`.

### Entry points
| Entry point | Loads the user file | Honours `RDF_FINGERPRINTER_PREFIXES_FILE` / `_PREFIX_LOOKUP` / `_SHAPES_NAMESPACE` | Calls `resolve_namespaces` |
|---|---|---|---|
| `fingerprint` CLI (`main.py`) | yes, before `collect`, from `--prefixes` else the env | all three, through `config`; it builds `PrefixCcList` unless switched off; it validates the shapes namespace in its usage `try` before `collect` | via `fingerprint_report` |
| `fingerprint_report` (library) | no; it takes `user_prefixes` | none directly: it uses only what it is passed (`prefix_list=None` means no fetch); the packaged file is always loaded | yes, after `collect` |
| `fingerprint-gen-*` CLI (`generate.py`) | yes, from `--prefixes` else the env | the prefixes file and the shapes namespace; never a lookup | via `generate_from_profile_file` |
| `generate_from_profile_file(profile, output, formats, *, user_prefixes=None, …)` | no; it takes `user_prefixes` | none | yes, without a lookup, always (saved and old profiles) |
| `generate_representations(run, …)` | no | none | yes, without a lookup, when `run.namespaces` is `None`, so a library caller never gets full IRIs |

## Algorithm / approach

Resolution for the brainframe profile (worked example; graph IRIs included):

| Namespace | Source | Prefix |
|---|---|---|
| `http://www.w3.org/2000/01/rdf-schema#` | packaged | `rdfs` |
| `https://ontology.brainframe.com/2016/04/brainframe#` | prefix.cc has none → generated, rule 3 | `brainframe` |
| `https://my.brainframe.com/#/knowledge/RelationId/` | generated, rule 3 (fragment segments) | `relationid` |
| `https://my.brainframe.com/graph/` | generated, rule 3 (depth 4, lexically first) | `graph` |
| `https://ontology.brainframe.com/graph/` | generated, rule 3, then rule 5 | `graph2` |

The steps of `resolve_namespaces`:
1. Gather the namespaces.
2. Apply the user list; a user prefix displaces its holder.
3. Keep the saved entries that do not clash.
4. Apply the packaged list.
5. If names are still missing and `prefix_list` is set, `fetch()` once. On `PrefixLookupError`,
   log the WARNING and go on.
6. Generate the rest.
7. Return `run.model_copy(update={"namespaces": …})`.

Each step skips reserved and taken names, as the spec says. The function is pure apart from the one
fetch. Running it on its own output gives the same table, and re-rendering never fetches.

Shapes: `…/brainframe#Asset` → `…/brainframe/shape/Asset`, written `brainframe-shape:Asset`; its
`rdfs:label` property shape is `brainframe-shape:Asset-rdfs-label`.

Modules: the spec's example has classes A–G with module size 3, giving `ex~1` = {A, B, C}, `ex~2` =
{E, F} and `ex~3` = {D, G}. It is the clustering unit test's first case.

### Verification map
| Kind | Scenarios | How |
|---|---|---|
| Automated, unit and Gherkin | every scenario of the four deltas not listed below | pytest-bdd and unit tests; prefix.cc faked |
| Automated, golden | profile-representations › Golden outputs | the fixed test profile |
| Automated, readability fixture | "Short names only", "No long IRIs in the diagram", "Search data is present" | `tests/test_data/profiles/readability-profile.json` (new): a fragment-route namespace, a hash namespace, a sub-namespace, a meta class, and an unnamed vocabulary |
| Manual, once (task 6.2) | "Search narrows the classes", "Namespace switched off", phone width, dark mode, size and time | in a browser, on the brainframe outputs; the search and switch behaviour was also driven once with jsdom 24 outside the project (2026-10-31): `risk` → 3 shown / 49 hidden, every shown class or row matches, contents follow, switches combine with search |

### Anti-patterns
| Don't | Do instead | Why |
|---|---|---|
| Take the first namespace that begins an IRI | `PrefixTable.shorten`, longest namespace | Hierarchical prefixes would hide each other |
| Fetch from prefix.cc in a generator, a template, or once per namespace | One `fetch()` in `resolve_namespaces` | Offline rendering, one request, no namespace leak |
| Turn off certificate checks to read prefix.cc over HTTPS | A verified HTTPS fetch, then plain HTTP on a certificate failure (developer's choice) | Never disable TLS verification |
| `ns1`, `ns2` prefixes | The spec's rules 1–5 | They tell a reader nothing |
| Keep `render_report` "for compatibility" | Delete it (DEC-9) | Two render paths, only one filtered |
| Build the HTML in the browser from JSON | Server-rendered HTML, with the script toggling `hidden` | Readable without JavaScript; golden-testable |
| Percent-encode the class IRI into the shape IRI | `shape_iri` | Readable and diffable |
| Pass dicts around for tables and rows | LinkML classes and `PrefixTable` | Values are domain objects (domain-object-model DEC-1) |
| Validate `--prefixes` after collecting | Load it before `collect` | A usage error must come before any query |

## Error matrix

| Failure mode | How it is detected | Expected handling |
|---|---|---|
| The user prefix file is missing, unreadable or malformed | `load_prefixes` raises `ConfigError`, mapped to `UsageError` | Exit 2 before any query; `<--prefixes|RDF_FINGERPRINTER_PREFIXES_FILE>: <file>: <reason>` |
| An invalid `RDF_FINGERPRINTER_PREFIX_LOOKUP` | `config.validate()` | Exit 2 before any query |
| `--module-size` below 1 | Click `IntRange(min=1)` | Exit 2 |
| An unwritable `--shapes-namespace` | `to_iriref` → `UsageError` | Exit 2 (before the query on `fingerprint`) |
| A file maps two prefixes to one namespace | Building the table | The first wins; DEBUG |
| A file names a reserved or `-shape` prefix | The precedence rules | Skipped; the namespace falls through; DEBUG |
| prefix.cc's HTTPS certificate fails verification | `ssl.SSLCertVerificationError` (possibly inside `URLError`) | Fetch over HTTP; INFO line |
| prefix.cc times out, refuses, is blocked, answers HTTP ≥ 400, or breaks off mid-answer | `OSError` (incl. `URLError`, `HTTPError`, timeouts, resets), `http.client.HTTPException`, `ValueError` (incl. JSON and Unicode errors) → `PrefixLookupError` | One WARNING; the missing prefixes are generated; the exit status is unchanged |
| The prefix.cc body is not a JSON object | Parse → `PrefixLookupError` | As above |
| A prefix.cc entry has an invalid name, an unwritable IRI, or a taken or reserved name | `_PREFIX_KEY` (the key with `:` appended), `to_iriref`, the table | Entry skipped; DEBUG |
| `--exclude-namespace` or `--include-namespace` matches nothing | `PrefixTable` lookup | WARNING (spec text); ignored |
| A gathered namespace cannot be written as an IRI (`to_iriref` fails) | Gathering the namespaces | Left out of the table and never declared; its IRIs stay unwritable caveats |
| A local name is not a valid Turtle local name | `_SAFE_LOCAL` | `<iri>` in Turtle; the CURIE stays elsewhere |
| A class IRI equals its namespace | An empty local name | Shown as `prefix:`; the shape local name is `_` |
| An old `profile.json` has no `namespaces` | The field is `None` | Resolved without a fetch |
| The page exceeds the size or time ceiling | Task 6.2 | D-7's fallback |

## Risks / Trade-offs

- [The standard vocabularies (`rdf`, `rdfs`, `owl`, `xsd`, `sh`, `fp`) are always offered under their
  standard prefix after the packaged file, and `rdf` is always in the table (the analytics add
  `rdf:langString`)] → Found in implementation; keeps the reserved names meaningful even with no
  packaged file.
- [prefix.cc over HTTP can be tampered with in transit] → Accepted by the developer: the names
  still pass `_PREFIX_KEY` and `to_iriref`, so the harm is limited to labels, and only happens when
  HTTPS fails on the certificate.
- [Shape IRIs are minted in namespaces the user does not own] → Accepted by the developer;
  `--shapes-namespace` is the way out, now on `fingerprint` too.
- [Generated names move when the user's file changes] → Intended; the source column shows the
  origin of each name.
- [Cluster borders move when classes are added] → Accepted; the overview keeps the reader
  oriented.
- [Breaking changes for library users] → Released as 3.0.0, with a migration section.
- [`llm-schema-tools` (a pitch, not shaped) has the no-go "No breaking change to
  `generate_endpoint_fingerprint_report` or the HTML report"] → This change lands first; that
  pitch's no-go must be re-stated against 3.0.0 when it is shaped.
- [Python's socket timeout does not bound DNS resolution (`getaddrinfo`)] → Accepted: a hung resolver
  can delay the lookup beyond 10 s; `--no-prefix-lookup` is the way out on such networks.
- [Tests reaching prefix.cc] → `tests/conftest.py` sets `RDF_FINGERPRINTER_PREFIX_LOOKUP=false` for
  every test (autouse); `make test-e2e` sets it too. Manual scenarios carry `@manual` and are skipped.

## Open Questions

None. The visual details are set in task 4.1, within D-7.
