# EPIC: Pitfall scans — the fingerprint reports modelling pitfalls, not only statistics

## Appetite

LARGE. The change adds a new collection stage, a new capability (`pitfall-scans`) with a packaged
check catalogue, new profile and view models, a report section, a new output format and CLI and
library options. It touches every layer, but it reuses the collection, rendering and generator
frameworks as they are. Seeds are in `inputs/`:
- `brainframe-modelling-analysis.md` and `brainframe-robot-report.md` (the 2026-11-01 quality run);
- `seed-queries/` (29 SPARQL checks: 25 derived from OOPS!, 4 extra);
- `developer-requests.md` (verbatim).

Golden-thread parents: `openspec/specs/statistics-collection` (staged, read-only collection),
`fingerprint-report`, `profile-representations` and `namespace-prefixes`.

## Why

The fingerprint describes *what* a dataset holds, but not *what is wrong with how it is modelled*.
On brainframe, finding the pitfalls needed a separate toolchain (ROBOT in Docker, hand-written
SPARQL, a second store). Among them, 1,100 relations are used but never defined. The fingerprinter
already talks to the endpoint and knows the graphs, so it can run the same checks in the same pass
and show them next to the profile.

## Solution outline

- **A packaged catalogue of pitfall checks.** Each check is one SPARQL `SELECT` file with a metadata
  header (id, title, importance, scope, source). The catalogue starts from the 29 seed queries: OOPS!
  P04–P41 where SPARQL can express them, plus four extra checks (punning, individuals as predicates,
  domain and range use in the data).
- **A new, opt-in collection stage.** After the profile stages, the run sends each check once per
  profiled graph, over a dataset made of that graph plus the schema graphs the user names. It stores
  the count and the first examples of each check in `profile.json`. Failures and timeouts are
  recorded like other collection failures.
- **Pitfalls in every output where they belong:**
  - the report page gets a *Pitfalls* section, with a summary by importance, one entry per check
    with examples as short names, and a badge on the class sections the findings name;
  - a new `pitfalls` format writes ROBOT-compatible TSV;
  - an optional `--fail-on` level turns findings into an exit status for CI.
- **User checks:** a folder of the user's own `.rq` files, with the same contract, extends or
  replaces the catalogue.

## Key decisions

- **DEC-1 Checks are SPARQL files with a header contract.** Each file returns `?entity ?property
  ?value`, ROBOT's report convention, so ROBOT profiles and the fingerprinter share queries. The
  header comments give `id`, `title`, `importance` (`critical` | `important` | `minor`), `scope`
  (`schema` | `data`), `source` (e.g. `OOPS! P35`) and `heuristic` (true or false). The files live in
  `fingerprint/adapters/queries/pitfalls/`. Rejected: checks as Python code (users couldn't extend
  them; ROBOT couldn't share them); running OOPS! itself (Java, a Maven build, no SPARQL, and a web
  service).
- **DEC-2 Opt-in, a new setting.** `pitfall_scan` (`--pitfalls`, `RDF_FINGERPRINTER_PITFALL_SCAN`) is
  false by default, like `graph_statistics`: several checks scan every triple. Rejected: on by default
  (it would surprise users of large endpoints with full scans).
- **DEC-3 The scan dataset: each profiled graph plus the schema graphs.** `--schema-graph IRI`
  (repeatable; setting `schema_graphs`) names the graphs that hold the ontology. For a named graph,
  each check runs with `FROM <graph>` plus one `FROM <schema>` per schema graph. For the default
  graph, it runs with no `FROM`, which is the store's default graph. A schema graph that is itself
  profiled is scanned on its own, too. Rejected: one scan over a union of every graph (it can't
  include the default graph portably, and it mixes unrelated graphs); `GRAPH` blocks (a pattern
  can't join across two graphs).
- **DEC-4 Count plus a bounded sample per check.** The check body runs twice: wrapped as
  `SELECT (COUNT(*) AS ?n)`, then with `LIMIT pitfall_examples` (default 10). The profile keeps the
  count and the examples, not every row. Rejected: storing every row (P35 alone is 1,100 rows on
  brainframe, and unbounded in general).
- **DEC-5 Results are part of the raw profile.** `GraphProfile.pitfalls` holds the results, and a run
  without the scan has none. The analytics only add the summary. The representations derive from the
  saved profile, as for everything else (profile-representations), so `fingerprint-gen-doc` and
  `fingerprint-gen-pitfalls` work offline. Rejected: a separate `pitfalls.json` (two files to keep
  together).
- **DEC-6 Failures follow the collection rules.** A check that times out or is rejected is a recorded
  `Failure` with the query kind `pitfall` and the check id, and the run exits 1, as for any recorded
  failure. Rejected: ignoring failed checks silently (a clean-looking report would be wrong).
- **DEC-7 Read-only is enforced.** Every check, packaged or the user's, is parsed before any query and
  must be a `SELECT`. Anything else is a usage error. This keeps the "Read-only and credential-safe"
  requirement. Rejected: trusting user files.
- **DEC-8 User checks extend the catalogue.** `--pitfall-checks DIR` adds the user's `.rq` files; a
  user check with a packaged check's id replaces it. `--skip-pitfall ID` (repeatable) leaves checks
  out. Rejected: replace-only (users would lose the packaged checks).
- **DEC-9 One new format, `pitfalls`.** It writes `pitfalls-<graph>.tsv` with ROBOT's columns: Level,
  Rule Name, Subject, Property, Value. The levels map as critical → ERROR, important → WARN,
  minor → INFO. This lets pitfall output join ROBOT-based pipelines. Rejected: JSON only (no
  existing tool reads it); a SHACL report (the findings are not shape violations).
- **DEC-10 `--fail-on LEVEL` adds exit status 5.** Exit 5 means the run succeeded but found pitfalls
  at or above the level (`critical` | `important` | `minor`; default: none). Collection failures still
  exit 1 and take precedence. Rejected: reusing exit 1 (it couldn't tell "data is bad" from "the run
  failed").
- **DEC-11 Findings' IRIs join the namespace table.** The entity, property and value IRIs of each
  finding are gathered with the rest (namespace-prefixes), so the report shows them as short names.
  The filters do not hide findings: a finding in a hidden namespace is still a finding.
- **DEC-12 Our own words, with attribution.** Check titles and descriptions are written fresh. OOPS!
  is cited as the source catalogue, with its pitfall code and a link. Rejected: copying OOPS!'s texts
  (their licence was not checked).

## Rabbit-holes

- Some checks are inherently expensive on large stores: P35 scans every predicate, P32 compares class
  pairs, P06 uses a property path. The scan is opt-in, each query has the run's timeout, and a
  timeout is a recorded failure. Do not try to optimise the checks per store.
- Store differences in `FROM` and default-graph semantics (union-default stores, rdflib, Oxigraph).
  Settle on what the e2e store and the unit-test fake do; document the rest.
- Heuristic checks (P07, P20, P21, P12/P30) give false positives. They are marked `heuristic` and
  are minor; do not tune them.
- The "closed world" reading of the domain and range checks: label them as data checks against the
  declared schema, not as OWL errors.

## No-gos

- No reasoning, no OWL API, and no dependency on ROBOT or OOPS! at run time.
- No lexical or WordNet checks (OOPS! P02 and P31; full P12/P30), and no HTTP checks of namespaces
  (P37, P39, P40).
- No automatic fixes, and no changes to the SHACL shapes or the PlantUML diagrams because of
  findings.
- No pitfall scan by default, and no change to the existing exit codes 0–4.
- No per-store tuning of the checks.

---

## What Changes

- New settings and options: `pitfall_scan` (`--pitfalls`), `schema_graphs` (`--schema-graph`),
  `pitfall_examples` (`--pitfall-examples`), and the CLI-only `--pitfall-checks DIR`,
  `--skip-pitfall ID` and `--fail-on LEVEL`.
- A packaged catalogue of 29 checks; the seed queries, rewritten to the header contract.
- Profile model: `GraphProfile.pitfalls` (`PitfallResult` with check id, title, importance, scope,
  source, count, examples and duration); `QueryKind.pitfall`.
- Report page: a *Pitfalls* section, badges on the class sections, and a contents entry.
- A new format `pitfalls` (`--format pitfalls`, `fingerprint-gen-pitfalls`) writing ROBOT-style TSV.
- Exit status 5 with `--fail-on`.
- `make scan-files ONTOLOGY=… [DATA=…] OUT=…`: loads files into the dev Oxigraph and fingerprints
  them with the scan (developer tooling).
- Docs: a *Pitfalls* page with the catalogue; the CLI, settings and exit-status tables.

## Capabilities

### New Capabilities
- `pitfall-scans`: the check catalogue and contract, the scan stage, results in the profile, user
  checks, the TSV format, and `--fail-on`.

### Modified Capabilities
- `statistics-collection`: "Settings" gains the scan settings; "Read-only and credential-safe"
  covers the checks.
- `fingerprint-report`: "Report content" gains the Pitfalls section; "Exit status" gains code 5;
  "Formats rendered after collecting" gains `pitfalls`.
- `namespace-prefixes`: "Every namespace has a prefix" gathers the findings' IRIs too.
- `developer-tooling`: `make scan-files`.

## Impact

- **Code:**
  - `fingerprint/adapters/queries/pitfalls/` (29 `.rq` files) and a catalogue loader;
  - `fingerprint/domain/` (a `pitfalls.py` for the header contract and the level mapping);
  - `fingerprint/service_layer/` (a scan stage in collection, the summary in the analytics, a
    `PitfallsGenerator`, the report view);
  - `fingerprint/entrypoints/cli/` (the options, `fingerprint-gen-pitfalls`, exit 5);
  - `model/*.yaml` and the generated models;
  - `fingerprint_report_templates/` (the report section, a `pitfalls_tsv` package).
- **Endpoints:** with `--pitfalls`, up to 2 × 29 queries more per profiled graph, some of them full
  scans.
- **Tests:**
  - each check against small positive and negative Turtle fixtures, run through `FakeSparql`;
  - golden files for the TSV and the page;
  - e2e against Oxigraph with a schema graph.
- **Release:** a MINOR version (new opt-in features; nothing breaking).
