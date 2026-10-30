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
- `eds4jinja2` constraint: `^<upstream release>` (DEC-8); `python = ">=3.12,<3.15"` (DEC-7).
- mypy starts with `ignore_missing_imports` for `eds4jinja2`/`SPARQLWrapper` (no stubs).

## Algorithm / approach

Prerequisite (outside this repo): eds4jinja2 release with loosened pins (DEC-8).
Slices, each one commit and green on its own: (1) pyproject + lock + eds4jinja2 upgrade, delete legacy files,
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
| `eds4jinja2` won't resolve on 3.12–3.14 | `poetry lock` / CI matrix fails | fix pins upstream (DEC-8), not here |
| Templates render differently under eds4jinja2 1.x | Fuseki e2e suites fail | fix templates minimally; report-output No-go applies |
| Fuseki not up in CI | e2e test connection error | `make fuseki-create-test-dbs` precedes `check-all` |

## Risks / Trade-offs

- [Dropping 3.8–3.11 breaks old installs] → semver MINOR bump to 0.4.0 + CHANGELOG note.
- [Trusted Publishing not configured on PyPI] → first release fails; configure it before tagging.

## Open Questions

- Which eds4jinja2 version carries the loosened pins? (blocks task 0.1)
- Is Read the Docs still used? If not, drop `.readthedocs.yml`/Sphinx in a follow-up rather than fix it.
