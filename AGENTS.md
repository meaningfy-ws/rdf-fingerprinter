<!-- meaningfy-template-version: 3.0.0 -->
<!-- CANONICAL, CLI-agnostic agent instruction file (opencode reads AGENTS.md natively; Claude Code
     reads it through the @AGENTS.md import in CLAUDE.md). Edit THIS file. CLAUDE.md is a thin
     pointer that adds only Claude-specific guidance — never a symlink, never a copy. This file
     ROUTES to skills and to the global standard; it never restates that standard (DEC-12 —
     global vs repo split). -->

# Project: RDF Fingerprinter

Meaningfy project. Build clean, layered, well-tested code; minimise WTFs-per-minute. The
company-wide standard (Clean Code, Clean Architecture, testing, tooling) lives in your **global
agent instructions** (`~/.claude/CLAUDE.md` on Claude Code, `~/.config/opencode/AGENTS.md` on
opencode) — this file does **not** repeat it; it ROUTES to it and to the
installed skills, and records only what is specific to **this** repo.

## Skill routing (use the skill for the task)

- Structuring Python code (domain/adapters/services/entrypoints, SOLID, CI) → **cosmic-python**
- Keeping code minimal — YAGNI, avoid over-engineering, simplest working approach → **ponytail**
  (`/ponytail` to set intensity; `/ponytail-review` for a delete-list on the diff)
- System / solution design (C4, ADRs, contracts) → **architecture**
- Modelling the domain / generating code from a model (`make generate-models`) → **conceptual-modelling**
  (product repos only)
- Any new feature or non-trivial change → start by exploring options (**superpowers:brainstorming**)
- Any feature or bugfix implementation → **superpowers:test-driven-development** (tests first)
- Debugging → **superpowers:systematic-debugging**
- Shaping an EPIC + deriving its PLAN → **epic-planning** + the opsx workflow commands
  (`/opsx:*` on Claude Code, `opsx-*` on opencode)
- Spec readiness (the PLAN clarity gate, ≥9/10) → **clarity-gate**
- BDD features → **bdd-gherkin**
- Commits / branches / PRs → **meaningfy-git-workflow** (mechanics via **commit-commands**)
- Pre-PR review → **meaningfy-code-review** (+ external **code-review**)
- Deploy / release / versioned image (deployable repos) → **ci-cd-delivery**
- Docs → **technical-writing**

If a request conflicts with these, flag it before proceeding.

## The spine — where work is shaped and remembered

This repo carries the Meaningfy **spine** under `openspec/` (OpenSpec, schema `meaningfy`):

- **EPIC ≡ `openspec/changes/<id>/proposal.md`** (the Shape-Up work shape: appetite, why, solution,
  key decisions, rabbit-holes, no-gos).
- **PLAN ≡ `openspec/changes/<id>/design.md` + `tasks.md`** (the clarity gate scores the pair ≥9/10).
- **Normative requirements ≡ `openspec/changes/<id>/specs/<cap>/spec.md`** (RFC-2119 SHALL +
  Given/When/Then; no EARS). They merge into **`openspec/specs/`** — the durable truth — on archive.
- **Seed inputs** (briefs, notes) live in `openspec/changes/<id>/inputs/` — preserved, never groomed.
- **Orientation** is `openspec/config.yaml`'s `context:` field (the native index) — **not** a
  hand-curated MEMORY.md. The truth is `openspec/specs/`.

Drive it with the opsx workflow commands (`/opsx:*` on Claude Code, `opsx-*` on opencode): `propose`,
`explore`, `apply`, `sync`, `archive` — core profile.

**External method skills land in the spine (binding).** `superpowers` provides *disciplines*, not a
parallel spec system — its artifacts MUST land in `openspec/changes/<id>/`, never a `docs/superpowers/`
tree. A **brainstorming** design feeds the **EPIC** (`proposal.md`); **writing-plans is SUPERSEDED** by
the **PLAN** (`design.md`+`tasks.md`); execution uses superpowers TDD, tracked via the opsx `apply`
command.

**Golden thread (cite your parent).** Each artifact cites the one above it: the PLAN (`tasks.md`)
cites its EPIC id on the first line; specs cite their capability; commits reference the change. This
is how any commit traces up to the requirement that justifies it.

## Implementation loop (orchestration)

Before editing a symbol, run gitnexus impact (status → analyze → impact/context); stop and
report HIGH/CRITICAL risk. Loop: generate (tests first) → verify (run tests) → integrate
(present, get consent). On a design-level failure, fix the spec, not the code (Rule of
Divergence). Commit only on explicit developer consent.

## Working conventions

- The innermost layer is **`domain`** (the book's `models/`). Direction:
  `entrypoints → services → domain`, `adapters → domain`. `domain` imports nothing upward.
  Enforced by `.importlinter`; checked via `make check-architecture`.
- Run Python tooling through Poetry (`poetry run pytest`, `poetry run ruff`, …). Never invoke
  bare `python`/`pytest` — prefer the `make` targets below.
- **Subagents** — before spawning one, follow *Subagent dispatch* in the `guardrails` skill: spawn
  only when it pays, brief it fresh, take the base report back, and have finished work checked by a
  second subagent.
- Default branch is **`master`** (the PR target). Branch off it; never commit to it
  directly.

## `.claude/` is a regenerable index — the truth is `openspec/specs/`

`.claude/memory/MEMORY.md` is a cheap orientation note (≤200 lines; stable patterns only). It is an
**index, not authority** — if it disagrees with `openspec/specs/`, `specs/` wins. The legacy
`.claude/memory/epics/EPIC.md`+`PLAN.md`+`task.md` model is **superseded** by the spine's native
artifacts above; do not reintroduce parallel epic files under `.claude/`.

## Project specifics

- **Archetype:** library (PyPI `rdf-fingerprinter`, console script `fingerprint`).
- **Top-level package(s):** `fingerprint/` (code) and `fingerprint_report_templates/` (packaged
  eds4jinja2 report templates + SPARQL queries). No `/src`.
- **Modules:** `fingerprint/service_layer/handlers.py` (report generation),
  `fingerprint/entrypoints/cli/main.py` (click CLI).
- **External systems:** any SPARQL endpoint; tests use a local Oxigraph
  (`make oxigraph-load-test-data`, config in `docker/`) for the local-only `tests/e2e`; the
  endpoint comes from `RDF_FINGERPRINTER_TEST_ENDPOINT`. `tests/unit` need no store.
- **Deployable?** no — released as a Python package.
- **Make targets:** `make install` (Poetry), `make check-all` (the gate), `make test`, `make build`,
  `make test-e2e`, `make oxigraph-load-test-data`, `make build-docs`. Releases publish from a
  GitHub Release via Trusted Publishing (`publish.yml`); docs deploy to GitHub Pages (`docs.yml`).
- **Release authority (developer, 2026-10-31):** an agent MAY merge a PR to `master` and publish a
  release without asking again, when all of these hold: the PR's CI checks are green; `make
  check-all` and `make test-e2e` (against `make oxigraph-load-test-data`) pass locally; the version
  in `pyproject.toml` is bumped per SemVer and `CHANGELOG.md` has its entry. A release is a
  `vX.Y.Z` tag plus a published GitHub Release (`gh release create`); `publish.yml` uploads to PyPI
  with Trusted Publishing — no token exists or is needed. Report the release URL afterwards.
  Changing repository or environment settings still needs the developer's go-ahead.
- **Commits and PRs carry no AI attribution** (no `Co-Authored-By`, no "Generated with" line).
- **GitNexus repo name:** rdf-fingerprinter
