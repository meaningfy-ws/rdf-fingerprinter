# EPIC: develop integration branch

## Appetite

TINY

## Why

The developer created a `develop` integration branch (2026-11-01) and wants feature PRs into it as
well as `master`. CI gated only PRs into `master`, so a PR into `develop` ran no checks. The living
spec "CI runs the gate" names `master` alone, and its guard test failed once `ci.yml` added
`develop`, which broke `check-all` on `master` after the 3.3.0 merge.

## Solution outline

CI runs `make check-all` on pushes and pull requests to `master` and `develop`; the requirement and
its guard test say so. The branch flow itself is recorded in `AGENTS.md` and `development.adoc`
(commit 3c94fbc).

## Key decisions

- **DEC-1**: `master` stays the default and release branch; `develop` is the integration branch —
  the developer's choice; rejected: master only.
- **DEC-2**: docs keep deploying from `master` only — the published site follows releases; rejected:
  deploying from `develop`.

## Rabbit-holes

- Branch protection on `develop` is a repository setting; it needs the developer's go-ahead and is
  not part of this change.

## No-gos

- No change to `docs.yml`, `publish.yml` or any repository setting.

---

## What Changes

- "CI runs the gate" covers pull requests and pushes to `develop` too.

## Capabilities

### Modified Capabilities
- `developer-tooling`: CI runs the gate on `master` and `develop`.

## Impact

- `.github/workflows/ci.yml` (already changed in 3c94fbc), `tests/guards/test_repository_wiring.py`,
  `tests/guards/untraced_scenarios.txt`.
