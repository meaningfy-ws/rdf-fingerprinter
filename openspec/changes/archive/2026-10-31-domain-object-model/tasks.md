> Derives from: EPIC domain-object-model (proposal.md)

## 0. eds4jinja2 2.1 (in ../eds4jinja2, its own OpenSpec change)

- [x] 0.1 OpenSpec changes `render-documents` (spec `batch-document-rendering`) and `make-documents` (spec `checked-document-writing`) in eds4jinja2, split at the developer's request for `ReportBuilder.render_documents(outputs, *, autoescape)` and `make_documents(outputs, *, check, autoescape)` as P-6 specifies; branch `feature/batch-documents` there. Specification only: the developer implements it (2026-10-31)
- [x] 0.2 The developer implements and releases eds4jinja2 2.1.0; task 6.1 waits for it (P-6)

## 1. Rule, check and generated modules

- [x] 1.1 AGENTS.md *Working conventions*: the domain-objects rule (DEC-1)
- [x] 1.2 `tests/unit/test_no_composed_dicts.py` as P-1 specifies (annotations incl. bare `dict`; displays, comprehensions, `dict()` in functions; `update=`/`**`/UPPER_CASE/`# dict-ok:` exemptions) with `tests/unit/composed_dicts_allowlist.txt` holding today's offender count per file (Requirement: Values are domain objects)
- [x] 1.3 `fingerprint/domain/profile.py` and `profile_run.schema.json` from `make generate-models`; `fingerprint/domain/generated/` removed; imports, Ruff exclude, `.importlinter`, Makefile, docs paths (P-2; Requirement: Generated models stay in sync; Requirement: Generated code is read-only)

## 2. Configuration

- [x] 2.1 `adapters/config_resolver.py` (`ConfigResolverABC`, `EnvConfigResolver`, `DefaultConfigResolver`, instance-resolver `env_property`) with tests (P-7)
- [x] 2.2 `FingerprintConfig` + `config` in `fingerprint/__init__.py` with the P-7 variables and `validate()` raising `ConfigError`; constants replaced by `config.X`; `validate()` called at every entry point; import side-effect free (Requirement: Configuration through one typed config; Requirement: Import has no side effects)
- [x] 2.3 `SettingsOverride` in `model/fingerprint_stats.yaml` (+ field-name test); `resolve_settings` keeps its signature and builds overrides; `MappingConfigResolver`; CLI options, environment, `selected_graphs`, `--config` and `additional_config["collection"]` as overrides; `settings_sources.py` removed; `main.py` and `handlers.py` cleared from the allow-list (`generate.py` with the generator options in 5.2) (P-7; Requirement: Settings)

## 3. SPARQL client and collection (together: the row type changes under collection)

- [x] 3.1 Adapter: form-encoded POST via `urlopen(timeout=…)`, `Result.parse`, `SparqlPort` returning `ResultRow`s and `askAnswer`; `classify` with the 500-marker rule; backoff, markers and excerpt from config; `rows_from_json` removed (P-5; Requirement: Results are read as typed RDF terms; Requirement: Error classes and retries)
- [x] 3.2 `collection.py` builds the profile model objects from `ResultRow`s; blank nodes by `isinstance(BNode)` written as `_:<id>`; `ignore_imports = fingerprint.service_layer.collection -> rdflib` in the `service-io` contract (P-8); `FakeSparql` (`_once`, string rows in `on()`) returns rdflib `ResultRow`s; the `SPARQLWrapper.SPARQLWrapper.query` monkeypatches in `tests/unit/steps/test_fingerprint_report_steps.py`, `tests/unit/steps/test_profile_representations_steps.py` and `tests/e2e/test_representations.py` move to the new adapter; message-text assertions and `tests/unit/test_adapters_sparql.py` (SPARQLWrapper exceptions) updated; `SparqlWrapperClient` renamed `SparqlHttpClient` (P-5); SPARQLWrapper removed from `pyproject.toml`; a live collection equals `sample-profile.json` but for timestamps and version; `make test-e2e` green (P-8)

## 4. Analytics builds objects

- [x] 4.1 `domain/analytics.py` helpers return model objects (`CardinalityStatistics`, `CardinalityChoice`, `ValueIndicators`, mixins of `PropertyAnalytics`); `drop_none` removed; `domain/iri.py` prefix tables marked as lookup tables; analytics scenarios unchanged (P-8, P-1)

## 5. Views and generators

- [x] 5.1 `model/fingerprint_views.yaml` → `fingerprint/domain/views.py`; `check-models` diffs it (P-2, P-3)
- [x] 5.2 Generator hooks `visit_graph` / `visit_class` (pre-order filters) → `visit_property` → `end_class(…, properties)` → `end_graph(…, classes)`; `serialize() -> list[RenderedDocument]`; `GENERATORS` keyed by `RepresentationFormat`; `GeneratorOptions`; `representations.py` and the CLI on the enum and the options model (P-4, P-1)
- [x] 5.3 SHACL, PlantUML and document generators build view objects; the template edits listed in P-3; golden files byte-equal (DEC-8)

## 6. Rendering through eds4jinja2

- [x] 6.1 After 0.2: `eds4jinja2>=2.1,<3`; the port's `render` / `make` on `render_documents` / `make_documents` with the Turtle check and the format's autoescape; `report.py` on `make`; the `template_env` guard test removed; with it the review's fit items: an `end_profile` hook so `DocumentGenerator` overrides no walk method and `per_graph` decides, a shared `GraphView` mixin (`graph_label`, `slug`, `skipped`), no slug in `RenderedDocument.file_name`, `check` as a callable; `make test-e2e` green (P-6)

## 7. Close

- [x] 7.1 Allow-list of 1.2 empty; only `# dict-ok:` marks remain, each with its reason
- [x] 7.2 Docs: architecture (L3/L4, data flow), decisions (AD-12 domain objects and configuration; AD-1, AD-6, AD-9 updated for P-5/P-6), how-it-works (error classes on urllib), statistics (the variables table), api-reference (import paths, `GeneratorOptions`); CHANGELOG 2.1.0 (import path, SPARQLWrapper removed and the new request, the variables, stricter per-source settings checks)
- [x] 7.3 Pre-PR review (five lenses); act on findings
- [x] 7.4 `/opsx:archive` (one ADDED/MODIFIED section per delta; check the merged counts); PR #40 ready to merge

## Roadmap

- [x] 1.1 · [x] 1.2 · [x] 1.3 · [x] 0.1 · [x] 2.1 · [x] 2.2 · [x] 2.3 · [x] 3.1 · [x] 3.2 · [x] 4.1 · [x] 5.1 · [x] 5.2 · [x] 5.3 · [x] 0.2 · [x] 6.1 · [x] 7.1 · [x] 7.2 · [x] 7.3 · [ ] 7.4

## Verification

Each group: `make check-all`, golden files unchanged; `make test-e2e` after 3 and 6; `openspec validate domain-object-model --strict`; clarity gate ≥ 9/10 on this PLAN.
