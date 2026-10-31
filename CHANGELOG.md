# Changelog

All notable changes to this project are documented in this file. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
- Docs: Representations, How It Works, Glossary, Architecture Decisions (AD-1 to AD-11) and a use
  case catalogue (UC-W1, UC-W2 and their realisations).

### Changed
- The output folder of `fingerprint` now also holds `profile.json`.
- Report rendering, setting sources and exceptions moved to their layers (`adapters/template_renderer.py`,
  `adapters/settings_sources.py`, an `exceptions` module per layer); every old import path still works.
- `make test` fails under 80 % coverage; every Gherkin scenario is tagged with its use case.

### Dependencies
- rdflib is now a declared runtime dependency (it was already installed through eds4jinja2);
  pySHACL 0.40.1 for tests.

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
