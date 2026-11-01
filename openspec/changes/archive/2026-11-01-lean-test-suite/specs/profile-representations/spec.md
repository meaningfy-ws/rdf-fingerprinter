## MODIFIED Requirements

### Requirement: SHACL shapes
The SHACL generator SHALL write one Turtle file per profiled graph with a shown class, with an
open `sh:NodeShape` per shown class (see "Namespace filters"), named by the "Shape IRI policy"
(`sh:targetClass`, no `sh:closed`) holding a `sh:PropertyShape` per property, inherited ones
included (archived change 2026-10-31-profile-representations, DEC-5). Counts SHALL follow the accepted cardinality label; value constraints SHALL follow
the value types (`sh:datatype` for one datatype, `sh:class` for one class, `sh:nodeKind`, `sh:or`
when mixed; a literal without a datatype but with a language counts as `rdf:langString`). Severity
SHALL follow the first matching rule: no cardinality label, or confidence below the acceptance
threshold → `sh:Info`; label support below 1, a class read in first-N mode, `sh:class` when the run looked up object
types across graphs, or a class with declared subclasses → `sh:Warning`; otherwise the default `sh:Violation`. Shapes SHALL be annotated with confidence and observed/total instances, and a first-N
class marked as sampled.

#### Scenario Outline: Severity from the threshold
- **WHEN** at threshold 0.8 a property of a class read in <mode> has <usage>
- **THEN** its property shape has severity <severity>

  Examples:
    | mode    | usage                                     | severity               |
    | exact   | presence only, no cardinality label       | sh:Info                |
    | exact   | confidence 0.3, label support 1.0         | sh:Info                |
    | exact   | confidence 1.0, label support 0.9         | sh:Warning             |
    | first-N | confidence 1.0, label support 1.0         | sh:Warning             |
    | exact   | confidence 1.0, label support 1.0         | sh:Violation (default) |

#### Scenario: Language-tagged literals without a datatype
- **WHEN** a store leaves the datatype of language-tagged literals unbound
- **THEN** the property shape allows `rdf:langString`, and the shapes still conform on that data

#### Scenario Outline: Counts from the cardinality label
- **WHEN** a property's accepted label is <label>
- **THEN** its property shape has <counts>

  Examples:
    | label        | counts                         |
    | exactly_one  | `sh:minCount 1`, `sh:maxCount 1` |
    | zero_or_one  | `sh:maxCount 1` only            |
    | one_or_more  | `sh:minCount 1` only            |
    | zero_or_more | neither                         |
    | exactly_n 3  | `sh:minCount 3`, `sh:maxCount 3` |

#### Scenario: Shapes report no violation on their own data
- **WHEN** the shapes generated from the e2e test data validate that same data with a SHACL engine
- **THEN** no result has severity `sh:Violation` (results at `sh:Warning` and `sh:Info` are expected, so `sh:conforms` may be false) (first-N classes and cross-graph types are at most `sh:Warning`)

#### Scenario: Sampled class is marked
- **WHEN** a class was read in first-N mode
- **THEN** its node shape is annotated with the observed and total instance counts and marked as sampled

#### Scenario: A class with declared subclasses is graded at most Warning
- **WHEN** a class with a declared subclass has a property that every instance has
- **THEN** its property shape has severity `sh:Warning`
