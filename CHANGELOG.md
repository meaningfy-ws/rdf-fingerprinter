# Changelog

All notable changes to this project are documented in this file. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
