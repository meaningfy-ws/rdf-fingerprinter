> Derives from: EPIC namespace-filter (`proposal.md`, DEC-1 to DEC-13); design in `design.md` (P-1 to P-12).

Each task is test-first (`superpowers:test-driven-development`): write the named tests red, then
the code, then **the task's named tests green**. `make test` as a whole stays red while Gherkin
scenarios are unbound (table "Still red until bound" below); every other test must stay green, and
the gate (task 1.10) requires everything green. Each task is one commit
(`Refs: namespace-filter DEC-n, P-n`). Before editing an existing symbol, run GitNexus impact
(`AGENTS.md`, "Implementation loop"); the symbols named below are the ones to check. Before task
1.1, rebase `feature/namespace-filter` onto `master` once PR #45 (3.2.0) has merged. The Gherkin
scenarios are already in `tests/features/` (design "Scenario → feature map"); the tasks write their
step definitions. Scenario titles are cited as `cap › Requirement › Scenario`.

### Still red until bound

| Scenarios (feature file) | Red items | Red from | Green after |
|---|---|---|---|
| profile-representations `› Namespace filters`: Excluded by option (two new steps); Meta properties kept by default; A meta namespace excluded by name; Properties of an excluded namespace (5 rows); An edge to an excluded class (5 rows); A merged class loses its excluded member; Matching a filter value (6 rows); Include wins over exclude; A name that hides nothing; Datatypes are not filtered; Pitfall findings are not filtered; The saved profile keeps excluded terms | 25 | this PLAN | 1.4 |
| profile-representations `› Namespace filters › Excluded namespaces are noted`, rows pattern schema, ShExC, shapes, diagram | 4 | this PLAN | 1.5 |
| profile-representations `› Namespace filters › Excluded namespaces are noted`, row report; `› Every class of a graph excluded`; fingerprint-report `› Navigation, search and filters › Property rows carry their prefix` | 3 | this PLAN | 1.6 |
| **Total** (`pytest tests/bdd` failures) | **32** | | |

## 1. Term-level namespace filters

- [x] 1.1 Model: the additions of design "Layering and modules" to `model/fingerprint_views.yaml` (`FilterOption`, `FilterMatch`, `NamespaceFilter`, `GraphView.excluded_note`, `ExcludedGraphNote`, `Caveats.excluded`, `PrefixDeclaration.excluded`, `DocumentProperty.prefix`, `ProfileDocument.switches`, the two option descriptions) and `model/fingerprint_analytics.yaml` (`ExcludedTerms`, `GraphAnalytics.excluded_terms`, `NamespaceUse`, `ProfileAnalytics.namespace_uses`); `make generate-models`; `fingerprint.domain.namespace_filter` added to the `generated` contract in `.importlinter`
  - Layer: domain (model). Depends on: —.
  - Tests: `make check-models` green; `tests/unit/adapters/test_profile_file.py` round-trip still green and `model/fingerprint_stats.yaml` unchanged (`git diff --exit-code model/fingerprint_stats.yaml`).
- [x] 1.2 `PrefixTable.match` replacing `resolve` (P-4); `fingerprint/domain/namespace_filter.py` with `META_NAMESPACES` (moved from `generator.py`) and `namespace_filter` (design §A)
  - Layer: domain. Depends on: 1.1. GitNexus impact: `PrefixTable.resolve`, `META_NAMESPACES`.
  - Tests: TC-F1, TC-F2; 100% branch coverage of the new code.
- [x] 1.3 `value_type_indicators` extracted from `_partition_indicators` in `fingerprint/domain/analytics.py` (P-2); `namespace_uses` (moved from `DocumentGenerator.namespace_table`) and `exclude_terms` (on the analysed profile, removing and counting per design §B, leaving every field §C marks unchanged) and `note_text` (§D) in `namespace_filter.py`; `filter_runs()` strategy in `tests/unit/domain/strategies.py`
  - Layer: domain. Depends on: 1.2. GitNexus impact: `_partition_indicators`, `value_profile`.
  - Tests: TC-F3, TC-F4, TC-F5 (Hypothesis, including the unchanged-fields property), TC-F6, TC-F7; 100% branch coverage.
- [x] 1.4 Wiring (design §E, P-1, P-3, P-8): `generate_representations` analyses as today, then applies `exclude_terms` to the analytics and warns; `warn_unknown_filters` folded in; `excluded_namespaces()` removed and `Generator.__init__` built on `namespace_filter`; `filter_profile()` and the other profiles the scenarios name in `tests/builders.py`; step definitions for the 1.4 rows of "Still red until bound"
  - Layer: service_layer, tests. Depends on: 1.3. GitNexus impact: `generate_representations`, `warn_unknown_filters`, `excluded_namespaces`, `Generator.__init__`.
  - Tests: TC-R1, TC-R2 (including the inherited property of an excluded parent), TC-G1 (first half); Gherkin: the 25 items of the 1.4 row.
- [x] 1.5 The note in the per-graph outputs (P-6, design §D and §F): `Generator.excluded_note`; `excluded_note` set by `PatternGenerator.views`, `ShaclGenerator.end_graph`, `PlantumlGenerator.end_graph` (overview and modules) and copied by `fingerprint/domain/shex.py`; the `#`/`'` line in the pattern, ShExC, SHACL and PlantUML templates
  - Layer: domain, service_layer, templates. Depends on: 1.4. GitNexus impact: `PatternGenerator.views`, `ShaclGenerator.end_graph`, `PlantumlGenerator.end_graph`, `shex_view`.
  - Tests: TC-G1 (second half); Gherkin `› Excluded namespaces are noted` rows pattern schema, ShExC, shapes, diagram; `› Golden file per output` still green for every format except the report.
- [x] 1.6 The report (P-9, design §B "Namespace uses" and §H): `namespace_uses` read by `namespace_table`, `DocumentProperty.prefix`, row `data-ns`, the switch list from the non-empty class and property prefixes (no switch for `""`), the script change, `PrefixDeclaration.excluded` in the namespace table, `Caveats.excluded`, the `empty` rule, and the sentence `Every class of this graph is in a hidden or excluded namespace (see caveats).` in place of `Every class of this graph is in a hidden namespace (see caveats).`; then checks M-1 to M-5 of `inputs/manual-checks.md` run by hand with its commands (they cover the four `@manual` scenarios), each result recorded there with date and browser
  - Layer: service_layer, templates. Depends on: 1.5. GitNexus impact: `DocumentGenerator.visit_property`, `end_graph`, `namespace_table`, `end_profile`.
  - Tests: TC-D1; Gherkin `› Excluded namespaces are noted` row report, `› Every class of a graph excluded`, fingerprint-report `› Property rows carry their prefix`.
- [x] 1.7 Help texts of `--exclude-namespace` and `--include-namespace` in `fingerprint/entrypoints/cli/main.py` and `generate.py` (design §G)
  - Layer: entrypoints. Depends on: 1.4.
  - Tests: `tests/unit/entrypoints/` green.
- [x] 1.8 `make refresh-golden`; review the diff: only `tests/test_data/golden/main.html` and `golden/scanned/main.html` change, and only by row `data-ns` attributes and switches (P-10); any other diff is a defect to fix before going on
  - Layer: tests (golden). Depends on: 1.6.
  - Tests: IT-1.
- [ ] 1.9 Docs: `docs/modules/ROOT/pages/representations.adoc` "Namespace filters" rewritten (two tiers; the matching rule with the §A examples and shell quoting of `'rel*'`; that stems and globs are case-sensitive while no two prefixes differ only in case, so a glob never misses a prefix by case; that a full namespace IRI is now a stem; what "every term" covers; the note; the warnings; that datatypes, pitfalls and collection failures are not filtered; that only the four value-type fields of §C change; that a `Generator` built directly hides classes only; that a property inherited from an excluded parent appears in no diagram box (design "Risks / Trade-offs")); the options table row; `api-reference.adoc` (the `exclude_namespaces=["skos"]` example now leaves out every `skos:` term, and the scope sentence on `Generator`); `report.adoc` (switches for property rows, the marked table); `llm-schema.adoc` (a pointer and the brainframe example); `how-it-works.adoc` line on switches if it names classes only
  - Layer: docs. Depends on: 1.6.
  - Tests: `make build-docs` green; links resolve.
- [ ] 1.10 Gate (design "Exit criteria"): `make check-all`; `make oxigraph-load-test-data` + `make test-e2e`; `make check-mutation` (≥ 0.950; survivors get a test in the owning tier, or dead code is deleted and listed here; `mutation_score.txt` raised if higher); `openspec validate --all --strict`; IT-4, the brainframe acceptance (commands in `inputs/manual-checks.md`, "Acceptance measurement"), recorded in `inputs/brainframe-evidence.md` ("After the change": pattern, ShExC and report sizes with and without `--exclude-namespace relationid`, the note line, and `grep -c relationid:` = 0 in the filtered pattern file)
  - Layer: all. Depends on: 1.1–1.9.
  - Tests: IT-1 to IT-4; every row of "Still red until bound" green; the manual checks of 1.6 recorded.
- [ ] 1.11 Release 3.3.0 (P-11; DEC-3, DEC-5):
  - `pyproject.toml` version `3.2.0` → `3.3.0`;
  - `CHANGELOG.md`: turn `## [Unreleased]` into `## [3.3.0] - <date>` (keep an empty `## [Unreleased]` above it), with **Changed** (1. `--exclude-namespace` now leaves out every term of the matching namespaces in every output, not only their classes; the meta vocabularies are still hidden at class level only. 2. A full namespace IRI given to `--exclude-namespace` or `--include-namespace` is now a stem: it also matches the namespaces under it, so `http://example.org/` now also catches `http://example.org/rel/`), **Added** (prefix globs and IRI stems; the `excluded namespaces` note; the hides-nothing warning; report switches for property rows and the marked namespace table), and the note that `profile.json` is unchanged;
  - PR to `master` with green CI; merge; a bare tag `3.3.0`; `gh release create 3.3.0`; report the release URL (`AGENTS.md` "Release authority").
  - Layer: release. Depends on: 1.10.
  - Tests: `publish.yml` succeeds; `pip install rdf-fingerprinter==3.3.0` in a clean venv runs `fingerprint-gen-pattern --help` and its help names "prefix glob".

## Roadmap

- [x] 1.1 · [x] 1.2 · [x] 1.3 · [x] 1.4 · [x] 1.7 · [x] 1.5 · [x] 1.6 · [x] 1.8 · [ ] 1.9 · [ ] 1.10 · [ ] 1.11

## Verification

The change is complete when `make check-all`, `make test-e2e` and `make check-mutation` pass;
`openspec validate --all --strict` is clean; every spec scenario of the two deltas has its
same-titled Gherkin scenario passing (`tests/guards/test_traceability.py`), the `@manual` ones
recorded in `inputs/manual-checks.md`; the brainframe acceptance is recorded; and the PLAN passed
the independent clarity gate (≥ 9/10) before task 1.1.
