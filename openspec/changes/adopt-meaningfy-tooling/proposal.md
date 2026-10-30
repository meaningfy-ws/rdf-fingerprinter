# EPIC: Adopt the Meaningfy tooling baseline

## Appetite

SMALL — tooling and packaging only; the library's behaviour and public API stay as they are.

## Why

The library is still on `setup.py` + `requirements.txt`, runs no lint/type/architecture checks,
supports an EOL Python, and publishes to PyPI with a long-lived token. Every later upgrade (new
features, refactoring toward cosmic-python layers) needs a green, enforced `make check-all` first.

## Solution outline

One Poetry `pyproject.toml` replaces the four legacy packaging files. Ruff, mypy, pytest,
coverage and import-linter each get their own root config. The Makefile gains the standard gate
targets, ending in `make check-all`; CI runs exactly that. Releases move to release-please +
PyPI Trusted Publishing. Gaps and the reasons for each item are in `inputs/gap-report.md`.

## Key decisions

- **DEC-1**: Archetype **library** — it ships to PyPI and is not deployed; rejected: product
  (no `model/`, no image needed).
- **DEC-2**: Poetry `pyproject.toml` with `[dependency-groups]`, the version lives in
  `pyproject.toml` only; rejected: keeping setup.py (no lock, no groups).
- **DEC-3**: Ruff replaces flake8; rejected: wiring up flake8 (unused today, slower, more tools).
- **DEC-4**: `.importlinter` encodes today's layers (`entrypoints → service_layer`) only; the
  domain/adapters split waits for a real need; rejected: scaffolding empty layer packages now.
- **DEC-5**: Trusted Publishing (OIDC) from a `release.yaml`; rejected: `PIPY_USER_TOKEN` secret.
- **DEC-6**: Keep Sphinx/Read the Docs for now; rejected: Antora migration in this change.
- **DEC-7**: Minimum Python **3.12** (developer decision, 2026-10-30; matches the local toolchain, 3.12–3.14); rejected: 3.8/3.9 (EOL), 3.10/3.11 (developer chose the newer floor).

## Rabbit-holes

- Lint debt: run `ruff --fix` once in its own commit; do not hand-polish legacy code.
- Coverage: both suites need Fuseki, so the threshold is measured with Fuseki up in CI; do not
  build mocks to chase a number in this change.
- `eds4jinja2` pins old transitive dependencies; if resolution fails on 3.12+, stop and park it.

## No-gos

- No change to the CLI options, `generate_endpoint_fingerprint_report` signature or report output.
- No restructuring into domain/adapters/services packages.
- No Antora docs, `infra/`, Sonar, or community files (CONTRIBUTING, CODE_OF_CONDUCT).
- No fix of the logging-on-import defect here — it gets its own change (see gap report).

---

## What Changes

- Add `pyproject.toml` (Poetry) and `poetry.lock`; remove `setup.py`, `setup.cfg`,
  `requirements.txt`, `requirements-dev.txt`, `MANIFEST.in`.
- **BREAKING**: drop Python 3.8–3.11 support (DEC-7).
- Add `ruff.toml`, `mypy.ini`, `pytest.ini`, `.coveragerc`, `.importlinter`.
- Makefile: `install` via Poetry; add `lint`, `format`, `typecheck`, `check-architecture`,
  `validate-specs`, `check-all`; `build` replaces `publish-pipy`.
- CI: replace `test.yml` + `package.yml` with `ci.yaml` (runs `make check-all`) and
  `release.yaml` (release-please + Trusted Publishing).
- Add `CHANGELOG.md` and `SECURITY.md`.

## Capabilities

### New Capabilities
- `developer-tooling`: the quality gates and release path every contributor and CI run.

### Modified Capabilities

## Impact

Build, CI and release only. PyPI publisher must be configured for Trusted Publishing on
`meaningfy-ws/rdf-fingerprinter` before the first release. Contributors switch from
`pip install -r` to `make install` (Poetry).
