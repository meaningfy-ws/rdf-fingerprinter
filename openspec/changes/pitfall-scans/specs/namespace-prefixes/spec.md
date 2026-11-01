## MODIFIED Requirements

### Requirement: Every namespace has a prefix
After collection the fingerprinter SHALL give a prefix to the namespace of each profiled graph IRI,
class, property, value type, parent class and linked class, and of each IRI entity, property and
value in a pitfall example (pitfall-scans DEC-11). The namespace of an IRI SHALL be:
- the IRI up to and including its last `#`, when no `/` follows that `#`;
- otherwise, up to and including its last `/`;
- for a `urn:` IRI with neither, up to and including its last `:`.

No two namespaces SHALL share a prefix, and the table SHALL be identical for identical inputs (EPIC
DEC-1, DEC-2).

#### Scenario: Unknown vocabulary is named
- **WHEN** a profile uses `https://ontology.brainframe.com/2016/04/brainframe#Person` and no prefix source names that namespace
- **THEN** the namespace table holds the generated prefix `brainframe` for `https://ontology.brainframe.com/2016/04/brainframe#`

#### Scenario: A fragment route is not a hash namespace
- **WHEN** a profile uses `https://my.brainframe.com/#/knowledge/Person/7a08`
- **THEN** its namespace is `https://my.brainframe.com/#/knowledge/Person/`

#### Scenario: Deterministic table
- **WHEN** the same profile is resolved twice with the same prefix sources
- **THEN** both namespace tables are equal

#### Scenario: Pitfall examples are named
- **WHEN** a pitfall example's entity is `http://other.org/vocab#thing` and nothing else in the profile uses that namespace
- **THEN** the namespace table holds a prefix for `http://other.org/vocab#`
