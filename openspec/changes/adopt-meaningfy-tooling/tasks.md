> Derives from: EPIC adopt-meaningfy-tooling (proposal.md)

## 1. Packaging

- [ ] 1.1 Add Poetry `pyproject.toml` (DEC-2, DEC-7) and `poetry.lock`; remove setup.py, setup.cfg, requirements*.txt, MANIFEST.in
- [ ] 1.2 Verify the wheel ships `fingerprint_report_templates` and the `fingerprint` script works (Requirement: Tokenless release)

## 2. Quality gates

- [ ] 2.1 Add ruff.toml, mypy.ini, pytest.ini, .coveragerc, .importlinter (DEC-3, DEC-4)
- [ ] 2.2 Makefile: Poetry `install`, `lint`, `format`, `typecheck`, `check-architecture`, `validate-specs`, `check-all`, `build` (Requirement: Single quality gate)
- [ ] 2.3 Fix lint/type debt in its own commit until `make check-all` is green

## 3. CI and release

- [ ] 3.1 Replace test.yml with ci.yaml running Fuseki + `make check-all` (Requirement: CI runs the gate)
- [ ] 3.2 Replace package.yml with release.yaml: release-please + Trusted Publishing (DEC-5)
- [ ] 3.3 Add CHANGELOG.md (0.4.0 entry) and SECURITY.md

## Roadmap

- [ ] 1.1 · [ ] 1.2 · [ ] 2.1 · [ ] 2.2 · [ ] 2.3 · [ ] 3.1 · [ ] 3.2 · [ ] 3.3

## Verification

`make check-all` green locally and in CI; `openspec validate --strict`; built wheel inspected.
