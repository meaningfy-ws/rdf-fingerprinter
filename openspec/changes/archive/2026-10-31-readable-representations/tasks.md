> Derives from: the EPIC `readable-representations` (proposal.md)

## 1. Model, configuration and acceptance

- [x] 1.1 Model work of design D-3 (stats and views), then `make generate-models`; a round-trip test including an old file without `namespaces` (namespace-prefixes › The namespace table is saved with the profile)
- [x] 1.2 `FingerprintConfig`: `prefixes_file` defaults to `None` (the user layer), new `prefix_lookup`, `shapes_namespace` defaults to `None`; `validate()` covers them (design D-2, D-10)
- [x] 1.3 Gherkin (bdd-gherkin): a new `tests/features/namespace_prefixes.feature`; update `fingerprint_report.feature`, `profile_representations.feature` and `statistics_collection.feature` for every added, modified and removed requirement; step stubs in `tests/unit/steps/`
- [x] 1.5 `tests/conftest.py`: autouse `RDF_FINGERPRINTER_PREFIX_LOOKUP=false`; the same in `make test-e2e` (design Risks)
- [x] 1.4 The readability fixture `tests/test_data/profiles/readability-profile.json` (design Verification map)

## 2. Prefix resolution

- [x] 2.1 `fingerprint/domain/prefixes.py`: `namespace_of`, `path_segments`, `generate_prefixes` and `PrefixTable`, test-first from the spec's Examples (design D-4; namespace-prefixes › Every namespace has a prefix, › Generated prefixes, › Short names in every output)
- [x] 2.2 `load_prefixes(path, source) -> list[NamespacePrefix]`, with messages naming their source (design D-2)
- [x] 2.3 The `PrefixListSource` port, `PrefixCcList` (HTTPS, then HTTP on a certificate failure; 10 s per operation) and `FakePrefixList` (design D-1; namespace-prefixes › prefix.cc lookup is best effort)
- [x] 2.4 `service_layer/prefixes.py:resolve_namespaces`, with the precedence and displacement rules (design Algorithm; namespace-prefixes › Prefix source precedence)
- [x] 2.5 `split_curie`, `curie` and `turtle_term` take a `PrefixTable`; `prefixes` leaves the `TemplateRenderer` protocol; the renderer binds its filters per call; `Generator.table` (design D-5)

## 3. One render path and the CLI

- [x] 3.1 Delete `report.py`, the 1.x functions, `profile_document/`, the diagram composition and `GraphText`; delete or port `tests/unit/test_service_layer_report.py`, the 1.x tests in `tests/unit/test_service_layer_handlers.py`, `tests/test_data/golden/profile.html`, and port `tests/test_data/custom_template/` to the document view model; the new `fingerprint_report` flow (design D-6; fingerprint-report › Library outcomes, › The profile is saved with the report, › Report renders from the analytics; statistics-collection › Settings)
- [x] 3.2 CLI options, exactly as listed in fingerprint-report › Formats rendered after collecting, wired as in design.md's Entry points table: load the user file before `collect`, map `ConfigError` to `UsageError`, build `PrefixCcList` unless switched off, `--format doc` a no-op
- [x] 3.3 `Generator.shown`, with the meta defaults, excludes and includes, the WARNING for unknown names, and `Caveats.hidden` (design D-9; profile-representations › Namespace filters)
- [x] 3.4 No SHACL or PlantUML file for a graph with no shown class (profile-representations › No files for empty graphs, › SHACL shapes)

## 4. The page

- [x] 4.1 Set the visual design with the `frontend-design` skill, within D-7, and record it in design.md D-7
- [x] 4.2 `DocumentGenerator` on `fingerprint_report` writing `main.html`; the view-model additions (namespace table with sources, collection section, caveats) (design D-6; profile-representations › Application-profile document)
- [x] 4.3 Rewrite the `fingerprint_report` templates (fingerprint-report › Report content, › One self-contained page)
- [x] 4.4 The inline script, and static tests: no external resources, content outside the script, data attributes (fingerprint-report › Navigation, search and filters)

## 5. SHACL and diagrams

- [x] 5.1 `shape_iri`, de-duplication, shape prefix declarations and `--shapes-namespace` on `fingerprint`; update the help texts (design D-10; profile-representations › Shape IRI policy, › SHACL shapes)
- [x] 5.2 `fingerprint/domain/modules.py` clustering, test-first from the spec's A–G example (design D-8)
- [x] 5.3 `PlantumlGenerator`: the overview and the modules, the reference boxes, the hidden-class rules and one file each (profile-representations › PlantUML class diagram)

## 6. Goldens, end-to-end, docs and release prep

- [x] 6.1 Regenerate every golden file (one per written file) and review the diffs (profile-representations › Golden outputs)
- [x] 6.2 `make check-all`; `make test-e2e` with `RDF_FINGERPRINTER_PREFIX_LOOKUP=false`, updating `tests/e2e/test_report_generation.py` and `tests/e2e/test_representations.py`; rerun the brainframe test into `temp/brainframe-fingerprint/`; the manual checks of the Verification map — done: e2e 85/85 (the live-collection test now compares in any row order); search and switches driven with jsdom; phone width and dark mode left to a browser look (CSS only)
- [x] 6.3 Docs: `docs/modules/ROOT/pages/{index,getting-started,report,statistics,representations,api-reference,how-it-works,architecture}.adoc` and the use cases `ucb1-2.adoc` and `ucb2-1.adoc` (options, outputs, prefix control, library migration); `CHANGELOG.md` with the BREAKING entries; version 3.0.0 in `pyproject.toml`

## Roadmap

- [x] 1.1 · [x] 1.2 · [x] 1.3 · [x] 1.4 · [x] 2.1 · [x] 2.2 · [x] 2.3 · [x] 2.4 · [x] 2.5 · [x] 3.1 · [x] 3.2 · [x] 3.3 · [x] 3.4 · [x] 5.1 · [x] 5.2 · [x] 5.3 · [x] 4.1 · [x] 4.2 · [x] 4.3 · [x] 4.4 · [x] 6.1 · [x] 6.2 · [x] 6.3

## Verification

`make check-all`, `make test-e2e` and `openspec validate readable-representations --strict` all pass, and the manual checks of design.md's Verification map are done.
