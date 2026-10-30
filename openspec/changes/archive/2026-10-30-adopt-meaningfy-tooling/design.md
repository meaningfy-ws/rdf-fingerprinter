> Derives from: EPIC adopt-meaningfy-tooling (proposal.md)

## Context

See `inputs/gap-report.md` and `inputs/eds4jinja2-findings.md`. The code is small (~150 LOC);
the cost is in packaging, CI and test infrastructure, not refactoring.

## Goals / Non-Goals

**Goals:** a green, enforced `make check-all` locally and in CI on 3.12–3.14; Poetry packaging;
tokenless release; importable from any directory; reports correct on strict SPARQL stores;
published docs on GitHub Pages; release 1.0.0.

**Non-Goals:** the EPIC's No-gos.

## Decisions

- Configs are copied from the sibling eds4jinja2 2.0 (same standard), then trimmed to this repo:
  no domain/adapters contracts (DEC-4), no pydantic mypy plugin, no BDD targets.
- Package data: `packages = [{include = "fingerprint"}, {include = "fingerprint_report_templates"}]`;
  Poetry includes non-Python files inside included packages, so `MANIFEST.in` goes away.
- Console script kept: `fingerprint = "fingerprint.entrypoints.cli.main:fingerprint_endpoint"`.
- Runtime deps: `eds4jinja2>=2.0,<3`, `click>=8.5,<9` only (DEC-12); `python = ">=3.12,<4.0"`
  as in eds4jinja2 (open upper bound so consumers' resolvers are not over-constrained).
- Version 1.0.0 in `pyproject.toml` (DEC-13; classifier stays Beta until the hardening EPIC);
  `fingerprint.__version__` = `importlib.metadata.version`.
- mypy non-strict baseline with `ignore_missing_imports` (eds4jinja2 ships no stubs).
- Test store (DEC-10): `docker/docker-compose.yml` holds only an in-memory `oxigraph` service;
  `make oxigraph-load-test-data` loads `tests/test_data`. Tests needing a store live in
  `tests/e2e` (`make test-e2e`, local); `tests/unit` need none and are what `make test` runs.
  The e2e tests read `RDF_FINGERPRINTER_TEST_ENDPOINT` (default `http://localhost:7878/query`).
- CI/CD (DEC-5), copied from eds4jinja2 and trimmed: `ci.yml` (matrix 3.12/3.13/3.14,
  `make check-all` + `make build`, Codecov on 3.14), `publish.yml` (gate → build → PyPI via
  OIDC, no SBOM/Sigstore job), `docs.yml` (Antora build on PR, deploy to Pages on master).
- Docs (DEC-6): `docs/antora.yml` (versionless, `version: ~`), `docs/antora-playbook.yml`
  (builds from the checkout), `package.json` (Antora + lunr search), pages: Introduction,
  Getting Started, The Report, API Reference, Development. The `.eapx`/`.ods` model files stay.

## Algorithm / approach

Slices, each green on its own: (1) pyproject + lock + eds4jinja2 upgrade + delete legacy files,
(2) code fixes: logging, resources, SPARQL `STR()`, (3) tool configs + Makefile + Oxigraph store,
(4) `ruff --fix`/format debt, (5) CI + publish workflows, CHANGELOG, SECURITY, README,
(6) Antora docs + `docs.yml`, Sphinx/RTD removed, version 1.0.0.

### Anti-patterns
| Don't | Do instead | Why |
|---|---|---|
| Put `[tool.ruff]`/`[tool.pytest]` in pyproject | dedicated root files | Meaningfy config-in-root standard |
| Configure logging in a library module | `getLogger(__name__)`; configure in the CLI | importing must have no side effects |
| Assert byte-equal reports across stores | assert structure (titles, tables, classes) | spec-legal store differences |

## Error matrix
| Failure mode | How it is detected | Expected handling |
|---|---|---|
| Templates missing from wheel | `unzip -l dist/*.whl` in `make build` check | fix `packages` include |
| `eds4jinja2` won't resolve on 3.12–3.14 | `poetry lock` / CI matrix fails | fix upstream (DEC-8), not here |
| Report differs between stores beyond spec-legal noise | `RDF_FINGERPRINTER_TEST_ENDPOINT=<other store> make test-e2e` | portable SPARQL fix in templates (DEC-11) |
| e2e regression reaches a release (CI runs no store) | `make test-e2e` before tagging (Development page) | fix before publishing |
| Docs build breaks | `docs.yml` build job on the PR | fix the AsciiDoc |

## Risks / Trade-offs

- [Dropping 3.8–3.11 and the logging config breaks old installs/scripts] → 1.0.0 + CHANGELOG
  "Breaking" section.
- [Trusted Publishing not configured on PyPI] → first release fails; configure it before tagging.
- [GitHub Pages source not set to "GitHub Actions"] → the deploy job fails; set it once.
- [Read the Docs keeps serving 0.2.6] → owner deletes or redirects the RTD project (account action).

## Open Questions

None blocking. Follow-ups for the next (hardening/features) EPIC, from rdf-fingerprinter-ws's
`data-profiling-tool` DEC-4: (1) profile in a few whole-graph queries instead of one per class
(~3 s vs >2 min there), (2) a JSON fingerprint, (3) default graph plus a named ontology graph for
labels and superclasses, (6) prefix-compacted class headings. Items (4) import without
`logging.conf` and (5) Python 3.12+ are delivered here.
