> Derives from: EPIC adopt-meaningfy-tooling (proposal.md)

## 0. Prerequisite

- [x] 0.1 eds4jinja2 released with loosened numpy/pandas pins and installable on 3.12–3.14 (DEC-8; eds4jinja2 2.0.0 on PyPI, 2026-10-30)

## 1. Packaging

- [x] 1.1 Add Poetry `pyproject.toml` (DEC-2, DEC-7, DEC-12) and `poetry.lock`; remove setup.py, setup.cfg, requirements*.txt, MANIFEST.in
- [x] 1.2 Upgrade eds4jinja2 to `>=2.0,<3` and move the `ReportBuilder` import to `eds4jinja2.services.report_builder` (DEC-8)
- [x] 1.3 Verify the wheel ships `fingerprint_report_templates` and the `fingerprint` script works (Requirement: Tokenless release)

## 2. Runtime fixes

- [x] 2.1 Remove `logging.conf` and import-time `fileConfig`; `getLogger(__name__)`; CLI `basicConfig` (DEC-9; Requirement: Import has no side effects)
- [x] 2.2 Locate templates with `importlib.resources.files()`; drop the backport fallback (DEC-12)
- [x] 2.3 Wrap `GROUP_CONCAT` arguments in `STR()` (DEC-11; Requirement: Reports on strict SPARQL stores)

## 3. Quality gates and test store

- [x] 3.1 Add ruff.toml, mypy.ini, pytest.ini, .coveragerc, .importlinter (DEC-3, DEC-4)
- [x] 3.2 Makefile: Poetry `install`, `lint`, `format`, `typecheck`, `check-architecture`, `check-spec`, `test`, `check-all`, `build`; Oxigraph + Fuseki store targets (DEC-10; Requirement: Single quality gate)
- [x] 3.3 Tests read `RDF_FINGERPRINTER_TEST_ENDPOINT`; green on Oxigraph and Fuseki
- [x] 3.5 Oxigraph only: drop Fuseki targets/service; store tests to `tests/e2e`, `make test-e2e`; `make test` = unit (DEC-10)
- [x] 3.4 Fix lint/type debt until `make check-all` is green

## 4. CI and release

- [x] 4.1 Replace test.yml with ci.yml: 3.12–3.14, `make check-all`, no store (Requirement: CI runs the gate)
- [x] 4.2 Replace package.yml with publish.yml: Trusted Publishing on GitHub Release (DEC-5)
- [x] 4.3 Add CHANGELOG.md (1.0.0 entry) and SECURITY.md; update README

## 5. Docs and 1.0

- [x] 5.1 Antora docs (Introduction, Getting Started, The Report, API Reference, Development); remove Sphinx + `.readthedocs.yml` (DEC-6; Requirement: Published documentation)
- [x] 5.2 `docs.yml`: build on PR, deploy to GitHub Pages on master (DEC-5, DEC-6)
- [x] 5.3 Version 1.0.0 (DEC-13)

## Roadmap

- [x] 0.1 · [x] 1.1 · [x] 1.2 · [x] 1.3 · [x] 2.1 · [x] 2.2 · [x] 2.3 · [x] 3.1 · [x] 3.2 · [x] 3.3 · [x] 3.4 · [x] 4.1 · [x] 4.2 · [x] 4.3 · [x] 3.5 · [x] 5.1 · [x] 5.2 · [x] 5.3

## Verification

`make check-all` green locally (3.12, 3.13, 3.14) and in CI; `make test-e2e` green on Oxigraph;
`make build-docs` without warnings;
`openspec validate --strict`; built wheel inspected; package imported from outside the repo root.
