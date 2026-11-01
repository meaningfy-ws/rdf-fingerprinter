# Baseline — lean-test-suite (task 1.1, secondary)

Measured 2026-11-01 on `master` at `e28cb1c` (after PR #42), Python 3.12.3, local Oxigraph.

## Totals

| Measure | Value |
|---|---|
| Unit tier (`make test`) | 583 passed, 2 skipped, 31.9 s wall (with coverage) |
| e2e tier (`make test-e2e`) | 85 passed, 9.5 s |
| Collected (unit + e2e, parametrised rows counted) | 670 |
| Line coverage, `fingerprint/` | 98.53% |
| Branch coverage, `fingerprint/` (unit) | 98% — 430 branches, 19 partial |

## Branch coverage per layer (unit tier; generated `profile.py`/`views.py` excluded)

| Layer | Statements | Missed | Branches | Partial | Cover |
|---|---|---|---|---|---|
| `domain/` | 368 | 2 | 110 | 4 | 99% |
| `adapters/` | 316 | 5 | 70 | 7 | 97% |
| `service_layer/` | 957 | 22 | 242 | 8 | 97% |
| `entrypoints/` | 113 | 0 | 8 | 0 | 100% |

## Spec ↔ feature scenario titles

| Capability | Spec scenarios | Feature scenarios | Identical titles |
|---|---|---|---|
| fingerprint-report | 23 | 22 | 12 |
| namespace-prefixes | 14 | 7 | 3 |
| profile-analytics | 15 | 16 | 8 |
| profile-representations | 21 | 23 | 11 |
| statistics-collection | 29 | 28 | 1 |
| developer-tooling | 18 + this change's 9 | — | (allow-list) |

## Tests per file (collected, parametrised rows counted)

| File | Tests |
|---|---|
| `tests/e2e/test_queries.py` | 71 |
| `tests/unit/test_no_composed_dicts.py` | 57 |
| `tests/unit/test_domain_analytics.py` | 41 |
| `tests/unit/steps/test_statistics_collection_steps.py` | 41 |
| `tests/unit/test_adapters_sparql.py` | 39 |
| `tests/unit/steps/test_profile_representations_steps.py` | 36 |
| `tests/unit/test_domain_prefixes.py` | 32 |
| `tests/unit/steps/test_fingerprint_report_steps.py` | 30 |
| `tests/unit/test_service_layer_shacl.py` | 28 |
| `tests/unit/test_domain_iri.py` | 28 |
| `tests/unit/steps/test_profile_analytics_steps.py` | 26 |
| `tests/unit/test_config.py` | 25 |
| `tests/unit/test_service_layer_collection.py` | 21 |
| `tests/unit/test_service_layer_settings.py` | 20 |
| `tests/unit/test_adapters_queries.py` | 16 |
| `tests/unit/steps/test_namespace_prefixes_steps.py` | 15 |
| `tests/unit/test_service_layer_plantuml.py` | 14 |
| `tests/unit/test_entrypoints_generate.py` | 14 |
| `tests/unit/test_adapters_prefixes.py` | 14 |
| `tests/unit/test_representations_golden.py` | 12 |
| `tests/unit/test_service_layer_prefixes.py` | 11 |
| `tests/unit/test_service_layer_representations.py` | 10 |
| `tests/unit/test_service_layer_generator.py` | 9 |
| `tests/unit/test_adapters_template_renderer.py` | 9 |
| `tests/unit/test_adapters_profile_file.py` | 8 |
| `tests/unit/test_entrypoints_main.py` | 6 |
| `tests/unit/test_service_layer_document.py` | 5 |
| `tests/unit/test_domain_shapes.py` | 5 |
| `tests/unit/test_domain_views.py` | 4 |
| `tests/unit/test_domain_modules.py` | 4 |
| `tests/e2e/test_representations.py` | 4 |
| `tests/e2e/test_entrypoints_cli.py` | 4 |
| `tests/unit/test_service_layer_handlers.py` | 3 |
| `tests/e2e/test_report_generation.py` | 3 |
| `tests/e2e/test_collection.py` | 3 |
| `tests/unit/test_package.py` | 2 |

## Mutation score

Recorded by task 1.2.
