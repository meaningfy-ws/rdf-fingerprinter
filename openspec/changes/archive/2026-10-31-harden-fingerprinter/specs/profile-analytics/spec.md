## ADDED Requirements

### Requirement: Analytics are derived, never collected
Every value of `fingerprint_analytics` SHALL be computed by pure functions from a `fingerprint_stats`
profile, without any endpoint access.

#### Scenario: Analytics from a stored profile
- **WHEN** a raw profile is loaded from JSON with no endpoint available
- **THEN** the analytics are computed and equal those computed right after collection

### Requirement: Cardinality statistics keep today's meaning
For each class and property, min SHALL be 0 when some observed instances lack the property and
otherwise the smallest count; max the largest count; mean the total values divided by the observed
instances (DEC-4). Confidence SHALL be the share of observed instances having the property.

#### Scenario: Mixed presence
- **WHEN** O = 4 and the histogram is `{1: 2, 2: 1}`
- **THEN** min is 0, max is 2, mean is 1.0, mean when present is 1.33 (rounded) and confidence is 0.75

### Requirement: Cardinality label
The analytics SHALL assign one label (`exactly_one`, `exactly_n`, `one_or_more`, `zero_or_one`,
`zero_or_more`) by the rule in `design.md` at the acceptance threshold, and SHALL keep its support
and the rejected stricter labels.

#### Scenario: Mandatory single value
- **WHEN** 97 of 100 instances have exactly one value and 3 have two, threshold 0.95
- **THEN** the label is `exactly_one` with support 0.97 and alternative labels are empty

#### Scenario: Below threshold
- **WHEN** O = 4 and the histogram is `{1: 2, 2: 1}`, threshold 0.95
- **THEN** the label is `zero_or_more` and the alternatives are `one_or_more` and `zero_or_one`

### Requirement: Value profile indicators
The analytics SHALL compute property kind, dominant value type, type purity, untyped object ratio,
languages, language coverage, mean literal length, distinct ratio, identifier-likeness and
enumeration candidacy from the value partitions.

#### Scenario: Mixed property kind
- **WHEN** a property has both literal and IRI objects
- **THEN** its property kind is `mixed`

#### Scenario: Identifier-like property
- **WHEN** every instance has exactly one value and all values are distinct
- **THEN** `is_identifier_like` is true

### Requirement: Hierarchy
The analytics SHALL list each class's parents, declared (`rdfs:subClassOf`) or implied (every
observed instance also has the parent type), and SHALL mark each property `own`, `inherited` or
`refined` relative to the parents.

#### Scenario: Implied parent
- **WHEN** every observed `ex:Student` is also typed `ex:Person` and no subclass edge is declared
- **THEN** `ex:Person` is a parent of `ex:Student` with source `implied`

#### Scenario: Inherited and refined properties
- **WHEN** `ex:Person` and `ex:Student` both have `ex:name` labelled `exactly_one`, and `ex:email` is `zero_or_one` on the parent but `exactly_one` on the child
- **THEN** on `ex:Student`, `ex:name` is `inherited` and `ex:email` is `refined`

#### Scenario: Mutually implied classes
- **WHEN** every observed `ex:A` is an `ex:B` and every observed `ex:B` is an `ex:A`
- **THEN** each is recorded as an implied parent of the other and both have the same hierarchy depth as if neither edge existed

#### Scenario: Parent without a profile
- **WHEN** `ex:Student rdfs:subClassOf ex:Agent` is declared and `ex:Agent` has no instances in the graph
- **THEN** `ex:Agent` is listed as a declared parent and every property of `ex:Student` is `own`

#### Scenario: Hierarchy cycle
- **WHEN** the declared edges contain a cycle A ⊑ B ⊑ A
- **THEN** hierarchy depth is computed without looping and both classes have a finite depth

### Requirement: Further indicators
The analytics SHALL compute the remaining class and graph indicators of `fingerprint_analytics`
(own and mandatory property counts, mean out-degree, label coverage, sample ratio, class and
property counts, typed-subject ratio, vocabularies, cross-graph object types, median, mode,
standard deviation, top-K share, entropy estimate) by the formulas in `design.md`.

#### Scenario: Label coverage
- **WHEN** 80 of 100 instances of a class have `rdfs:label` and 90 have `skos:prefLabel`
- **THEN** its label coverage is 0.9

#### Scenario: Entropy of a single value
- **WHEN** every value of a property is the same
- **THEN** its entropy estimate is 0

### Requirement: Exactness is visible
Every class and property analytics SHALL state whether its numbers are exact (`is_exact` false when
the class was read in first_n mode or a distinct count is a lower bound).

#### Scenario: First N class
- **WHEN** a class was read in first_n mode
- **THEN** the class and every property analytics of that class have `is_exact` false

#### Scenario: Presence-only property
- **WHEN** a property was found only by the completeness check
- **THEN** its analytics have `is_exact` false and no min, max, mean, confidence or label
