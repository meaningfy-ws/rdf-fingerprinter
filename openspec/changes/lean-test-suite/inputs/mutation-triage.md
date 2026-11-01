## domain

Survivors of `mutation-survivors-baseline.txt` re-checked on the current tree: 151 (149 survived + 2 timeouts).
After the new tests: 51 left (50 survived + 1 timeout, caught by non-termination). Classes: gap = real, killed by a new test; equivalent, cosmetic, dead = no test.

| module | before | after | gap | equivalent | cosmetic | dead |
|---|---|---|---|---|---|---|
| analytics | 79 | 28 | 51 | 27 | 0 | 1 |
| prefixes | 41 | 12 | 30 | 11 | 0 | 0 |
| modules | 16 | 9 | 7 | 9 | 0 | 0 |
| shapes | 9 | 0 | 9 | 0 | 0 | 0 |
| iri | 5 | 1 | 4 | 1 | 0 | 0 |
| exceptions | 1 | 1 | 0 | 0 | 1 | 0 |

`after` counts `generate_prefixes_24` (a gap whose timeout mutmut still lists). Equivalent includes 4 mutants that differ only at `acceptance_threshold = 0` and 11 `exclude_none` mutants.

### Per mutant (`fingerprint.domain.` omitted; the number is the `__mutmut_N` suffix)

- iri.x_turtle_number__mutmut_2 — gap — False renders `false`; a value whose 5th-place rounding differs — tests/unit/domain/test_iri.py::test_turtle_number
- iri.x_turtle_number__mutmut_5 — gap — False renders `false`; a value whose 5th-place rounding differs — tests/unit/domain/test_iri.py::test_turtle_number
- iri.x_turtle_number__mutmut_6 — gap — False renders `false`; a value whose 5th-place rounding differs — tests/unit/domain/test_iri.py::test_turtle_number
- iri.x_turtle_number__mutmut_15 — gap — False renders `false`; a value whose 5th-place rounding differs — tests/unit/domain/test_iri.py::test_turtle_number
- iri.x_turtle_number__mutmut_16 — equivalent — `rstrip('XX0XX')` strips the char set {X,0}; X never occurs
- prefixes.x_namespace_of__mutmut_3 — equivalent — only differs for IRIs with two `#` (invalid) or a separator at index 0 (relative)
- prefixes.x_namespace_of__mutmut_6 — equivalent — only differs for IRIs with two `#` (invalid) or a separator at index 0 (relative)
- prefixes.x_namespace_of__mutmut_7 — equivalent — only differs for IRIs with two `#` (invalid) or a separator at index 0 (relative)
- prefixes.x_namespace_of__mutmut_10 — gap — `#` followed by `/` boundaries — tests/unit/domain/test_prefixes.py::test_namespace_of
- prefixes.x_namespace_of__mutmut_11 — gap — `#` followed by `/` boundaries — tests/unit/domain/test_prefixes.py::test_namespace_of
- prefixes.x_namespace_of__mutmut_18 — equivalent — only differs for IRIs with two `#` (invalid) or a separator at index 0 (relative)
- prefixes.x_namespace_of__mutmut_19 — equivalent — only differs for IRIs with two `#` (invalid) or a separator at index 0 (relative)
- prefixes.x__parts__mutmut_4 — equivalent — the `urn` scheme label is only compared with itself
- prefixes.x__parts__mutmut_5 — equivalent — the `urn` scheme label is only compared with itself
- prefixes.x__parts__mutmut_22 — equivalent — host-less label list differs only against a host-less known entry of the same scheme: not a real namespace
- prefixes.x__parts__mutmut_23 — equivalent — scheme case only compared with itself
- prefixes.x_is_reserved__mutmut_2 — gap — the shape prefixes are reserved, others are not — tests/unit/domain/test_prefixes.py::test_is_reserved
- prefixes.x_is_reserved__mutmut_3 — gap — the shape prefixes are reserved, others are not — tests/unit/domain/test_prefixes.py::test_is_reserved
- prefixes.x_is_reserved__mutmut_4 — gap — the shape prefixes are reserved, others are not — tests/unit/domain/test_prefixes.py::test_is_reserved
- prefixes.x__clean__mutmut_9 — gap — stripping, collapsing, digit-leading names — tests/unit/domain/test_prefixes.py::test_the_own_name_of_a_namespace
- prefixes.x__clean__mutmut_16 — gap — stripping, collapsing, digit-leading names — tests/unit/domain/test_prefixes.py::test_the_own_name_of_a_namespace
- prefixes.x__clean__mutmut_18 — equivalent — `strip('XX-XX')` strips {X,-}; the cleaned text is lowercase
- prefixes.x__clean__mutmut_19 — gap — stripping, collapsing, digit-leading names — tests/unit/domain/test_prefixes.py::test_the_own_name_of_a_namespace
- prefixes.x__parent_name__mutmut_7 — gap — other-scheme/other-entry skipping, deepest parent, equal-depth tie, same host+path is no parent — tests/unit/domain/test_prefixes.py::test_the_parent_of_a_namespace
- prefixes.x__parent_name__mutmut_11 — gap — other-scheme/other-entry skipping, deepest parent, equal-depth tie, same host+path is no parent — tests/unit/domain/test_prefixes.py::test_the_parent_of_a_namespace
- prefixes.x__parent_name__mutmut_15 — gap — other-scheme/other-entry skipping, deepest parent, equal-depth tie, same host+path is no parent — tests/unit/domain/test_prefixes.py::test_the_parent_of_a_namespace
- prefixes.x__parent_name__mutmut_17 — gap — other-scheme/other-entry skipping, deepest parent, equal-depth tie, same host+path is no parent — tests/unit/domain/test_prefixes.py::test_the_parent_of_a_namespace
- prefixes.x__parent_name__mutmut_22 — gap — other-scheme/other-entry skipping, deepest parent, equal-depth tie, same host+path is no parent — tests/unit/domain/test_prefixes.py::test_the_parent_of_a_namespace
- prefixes.x__parent_name__mutmut_23 — gap — other-scheme/other-entry skipping, deepest parent, equal-depth tie, same host+path is no parent — tests/unit/domain/test_prefixes.py::test_the_parent_of_a_namespace
- prefixes.x__parent_name__mutmut_24 — gap — other-scheme/other-entry skipping, deepest parent, equal-depth tie, same host+path is no parent — tests/unit/domain/test_prefixes.py::test_the_parent_of_a_namespace
- prefixes.x__parent_name__mutmut_27 — equivalent — `>=` vs `>` differs only on identical (rank, prefix): same extra, same name
- prefixes.x__parent_name__mutmut_29 — gap — other-scheme/other-entry skipping, deepest parent, equal-depth tie, same host+path is no parent — tests/unit/domain/test_prefixes.py::test_the_parent_of_a_namespace
- prefixes.x__own_name__mutmut_9 — gap — www and short second-level labels — tests/unit/domain/test_prefixes.py::test_the_own_name_of_a_namespace
- prefixes.x__own_name__mutmut_11 — gap — www and short second-level labels — tests/unit/domain/test_prefixes.py::test_the_own_name_of_a_namespace
- prefixes.x__own_name__mutmut_12 — gap — www and short second-level labels — tests/unit/domain/test_prefixes.py::test_the_own_name_of_a_namespace
- prefixes.x__own_name__mutmut_23 — gap — www and short second-level labels — tests/unit/domain/test_prefixes.py::test_the_own_name_of_a_namespace
- prefixes.x_generate_prefixes__mutmut_8 — gap — depth order, not lexical — tests/unit/domain/test_prefixes.py::test_a_host_parent_is_named_before_its_child...
- prefixes.x_generate_prefixes__mutmut_10 — gap — depth order, not lexical — tests/unit/domain/test_prefixes.py::test_a_host_parent_is_named_before_its_child...
- prefixes.x_generate_prefixes__mutmut_24 — gap — timeout: the clash loop never ends once `not in taken` is tested; caught by non-termination (mutmut reports a timeout), also covered by test_parents_are_named_before_children_and_clashes_count_up
- prefixes.xǁPrefixTableǁ__init____mutmut_9 — gap — longest entry first — tests/unit/domain/test_prefixes.py::test_an_iri_deeper_than_any_namespace... + test_properties.py (nested tables)
- prefixes.xǁPrefixTableǁ__init____mutmut_12 — gap — longest entry first — tests/unit/domain/test_prefixes.py::test_an_iri_deeper_than_any_namespace... + test_properties.py (nested tables)
- prefixes.xǁPrefixTableǁ__init____mutmut_14 — gap — longest entry first — tests/unit/domain/test_prefixes.py::test_an_iri_deeper_than_any_namespace... + test_properties.py (nested tables)
- prefixes.xǁPrefixTableǁentry_for__mutmut_2 — gap — exact-namespace precedence and longest-entry fallback — tests/unit/domain/test_prefixes.py::test_the_namespace_of_the_iri_wins... / test_an_iri_deeper_than_any_namespace...
- prefixes.xǁPrefixTableǁentry_for__mutmut_3 — gap — exact-namespace precedence and longest-entry fallback — tests/unit/domain/test_prefixes.py::test_the_namespace_of_the_iri_wins... / test_an_iri_deeper_than_any_namespace...
- prefixes.xǁPrefixTableǁentry_for__mutmut_6 — gap — exact-namespace precedence and longest-entry fallback — tests/unit/domain/test_prefixes.py::test_the_namespace_of_the_iri_wins... / test_an_iri_deeper_than_any_namespace...
- prefixes.xǁPrefixTableǁresolve__mutmut_3 — gap — resolve by namespace IRI — tests/unit/domain/test_prefixes.py::test_table_lookups
- modules.x_cluster__mutmut_4 — gap — empty input, size boundary, seed choice, tie by name — tests/unit/domain/test_modules.py::test_no_classes_make_no_module / test_a_namespace_of_exactly_the_size... / test_the_seed_is_the_most_linked...
- modules.x_cluster__mutmut_6 — gap — empty input, size boundary, seed choice, tie by name — tests/unit/domain/test_modules.py::test_no_classes_make_no_module / test_a_namespace_of_exactly_the_size... / test_the_seed_is_the_most_linked...
- modules.x_cluster__mutmut_12 — equivalent — links with an unknown endpoint or a self-link are never looked up
- modules.x_cluster__mutmut_13 — equivalent — links with an unknown endpoint or a self-link are never looked up
- modules.x_cluster__mutmut_38 — gap — empty input, size boundary, seed choice, tie by name — tests/unit/domain/test_modules.py::test_no_classes_make_no_module / test_a_namespace_of_exactly_the_size... / test_the_seed_is_the_most_linked...
- modules.x_cluster__mutmut_39 — gap — empty input, size boundary, seed choice, tie by name — tests/unit/domain/test_modules.py::test_no_classes_make_no_module / test_a_namespace_of_exactly_the_size... / test_the_seed_is_the_most_linked...
- modules.x_cluster__mutmut_42 — gap — empty input, size boundary, seed choice, tie by name — tests/unit/domain/test_modules.py::test_no_classes_make_no_module / test_a_namespace_of_exactly_the_size... / test_the_seed_is_the_most_linked...
- modules.x_cluster__mutmut_43 — equivalent — `_by_name` redundant: candidates are iterated in name order and max keeps the first of ties
- modules.x_cluster__mutmut_55 — gap — empty input, size boundary, seed choice, tie by name — tests/unit/domain/test_modules.py::test_no_classes_make_no_module / test_a_namespace_of_exactly_the_size... / test_the_seed_is_the_most_linked...
- modules.x_cluster__mutmut_58 — gap — empty input, size boundary, seed choice, tie by name — tests/unit/domain/test_modules.py::test_no_classes_make_no_module / test_a_namespace_of_exactly_the_size... / test_the_seed_is_the_most_linked...
- modules.x_cluster__mutmut_62 — equivalent — `_by_name` redundant: candidates are iterated in name order and max keeps the first of ties
- modules.x_cluster__mutmut_65 — equivalent — `_by_name` redundant: candidates are iterated in name order and max keeps the first of ties
- modules.xǁ_by_nameǁ__init____mutmut_1 — equivalent — `_by_name` redundant (see x_cluster 43/62/65)
- modules.xǁ_by_nameǁ__lt____mutmut_1 — equivalent — `_by_name` redundant (see x_cluster 43/62/65)
- modules.xǁ_by_nameǁ__eq____mutmut_1 — equivalent — `_by_name` redundant (see x_cluster 43/62/65)
- modules.xǁ_by_nameǁ__eq____mutmut_2 — equivalent — `_by_name` redundant (see x_cluster 43/62/65)
- analytics.x__weighted_value_at__mutmut_6 — dead — `raise IndexError` unreachable: counts total >= observed > any position
- analytics.x_cardinality_statistics__mutmut_48 — equivalent — a zero-weight (0, 0) bin changes neither median, mode nor stddev
- analytics.x_cardinality_statistics__mutmut_51 — equivalent — a zero-weight (0, 0) bin changes neither median, mode nor stddev
- analytics.x_cardinality_statistics__mutmut_73 — equivalent — a float position compares like its floor against integer cumulative counts
- analytics.x_cardinality_statistics__mutmut_75 — gap — median positions — tests/unit/domain/test_analytics.py::test_median_is_the_middle_value_or_the_mean_of_the_two_middle_ones
- analytics.x_cardinality_statistics__mutmut_76 — gap — median positions — tests/unit/domain/test_analytics.py::test_median_is_the_middle_value_or_the_mean_of_the_two_middle_ones
- analytics.x_cardinality_statistics__mutmut_81 — equivalent — a float position compares like its floor against integer cumulative counts
- analytics.x_cardinality_statistics__mutmut_82 — gap — median positions — tests/unit/domain/test_analytics.py::test_median_is_the_middle_value_or_the_mean_of_the_two_middle_ones
- analytics.x_cardinality_statistics__mutmut_93 — equivalent — counts are sorted by n, so the first of tied maxima is already the smallest n
- analytics.x_cardinality_label__mutmut_10 — gap — share equal to the threshold — tests/unit/domain/test_analytics.py::test_a_share_equal_to_the_threshold_is_accepted
- analytics.x_cardinality_label__mutmut_14 — equivalent — k = 1 is handled by the exactly_one branch before exactly_k is read
- analytics.x_cardinality_label__mutmut_25 — gap — share equal to the threshold — tests/unit/domain/test_analytics.py::test_a_share_equal_to_the_threshold_is_accepted
- analytics.x_cardinality_label__mutmut_29 — equivalent — (degenerate) default of bins.get(1) only read at acceptance_threshold 0, where the label is meaningless
- analytics.x_cardinality_label__mutmut_31 — equivalent — (degenerate) default of bins.get(1) only read at acceptance_threshold 0, where the label is meaningless
- analytics.x_cardinality_label__mutmut_33 — equivalent — (degenerate) default of bins.get(1) only read at acceptance_threshold 0, where the label is meaningless
- analytics.x_cardinality_label__mutmut_45 — gap — share equal to the threshold — tests/unit/domain/test_analytics.py::test_a_share_equal_to_the_threshold_is_accepted
- analytics.x__ordered_by_triples__mutmut_2 — gap — order by triples, not by name — tests/unit/domain/test_analytics.py::test_partitions_of_one_type_language_or_kind_add_up_and_rank_by_triples
- analytics.x__ordered_by_triples__mutmut_4 — gap — order by triples, not by name — tests/unit/domain/test_analytics.py::test_partitions_of_one_type_language_or_kind_add_up_and_rank_by_triples
- analytics.x__partition_indicators__mutmut_6 — gap — partitions add up; missing triple counts are 0 — tests/unit/domain/test_analytics.py::test_partitions_of_one_type... / test_a_partition_without_a_triple_count...
- analytics.x__partition_indicators__mutmut_20 — gap — partitions add up; missing triple counts are 0 — tests/unit/domain/test_analytics.py::test_partitions_of_one_type... / test_a_partition_without_a_triple_count...
- analytics.x__partition_indicators__mutmut_23 — gap — partitions add up; missing triple counts are 0 — tests/unit/domain/test_analytics.py::test_partitions_of_one_type... / test_a_partition_without_a_triple_count...
- analytics.x__partition_indicators__mutmut_24 — gap — partitions add up; missing triple counts are 0 — tests/unit/domain/test_analytics.py::test_partitions_of_one_type... / test_a_partition_without_a_triple_count...
- analytics.x__partition_indicators__mutmut_25 — gap — partitions add up; missing triple counts are 0 — tests/unit/domain/test_analytics.py::test_partitions_of_one_type... / test_a_partition_without_a_triple_count...
- analytics.x__partition_indicators__mutmut_27 — gap — partitions add up; missing triple counts are 0 — tests/unit/domain/test_analytics.py::test_partitions_of_one_type... / test_a_partition_without_a_triple_count...
- analytics.x__partition_indicators__mutmut_28 — gap — partitions add up; missing triple counts are 0 — tests/unit/domain/test_analytics.py::test_partitions_of_one_type... / test_a_partition_without_a_triple_count...
- analytics.x__partition_indicators__mutmut_31 — gap — partitions add up; missing triple counts are 0 — tests/unit/domain/test_analytics.py::test_partitions_of_one_type... / test_a_partition_without_a_triple_count...
- analytics.x__partition_indicators__mutmut_32 — gap — partitions add up; missing triple counts are 0 — tests/unit/domain/test_analytics.py::test_partitions_of_one_type... / test_a_partition_without_a_triple_count...
- analytics.x__partition_indicators__mutmut_34 — gap — partitions add up; missing triple counts are 0 — tests/unit/domain/test_analytics.py::test_partitions_of_one_type... / test_a_partition_without_a_triple_count...
- analytics.x__partition_indicators__mutmut_35 — gap — partitions add up; missing triple counts are 0 — tests/unit/domain/test_analytics.py::test_partitions_of_one_type... / test_a_partition_without_a_triple_count...
- analytics.x__partition_indicators__mutmut_36 — gap — partitions add up; missing triple counts are 0 — tests/unit/domain/test_analytics.py::test_partitions_of_one_type... / test_a_partition_without_a_triple_count...
- analytics.x__partition_indicators__mutmut_39 — gap — partitions add up; missing triple counts are 0 — tests/unit/domain/test_analytics.py::test_partitions_of_one_type... / test_a_partition_without_a_triple_count...
- analytics.x__partition_indicators__mutmut_40 — gap — partitions add up; missing triple counts are 0 — tests/unit/domain/test_analytics.py::test_partitions_of_one_type... / test_a_partition_without_a_triple_count...
- analytics.x__partition_indicators__mutmut_43 — gap — partitions add up; missing triple counts are 0 — tests/unit/domain/test_analytics.py::test_partitions_of_one_type... / test_a_partition_without_a_triple_count...
- analytics.x__partition_indicators__mutmut_79 — gap — partitions add up; missing triple counts are 0 — tests/unit/domain/test_analytics.py::test_partitions_of_one_type... / test_a_partition_without_a_triple_count...
- analytics.x__partition_indicators__mutmut_91 — gap — partitions add up; missing triple counts are 0 — tests/unit/domain/test_analytics.py::test_partitions_of_one_type... / test_a_partition_without_a_triple_count...
- analytics.x_value_profile__mutmut_25 — gap — top_k boundary, empty-total entropy, missing triple counts — tests/unit/domain/test_analytics.py::test_as_many_distinct_objects_as_the_top_k... / test_a_property_without_values... / test_a_partition_without_a_triple_count...
- analytics.x_value_profile__mutmut_29 — gap — top_k boundary, empty-total entropy, missing triple counts — tests/unit/domain/test_analytics.py::test_as_many_distinct_objects_as_the_top_k... / test_a_property_without_values... / test_a_partition_without_a_triple_count...
- analytics.x_value_profile__mutmut_47 — equivalent — with total 0 and no top triples the buckets are empty, the sum is 0 either way
- analytics.x_value_profile__mutmut_54 — gap — top_k boundary, empty-total entropy, missing triple counts — tests/unit/domain/test_analytics.py::test_as_many_distinct_objects_as_the_top_k... / test_a_property_without_values... / test_a_partition_without_a_triple_count...
- analytics.x_property_analytics__mutmut_5 — equivalent — explicit None vs omitted Optional fields: same values; nothing reads model_fields_set
- analytics.x_property_analytics__mutmut_11 — gap — unknown observed count; empty total — tests/unit/domain/test_analytics.py::test_a_class_without_observed_instances... / test_a_property_without_values...
- analytics.x_property_analytics__mutmut_38 — gap — unknown observed count; empty total — tests/unit/domain/test_analytics.py::test_a_class_without_observed_instances... / test_a_property_without_values...
- analytics.x_property_analytics__mutmut_40 — equivalent — (degenerate) differs only at acceptance_threshold 0 for a property no instance has
- analytics.x_property_analytics__mutmut_48 — equivalent — explicit None vs omitted Optional fields: same values; nothing reads model_fields_set
- analytics.x_property_analytics__mutmut_50 — equivalent — explicit None vs omitted Optional fields: same values; nothing reads model_fields_set
- analytics.x_property_analytics__mutmut_52 — equivalent — explicit None vs omitted Optional fields: same values; nothing reads model_fields_set
- analytics.x_property_analytics__mutmut_54 — equivalent — explicit None vs omitted Optional fields: same values; nothing reads model_fields_set
- analytics.x__parents__mutmut_3 — gap — observed 0, missing subject counts, absent co-type ratio — tests/unit/domain/test_analytics.py::test_a_class_without_observed_instances... / test_a_co_type_without_a_subject_count... / test_parent_without_profile...
- analytics.x__parents__mutmut_6 — gap — observed 0, missing subject counts, absent co-type ratio — tests/unit/domain/test_analytics.py::test_a_class_without_observed_instances... / test_a_co_type_without_a_subject_count... / test_parent_without_profile...
- analytics.x__parents__mutmut_15 — gap — observed 0, missing subject counts, absent co-type ratio — tests/unit/domain/test_analytics.py::test_a_class_without_observed_instances... / test_a_co_type_without_a_subject_count... / test_parent_without_profile...
- analytics.x__parents__mutmut_16 — gap — observed 0, missing subject counts, absent co-type ratio — tests/unit/domain/test_analytics.py::test_a_class_without_observed_instances... / test_a_co_type_without_a_subject_count... / test_parent_without_profile...
- analytics.x__parents__mutmut_33 — gap — observed 0, missing subject counts, absent co-type ratio — tests/unit/domain/test_analytics.py::test_a_class_without_observed_instances... / test_a_co_type_without_a_subject_count... / test_parent_without_profile...
- analytics.x__depth__mutmut_10 — gap — depth of a chain longer than one — tests/unit/domain/test_analytics.py::test_depth_is_the_longest_path...
- analytics.x__depth__mutmut_13 — gap — depth of a chain longer than one — tests/unit/domain/test_analytics.py::test_depth_is_the_longest_path...
- analytics.x__namespace__mutmut_7 — equivalent — only differs for IRIs with two `#` or one starting with `#`/`/`: not absolute IRIs
- analytics.x__namespace__mutmut_8 — gap — hash namespace, URN without a separator — tests/unit/domain/test_analytics.py::test_vocabularies_are_weighted...
- analytics.x__namespace__mutmut_13 — gap — hash namespace, URN without a separator — tests/unit/domain/test_analytics.py::test_vocabularies_are_weighted...
- analytics.x__namespace__mutmut_16 — equivalent — only differs for IRIs with two `#` or one starting with `#`/`/`: not absolute IRIs
- analytics.x__namespace__mutmut_17 — equivalent — only differs for IRIs with two `#` or one starting with `#`/`/`: not absolute IRIs
- analytics.x__class_analytics__mutmut_3 — gap — missing counts, no label property, class exactness — tests/unit/domain/test_analytics.py::test_an_exact_class_with_a_presence_only_property... / test_a_class_without_observed_instances...
- analytics.x__class_analytics__mutmut_25 — equivalent — explicit None vs omitted Optional fields: same values; nothing reads model_fields_set
- analytics.x__class_analytics__mutmut_27 — equivalent — explicit None vs omitted Optional fields: same values; nothing reads model_fields_set
- analytics.x__class_analytics__mutmut_41 — gap — missing counts, no label property, class exactness — tests/unit/domain/test_analytics.py::test_an_exact_class_with_a_presence_only_property... / test_a_class_without_observed_instances...
- analytics.x__class_analytics__mutmut_43 — gap — missing counts, no label property, class exactness — tests/unit/domain/test_analytics.py::test_an_exact_class_with_a_presence_only_property... / test_a_class_without_observed_instances...
- analytics.x__class_analytics__mutmut_47 — gap — missing counts, no label property, class exactness — tests/unit/domain/test_analytics.py::test_an_exact_class_with_a_presence_only_property... / test_a_class_without_observed_instances...
- analytics.x__class_analytics__mutmut_49 — gap — missing counts, no label property, class exactness — tests/unit/domain/test_analytics.py::test_an_exact_class_with_a_presence_only_property... / test_a_class_without_observed_instances...
- analytics.x__class_analytics__mutmut_54 — gap — missing counts, no label property, class exactness — tests/unit/domain/test_analytics.py::test_an_exact_class_with_a_presence_only_property... / test_a_class_without_observed_instances...
- analytics.x__vocabularies__mutmut_4 — gap — weights add up and order — tests/unit/domain/test_analytics.py::test_vocabularies_are_weighted...
- analytics.x__vocabularies__mutmut_5 — gap — weights add up and order — tests/unit/domain/test_analytics.py::test_vocabularies_are_weighted...
- analytics.x__vocabularies__mutmut_9 — gap — weights add up and order — tests/unit/domain/test_analytics.py::test_vocabularies_are_weighted...
- analytics.x__vocabularies__mutmut_10 — gap — weights add up and order — tests/unit/domain/test_analytics.py::test_vocabularies_are_weighted...
- analytics.x__vocabularies__mutmut_13 — gap — weights add up and order — tests/unit/domain/test_analytics.py::test_vocabularies_are_weighted...
- analytics.x_graph_analytics__mutmut_30 — equivalent — default never used: every class is a key of the hierarchy
- analytics.x_graph_analytics__mutmut_32 — equivalent — default never used: every class is a key of the hierarchy
- analytics.x_graph_analytics__mutmut_70 — gap — one of the two counts absent — tests/unit/domain/test_analytics.py::test_typed_subjects_need_both_counts
- analytics.x_graph_analytics__mutmut_88 — equivalent — explicit None vs omitted Optional fields: same values; nothing reads model_fields_set
- analytics.x_graph_analytics__mutmut_90 — equivalent — explicit None vs omitted Optional fields: same values; nothing reads model_fields_set
- analytics.x_analyse__mutmut_15 — equivalent — explicit None vs omitted Optional fields: same values; nothing reads model_fields_set
- analytics.x_analyse__mutmut_17 — equivalent — explicit None vs omitted Optional fields: same values; nothing reads model_fields_set
- exceptions.xǁIriRefErrorǁ__init____mutmut_1 — cosmetic — message text only; the collection's Failure builds its own text and reads `.iri`
- shapes.x__split__mutmut_4 — gap — entry namespace vs own namespace; the `ns` fallback — tests/unit/domain/test_shapes.py::test_a_class_under_a_broader_entry... / test_a_class_without_an_entry...
- shapes.x__split__mutmut_5 — gap — entry namespace vs own namespace; the `ns` fallback — tests/unit/domain/test_shapes.py::test_a_class_under_a_broader_entry... / test_a_class_without_an_entry...
- shapes.x__split__mutmut_6 — gap — entry namespace vs own namespace; the `ns` fallback — tests/unit/domain/test_shapes.py::test_a_class_under_a_broader_entry... / test_a_class_without_an_entry...
- shapes.x__split__mutmut_9 — gap — entry namespace vs own namespace; the `ns` fallback — tests/unit/domain/test_shapes.py::test_a_class_under_a_broader_entry... / test_a_class_without_an_entry...
- shapes.x__split__mutmut_10 — gap — entry namespace vs own namespace; the `ns` fallback — tests/unit/domain/test_shapes.py::test_a_class_under_a_broader_entry... / test_a_class_without_an_entry...
- shapes.x__split__mutmut_11 — gap — entry namespace vs own namespace; the `ns` fallback — tests/unit/domain/test_shapes.py::test_a_class_under_a_broader_entry... / test_a_class_without_an_entry...
- shapes.x_shapes_base__mutmut_4 — gap — the stripped characters and the URN-with-slash rule — tests/unit/domain/test_shapes.py::test_shapes_base
- shapes.x_shapes_base__mutmut_10 — gap — the stripped characters and the URN-with-slash rule — tests/unit/domain/test_shapes.py::test_shapes_base
- shapes.x_shapes_base__mutmut_14 — gap — the stripped characters and the URN-with-slash rule — tests/unit/domain/test_shapes.py::test_shapes_base

### Dead / redundant code for the lead

- `analytics._weighted_value_at`: the final `raise IndexError(position)` is unreachable. `counts` always sums to `with_property + max(without, 0) >= observed`, and the positions asked are `<= observed - 1`; `cardinality_statistics` returns before reading them when `observed <= 0`. Delete the raise (return the last value) and `test_a_position_beyond_the_histogram_is_an_index_error`.
- `modules._by_name`: redundant. `unassigned` stays in name order, so `max(...)` keeps the first of equal scores, which is already the smaller name; `key=lambda c: sum(...)` (and `s[0]`) is enough. 7 mutants of the class and its call sites survive for this reason; the tie tests pin the behaviour.
- `analytics._namespace` duplicates `prefixes.namespace_of` with weaker rules (no URN, no `#`-then-`/` case): graph vocabularies and the prefix table can disagree on a namespace.
- `analytics.graph_analytics`: `acyclic.get(c.class_iri, set())` can be `acyclic[c.class_iri]` (the default is never used).
- `analytics.cardinality_statistics`: `if without > 0` is unnecessary for valid input (a `(0, 0)` bin changes nothing); optional simplification.

### Spec question

- `cardinality_label` at `acceptance_threshold = 0` returns `exactly_one` with support 0.0 even when no instance has exactly one value. The schema allows 0. Not pinned by a test; decide whether 0 should be rejected or the label defined.

## Lead decisions on the domain findings (2026-11-01)

- `analytics._weighted_value_at`: the unreachable `raise IndexError` is deleted (the EPIC's dead-code
  exception; GitNexus impact LOW, one caller); the function is now a single `next()` over running totals,
  and the test that only reached the raise is gone.
- Not changed (outside this EPIC's no-production-change scope; follow-ups for the developer):
  `modules._by_name` (redundant tie-break key, behaviour pinned by the new tie tests);
  `analytics._namespace` duplicating `prefixes.namespace_of` with weaker rules;
  the unused `set()` default in `graph_analytics`; the optional `if without > 0`.
- Open spec question for the developer: at `acceptance_threshold = 0`, `cardinality_label` returns
  `exactly_one` with support 0.0 even when no instance has exactly one value; the schema allows 0.
  Either reject 0 or define the label.

## service_layer.collection

Survivors of `mutation-survivors-baseline.txt` re-checked on the current tree: 287. After the new tests: 75 left. Same classes as above.

| module | before | after | gap | equivalent | cosmetic | dead |
|---|---|---|---|---|---|---|
| collection | 287 | 75 | 212 | 13 | 62 | 0 |

Cosmetic = logger text/arguments and an unreachable assertion message; no scenario or CLI contract fixes them. Failure messages that land in the profile are gaps and are pinned exactly. All new tests are in `tests/unit/service_layer/test_collection.py` (FakeSparql rules and named-graph data no Gherkin scenario reaches). Per-mutant lines: `fingerprint.service_layer.collection.` and `xǁ_Collectionǁ` omitted.

Dead code: none. The `done[-1] if done else "Q8"` fallback in `profile_class` is needed only by the `IriRefError` handler (exact mode raises before `Q8` is appended); in the `QueryTimeout`/`PermanentError` handlers it could be plain `done[-1]` (optional).

- collection.x__term__mutmut_4 — cosmetic — text of an assertion that cannot fire
- collection.x__term__mutmut_5 — cosmetic — text of an assertion that cannot fire
- collection.x__int__mutmut_2 — gap — empty and unbound counts read as None — test_collection.py
- collection.x__int__mutmut_4 — gap — empty and unbound counts read as None — test_collection.py
- collection.x__int__mutmut_6 — gap — empty and unbound counts read as None — test_collection.py
- collection.x__int__mutmut_8 — gap — empty and unbound counts read as None — test_collection.py
- collection.fail__mutmut_5 — gap — a failure carries its graph (None for the default graph) and property — test_collection.py
- collection.fail__mutmut_7 — gap — a failure carries its graph (None for the default graph) and property — test_collection.py
- collection.fail__mutmut_11 — gap — a failure carries its graph (None for the default graph) and property — test_collection.py
- collection.fail__mutmut_13 — gap — a failure carries its graph (None for the default graph) and property — test_collection.py
- collection.fail__mutmut_15 — gap — a failure carries its graph (None for the default graph) and property — test_collection.py
- collection.ask__mutmut_3 — gap — the presence check asks inside its graph — test_collection.py
- collection._run__mutmut_12 — gap — a refusal past discovery is recorded as a rejection with its text — test_collection.py
- collection._run__mutmut_13 — equivalent — status of the re-raised error is read only for 400/413 on a first-N list; `EndpointUnreachable` carries only 401/403/407
- collection._run__mutmut_14 — gap — a refusal past discovery is recorded as a rejection with its text — test_collection.py
- collection._run__mutmut_15 — equivalent — status of the re-raised error is read only for 400/413 on a first-N list; `EndpointUnreachable` carries only 401/403/407
- collection._run__mutmut_16 — gap — a refusal past discovery is recorded as a rejection with its text — test_collection.py
- collection.named_graphs__mutmut_3 — gap — graph names; listing failure text for timeout vs rejection — test_collection.py
- collection.named_graphs__mutmut_12 — gap — graph names; listing failure text for timeout vs rejection — test_collection.py
- collection.named_graphs__mutmut_13 — gap — graph names; listing failure text for timeout vs rejection — test_collection.py
- collection.named_graphs__mutmut_14 — gap — graph names; listing failure text for timeout vs rejection — test_collection.py
- collection.named_graphs__mutmut_15 — gap — graph names; listing failure text for timeout vs rejection — test_collection.py
- collection.named_graphs__mutmut_16 — gap — graph names; listing failure text for timeout vs rejection — test_collection.py
- collection.named_graphs__mutmut_17 — gap — graph names; listing failure text for timeout vs rejection — test_collection.py
- collection.named_graphs__mutmut_18 — gap — graph names; listing failure text for timeout vs rejection — test_collection.py
- collection.named_graphs__mutmut_19 — cosmetic — log call
- collection.named_graphs__mutmut_21 — gap — graph names; listing failure text for timeout vs rejection — test_collection.py
- collection.declared_edges__mutmut_21 — gap — only rows with both ends become edges — test_collection.py
- collection.predicates__mutmut_3 — gap — Q2/Q2a stay in their graph; triples read; fallback failure text — test_collection.py
- collection.predicates__mutmut_5 — gap — Q2/Q2a stay in their graph; triples read; fallback failure text — test_collection.py
- collection.predicates__mutmut_9 — gap — Q2/Q2a stay in their graph; triples read; fallback failure text — test_collection.py
- collection.predicates__mutmut_11 — gap — Q2/Q2a stay in their graph; triples read; fallback failure text — test_collection.py
- collection.predicates__mutmut_15 — gap — Q2/Q2a stay in their graph; triples read; fallback failure text — test_collection.py
- collection.predicates__mutmut_21 — cosmetic — log text
- collection.predicates__mutmut_22 — cosmetic — log text
- collection.predicates__mutmut_26 — cosmetic — log text
- collection.predicates__mutmut_27 — cosmetic — log text
- collection.predicates__mutmut_29 — cosmetic — log text
- collection.predicates__mutmut_30 — cosmetic — log text
- collection.predicates__mutmut_31 — cosmetic — log text
- collection.predicates__mutmut_32 — cosmetic — log text
- collection.predicates__mutmut_33 — cosmetic — log text
- collection.predicates__mutmut_34 — cosmetic — log text
- collection.predicates__mutmut_35 — cosmetic — log text
- collection.predicates__mutmut_36 — cosmetic — log text
- collection.predicates__mutmut_37 — cosmetic — log text
- collection.predicates__mutmut_38 — cosmetic — log text
- collection.predicates__mutmut_39 — cosmetic — log text
- collection.predicates__mutmut_40 — cosmetic — log text
- collection.predicates__mutmut_41 — cosmetic — log text
- collection.predicates__mutmut_42 — cosmetic — log text
- collection.predicates__mutmut_43 — cosmetic — log text
- collection.predicates__mutmut_49 — gap — Q2/Q2a stay in their graph; triples read; fallback failure text — test_collection.py
- collection.predicates__mutmut_51 — gap — Q2/Q2a stay in their graph; triples read; fallback failure text — test_collection.py
- collection.predicates__mutmut_59 — gap — Q2/Q2a stay in their graph; triples read; fallback failure text — test_collection.py
- collection.predicates__mutmut_62 — gap — Q2/Q2a stay in their graph; triples read; fallback failure text — test_collection.py
- collection.predicates__mutmut_66 — gap — Q2/Q2a stay in their graph; triples read; fallback failure text — test_collection.py
- collection.predicates__mutmut_67 — gap — Q2/Q2a stay in their graph; triples read; fallback failure text — test_collection.py
- collection.predicates__mutmut_68 — gap — Q2/Q2a stay in their graph; triples read; fallback failure text — test_collection.py
- collection.graph_totals__mutmut_16 — gap — totals read per graph; failure text and graph — test_collection.py
- collection.graph_totals__mutmut_18 — gap — totals read per graph; failure text and graph — test_collection.py
- collection.graph_totals__mutmut_25 — gap — totals read per graph; failure text and graph — test_collection.py
- collection.graph_totals__mutmut_28 — gap — totals read per graph; failure text and graph — test_collection.py
- collection.graph_totals__mutmut_29 — gap — totals read per graph; failure text and graph — test_collection.py
- collection.graph_totals__mutmut_30 — gap — totals read per graph; failure text and graph — test_collection.py
- collection.graph_totals__mutmut_31 — gap — totals read per graph; failure text and graph — test_collection.py
- collection.graph_totals__mutmut_34 — gap — totals read per graph; failure text and graph — test_collection.py
- collection.graph_totals__mutmut_37 — gap — totals read per graph; failure text and graph — test_collection.py
- collection.graph_totals__mutmut_38 — gap — totals read per graph; failure text and graph — test_collection.py
- collection.graph_totals__mutmut_39 — gap — totals read per graph; failure text and graph — test_collection.py
- collection.graph_totals__mutmut_40 — gap — totals read per graph; failure text and graph — test_collection.py
- collection.graph_totals__mutmut_41 — gap — totals read per graph; failure text and graph — test_collection.py
- collection.graph_totals__mutmut_42 — gap — totals read per graph; failure text and graph — test_collection.py
- collection.class_counts__mutmut_12 — gap — per-graph class counts, empty count = 0, unusable class, failure text/graph — test_collection.py
- collection.class_counts__mutmut_22 — cosmetic — log text
- collection.class_counts__mutmut_23 — cosmetic — log text
- collection.class_counts__mutmut_24 — cosmetic — log text
- collection.class_counts__mutmut_25 — cosmetic — log text
- collection.class_counts__mutmut_28 — cosmetic — log text
- collection.class_counts__mutmut_29 — cosmetic — log text
- collection.class_counts__mutmut_33 — cosmetic — log text
- collection.class_counts__mutmut_40 — gap — per-graph class counts, empty count = 0, unusable class, failure text/graph — test_collection.py
- collection.class_counts__mutmut_42 — gap — per-graph class counts, empty count = 0, unusable class, failure text/graph — test_collection.py
- collection.class_counts__mutmut_50 — gap — per-graph class counts, empty count = 0, unusable class, failure text/graph — test_collection.py
- collection.class_counts__mutmut_53 — gap — per-graph class counts, empty count = 0, unusable class, failure text/graph — test_collection.py
- collection.class_counts__mutmut_62 — gap — per-graph class counts, empty count = 0, unusable class, failure text/graph — test_collection.py
- collection.class_counts__mutmut_65 — gap — per-graph class counts, empty count = 0, unusable class, failure text/graph — test_collection.py
- collection.class_counts__mutmut_73 — gap — per-graph class counts, empty count = 0, unusable class, failure text/graph — test_collection.py
- collection.class_counts__mutmut_74 — gap — per-graph class counts, empty count = 0, unusable class, failure text/graph — test_collection.py
- collection.class_counts__mutmut_75 — gap — per-graph class counts, empty count = 0, unusable class, failure text/graph — test_collection.py
- collection.class_counts__mutmut_76 — gap — per-graph class counts, empty count = 0, unusable class, failure text/graph — test_collection.py
- collection.class_counts__mutmut_77 — gap — per-graph class counts, empty count = 0, unusable class, failure text/graph — test_collection.py
- collection.class_counts__mutmut_78 — gap — per-graph class counts, empty count = 0, unusable class, failure text/graph — test_collection.py
- collection.class_counts__mutmut_79 — gap — per-graph class counts, empty count = 0, unusable class, failure text/graph — test_collection.py
- collection.class_counts__mutmut_80 — gap — per-graph class counts, empty count = 0, unusable class, failure text/graph — test_collection.py
- collection.class_counts__mutmut_81 — gap — per-graph class counts, empty count = 0, unusable class, failure text/graph — test_collection.py
- collection.class_counts__mutmut_82 — gap — per-graph class counts, empty count = 0, unusable class, failure text/graph — test_collection.py
- collection.class_counts__mutmut_83 — gap — per-graph class counts, empty count = 0, unusable class, failure text/graph — test_collection.py
- collection.class_counts__mutmut_84 — gap — per-graph class counts, empty count = 0, unusable class, failure text/graph — test_collection.py
- collection.class_counts__mutmut_86 — gap — per-graph class counts, empty count = 0, unusable class, failure text/graph — test_collection.py
- collection.class_counts__mutmut_87 — gap — per-graph class counts, empty count = 0, unusable class, failure text/graph — test_collection.py
- collection.first_wave__mutmut_9 — gap — one sample per class, graph scoped, kind of the failed query, distinct sum, typed reads — test_collection.py
- collection.first_wave__mutmut_10 — gap — one sample per class, graph scoped, kind of the failed query, distinct sum, typed reads — test_collection.py
- collection.first_wave__mutmut_11 — gap — one sample per class, graph scoped, kind of the failed query, distinct sum, typed reads — test_collection.py
- collection.first_wave__mutmut_16 — gap — one sample per class, graph scoped, kind of the failed query, distinct sum, typed reads — test_collection.py
- collection.first_wave__mutmut_20 — gap — one sample per class, graph scoped, kind of the failed query, distinct sum, typed reads — test_collection.py
- collection.first_wave__mutmut_34 — cosmetic — log text
- collection.first_wave__mutmut_35 — cosmetic — log text
- collection.first_wave__mutmut_36 — cosmetic — log text
- collection.first_wave__mutmut_37 — cosmetic — log text
- collection.first_wave__mutmut_38 — cosmetic — log text
- collection.first_wave__mutmut_39 — cosmetic — log text
- collection.first_wave__mutmut_40 — cosmetic — log text
- collection.first_wave__mutmut_42 — gap — one sample per class, graph scoped, kind of the failed query, distinct sum, typed reads — test_collection.py
- collection.first_wave__mutmut_53 — gap — one sample per class, graph scoped, kind of the failed query, distinct sum, typed reads — test_collection.py
- collection.first_wave__mutmut_55 — gap — one sample per class, graph scoped, kind of the failed query, distinct sum, typed reads — test_collection.py
- collection.first_wave__mutmut_59 — gap — one sample per class, graph scoped, kind of the failed query, distinct sum, typed reads — test_collection.py
- collection.first_wave__mutmut_63 — gap — one sample per class, graph scoped, kind of the failed query, distinct sum, typed reads — test_collection.py
- collection.first_wave__mutmut_67 — gap — one sample per class, graph scoped, kind of the failed query, distinct sum, typed reads — test_collection.py
- collection.first_wave__mutmut_85 — gap — one sample per class, graph scoped, kind of the failed query, distinct sum, typed reads — test_collection.py
- collection.first_wave__mutmut_88 — gap — one sample per class, graph scoped, kind of the failed query, distinct sum, typed reads — test_collection.py
- collection.first_wave__mutmut_115 — gap — one sample per class, graph scoped, kind of the failed query, distinct sum, typed reads — test_collection.py
- collection.first_wave__mutmut_116 — gap — one sample per class, graph scoped, kind of the failed query, distinct sum, typed reads — test_collection.py
- collection.first_wave__mutmut_117 — gap — one sample per class, graph scoped, kind of the failed query, distinct sum, typed reads — test_collection.py
- collection.first_wave__mutmut_119 — gap — one sample per class, graph scoped, kind of the failed query, distinct sum, typed reads — test_collection.py
- collection.first_wave__mutmut_122 — gap — one sample per class, graph scoped, kind of the failed query, distinct sum, typed reads — test_collection.py
- collection.first_wave__mutmut_129 — gap — one sample per class, graph scoped, kind of the failed query, distinct sum, typed reads — test_collection.py
- collection.first_wave__mutmut_135 — gap — one sample per class, graph scoped, kind of the failed query, distinct sum, typed reads — test_collection.py
- collection.first_wave__mutmut_137 — gap — one sample per class, graph scoped, kind of the failed query, distinct sum, typed reads — test_collection.py
- collection.first_wave__mutmut_141 — gap — one sample per class, graph scoped, kind of the failed query, distinct sum, typed reads — test_collection.py
- collection.first_wave__mutmut_142 — gap — one sample per class, graph scoped, kind of the failed query, distinct sum, typed reads — test_collection.py
- collection.first_wave__mutmut_143 — gap — one sample per class, graph scoped, kind of the failed query, distinct sum, typed reads — test_collection.py
- collection.first_wave__mutmut_146 — gap — one sample per class, graph scoped, kind of the failed query, distinct sum, typed reads — test_collection.py
- collection.first_wave__mutmut_157 — gap — one sample per class, graph scoped, kind of the failed query, distinct sum, typed reads — test_collection.py
- collection.first_wave__mutmut_158 — gap — one sample per class, graph scoped, kind of the failed query, distinct sum, typed reads — test_collection.py
- collection.first_wave__mutmut_159 — gap — one sample per class, graph scoped, kind of the failed query, distinct sum, typed reads — test_collection.py
- collection.first_wave__mutmut_182 — gap — one sample per class, graph scoped, kind of the failed query, distinct sum, typed reads — test_collection.py
- collection.first_wave__mutmut_187 — gap — one sample per class, graph scoped, kind of the failed query, distinct sum, typed reads — test_collection.py
- collection.first_wave__mutmut_199 — gap — one sample per class, graph scoped, kind of the failed query, distinct sum, typed reads — test_collection.py
- collection.first_wave__mutmut_208 — gap — one sample per class, graph scoped, kind of the failed query, distinct sum, typed reads — test_collection.py
- collection.first_wave__mutmut_212 — gap — one sample per class, graph scoped, kind of the failed query, distinct sum, typed reads — test_collection.py
- collection.first_wave__mutmut_215 — gap — one sample per class, graph scoped, kind of the failed query, distinct sum, typed reads — test_collection.py
- collection.literal_partition__mutmut_5 — gap — datatype from language, lengths and min/max text — test_collection.py
- collection.literal_partition__mutmut_8 — gap — datatype from language, lengths and min/max text — test_collection.py
- collection.literal_partition__mutmut_9 — gap — datatype from language, lengths and min/max text — test_collection.py
- collection.literal_partition__mutmut_10 — gap — datatype from language, lengths and min/max text — test_collection.py
- collection.literal_partition__mutmut_15 — gap — datatype from language, lengths and min/max text — test_collection.py
- collection.literal_partition__mutmut_18 — gap — datatype from language, lengths and min/max text — test_collection.py
- collection.literal_partition__mutmut_19 — gap — datatype from language, lengths and min/max text — test_collection.py
- collection.literal_partition__mutmut_20 — gap — datatype from language, lengths and min/max text — test_collection.py
- collection.literal_partition__mutmut_25 — gap — datatype from language, lengths and min/max text — test_collection.py
- collection.literal_partition__mutmut_26 — gap — datatype from language, lengths and min/max text — test_collection.py
- collection.literal_partition__mutmut_27 — gap — datatype from language, lengths and min/max text — test_collection.py
- collection.literal_partition__mutmut_28 — gap — datatype from language, lengths and min/max text — test_collection.py
- collection.literal_partition__mutmut_36 — gap — datatype from language, lengths and min/max text — test_collection.py
- collection.literal_partition__mutmut_45 — gap — datatype from language, lengths and min/max text — test_collection.py
- collection.literal_partition__mutmut_48 — gap — datatype from language, lengths and min/max text — test_collection.py
- collection.literal_partition__mutmut_51 — gap — datatype from language, lengths and min/max text — test_collection.py
- collection.second_wave__mutmut_11 — gap — Q9/Q10/Q11 values, graph scope, switches and failure arguments — test_collection.py
- collection.second_wave__mutmut_16 — gap — Q9/Q10/Q11 values, graph scope, switches and failure arguments — test_collection.py
- collection.second_wave__mutmut_18 — gap — Q9/Q10/Q11 values, graph scope, switches and failure arguments — test_collection.py
- collection.second_wave__mutmut_24 — gap — Q9/Q10/Q11 values, graph scope, switches and failure arguments — test_collection.py
- collection.second_wave__mutmut_26 — gap — Q9/Q10/Q11 values, graph scope, switches and failure arguments — test_collection.py
- collection.second_wave__mutmut_30 — gap — Q9/Q10/Q11 values, graph scope, switches and failure arguments — test_collection.py
- collection.second_wave__mutmut_37 — gap — Q9/Q10/Q11 values, graph scope, switches and failure arguments — test_collection.py
- collection.second_wave__mutmut_38 — gap — Q9/Q10/Q11 values, graph scope, switches and failure arguments — test_collection.py
- collection.second_wave__mutmut_40 — gap — Q9/Q10/Q11 values, graph scope, switches and failure arguments — test_collection.py
- collection.second_wave__mutmut_41 — gap — Q9/Q10/Q11 values, graph scope, switches and failure arguments — test_collection.py
- collection.second_wave__mutmut_42 — gap — Q9/Q10/Q11 values, graph scope, switches and failure arguments — test_collection.py
- collection.second_wave__mutmut_43 — gap — Q9/Q10/Q11 values, graph scope, switches and failure arguments — test_collection.py
- collection.second_wave__mutmut_45 — gap — Q9/Q10/Q11 values, graph scope, switches and failure arguments — test_collection.py
- collection.second_wave__mutmut_46 — gap — Q9/Q10/Q11 values, graph scope, switches and failure arguments — test_collection.py
- collection.second_wave__mutmut_47 — gap — Q9/Q10/Q11 values, graph scope, switches and failure arguments — test_collection.py
- collection.second_wave__mutmut_48 — gap — Q9/Q10/Q11 values, graph scope, switches and failure arguments — test_collection.py
- collection.second_wave__mutmut_52 — gap — Q9/Q10/Q11 values, graph scope, switches and failure arguments — test_collection.py
- collection.second_wave__mutmut_53 — gap — Q9/Q10/Q11 values, graph scope, switches and failure arguments — test_collection.py
- collection.second_wave__mutmut_58 — gap — Q9/Q10/Q11 values, graph scope, switches and failure arguments — test_collection.py
- collection.second_wave__mutmut_62 — gap — Q9/Q10/Q11 values, graph scope, switches and failure arguments — test_collection.py
- collection.second_wave__mutmut_66 — gap — Q9/Q10/Q11 values, graph scope, switches and failure arguments — test_collection.py
- collection.second_wave__mutmut_78 — gap — Q9/Q10/Q11 values, graph scope, switches and failure arguments — test_collection.py
- collection.second_wave__mutmut_79 — gap — Q9/Q10/Q11 values, graph scope, switches and failure arguments — test_collection.py
- collection.second_wave__mutmut_80 — gap — Q9/Q10/Q11 values, graph scope, switches and failure arguments — test_collection.py
- collection.second_wave__mutmut_81 — gap — Q9/Q10/Q11 values, graph scope, switches and failure arguments — test_collection.py
- collection.second_wave__mutmut_83 — gap — Q9/Q10/Q11 values, graph scope, switches and failure arguments — test_collection.py
- collection.second_wave__mutmut_84 — gap — Q9/Q10/Q11 values, graph scope, switches and failure arguments — test_collection.py
- collection.second_wave__mutmut_85 — gap — Q9/Q10/Q11 values, graph scope, switches and failure arguments — test_collection.py
- collection.second_wave__mutmut_86 — gap — Q9/Q10/Q11 values, graph scope, switches and failure arguments — test_collection.py
- collection.second_wave__mutmut_91 — gap — Q9/Q10/Q11 values, graph scope, switches and failure arguments — test_collection.py
- collection.second_wave__mutmut_92 — gap — Q9/Q10/Q11 values, graph scope, switches and failure arguments — test_collection.py
- collection.second_wave__mutmut_93 — gap — Q9/Q10/Q11 values, graph scope, switches and failure arguments — test_collection.py
- collection.second_wave__mutmut_94 — gap — Q9/Q10/Q11 values, graph scope, switches and failure arguments — test_collection.py
- collection.second_wave__mutmut_95 — gap — Q9/Q10/Q11 values, graph scope, switches and failure arguments — test_collection.py
- collection.second_wave__mutmut_96 — gap — Q9/Q10/Q11 values, graph scope, switches and failure arguments — test_collection.py
- collection.second_wave__mutmut_97 — gap — Q9/Q10/Q11 values, graph scope, switches and failure arguments — test_collection.py
- collection.second_wave__mutmut_100 — gap — Q9/Q10/Q11 values, graph scope, switches and failure arguments — test_collection.py
- collection.second_wave__mutmut_103 — gap — Q9/Q10/Q11 values, graph scope, switches and failure arguments — test_collection.py
- collection.second_wave__mutmut_107 — gap — Q9/Q10/Q11 values, graph scope, switches and failure arguments — test_collection.py
- collection.second_wave__mutmut_110 — gap — Q9/Q10/Q11 values, graph scope, switches and failure arguments — test_collection.py
- collection.second_wave__mutmut_117 — gap — Q9/Q10/Q11 values, graph scope, switches and failure arguments — test_collection.py
- collection.second_wave__mutmut_118 — gap — Q9/Q10/Q11 values, graph scope, switches and failure arguments — test_collection.py
- collection.second_wave__mutmut_119 — gap — Q9/Q10/Q11 values, graph scope, switches and failure arguments — test_collection.py
- collection.second_wave__mutmut_121 — gap — Q9/Q10/Q11 values, graph scope, switches and failure arguments — test_collection.py
- collection.second_wave__mutmut_122 — gap — Q9/Q10/Q11 values, graph scope, switches and failure arguments — test_collection.py
- collection.second_wave__mutmut_123 — gap — Q9/Q10/Q11 values, graph scope, switches and failure arguments — test_collection.py
- collection.profile_class__mutmut_2 — equivalent — `last` initial value and the `done[-1] if done else "Q8"` fallback are never read: `done` is non-empty where they run
- collection.profile_class__mutmut_3 — equivalent — `last` initial value and the `done[-1] if done else "Q8"` fallback are never read: `done` is non-empty where they run
- collection.profile_class__mutmut_4 — equivalent — `last` initial value and the `done[-1] if done else "Q8"` fallback are never read: `done` is non-empty where they run
- collection.profile_class__mutmut_21 — gap — attempts, last failing query, too-large rule, graph of the failure — test_collection.py
- collection.profile_class__mutmut_22 — gap — attempts, last failing query, too-large rule, graph of the failure — test_collection.py
- collection.profile_class__mutmut_25 — gap — attempts, last failing query, too-large rule, graph of the failure — test_collection.py
- collection.profile_class__mutmut_26 — gap — attempts, last failing query, too-large rule, graph of the failure — test_collection.py
- collection.profile_class__mutmut_27 — gap — attempts, last failing query, too-large rule, graph of the failure — test_collection.py
- collection.profile_class__mutmut_29 — gap — attempts, last failing query, too-large rule, graph of the failure — test_collection.py
- collection.profile_class__mutmut_30 — gap — attempts, last failing query, too-large rule, graph of the failure — test_collection.py
- collection.profile_class__mutmut_34 — gap — attempts, last failing query, too-large rule, graph of the failure — test_collection.py
- collection.profile_class__mutmut_35 — equivalent — `last` initial value and the `done[-1] if done else "Q8"` fallback are never read: `done` is non-empty where they run
- collection.profile_class__mutmut_38 — equivalent — `last` initial value and the `done[-1] if done else "Q8"` fallback are never read: `done` is non-empty where they run
- collection.profile_class__mutmut_39 — equivalent — `last` initial value and the `done[-1] if done else "Q8"` fallback are never read: `done` is non-empty where they run
- collection.profile_class__mutmut_40 — cosmetic — log text and arguments
- collection.profile_class__mutmut_41 — cosmetic — log text and arguments
- collection.profile_class__mutmut_43 — cosmetic — log text and arguments
- collection.profile_class__mutmut_46 — cosmetic — log text and arguments
- collection.profile_class__mutmut_48 — cosmetic — log text and arguments
- collection.profile_class__mutmut_49 — cosmetic — log text and arguments
- collection.profile_class__mutmut_51 — cosmetic — log text and arguments
- collection.profile_class__mutmut_52 — cosmetic — log text and arguments
- collection.profile_class__mutmut_53 — cosmetic — log text and arguments
- collection.profile_class__mutmut_54 — cosmetic — log text and arguments
- collection.profile_class__mutmut_60 — cosmetic — log text and arguments
- collection.profile_class__mutmut_64 — equivalent — `last` initial value and the `done[-1] if done else "Q8"` fallback are never read: `done` is non-empty where they run
- collection.profile_class__mutmut_65 — gap — attempts, last failing query, too-large rule, graph of the failure — test_collection.py
- collection.profile_class__mutmut_67 — equivalent — `last` initial value and the `done[-1] if done else "Q8"` fallback are never read: `done` is non-empty where they run
- collection.profile_class__mutmut_68 — equivalent — `last` initial value and the `done[-1] if done else "Q8"` fallback are never read: `done` is non-empty where they run
- collection.profile_class__mutmut_69 — gap — attempts, last failing query, too-large rule, graph of the failure — test_collection.py
- collection.profile_class__mutmut_70 — gap — attempts, last failing query, too-large rule, graph of the failure — test_collection.py
- collection.profile_class__mutmut_73 — gap — attempts, last failing query, too-large rule, graph of the failure — test_collection.py
- collection.profile_class__mutmut_74 — gap — attempts, last failing query, too-large rule, graph of the failure — test_collection.py
- collection.profile_class__mutmut_77 — gap — attempts, last failing query, too-large rule, graph of the failure — test_collection.py
- collection.profile_class__mutmut_80 — gap — attempts, last failing query, too-large rule, graph of the failure — test_collection.py
- collection.profile_class__mutmut_91 — gap — attempts, last failing query, too-large rule, graph of the failure — test_collection.py
- collection.profile_class__mutmut_92 — gap — attempts, last failing query, too-large rule, graph of the failure — test_collection.py
- collection.profile_class__mutmut_101 — gap — attempts, last failing query, too-large rule, graph of the failure — test_collection.py
- collection.profile_class__mutmut_109 — cosmetic — log text and arguments
- collection.profile_class__mutmut_111 — cosmetic — log text and arguments
- collection.profile_class__mutmut_112 — cosmetic — log text and arguments
- collection.profile_class__mutmut_113 — cosmetic — log text and arguments
- collection.profile_class__mutmut_114 — cosmetic — log text and arguments
- collection.profile_class__mutmut_115 — cosmetic — log text and arguments
- collection.profile_class__mutmut_122 — cosmetic — log text and arguments
- collection.profile_graph__mutmut_1 — cosmetic — log text and label
- collection.profile_graph__mutmut_2 — cosmetic — log text and label
- collection.profile_graph__mutmut_3 — cosmetic — log text and label
- collection.profile_graph__mutmut_4 — cosmetic — log text and label
- collection.profile_graph__mutmut_6 — cosmetic — log text and label
- collection.profile_graph__mutmut_7 — cosmetic — log text and label
- collection.profile_graph__mutmut_8 — cosmetic — log text and label
- collection.profile_graph__mutmut_9 — cosmetic — log text and label
- collection.profile_graph__mutmut_14 — gap — class order (largest first, then IRI), graph scope, blank-node class failure — test_collection.py
- collection.profile_graph__mutmut_17 — equivalent — `predicates = ""` differs from None only when the completeness check is off (guarded before it is read); `max_workers=None` is the library default sizing
- collection.profile_graph__mutmut_22 — gap — class order (largest first, then IRI), graph scope, blank-node class failure — test_collection.py
- collection.profile_graph__mutmut_35 — gap — class order (largest first, then IRI), graph scope, blank-node class failure — test_collection.py
- collection.profile_graph__mutmut_36 — gap — class order (largest first, then IRI), graph scope, blank-node class failure — test_collection.py
- collection.profile_graph__mutmut_39 — gap — class order (largest first, then IRI), graph scope, blank-node class failure — test_collection.py
- collection.profile_graph__mutmut_40 — gap — class order (largest first, then IRI), graph scope, blank-node class failure — test_collection.py
- collection.profile_graph__mutmut_46 — gap — class order (largest first, then IRI), graph scope, blank-node class failure — test_collection.py
- collection.profile_graph__mutmut_48 — gap — class order (largest first, then IRI), graph scope, blank-node class failure — test_collection.py
- collection.profile_graph__mutmut_50 — gap — class order (largest first, then IRI), graph scope, blank-node class failure — test_collection.py
- collection.profile_graph__mutmut_52 — gap — class order (largest first, then IRI), graph scope, blank-node class failure — test_collection.py
- collection.profile_graph__mutmut_53 — equivalent — `predicates = ""` differs from None only when the completeness check is off (guarded before it is read); `max_workers=None` is the library default sizing
- collection.x_collect__mutmut_1 — gap — run metadata, depth graphs reads no hierarchy, unusable graph IRI — test_collection.py
- collection.x_collect__mutmut_2 — gap — run metadata, depth graphs reads no hierarchy, unusable graph IRI — test_collection.py
- collection.x_collect__mutmut_17 — gap — run metadata, depth graphs reads no hierarchy, unusable graph IRI — test_collection.py
- collection.x_collect__mutmut_25 — gap — run metadata, depth graphs reads no hierarchy, unusable graph IRI — test_collection.py
- collection.x_collect__mutmut_26 — gap — run metadata, depth graphs reads no hierarchy, unusable graph IRI — test_collection.py
- collection.x_collect__mutmut_27 — gap — run metadata, depth graphs reads no hierarchy, unusable graph IRI — test_collection.py
- collection.x_collect__mutmut_28 — gap — run metadata, depth graphs reads no hierarchy, unusable graph IRI — test_collection.py
- collection.x_collect__mutmut_29 — gap — run metadata, depth graphs reads no hierarchy, unusable graph IRI — test_collection.py
- collection.x_collect__mutmut_30 — gap — run metadata, depth graphs reads no hierarchy, unusable graph IRI — test_collection.py
- collection.x_collect__mutmut_31 — gap — run metadata, depth graphs reads no hierarchy, unusable graph IRI — test_collection.py
- collection.x_collect__mutmut_32 — gap — run metadata, depth graphs reads no hierarchy, unusable graph IRI — test_collection.py
- collection.x_collect__mutmut_34 — gap — run metadata, depth graphs reads no hierarchy, unusable graph IRI — test_collection.py
- collection.x_collect__mutmut_35 — gap — run metadata, depth graphs reads no hierarchy, unusable graph IRI — test_collection.py
- collection.x_collect__mutmut_36 — gap — run metadata, depth graphs reads no hierarchy, unusable graph IRI — test_collection.py
- collection.x_collect__mutmut_41 — gap — run metadata, depth graphs reads no hierarchy, unusable graph IRI — test_collection.py
- collection.x_collect__mutmut_42 — gap — run metadata, depth graphs reads no hierarchy, unusable graph IRI — test_collection.py
- collection.x_collect__mutmut_43 — gap — run metadata, depth graphs reads no hierarchy, unusable graph IRI — test_collection.py
- collection.x_collect__mutmut_47 — gap — run metadata, depth graphs reads no hierarchy, unusable graph IRI — test_collection.py

## service_layer.generators

Survivors re-checked on the current tree: 146 (the baseline listed 158). After the new tests: 37 left (22 equivalent, 3 cosmetic, 11 dead, 1 killed by timeout, which mutmut lists as survived); every other gap is killed. The dead ones show as `no tests` in mutmut.

| module | before | gap | equivalent | cosmetic | dead |
|---|---|---|---|---|---|
| document | 45 | 37 | 3 | 0 | 5 |
| generator | 39 | 29 | 1 | 3 | 6 |
| plantuml | 44 | 35 | 9 | 0 | 0 |
| shacl | 29 | 20 | 9 | 0 | 0 |

### Per mutant (`fingerprint.service_layer.generators.` omitted; the number is the `__mutmut_N` suffix)

- plantuml.xǁPlantumlGeneratorǁ__init____mutmut_3 — gap — diagram order, aliases, references, links, types — tests/unit/service_layer/test_plantuml.py
- plantuml.xǁPlantumlGeneratorǁ__init____mutmut_11 — gap — diagram order, aliases, references, links, types — tests/unit/service_layer/test_plantuml.py
- plantuml.xǁPlantumlGeneratorǁ__init____mutmut_12 — equivalent — the index is reset in visit_graph / outputs before its first read
- plantuml.xǁPlantumlGeneratorǁ__init____mutmut_13 — equivalent — the index is reset in visit_graph / outputs before its first read
- plantuml.xǁPlantumlGeneratorǁ__init____mutmut_14 — equivalent — the index is reset in visit_graph / outputs before its first read
- plantuml.xǁPlantumlGeneratorǁ__init____mutmut_15 — equivalent — the index is reset in visit_graph / outputs before its first read
- plantuml.xǁPlantumlGeneratorǁ__init____mutmut_16 — equivalent — the index is reset in visit_graph / outputs before its first read
- plantuml.xǁPlantumlGeneratorǁ__init____mutmut_17 — equivalent — the index is reset in visit_graph / outputs before its first read
- plantuml.xǁPlantumlGeneratorǁvisit_graph__mutmut_11 — gap — diagram order, aliases, references, links, types — tests/unit/service_layer/test_plantuml.py
- plantuml.xǁPlantumlGeneratorǁvisit_graph__mutmut_12 — gap — diagram order, aliases, references, links, types — tests/unit/service_layer/test_plantuml.py
- plantuml.xǁPlantumlGeneratorǁend_class__mutmut_4 — gap — diagram order, aliases, references, links, types — tests/unit/service_layer/test_plantuml.py
- plantuml.xǁPlantumlGeneratorǁend_class__mutmut_6 — gap — diagram order, aliases, references, links, types — tests/unit/service_layer/test_plantuml.py
- plantuml.xǁPlantumlGeneratorǁend_class__mutmut_8 — gap — diagram order, aliases, references, links, types — tests/unit/service_layer/test_plantuml.py
- plantuml.xǁPlantumlGeneratorǁend_class__mutmut_9 — gap — diagram order, aliases, references, links, types — tests/unit/service_layer/test_plantuml.py
- plantuml.xǁPlantumlGeneratorǁend_graph__mutmut_2 — gap — diagram order, aliases, references, links, types — tests/unit/service_layer/test_plantuml.py
- plantuml.xǁPlantumlGeneratorǁend_graph__mutmut_4 — gap — diagram order, aliases, references, links, types — tests/unit/service_layer/test_plantuml.py
- plantuml.xǁPlantumlGeneratorǁend_graph__mutmut_5 — gap — diagram order, aliases, references, links, types — tests/unit/service_layer/test_plantuml.py
- plantuml.xǁPlantumlGeneratorǁend_graph__mutmut_18 — gap — diagram order, aliases, references, links, types — tests/unit/service_layer/test_plantuml.py
- plantuml.xǁPlantumlGeneratorǁend_graph__mutmut_20 — gap — diagram order, aliases, references, links, types — tests/unit/service_layer/test_plantuml.py
- plantuml.xǁPlantumlGeneratorǁend_graph__mutmut_51 — equivalent — names and groups always have equal length, so strict zip never differs
- plantuml.xǁPlantumlGeneratorǁend_graph__mutmut_54 — equivalent — names and groups always have equal length, so strict zip never differs
- plantuml.xǁPlantumlGeneratorǁend_graph__mutmut_55 — equivalent — names and groups always have equal length, so strict zip never differs
- plantuml.xǁPlantumlGeneratorǁprefix__mutmut_4 — gap — diagram order, aliases, references, links, types — tests/unit/service_layer/test_plantuml.py
- plantuml.xǁPlantumlGeneratorǁalias__mutmut_2 — gap — diagram order, aliases, references, links, types — tests/unit/service_layer/test_plantuml.py
- plantuml.xǁPlantumlGeneratorǁreferences__mutmut_12 — gap — diagram order, aliases, references, links, types — tests/unit/service_layer/test_plantuml.py
- plantuml.xǁPlantumlGeneratorǁreferences__mutmut_14 — gap — diagram order, aliases, references, links, types — tests/unit/service_layer/test_plantuml.py
- plantuml.xǁPlantumlGeneratorǁoverview__mutmut_5 — gap — diagram order, aliases, references, links, types — tests/unit/service_layer/test_plantuml.py
- plantuml.xǁPlantumlGeneratorǁoverview__mutmut_21 — gap — diagram order, aliases, references, links, types — tests/unit/service_layer/test_plantuml.py
- plantuml.xǁPlantumlGeneratorǁoverview__mutmut_23 — gap — diagram order, aliases, references, links, types — tests/unit/service_layer/test_plantuml.py
- plantuml.xǁPlantumlGeneratorǁoverview__mutmut_45 — gap — diagram order, aliases, references, links, types — tests/unit/service_layer/test_plantuml.py
- plantuml.xǁPlantumlGeneratorǁoverview__mutmut_51 — gap — diagram order, aliases, references, links, types — tests/unit/service_layer/test_plantuml.py
- plantuml.xǁPlantumlGeneratorǁoverview__mutmut_53 — gap — diagram order, aliases, references, links, types — tests/unit/service_layer/test_plantuml.py
- plantuml.xǁPlantumlGeneratorǁoverview__mutmut_55 — gap — diagram order, aliases, references, links, types — tests/unit/service_layer/test_plantuml.py
- plantuml.xǁPlantumlGeneratorǁoverview__mutmut_57 — gap — diagram order, aliases, references, links, types — tests/unit/service_layer/test_plantuml.py
- plantuml.xǁPlantumlGeneratorǁoverview__mutmut_58 — gap — diagram order, aliases, references, links, types — tests/unit/service_layer/test_plantuml.py
- plantuml.xǁPlantumlGeneratorǁoutputs__mutmut_2 — gap — diagram order, aliases, references, links, types — tests/unit/service_layer/test_plantuml.py
- plantuml.xǁPlantumlGeneratorǁoutputs__mutmut_4 — gap — diagram order, aliases, references, links, types — tests/unit/service_layer/test_plantuml.py
- plantuml.xǁPlantumlGeneratorǁoutputs__mutmut_5 — gap — diagram order, aliases, references, links, types — tests/unit/service_layer/test_plantuml.py
- plantuml.xǁPlantumlGeneratorǁoutputs__mutmut_6 — gap — diagram order, aliases, references, links, types — tests/unit/service_layer/test_plantuml.py
- plantuml.xǁPlantumlGeneratorǁtypes__mutmut_5 — gap — diagram order, aliases, references, links, types — tests/unit/service_layer/test_plantuml.py
- plantuml.xǁPlantumlGeneratorǁtypes__mutmut_9 — gap — diagram order, aliases, references, links, types — tests/unit/service_layer/test_plantuml.py
- plantuml.xǁPlantumlGeneratorǁtypes__mutmut_11 — gap — diagram order, aliases, references, links, types — tests/unit/service_layer/test_plantuml.py
- plantuml.xǁPlantumlGeneratorǁtypes__mutmut_18 — gap — diagram order, aliases, references, links, types — tests/unit/service_layer/test_plantuml.py
- plantuml.x__alias_order__mutmut_1 — gap — diagram order, aliases, references, links, types — tests/unit/service_layer/test_plantuml.py
- document.xǁDocumentGeneratorǁvisit_property__mutmut_6 — gap — cardinality, parents, sample note, failures, untyped, hidden, skipped — tests/unit/service_layer/test_document.py
- document.xǁDocumentGeneratorǁvisit_property__mutmut_7 — gap — cardinality, parents, sample note, failures, untyped, hidden, skipped — tests/unit/service_layer/test_document.py
- document.xǁDocumentGeneratorǁvisit_property__mutmut_8 — gap — cardinality, parents, sample note, failures, untyped, hidden, skipped — tests/unit/service_layer/test_document.py
- document.xǁDocumentGeneratorǁvisit_property__mutmut_9 — gap — cardinality, parents, sample note, failures, untyped, hidden, skipped — tests/unit/service_layer/test_document.py
- document.xǁDocumentGeneratorǁend_class__mutmut_5 — gap — cardinality, parents, sample note, failures, untyped, hidden, skipped — tests/unit/service_layer/test_document.py
- document.xǁDocumentGeneratorǁend_class__mutmut_7 — gap — cardinality, parents, sample note, failures, untyped, hidden, skipped — tests/unit/service_layer/test_document.py
- document.xǁDocumentGeneratorǁend_class__mutmut_9 — gap — cardinality, parents, sample note, failures, untyped, hidden, skipped — tests/unit/service_layer/test_document.py
- document.xǁDocumentGeneratorǁend_class__mutmut_19 — gap — cardinality, parents, sample note, failures, untyped, hidden, skipped — tests/unit/service_layer/test_document.py
- document.xǁDocumentGeneratorǁend_class__mutmut_30 — gap — cardinality, parents, sample note, failures, untyped, hidden, skipped — tests/unit/service_layer/test_document.py
- document.xǁDocumentGeneratorǁend_class__mutmut_37 — gap — cardinality, parents, sample note, failures, untyped, hidden, skipped — tests/unit/service_layer/test_document.py
- document.xǁDocumentGeneratorǁend_class__mutmut_45 — gap — cardinality, parents, sample note, failures, untyped, hidden, skipped — tests/unit/service_layer/test_document.py
- document.xǁDocumentGeneratorǁend_class__mutmut_47 — gap — cardinality, parents, sample note, failures, untyped, hidden, skipped — tests/unit/service_layer/test_document.py
- document.xǁDocumentGeneratorǁend_class__mutmut_48 — gap — cardinality, parents, sample note, failures, untyped, hidden, skipped — tests/unit/service_layer/test_document.py
- document.xǁDocumentGeneratorǁend_class__mutmut_49 — gap — cardinality, parents, sample note, failures, untyped, hidden, skipped — tests/unit/service_layer/test_document.py
- document.xǁDocumentGeneratorǁend_class__mutmut_50 — gap — cardinality, parents, sample note, failures, untyped, hidden, skipped — tests/unit/service_layer/test_document.py
- document.xǁDocumentGeneratorǁend_class__mutmut_51 — gap — cardinality, parents, sample note, failures, untyped, hidden, skipped — tests/unit/service_layer/test_document.py
- document.xǁDocumentGeneratorǁend_profile__mutmut_13 — gap — cardinality, parents, sample note, failures, untyped, hidden, skipped — tests/unit/service_layer/test_document.py
- document.xǁDocumentGeneratorǁend_profile__mutmut_15 — gap — cardinality, parents, sample note, failures, untyped, hidden, skipped — tests/unit/service_layer/test_document.py
- document.xǁDocumentGeneratorǁend_profile__mutmut_19 — gap — cardinality, parents, sample note, failures, untyped, hidden, skipped — tests/unit/service_layer/test_document.py
- document.xǁDocumentGeneratorǁend_profile__mutmut_21 — gap — cardinality, parents, sample note, failures, untyped, hidden, skipped — tests/unit/service_layer/test_document.py
- document.xǁDocumentGeneratorǁend_profile__mutmut_23 — gap — cardinality, parents, sample note, failures, untyped, hidden, skipped — tests/unit/service_layer/test_document.py
- document.xǁDocumentGeneratorǁend_profile__mutmut_25 — gap — cardinality, parents, sample note, failures, untyped, hidden, skipped — tests/unit/service_layer/test_document.py
- document.xǁDocumentGeneratorǁend_profile__mutmut_27 — gap — cardinality, parents, sample note, failures, untyped, hidden, skipped — tests/unit/service_layer/test_document.py
- document.xǁDocumentGeneratorǁend_profile__mutmut_29 — gap — cardinality, parents, sample note, failures, untyped, hidden, skipped — tests/unit/service_layer/test_document.py
- document.xǁDocumentGeneratorǁend_profile__mutmut_31 — gap — cardinality, parents, sample note, failures, untyped, hidden, skipped — tests/unit/service_layer/test_document.py
- document.xǁDocumentGeneratorǁend_profile__mutmut_33 — gap — cardinality, parents, sample note, failures, untyped, hidden, skipped — tests/unit/service_layer/test_document.py
- document.xǁDocumentGeneratorǁend_profile__mutmut_34 — gap — cardinality, parents, sample note, failures, untyped, hidden, skipped — tests/unit/service_layer/test_document.py
- document.xǁDocumentGeneratorǁend_profile__mutmut_35 — gap — cardinality, parents, sample note, failures, untyped, hidden, skipped — tests/unit/service_layer/test_document.py
- document.xǁDocumentGeneratorǁend_profile__mutmut_36 — gap — cardinality, parents, sample note, failures, untyped, hidden, skipped — tests/unit/service_layer/test_document.py
- document.xǁDocumentGeneratorǁend_profile__mutmut_37 — gap — cardinality, parents, sample note, failures, untyped, hidden, skipped — tests/unit/service_layer/test_document.py
- document.xǁDocumentGeneratorǁend_profile__mutmut_38 — gap — cardinality, parents, sample note, failures, untyped, hidden, skipped — tests/unit/service_layer/test_document.py
- document.xǁDocumentGeneratorǁend_profile__mutmut_39 — gap — cardinality, parents, sample note, failures, untyped, hidden, skipped — tests/unit/service_layer/test_document.py
- document.xǁDocumentGeneratorǁend_profile__mutmut_46 — gap — cardinality, parents, sample note, failures, untyped, hidden, skipped — tests/unit/service_layer/test_document.py
- document.xǁDocumentGeneratorǁend_profile__mutmut_64 — equivalent — Settings holds str/int/float/bool/list only: json and python dumps print the same
- document.xǁDocumentGeneratorǁend_profile__mutmut_65 — equivalent — Settings holds str/int/float/bool/list only: json and python dumps print the same
- document.xǁDocumentGeneratorǁend_profile__mutmut_66 — equivalent — Settings holds str/int/float/bool/list only: json and python dumps print the same
- document.xǁDocumentGeneratorǁend_profile__mutmut_80 — gap — cardinality, parents, sample note, failures, untyped, hidden, skipped — tests/unit/service_layer/test_document.py
- document.xǁDocumentGeneratorǁend_profile__mutmut_86 — gap — cardinality, parents, sample note, failures, untyped, hidden, skipped — tests/unit/service_layer/test_document.py
- document.xǁDocumentGeneratorǁend_profile__mutmut_100 — gap — cardinality, parents, sample note, failures, untyped, hidden, skipped — tests/unit/service_layer/test_document.py
- document.xǁDocumentGeneratorǁend_profile__mutmut_104 — gap — cardinality, parents, sample note, failures, untyped, hidden, skipped — tests/unit/service_layer/test_document.py
- shacl.xǁShaclGeneratorǁ__init____mutmut_15 — equivalent — reset in visit_graph before use
- shacl.xǁShaclGeneratorǁ__init____mutmut_16 — equivalent — reset in visit_graph before use
- shacl.xǁShaclGeneratorǁ__init____mutmut_17 — equivalent — reset in visit_graph before use
- shacl.xǁShaclGeneratorǁvisit_graph__mutmut_7 — equivalent — declared parents always mirror graph.declared_subclass_edges; the second union adds nothing (redundant code)
- shacl.xǁShaclGeneratorǁvisit_graph__mutmut_8 — equivalent — declared parents always mirror graph.declared_subclass_edges; the second union adds nothing (redundant code)
- shacl.xǁShaclGeneratorǁvisit_graph__mutmut_9 — gap — severity, annotations, value constraints, comments — tests/unit/service_layer/test_shacl.py
- shacl.xǁShaclGeneratorǁvisit_property__mutmut_4 — gap — severity, annotations, value constraints, comments — tests/unit/service_layer/test_shacl.py
- shacl.xǁShaclGeneratorǁvisit_property__mutmut_9 — gap — severity, annotations, value constraints, comments — tests/unit/service_layer/test_shacl.py
- shacl.xǁShaclGeneratorǁvisit_property__mutmut_11 — equivalent — has_class is only read when the property is labelled
- shacl.xǁShaclGeneratorǁvisit_property__mutmut_32 — gap — severity, annotations, value constraints, comments — tests/unit/service_layer/test_shacl.py
- shacl.xǁShaclGeneratorǁend_class__mutmut_20 — gap — severity, annotations, value constraints, comments — tests/unit/service_layer/test_shacl.py
- shacl.xǁShaclGeneratorǁend_class__mutmut_23 — gap — severity, annotations, value constraints, comments — tests/unit/service_layer/test_shacl.py
- shacl.xǁShaclGeneratorǁend_class__mutmut_24 — gap — severity, annotations, value constraints, comments — tests/unit/service_layer/test_shacl.py
- shacl.xǁShaclGeneratorǁend_class__mutmut_34 — gap — severity, annotations, value constraints, comments — tests/unit/service_layer/test_shacl.py
- shacl.xǁShaclGeneratorǁend_graph__mutmut_14 — gap — severity, annotations, value constraints, comments — tests/unit/service_layer/test_shacl.py
- shacl.xǁShaclGeneratorǁvalues__mutmut_3 — equivalent — None and False are both falsy at the only read
- shacl.xǁShaclGeneratorǁvalues__mutmut_12 — gap — severity, annotations, value constraints, comments — tests/unit/service_layer/test_shacl.py
- shacl.xǁShaclGeneratorǁvalues__mutmut_13 — gap — severity, annotations, value constraints, comments — tests/unit/service_layer/test_shacl.py
- shacl.xǁShaclGeneratorǁvalues__mutmut_22 — gap — severity, annotations, value constraints, comments — tests/unit/service_layer/test_shacl.py
- shacl.xǁShaclGeneratorǁvalue_constraints__mutmut_4 — gap — severity, annotations, value constraints, comments — tests/unit/service_layer/test_shacl.py
- shacl.xǁShaclGeneratorǁvalue_constraints__mutmut_14 — gap — severity, annotations, value constraints, comments — tests/unit/service_layer/test_shacl.py
- shacl.xǁShaclGeneratorǁvalue_constraints__mutmut_34 — gap — severity, annotations, value constraints, comments — tests/unit/service_layer/test_shacl.py
- shacl.xǁShaclGeneratorǁvalue_constraints__mutmut_39 — gap — severity, annotations, value constraints, comments — tests/unit/service_layer/test_shacl.py
- shacl.xǁShaclGeneratorǁvalue_constraints__mutmut_45 — gap — severity, annotations, value constraints, comments — tests/unit/service_layer/test_shacl.py
- shacl.xǁShaclGeneratorǁseverity__mutmut_4 — equivalent — a labelled property always has confidence and label_support
- shacl.xǁShaclGeneratorǁseverity__mutmut_5 — gap — severity, annotations, value constraints, comments — tests/unit/service_layer/test_shacl.py
- shacl.xǁShaclGeneratorǁseverity__mutmut_8 — equivalent — a labelled property always has confidence and label_support
- shacl.xǁShaclGeneratorǁseverity__mutmut_14 — gap — severity, annotations, value constraints, comments — tests/unit/service_layer/test_shacl.py
- generator.x_graph_slug__mutmut_6 — gap — framework walk, renderer arguments, slug/label rules — tests/unit/service_layer/test_generator.py
- generator.x_graph_slug__mutmut_8 — gap — framework walk, renderer arguments, slug/label rules — tests/unit/service_layer/test_generator.py
- generator.x_graph_slug__mutmut_16 — gap — framework walk, renderer arguments, slug/label rules — tests/unit/service_layer/test_generator.py
- generator.x_graph_slug__mutmut_30 — equivalent — the name is lower-cased, so strip("X") strips nothing
- generator.x_graph_slug__mutmut_31 — gap — framework walk, renderer arguments, slug/label rules — tests/unit/service_layer/test_generator.py
- generator.x_graph_slug__mutmut_32 — gap — framework walk, renderer arguments, slug/label rules — tests/unit/service_layer/test_generator.py
- generator.x_graph_slug__mutmut_33 — gap — framework walk, renderer arguments, slug/label rules — tests/unit/service_layer/test_generator.py
- generator.x_plain_label__mutmut_5 — gap — framework walk, renderer arguments, slug/label rules — tests/unit/service_layer/test_generator.py
- generator.xǁGeneratorǁaccepts__mutmut_4 — cosmetic — log text; the test pins that the IRI is logged, no contract fixes the wording
- generator.xǁGeneratorǁaccepts__mutmut_6 — cosmetic — log text; the test pins that the IRI is logged, no contract fixes the wording
- generator.xǁGeneratorǁaccepts__mutmut_7 — cosmetic — log text; the test pins that the IRI is logged, no contract fixes the wording
- generator.xǁGeneratorǁnamespace__mutmut_1 — gap — framework walk, renderer arguments, slug/label rules — tests/unit/service_layer/test_generator.py
- generator.xǁGeneratorǁnamespace__mutmut_3 — gap — framework walk, renderer arguments, slug/label rules — tests/unit/service_layer/test_generator.py
- generator.xǁGeneratorǁlabel__mutmut_4 — dead — Generator.namespaces / used_namespaces() are never read (grep: no caller in fingerprint/ or tests/)
- generator.xǁGeneratorǁview__mutmut_5 — gap — framework walk, renderer arguments, slug/label rules — tests/unit/service_layer/test_generator.py
- generator.xǁGeneratorǁview__mutmut_15 — gap — framework walk, renderer arguments, slug/label rules — tests/unit/service_layer/test_generator.py
- generator.xǁGeneratorǁview__mutmut_23 — gap — framework walk, renderer arguments, slug/label rules — tests/unit/service_layer/test_generator.py
- generator.xǁGeneratorǁview__mutmut_36 — gap — framework walk, renderer arguments, slug/label rules — tests/unit/service_layer/test_generator.py
- generator.xǁGeneratorǁview__mutmut_53 — gap — framework walk, renderer arguments, slug/label rules — tests/unit/service_layer/test_generator.py
- generator.xǁGeneratorǁoutputs__mutmut_5 — gap — framework walk, renderer arguments, slug/label rules — tests/unit/service_layer/test_generator.py
- generator.xǁGeneratorǁoutputs__mutmut_8 — gap — framework walk, renderer arguments, slug/label rules — tests/unit/service_layer/test_generator.py
- generator.xǁGeneratorǁoutputs__mutmut_12 — gap — framework walk, renderer arguments, slug/label rules — tests/unit/service_layer/test_generator.py
- generator.xǁGeneratorǁoutputs__mutmut_13 — gap — framework walk, renderer arguments, slug/label rules — tests/unit/service_layer/test_generator.py
- generator.xǁGeneratorǁoutputs__mutmut_14 — gap — framework walk, renderer arguments, slug/label rules — tests/unit/service_layer/test_generator.py
- generator.xǁGeneratorǁserialize__mutmut_4 — gap — framework walk, renderer arguments, slug/label rules — tests/unit/service_layer/test_generator.py
- generator.xǁGeneratorǁserialize__mutmut_6 — gap — framework walk, renderer arguments, slug/label rules — tests/unit/service_layer/test_generator.py
- generator.xǁGeneratorǁserialize__mutmut_9 — gap — framework walk, renderer arguments, slug/label rules — tests/unit/service_layer/test_generator.py
- generator.xǁGeneratorǁserialize__mutmut_11 — gap — framework walk, renderer arguments, slug/label rules — tests/unit/service_layer/test_generator.py
- generator.xǁGeneratorǁwrite__mutmut_5 — gap — framework walk, renderer arguments, slug/label rules — tests/unit/service_layer/test_generator.py
- generator.xǁGeneratorǁwrite__mutmut_7 — gap — framework walk, renderer arguments, slug/label rules — tests/unit/service_layer/test_generator.py
- generator.xǁGeneratorǁwrite__mutmut_8 — gap — framework walk, renderer arguments, slug/label rules — tests/unit/service_layer/test_generator.py
- generator.xǁGeneratorǁwrite__mutmut_12 — gap — framework walk, renderer arguments, slug/label rules — tests/unit/service_layer/test_generator.py
- generator.xǁGeneratorǁwrite__mutmut_14 — gap — framework walk, renderer arguments, slug/label rules — tests/unit/service_layer/test_generator.py
- generator.xǁGeneratorǁwrite__mutmut_15 — gap — framework walk, renderer arguments, slug/label rules — tests/unit/service_layer/test_generator.py
- shacl.xǁShaclGeneratorǁshape__mutmut_14 — gap — `not in` never terminates: killed by timeout, any test of shape names reaches it
- generator.xǁGeneratorǁused_namespaces__mutmut_1 — dead — Generator.used_namespaces() has no caller in fingerprint/ or tests/
- generator.xǁGeneratorǁused_namespaces__mutmut_2 — dead — Generator.used_namespaces() has no caller in fingerprint/ or tests/
- generator.xǁGeneratorǁused_namespaces__mutmut_3 — dead — Generator.used_namespaces() has no caller in fingerprint/ or tests/
- generator.xǁGeneratorǁused_namespaces__mutmut_4 — dead — Generator.used_namespaces() has no caller in fingerprint/ or tests/
- generator.xǁGeneratorǁused_namespaces__mutmut_5 — dead — Generator.used_namespaces() has no caller in fingerprint/ or tests/
- document.xǁDocumentGeneratorǁterm__mutmut_1 — dead — DocumentGenerator.term() has no caller (the document builds DocumentTerm directly)
- document.xǁDocumentGeneratorǁterm__mutmut_2 — dead — DocumentGenerator.term() has no caller (the document builds DocumentTerm directly)
- document.xǁDocumentGeneratorǁterm__mutmut_3 — dead — DocumentGenerator.term() has no caller (the document builds DocumentTerm directly)
- document.xǁDocumentGeneratorǁterm__mutmut_4 — dead — DocumentGenerator.term() has no caller (the document builds DocumentTerm directly)
- document.xǁDocumentGeneratorǁterm__mutmut_5 — dead — DocumentGenerator.term() has no caller (the document builds DocumentTerm directly)

## service_layer.handlers

Survivors re-checked on the current tree: 30 (before). After the new tests: 1 (equivalent).

| module | before | gap | equivalent | cosmetic | dead |
|---|---|---|---|---|---|
| handlers | 30 | 23 | 1 | 6 | 0 |

Log-text mutants are cosmetic (no contract fixes the wording); the new tests pin the messages anyway, so mutmut no longer lists them.

### Per mutant (`fingerprint.service_layer.handlers.x_fingerprint_report__mutmut_N`; tests in tests/unit/service_layer/test_handlers.py)

- handlers.x_fingerprint_report__mutmut_4 — gap — usage message names the folder
- handlers.x_fingerprint_report__mutmut_6 — gap — options validated before any query
- handlers.x_fingerprint_report__mutmut_9 — gap — default client gets the endpoint
- handlers.x_fingerprint_report__mutmut_10 — gap — default client gets the settings timeout
- handlers.x_fingerprint_report__mutmut_23 — gap — prefix.cc source reaches resolution
- handlers.x_fingerprint_report__mutmut_25 — gap — user prefixes reach resolution
- handlers.x_fingerprint_report__mutmut_26 — gap — prefix.cc source reaches resolution
- handlers.x_fingerprint_report__mutmut_32 — gap — an injected renderer is used
- handlers.x_fingerprint_report__mutmut_33 — gap — an injected renderer is used
- handlers.x_fingerprint_report__mutmut_34 — gap — the `doc` format is noted, not rendered twice
- handlers.x_fingerprint_report__mutmut_35 — cosmetic — log text
- handlers.x_fingerprint_report__mutmut_36 — cosmetic — log text
- handlers.x_fingerprint_report__mutmut_37 — cosmetic — log text
- handlers.x_fingerprint_report__mutmut_43 — gap — options reach the document
- handlers.x_fingerprint_report__mutmut_44 — gap — renderer reaches the document
- handlers.x_fingerprint_report__mutmut_49 — gap — options reach the document
- handlers.x_fingerprint_report__mutmut_50 — gap — renderer reaches the document
- handlers.x_fingerprint_report__mutmut_56 — gap — options reach the other formats
- handlers.x_fingerprint_report__mutmut_57 — gap — renderer reaches the other formats
- handlers.x_fingerprint_report__mutmut_58 — equivalent — check_filters=None is falsy like False (`if check_filters:` only)
- handlers.x_fingerprint_report__mutmut_62 — gap — options reach the other formats
- handlers.x_fingerprint_report__mutmut_63 — gap — renderer reaches the other formats
- handlers.x_fingerprint_report__mutmut_64 — gap — filters are warned once, not per format
- handlers.x_fingerprint_report__mutmut_65 — gap — filters are warned once, not per format
- handlers.x_fingerprint_report__mutmut_67 — gap — failure log names the report
- handlers.x_fingerprint_report__mutmut_72 — cosmetic — log text
- handlers.x_fingerprint_report__mutmut_75 — gap — outcome log names the report
- handlers.x_fingerprint_report__mutmut_76 — cosmetic — log text
- handlers.x_fingerprint_report__mutmut_77 — gap — outcome log names the report
- handlers.x_fingerprint_report__mutmut_78 — cosmetic — log text

## service_layer.prefixes, settings, representations

Survivors re-checked on the current tree: prefixes 27, settings 19, representations 14 (baseline 27, 19, 18). After the new tests: prefixes 22 (5 equivalent, 17 cosmetic), settings 2 (dead), representations 0.

| module | before | gap | equivalent | cosmetic | dead |
|---|---|---|---|---|---|
| prefixes | 27 | 5 | 5 | 17 | 0 |
| settings | 19 | 17 | 0 | 0 | 2 |
| representations | 14 | 14 | 0 | 0 | 0 |

User-facing usage and warning messages are gaps (the specs state them); only debug log text is cosmetic.

### Per mutant (`fingerprint.service_layer.` omitted; the number is the `__mutmut_N` suffix)

- prefixes.x__iris__mutmut_2 — equivalent — NamespacePrefix and Settings hold no IRI-named field, so skipping them never changes what is yielded
- prefixes.x__iris__mutmut_4 — equivalent — NamespacePrefix and Settings hold no IRI-named field, so skipping them never changes what is yielded
- prefixes.x__iris__mutmut_5 — equivalent — NamespacePrefix and Settings hold no IRI-named field, so skipping them never changes what is yielded
- prefixes.x__iris__mutmut_7 — equivalent — NamespacePrefix and Settings hold no IRI-named field, so skipping them never changes what is yielded
- prefixes.x__iris__mutmut_8 — equivalent — NamespacePrefix and Settings hold no IRI-named field, so skipping them never changes what is yielded
- prefixes.x__writable__mutmut_2 — gap — an unwritable namespace is not in use — tests/unit/service_layer/test_prefixes.py
- prefixes.x_resolve_namespaces__mutmut_11 — gap — an unused namespace must not hold a prefix — tests/unit/service_layer/test_prefixes.py
- prefixes.x_resolve_namespaces__mutmut_28 — cosmetic — debug log text and arguments
- prefixes.x_resolve_namespaces__mutmut_29 — cosmetic — debug log text and arguments
- prefixes.x_resolve_namespaces__mutmut_30 — cosmetic — debug log text and arguments
- prefixes.x_resolve_namespaces__mutmut_31 — cosmetic — debug log text and arguments
- prefixes.x_resolve_namespaces__mutmut_32 — cosmetic — debug log text and arguments
- prefixes.x_resolve_namespaces__mutmut_33 — cosmetic — debug log text and arguments
- prefixes.x_resolve_namespaces__mutmut_34 — cosmetic — debug log text and arguments
- prefixes.x_resolve_namespaces__mutmut_35 — cosmetic — debug log text and arguments
- prefixes.x_resolve_namespaces__mutmut_36 — cosmetic — debug log text and arguments
- prefixes.x_resolve_namespaces__mutmut_37 — gap — an invalid, reserved or taken entry must not end its source — tests/unit/service_layer/test_prefixes.py
- prefixes.x_resolve_namespaces__mutmut_45 — cosmetic — debug log text and arguments
- prefixes.x_resolve_namespaces__mutmut_46 — cosmetic — debug log text and arguments
- prefixes.x_resolve_namespaces__mutmut_47 — cosmetic — debug log text and arguments
- prefixes.x_resolve_namespaces__mutmut_48 — cosmetic — debug log text and arguments
- prefixes.x_resolve_namespaces__mutmut_49 — cosmetic — debug log text and arguments
- prefixes.x_resolve_namespaces__mutmut_50 — cosmetic — debug log text and arguments
- prefixes.x_resolve_namespaces__mutmut_51 — cosmetic — debug log text and arguments
- prefixes.x_resolve_namespaces__mutmut_52 — cosmetic — debug log text and arguments
- prefixes.x_resolve_namespaces__mutmut_53 — gap — an invalid, reserved or taken entry must not end its source — tests/unit/service_layer/test_prefixes.py
- prefixes.x_resolve_namespaces__mutmut_76 — gap — the prefix.cc warning wording is asserted exactly — tests/unit/service_layer/test_prefixes.py
- settings.x_load_config_file__mutmut_2 — gap — usage message text, one line per field, origin named — tests/unit/service_layer/test_settings.py
- settings.x_load_config_file__mutmut_3 — gap — usage message text, one line per field, origin named — tests/unit/service_layer/test_settings.py
- settings.x_describe__mutmut_2 — gap — usage message text, one line per field, origin named — tests/unit/service_layer/test_settings.py
- settings.x_describe__mutmut_3 — gap — usage message text, one line per field, origin named — tests/unit/service_layer/test_settings.py
- settings.x_describe__mutmut_5 — gap — usage message text, one line per field, origin named — tests/unit/service_layer/test_settings.py
- settings.x_describe__mutmut_12 — gap — usage message text, one line per field, origin named — tests/unit/service_layer/test_settings.py
- settings.x_describe__mutmut_13 — gap — usage message text, one line per field, origin named — tests/unit/service_layer/test_settings.py
- settings.x_check_acceptance_threshold__mutmut_7 — gap — usage message text, one line per field, origin named — tests/unit/service_layer/test_settings.py
- settings.x_validate_endpoint__mutmut_9 — gap — usage message text, one line per field, origin named — tests/unit/service_layer/test_settings.py
- settings.x_load_user_prefixes__mutmut_8 — gap — usage message text, one line per field, origin named — tests/unit/service_layer/test_settings.py
- settings.x_load_user_prefixes__mutmut_12 — gap — usage message text, one line per field, origin named — tests/unit/service_layer/test_settings.py
- settings.x_load_user_prefixes__mutmut_17 — gap — usage message text, one line per field, origin named — tests/unit/service_layer/test_settings.py
- settings.x__override__mutmut_4 — gap — usage message text, one line per field, origin named — tests/unit/service_layer/test_settings.py
- settings.x__environment__mutmut_7 — gap — usage message text, one line per field, origin named — tests/unit/service_layer/test_settings.py
- settings.x__environment__mutmut_8 — gap — usage message text, one line per field, origin named — tests/unit/service_layer/test_settings.py
- settings.x_resolve_settings__mutmut_1 — gap — usage message text, one line per field, origin named — tests/unit/service_layer/test_settings.py
- settings.x_resolve_settings__mutmut_8 — gap — usage message text, one line per field, origin named — tests/unit/service_layer/test_settings.py
- settings.x_resolve_settings__mutmut_27 — dead — the merged values were each validated by their own source, so the final Settings(...) cannot fail
- settings.x_resolve_settings__mutmut_28 — dead — the merged values were each validated by their own source, so the final Settings(...) cannot fail
- representations.x_validate_options__mutmut_6 — gap — usage message, option bounds, namespace table and filters — tests/unit/service_layer/test_representations.py
- representations.x_validate_options__mutmut_7 — gap — usage message, option bounds, namespace table and filters — tests/unit/service_layer/test_representations.py
- representations.x_validate_options__mutmut_8 — gap — usage message, option bounds, namespace table and filters — tests/unit/service_layer/test_representations.py
- representations.x_validate_options__mutmut_9 — gap — usage message, option bounds, namespace table and filters — tests/unit/service_layer/test_representations.py
- representations.x_validate_options__mutmut_10 — gap — usage message, option bounds, namespace table and filters — tests/unit/service_layer/test_representations.py
- representations.x_warn_unknown_filters__mutmut_3 — gap — usage message, option bounds, namespace table and filters — tests/unit/service_layer/test_representations.py
- representations.x_warn_unknown_filters__mutmut_11 — gap — usage message, option bounds, namespace table and filters — tests/unit/service_layer/test_representations.py
- representations.x_warn_unknown_filters__mutmut_13 — gap — usage message, option bounds, namespace table and filters — tests/unit/service_layer/test_representations.py
- representations.x_warn_unknown_filters__mutmut_14 — gap — usage message, option bounds, namespace table and filters — tests/unit/service_layer/test_representations.py
- representations.x_make_generator__mutmut_9 — gap — usage message, option bounds, namespace table and filters — tests/unit/service_layer/test_representations.py
- representations.x_generate_representations__mutmut_2 — gap — usage message, option bounds, namespace table and filters — tests/unit/service_layer/test_representations.py
- representations.x_generate_representations__mutmut_7 — gap — usage message, option bounds, namespace table and filters — tests/unit/service_layer/test_representations.py
- representations.x_generate_representations__mutmut_9 — gap — usage message, option bounds, namespace table and filters — tests/unit/service_layer/test_representations.py
- representations.x_generate_representations__mutmut_11 — gap — usage message, option bounds, namespace table and filters — tests/unit/service_layer/test_representations.py

## Lead decisions on the service-layer findings (2026-11-01)

- Deleted as dead (no caller in `fingerprint/`, `tests/` or the templates; GitNexus impact: 0 callers,
  LOW): `Generator.used_namespaces()` with the `Generator.namespaces` dict it read, and
  `DocumentGenerator.term()`.
- Not changed (defensive or redundant rather than unreachable; follow-ups for the developer): the final
  `ValidationError` handler in `resolve_settings`; the declared-parents union in
  `ShaclGenerator.visit_graph` (mirrors `declared_subclass_edges`); the `module_size < 1` guard in
  `validate_options` (only reachable through `model_construct`).
