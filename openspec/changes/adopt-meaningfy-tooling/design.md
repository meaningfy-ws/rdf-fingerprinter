> Derives from: EPIC adopt-meaningfy-tooling (proposal.md)

## Context

See `inputs/gap-report.md`. The code is small; the cost is in packaging and CI, not refactoring.

## Goals / Non-Goals

**Goals:** a green, enforced `make check-all` locally and in CI; Poetry packaging; tokenless release.

**Non-Goals:** the EPIC's No-gos.

## Decisions

- Configs are copied from the project-setup templates, then trimmed to this repo: drop the
  `domain/adapters` contracts (DEC-4), drop LinkML/FastAPI/testcontainers groups.
- Package data: `packages = [{include = "fingerprint"}, {include = "fingerprint_report_templates"}]`;
  Poetry includes non-Python files inside included packages, so `MANIFEST.in` goes away.
- Console script kept: `fingerprint = "fingerprint.entrypoints.cli.main:fingerprint_endpoint"`.
- Runtime deps keep their current lower bounds (`~=` → `^`), `pathlib` dropped (stdlib).
- Coverage gate set to the measured baseline rounded down, raised to 80% in a later change.
- mypy starts with `ignore_missing_imports` for `eds4jinja2`/`SPARQLWrapper` (no stubs).

## Algorithm / approach

Slices, each one commit and green on its own: (1) pyproject + lock, delete legacy files,
(2) tool configs + Makefile targets, (3) `ruff --fix` debt, (4) CI + release workflows.

### Anti-patterns
| Don't | Do instead | Why |
|---|---|---|
| Put `[tool.ruff]`/`[tool.pytest]` in pyproject | dedicated root files | Meaningfy config-in-root standard |
| Mix lint auto-fixes with config changes | separate commit | reviewable diff |

## Error matrix
| Failure mode | How it is detected | Expected handling |
|---|---|---|
| Templates missing from wheel | `unzip -l dist/*.whl` check in CI build step | fix `packages` include |
| `eds4jinja2` won't resolve on 3.12+ | `poetry lock` fails | stop, park as open question |
| Fuseki not up in CI | e2e test connection error | `make fuseki-create-test-dbs` precedes `check-all` |

## Risks / Trade-offs

- [Dropping 3.8–3.11 breaks old installs] → semver MINOR bump to 0.4.0 + CHANGELOG note.
- [Trusted Publishing not configured on PyPI] → first release fails; configure it before tagging.

## Open Questions

- Is Read the Docs still used? If not, drop `.readthedocs.yml`/Sphinx in a follow-up rather than fix it.
