# Gap report — rdf-fingerprinter vs the Meaningfy standard (2026-10-30)

Audit input for `adopt-meaningfy-tooling`. Preserved, never groomed.
Archetype: **library** (PyPI `rdf-fingerprinter`, console script `fingerprint`). ~150 LOC of
Python in `fingerprint/`, report templates + SPARQL in `fingerprint_report_templates/`.

| Dimension | State | Finding |
|-----------|-------|---------|
| Spine | ✅ (this branch) | `openspec/` projected, schema pinned @ 1.4.1, `/opsx:*` core installed. |
| Agent file | ✅ (this branch) | `AGENTS.md` canonical + `CLAUDE.md` pointer, both regular files. |
| Layout | ✅ | Top-level package, no `/src`. |
| Packaging | ❌ | `setup.py` + `setup.cfg` + `requirements*.txt` + `MANIFEST.in`; no `pyproject.toml`, no lock. |
| Versions | ⚠️ | `python_requires>=3.8` (EOL); CI matrix 3.8/3.11; version in `fingerprint/__init__.py`. |
| Lint/format | ❌ | `flake8` listed but never run; no Ruff. |
| Types | ❌ | No mypy. |
| Tool configs | ⚠️ | pytest config in `setup.cfg [tool:pytest]`; no `pytest.ini`/`.coveragerc`/`ruff.toml`. |
| Tests | ⚠️ | `tests/unit`, `tests/e2e`; no marker hook, no coverage threshold. Both suites need a live Fuseki. |
| Architecture | ❌ | No `.importlinter`. Layers today: `entrypoints → service_layer`; no domain/adapters. |
| Makefile | ⚠️ | `install`/`test`/Fuseki/`publish-pipy`; no `lint`/`typecheck`/`check-architecture`/`check-all`. |
| CI | ⚠️ | `test.yml` calls make but no quality gates; runs `setup.py sdist`. |
| Release | ❌ | `package.yml` publishes with a long-lived PyPI token via `twine`; no `CHANGELOG.md`, no `SECURITY.md`. |
| Docs | ⚠️ | Sphinx + `.readthedocs.yml` (config pins Python 3.7 — likely broken). Not Antora. |
| Infra | ✅ (n/a) | `docker/` only hosts the test Fuseki; a library ships no image. |
| Memory | n/a | No legacy `.claude/memory/epics/`. |

## Defects spotted (not tooling — separate changes)

- `fingerprint/__init__.py` calls `logging.config.fileConfig('logging.conf')` at import, relative
  to the CWD: importing the installed library from any other directory raises `FileNotFoundError: logging.conf doesn't exist` (verified 2026-10-30).
  A library must not configure logging on import.
- `handlers.py` keeps an `importlib_resources` fallback and calls `pkg_resources.path(...).__enter__()`
  without ever exiting the context (leaks a temp dir on zipped installs).

## Deliberately not adopted (scaffolder `+ create` items judged unnecessary here)

`sonar-project.properties`, `VERSION` file, `INSTALL.md`, `CONTRIBUTING.md`,
`CODE_OF_CONDUCT.md`, `infra/`, Antora `docs/`, the `domain/adapters/services/commons` package
skeleton, `.claude/memory/MEMORY.md` (the `config.yaml` `context:` is the index).
