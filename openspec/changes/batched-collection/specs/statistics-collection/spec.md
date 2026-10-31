## ADDED Requirements

### Requirement: Batched results equal exact results
When a class is read in batched mode, its histograms, value partitions and distinct counts SHALL
equal those of an exact read, except distinct counts flagged as lower bounds (EPIC DEC-1). Draft:
the full requirement set is written when this EPIC is shaped.

#### Scenario: Batched equals exact
- **WHEN** the same class on the e2e store is collected once with policy `exact` and once with policy `batched` and batch size 1
- **THEN** the histograms, value partitions and unflagged distinct counts are equal
