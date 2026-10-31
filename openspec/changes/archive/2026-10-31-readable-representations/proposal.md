# EPIC: Readable representations: prefixes everywhere, one usable report, digestible diagrams

## Appetite

LARGE. The change touches every output (the report, SHACL, PlantUML), the saved profile, the CLI and
the library API. It adds no new statistics and changes no queries. Seeds:
`inputs/brainframe-application-test-remarks.md` (remarks R1–R7) and `inputs/developer-answers.md`
(the developer's answers, 2026-10-31).

## Why

On real data (brainframe: 79k triples, 58 classes, 1,212 predicate partitions) the fingerprinter
produces correct numbers, but in outputs nobody can read:
- Namespaces outside the packaged prefix file stay as full IRIs; one diagram holds 1,382 of them.
- `main.html` and `profile.html` repeat each other, and neither can be searched or filtered.
- Shape IRIs are percent-encoded URNs.
- One diagram holds every class of a graph.

## Solution outline

- **Every namespace has a prefix.** After collection, each namespace in use gets a prefix. It comes
  from the user's file, the packaged file or prefix.cc; if none of them names it, the prefix is
  generated. The table is saved in `profile.json`, so every output uses the same names, offline
  generators included (DEC-1, DEC-2, DEC-10).
- **One report, one render path.** The report is the document generator's page: a self-contained
  static HTML file with a plain, modern design, a table of contents, search, namespace filters and
  collapsible classes. IRIs are always shown as `prefix:local` (DEC-3, DEC-4, DEC-9).
- **Namespace filters.** By default no output shows the classes of the meta vocabularies (`rdf`,
  `rdfs`, `owl`, `sh`). `--exclude-namespace` and `--include-namespace` change that set (DEC-5,
  DEC-8).
- **Readable shape IRIs** follow the policy in DEC-6, e.g. `brainframe-shape:AccountingSystem`.
- **Digestible diagrams.** Each graph gets one overview diagram, plus one diagram per namespace. A
  large namespace is split into clusters of closely linked classes (DEC-7).

## Key decisions

- **DEC-1 Prefix sources, in precedence order:**
  1. a user prefix file (`--prefixes FILE` on every command, else `RDF_FINGERPRINTER_PREFIXES_FILE`);
  2. the table saved in the profile, when a saved profile is re-rendered;
  3. the packaged `prefixes.json`;
  4. prefix.cc, fetched as one full prefix list per run (HTTPS first, then plain HTTP only when the certificate fails, as the developer chose on 2026-10-31) and reversed locally;
  5. a generated prefix.

  The lookup is on by default and can be switched off with `--no-prefix-lookup` or
  `RDF_FINGERPRINTER_PREFIX_LOOKUP=false`. If it fails, the run logs one warning and goes on.

  Rationale: the user controls the names, and a single list download sends none of the store's
  namespaces to a third party. Rejected: per-namespace reverse lookups (one request per namespace,
  and they leak the store's namespaces); a vendored snapshot (it goes stale, and the developer asked
  for a lookup on every run); a lookup at render time (representations derive from the saved
  profile only).
- **DEC-2 Generated prefixes are deterministic and hierarchical.**
  - A sub-namespace of a named namespace takes the parent's prefix plus its extra path segments or
    subdomain labels: `ex-core`, `ex-data`.
  - Otherwise the prefix comes from the most specific meaningful path segment, else from the
    domain's own label.
  - Clashes get a numeric suffix.
  - The exact rules are in the `namespace-prefixes` spec.

  Rejected: `ns1`, `ns2`, … (the 2020 PoC); they tell a reader nothing.
- **DEC-3 One HTML page.** `main.html` is the only HTML output. The run always writes it, and
  `fingerprint-gen-doc` writes the same page from a saved `profile.json`. `--format doc` stays
  accepted on `fingerprint`, as a logged no-op. `profile.html` goes. Rejected: keeping two
  templates, since they repeat each other.
- **DEC-4 Static, self-contained, readable without JavaScript.** The HTML is rendered server-side.
  Inline CSS and a small inline vanilla script add search, filtering and collapsing. There are no
  external requests. The page's behaviour is checked statically by tests and once by hand; there are
  no browser tests (developer, 2026-10-31). Rejected: a JSON payload rendered in the browser; a UI
  framework; Playwright.
- **DEC-5 Namespace filters are a representation option.** `--exclude-namespace` and
  `--include-namespace` (prefix or IRI, repeatable) adjust the set of excluded namespaces, starting
  from the default (DEC-8). Every output drops the classes of the excluded namespaces, and the report
  lists what it hid. A name that is not in the table logs a warning and is ignored; it is not a usage
  error, because on `fingerprint` the table exists only after collection. Rejected: filtering at
  collection time (the profile would no longer describe the store).
- **DEC-6 Shape IRI policy (model2owl skipped).**
  - A class's shapes live in `<class namespace minus its trailing # / :>/shape/` under the prefix
    `<class prefix>-shape`. A URN namespace uses `…:shape:` instead.
  - A node shape is named `<local>`; a property shape is named
    `<local>-<property prefix>-<property local>`.
  - With `--shapes-namespace` set (now on `fingerprint` too), all shapes go there under the prefix `shape`, named
    `<class prefix>-<local>…`.
  - Collisions get `-2`, `-3`, … in sorted order.
  - Shape IRIs are minted inside the class's namespace even when the user does not own it. This was
    accepted by the developer (2026-10-31); `--shapes-namespace` is the way out.

  Rejected: percent-encoded URNs; blank-node property shapes.
- **DEC-7 An overview plus per-namespace modules, never one diagram per class.**
  - Each graph gets an overview (namespaces as packages, with counted links), plus one module
    diagram per namespace.
  - A namespace with more classes than `--module-size` (default 15) is split into deterministic
    clusters of linked classes.
  - A class from another module appears as a bare reference box.

  Rejected: one diagram per class; one diagram per graph.
- **DEC-8 Meta vocabularies are excluded by default.** Classes in the `rdf`, `rdfs`, `owl` and
  `sh` namespaces (matched by namespace IRI, whatever their prefix) are left out of every output
  unless included again (developer, 2026-10-31).
- **DEC-9 One render path; the 1.x library API is removed (developer: "major rework").** The
  following are removed: `render_report`, `generate_report_builder_config`,
  `generate_endpoint_fingerprint_report`, and the `template_location` / `extra_conf` /
  `conf.profile` template contract. The library entry is `fingerprint_report`. A custom template is
  a template package that renders the document view model, like `--template` on the generators.
  Rejected: keeping the 1.x contract next to the new page, which means two render paths and a
  filter only one of them honours.
- **DEC-10 The longest matching namespace wins** when an IRI is shortened. Otherwise `ex:` would
  hide `ex-core:` and show `ex:core/Thing`.

## Rabbit-holes

- prefix.cc: one download per run, with a capped timeout and no retries (format verified; see
  design Context).
- Hash and slash namespaces, and fragment routes (`…/#/knowledge/…`): the splitting rule is in the
  spec. Do not invent more.
- Clustering: the simplest deterministic greedy method; it is not tuned.
- Page size and render time: the page must not be larger or slower than today's on brainframe. That
  is a ceiling, not a performance project.

## No-gos

- No new statistics, queries or collection modes, and no filtering at collection time.
- No hosted or interactive web app, no external assets, no PlantUML rendering to images, no browser
  test stack.
- No model2owl integration. No diagram per class.
- No change to the exit codes.
- The side finding `declared_subclass_edges` on an empty default graph is not fixed here; it is a
  separate bug-fix follow-up.

---

## What Changes

- A namespace table (prefix, namespace, source) is resolved after collection and saved in
  `profile.json`. Older profiles still load.
- New options on `fingerprint` and `fingerprint-gen-*`: `--prefixes FILE`, `--no-prefix-lookup`,
  `--exclude-namespace`, `--include-namespace`. Also new: `--module-size` (PlantUML), and `--shapes-namespace` on `fingerprint`.
- **BREAKING** `profile.html` is no longer written. `main.html` is the one page, with a new layout.
- **BREAKING** The 1.x library API and its template contract are removed (DEC-9).
- **BREAKING** The default SHACL shape IRIs change, and property shapes become named IRIs.
- **BREAKING** PlantUML writes an overview plus module files per graph, not one file per graph.
- **BREAKING** Meta-vocabulary classes are excluded from outputs by default.
- An empty graph produces no SHACL or PlantUML file.
- Version 3.0.0.

## Capabilities

### New Capabilities
- `namespace-prefixes`: resolving, generating, saving and applying a prefix for every namespace.

### Modified Capabilities
- `fingerprint-report`: one static report rendered by the document generator, the library entry,
  and the new CLI options.
- `profile-representations`: the shape IRI policy, modular diagrams, the namespace filters, no files
  for empty graphs, and the golden files.
- `statistics-collection`: "Settings" loses the 1.x `additional_config["collection"]` route (DEC-9).

## Impact

- **Code:**
  - `fingerprint/service_layer/`: `handlers.py`, with `report.py` removed, plus `generators/` and a
    new prefix resolution step.
  - `fingerprint/adapters/`: a prefix.cc client, and `load_prefixes` changes.
  - `fingerprint/domain/`: `iri.py` (longest match), and new `prefixes.py`, `modules.py`, `shapes.py`.
  - `model/*.yaml` and the generated models.
  - `fingerprint/entrypoints/cli/`.
- **Templates:** `fingerprint_report/` is redesigned and becomes the document package;
  `profile_document/` is removed; `plantuml_diagram/` and `shacl_shapes/` change.
- **Tests:** every golden file is regenerated. There are new unit tests for prefix generation and
  resolution (prefix.cc faked), for the filters and for the clustering. The Gherkin for all three
  capabilities and the e2e tests (with the lookup off) are updated.
- **Network:** one optional HTTP download from prefix.cc per run, using the stdlib (`urllib`). No new
  dependency.
- **Docs and release:** the user guide (options, outputs, prefix control, library API), and
  `CHANGELOG.md`, released as 3.0.0.
