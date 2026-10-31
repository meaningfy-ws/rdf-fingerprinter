> Derives from: EPIC domain-object-model (proposal.md)

## 0. eds4jinja2 2.1 (in ../eds4jinja2, its own OpenSpec change)

- [ ] 0.1 OpenSpec change `batch-documents` in eds4jinja2: proposal, spec delta and tasks for `ReportBuilder.make_documents(outputs, check)` (P-6); TDD there; `make_document()` unchanged; CHANGELOG 2.1.0
- [ ] 0.2 PR in eds4jinja2, CI green; release 2.1.0 only after the developer's go-ahead (P-6)

## 1. Rule, check and generated modules

- [ ] 1.1 AGENTS.md *Working conventions*: the domain-objects rule (DEC-1); spec deltas for `developer-tooling` and `statistics-collection` (this change)
- [ ] 1.2 `tests/unit/test_no_composed_dicts.py` with `# dict-ok:` marks and a temporary allow-list file of today's offenders (P-1; Requirement: Values are domain objects)
- [ ] 1.3 Generated model moved to `fingerprint/domain/profile.py` and `profile_run.schema.json`; `fingerprint/domain/generated/` removed; imports, Makefile, Ruff exclude, `.importlinter`, docs paths updated (P-2; Requirement: Generated models stay in sync)

## 2. Configuration

- [ ] 2.1 `adapters/config_resolver.py` (`env_property`, `EnvConfigResolver`, `DefaultConfigResolver`) with tests (P-7)
- [ ] 2.2 `FingerprintConfig` in `fingerprint/__init__.py` with the P-7 variables; constants replaced by `config.X`; import still side-effect free (Requirement: Import has no side effects; Requirement: Configuration through one typed config)
- [ ] 2.3 `SettingsOverride` in `model/fingerprint_stats.yaml`; `resolve_settings(*overrides)`; config file parsed into an override; `settings_sources.py` removed; precedence scenarios unchanged (P-7; Requirement: Settings)

## 3. SPARQL client

- [ ] 3.1 Adapter on `urlopen` + `rdflib.query.Result.parse`; `SparqlPort` returns `ResultRow`s; `classify` on urllib/socket errors; retry backoff from config (P-5; Requirement: Error classes and retries)
- [ ] 3.2 `tests/unit/fakes.py` `FakeSparql` returns rdflib `ResultRow`s from its in-memory store; SPARQLWrapper removed from `pyproject.toml`; `make test-e2e` green

## 4. Collection builds objects

- [ ] 4.1 `collection.py` builds `GraphProfile` / `ClassProfile` / `PropertyProfile` / `ValuePartition` / … from `ResultRow`s; `Row` and `drop_none` uses removed; a live collection equals `sample-profile.json` but for timestamps and version (P-8)

## 5. Analytics builds objects

- [ ] 5.1 `domain/analytics.py` helpers return model objects; `drop_none` removed; every analytics scenario unchanged (P-8)

## 6. Views and generators

- [ ] 6.1 `model/fingerprint_views.yaml` → `fingerprint/domain/views.py` via `make generate-models` (P-2, P-3)
- [ ] 6.2 Generator base bottom-up (`visit_property` → `visit_class(…, properties)` → `visit_graph(…, classes)`), `GENERATORS` keyed by `RepresentationFormat` (P-4)
- [ ] 6.3 SHACL, PlantUML and document generators build view objects; templates read attributes; golden files byte-equal (DEC-8)

## 7. Rendering through eds4jinja2

- [ ] 7.1 After 0.2: `eds4jinja2>=2.1,<3`; the template renderer adapter calls `make_documents` with the Turtle check; `render`/`write` and the `template_env` guard test removed; `make test-e2e` green (P-6)

## 8. Close

- [ ] 8.1 Allow-list of 1.2 empty; only `# dict-ok:` marks remain, each with its reason
- [ ] 8.2 Docs: architecture (L3/L4, data flow), decisions (AD-12 domain objects and configuration; AD-1/AD-6/AD-9 updated for P-5/P-6), how-it-works (settings and variables), statistics (the variables table), api-reference (import paths); CHANGELOG 2.1.0 updated (import path, SPARQLWrapper removed, variables)
- [ ] 8.3 Pre-PR review (five lenses); act on findings
- [ ] 8.4 `/opsx:archive`; then PR #40 is ready to merge

## Roadmap

- [ ] 1.1 · [ ] 1.2 · [ ] 1.3 · [ ] 0.1 · [ ] 2.1 · [ ] 2.2 · [ ] 2.3 · [ ] 3.1 · [ ] 3.2 · [ ] 4.1 · [ ] 5.1 · [ ] 6.1 · [ ] 6.2 · [ ] 6.3 · [ ] 0.2 · [ ] 7.1 · [ ] 8.1 · [ ] 8.2 · [ ] 8.3 · [ ] 8.4

## Verification

Each group: `make check-all`, golden files unchanged, `make test-e2e` after 3, 4 and 7; `openspec validate domain-object-model --strict`; clarity gate ≥ 9/10 on this PLAN.
