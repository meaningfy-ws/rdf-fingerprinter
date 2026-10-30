# EPIC: Adopt the Meaningfy tooling baseline

## Appetite

MEDIUM — a radical modernisation of packaging, tooling, CI and the few runtime defects found on
the way (developer, 2026-10-30: "aim for a radical upgrade; keep backwards compatibility where
cheap, breaking changes are not a problem"; extended the same day: release as **1.0.0**, docs
on GitHub Pages, eds4jinja2's CI/CD minus e2e in GitHub). The public Python API and the report
output stay. Hardening is the next EPIC.

**Status: IN PROGRESS** — eds4jinja2 2.0.0 is on PyPI and measured (DEC-8,
`inputs/eds4jinja2-findings.md`).

## Why

The library is still on `setup.py` + `requirements.txt`, runs no lint/type/architecture checks,
supports an EOL Python, publishes to PyPI with a long-lived token, cannot be imported outside its
own repo root (logging config read from the CWD), and its SPARQL only works on lenient stores.
Every later upgrade needs a green, enforced `make check-all` first.

## Solution outline

One Poetry `pyproject.toml` replaces the five legacy packaging files. Ruff, mypy, pytest,
coverage and import-linter each get their own root config. The Makefile gains the standard gate
targets, ending in `make check-all`; CI runs exactly that on 3.12–3.14 without a SPARQL store
(the e2e tests run locally against Oxigraph, `make test-e2e`). Releases publish from a GitHub
Release via PyPI Trusted Publishing; Antora docs deploy to GitHub Pages. The library stops
configuring logging; the templates use portable SPARQL. Gaps: `inputs/gap-report.md`.

## Key decisions

- **DEC-1**: Archetype **library** — it ships to PyPI and is not deployed; rejected: product
  (no `model/`, no image needed).
- **DEC-2**: Poetry `pyproject.toml` with `[dependency-groups]`, the version lives in
  `pyproject.toml` only (`fingerprint.__version__` reads it from the installed metadata);
  rejected: keeping setup.py (no lock, no groups).
- **DEC-3**: Ruff replaces flake8; rejected: wiring up flake8 (unused today, slower, more tools).
- **DEC-4**: `.importlinter` encodes today's layers (`entrypoints → service_layer`) only; the
  domain/adapters split waits for a real need; rejected: scaffolding empty layer packages now.
- **DEC-5**: The minimal subset of eds4jinja2's CI/CD: `ci.yml` (gate on PR/master), `publish.yml`
  (Trusted Publishing on a published GitHub Release), `docs.yml` (Antora → GitHub Pages);
  rejected: `PIPY_USER_TOKEN` secret, release-please (the sibling does without), eds4jinja2's
  SBOM + Sigstore job (not minimal; a hardening item).
- **DEC-6**: Docs move to **AsciiDoc + Antora on GitHub Pages** (as eds4jinja2); Sphinx and
  `.readthedocs.yml` go. Read the Docs still serves 0.2.6 (built 2020-12-14) and no Pages site
  exists (checked 2026-10-30). Rejected: reviving Sphinx/RTD (config pins Python 3.7, stale).
- **DEC-7**: Minimum Python **3.12** (developer decision, 2026-10-30), tested on 3.12–3.14;
  rejected: 3.8/3.9 (EOL), 3.10/3.11 (developer chose the newer floor, as in eds4jinja2).
- **DEC-8**: Keep **eds4jinja2** and fix it upstream; depend on **eds4jinja2 `>=2.0,<3`**
  (released 2026-10-30: Python 3.12–3.14, pandas 3 / numpy 2); rejected: dropping it (templates
  are built on pandas DataFrames, a rewrite changes report output), staying on 1.0.4 (3.12-only).
  Evidence: `inputs/eds4jinja2-findings.md` — report output byte-identical to 0.2 on Fuseki.
- **DEC-9**: The library no longer configures logging: `logging.conf` and the import-time
  `fileConfig` go; modules only call `logging.getLogger(__name__)`, and the CLI calls
  `logging.basicConfig`. Breaking: the `fingerprinter` logger name and the DEBUG-to-stdout output
  are gone. Rejected: shipping `logging.conf` as package data (a library must not configure
  logging on import, and importing it from any other directory crashes today).
- **DEC-10**: **Oxigraph is the only test store**; e2e tests (those needing a store) live in
  `tests/e2e`, run locally with `make test-e2e`, not in GitHub. Measured 2026-10-30 (3 runs):
  suite 13.2–14.8 s vs Fuseki 13.9–16.5 s, treaties report 8.6 s vs 13.3 s, start-up ~1 s vs
  ~30 s plus dataset creation and auth. The endpoint comes from `RDF_FINGERPRINTER_TEST_ENDPOINT`,
  so any store can still be pointed at. Rejected: keeping Fuseki (slower, heavier, it hid
  DEC-11's bug), in-process pyoxigraph (the library talks HTTP to an endpoint).
- **DEC-13**: Release as **1.0.0** (developer, 2026-10-30): the API is stable and the breaking
  changes are bundled now; rejected: 0.4.0.
- **DEC-11**: Templates wrap `GROUP_CONCAT` arguments in `STR()`: SPARQL 1.1 makes
  `GROUP_CONCAT` over IRIs an error, which Oxigraph honours (columns came back empty) and Fuseki
  tolerates. Fuseki output is byte-identical after the fix.
- **DEC-12**: Templates are located with `importlib.resources.files()`; the leaked
  `path(...).__enter__()` and the `importlib-resources` backport go. Unused direct dependencies
  (`rdflib`, `SPARQLWrapper`, `pathlib`, `importlib-resources`) are dropped; eds4jinja2 brings
  what it needs.

## Rabbit-holes

- Lint debt: run `ruff --fix` + `ruff format` once; do not hand-polish legacy code.
- Coverage: reported, not gated, as in eds4jinja2; GitHub sees unit-test coverage only.
- Store differences the SPARQL spec allows (decimal lexical form `1` vs `1.0`, `GROUP_CONCAT`
  order) are accepted; tests assert structure, not byte-equality across stores.
- Speed work on eds4jinja2 is out of scope (measure first).

## No-gos

- No change to `generate_endpoint_fingerprint_report` / `generate_report_builder_config`
  signatures or to the CLI options.
- No restructuring into domain/adapters/services packages.
- No Antora docs, `infra/`, Sonar, or community files (CONTRIBUTING, CODE_OF_CONDUCT).
- No pruning of the legacy `resources/` samples (not packaged; a separate clean-up).
- No hardening (input validation, error handling, SBOM/signing) — the next EPIC.
- No deletion of the Read the Docs project itself (an account action outside the repo).

---

## What Changes

- Add `pyproject.toml` (Poetry) and `poetry.lock`; remove `setup.py`, `setup.cfg`,
  `requirements.txt`, `requirements-dev.txt`, `MANIFEST.in`.
- **BREAKING**: drop Python 3.8–3.11 support (DEC-7).
- **BREAKING**: the library no longer configures logging; `logging.conf` removed (DEC-9).
- Upgrade `eds4jinja2` 0.2 → 2.0 (DEC-8); update the `ReportBuilder` import.
- Portable SPARQL in the templates (DEC-11); `importlib.resources.files()` (DEC-12).
- Add `ruff.toml`, `mypy.ini`, `pytest.ini`, `.coveragerc`, `.importlinter`.
- Makefile: Poetry `install`; `lint`, `format`, `typecheck`, `check-architecture`, `check-spec`,
  `check-all`, `build`, `test-e2e`, Oxigraph store targets, `build-docs` (DEC-6, DEC-10).
- **BREAKING (contributors)**: Fuseki test targets removed (DEC-10).
- Docs: Antora under `docs/`, `package.json`; Sphinx files and `.readthedocs.yml` removed (DEC-6).
- Version **1.0.0** (DEC-13).
- CI: replace `test.yml` + `package.yml` with `ci.yml` (runs `make check-all`), `publish.yml`
  (Trusted Publishing) and `docs.yml` (GitHub Pages).
- Add `CHANGELOG.md` and `SECURITY.md`; README install/dev notes updated.

## Capabilities

### New Capabilities
- `developer-tooling`: the quality gates and release path every contributor and CI run.

### Modified Capabilities

## Impact

Build, CI, release, logging behaviour and SPARQL portability. PyPI publisher must be configured
for Trusted Publishing on `meaningfy-ws/rdf-fingerprinter` (workflow `publish.yml`, environment
`release`) before the first release, and GitHub Pages must be set to "GitHub Actions" as its source.
Contributors switch from `pip install -r` to `make install`.
