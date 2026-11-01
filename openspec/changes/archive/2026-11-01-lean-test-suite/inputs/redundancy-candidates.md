# Redundancy candidates — lean-test-suite group 7 (secondary)

Collected 2026-11-01 from the implementers' reports for groups 3–6. Each is a *candidate*: design P-6
decides (deletion stays only if branch coverage and, for `domain/` and `service_layer/`, the killed
mutant set are unchanged).

## Unit tests now duplicated by Gherkin scenarios (P-2: behaviour belongs to `tests/bdd/`)

namespace-prefixes (task 3.3 report):
- `tests/unit/service_layer/test_prefixes.py`: `test_the_first_source_wins`,
  `test_reserved_and_taken_names_fall_through_to_the_next_source`, `test_a_user_file_over_a_saved_table`,
  `test_a_user_prefix_displaces_a_saved_one`, `test_prefix_cc_offline_warns_once_and_generates`,
  `test_resolving_is_idempotent_and_deterministic` (partly)
- `tests/unit/domain/test_prefixes.py`: `test_namespace_of` (first two rows)
- `tests/unit/adapters/test_prefixes.py`: `test_an_expired_certificate_falls_back_to_http`
- `tests/unit/entrypoints/test_main.py`: `test_the_lookup_switched_off`

fingerprint-report (design worked example):
- `tests/unit/service_layer/test_handlers.py::test_a_missing_output_folder_is_refused_before_any_query`
  — keep only if "no query is sent" is not asserted by the Gherkin row; rename to say so
- `tests/e2e/test_entrypoints_cli.py::test_missing_output_folder_is_a_usage_error` — never reaches the
  store (P-2: not an e2e concern)

configuration (task 4.5 report):
- `tests/unit/service_layer/test_config.py::test_a_variable_changes_a_default` and
  `tests/unit/entrypoints/test_config.py::test_a_badly_typed_variable_exits_2_before_any_query` carry
  "Scenario:" docstrings and are allow-listed for developer-tooling; check overlap with the
  statistics-collection scenarios "Environment overrides the library configuration" and "Unknown
  configuration key" — if a Gherkin scenario proves the same, keep one and repoint the allow-list

profile-analytics (task 3.4 report): outline rows moved out of Gherkin rely on the parametrised tests in
`tests/unit/domain/test_analytics.py` — those stay (they are now the only owner).

## e2e tests that never reach the store (task 7.4)

Review every `tests/e2e/` test: a test whose path never sends a query (usage errors, missing folders,
option validation) belongs to the unit or bdd tier, or is already covered there.

## Dead-code candidates (task 7.5)

- `fingerprint/domain/analytics.py` `_weighted_value_at`'s `raise IndexError` looks unreachable from
  `cardinality_statistics` (task 6.3 report); covered today only by a direct test.
