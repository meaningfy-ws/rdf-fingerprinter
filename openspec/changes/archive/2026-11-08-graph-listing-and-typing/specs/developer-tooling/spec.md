## ADDED Requirements

### Requirement: Typed package
The distribution SHALL ship a `py.typed` marker in each top-level package, so a type checker reads
the library's annotations (PEP 561, graph-listing-and-typing DEC-3).

#### Scenario: Both packages are typed
- **WHEN** the packages are inspected
- **THEN** `fingerprint/py.typed` and `fingerprint_report_templates/py.typed` exist, and `make check-wheel` requires both in the wheel
