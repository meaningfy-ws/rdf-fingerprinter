# Capability: profile-analytics (openspec/specs/profile-analytics)
# Formulas: openspec/changes/archive/2026-10-31-harden-fingerprinter/design.md "Analytics (domain, pure)". Step definitions are written during implementation.
@uc_w1
Feature: Deriving analytics from the raw statistics
  As a data steward
  I want readable indicators computed from the observed statistics
  So that I can judge cardinalities, value types and hierarchy without doing the arithmetic

  Rule: Analytics come from the raw statistics alone

    Scenario: Analytics from a stored profile
      Given a raw profile stored as a file
      And no endpoint is reachable
      When the analytics are computed
      Then they equal the analytics computed right after collection

  Rule: Cardinality statistics keep their 1.x meaning

    Scenario Outline: Statistics from a histogram
      Given <observed> observed instances of a class
      And the histogram of a property is <histogram>
      When the analytics are computed
      Then min is <min>, max is <max>, mean is <mean> and confidence is <confidence>

      Examples:
        | observed | histogram       | min | max | mean | confidence |
        | 4        | 1:2, 2:1        | 0   | 2   | 1.0  | 0.75       |
        | 3        | 1:3             | 1   | 1   | 1.0  | 1.0        |
        | 5        | 2:5             | 2   | 2   | 2.0  | 1.0        |
        | 10       | 1:1             | 0   | 1   | 0.1  | 0.1        |

  Rule: A cardinality label is accepted only above the threshold

    Scenario Outline: Cardinality labels
      Given <observed> observed instances of a class
      And the histogram of a property is <histogram>
      And the acceptance threshold is 0.95
      When the analytics are computed
      Then the label is "<label>" with support <support>
      And the rejected alternatives are "<alternatives>"

      Examples:
        | observed | histogram   | label        | support | alternatives              |
        | 100      | 1:97, 2:3   | exactly_one  | 0.97    |                           |
        | 100      | 1:100       | exactly_one  | 1.0     |                           |
        | 100      | 3:96, 4:4   | exactly_n    | 0.96    | exactly_one               |
        | 100      | 1:50, 2:50  | one_or_more  | 1.0     | exactly_one               |
        | 100      | 1:90        | zero_or_one  | 1.0     | exactly_one               |
        | 4        | 1:2, 2:1    | zero_or_more | 1.0     | one_or_more, zero_or_one  |

  Rule: Value profiles describe what a property points to

    Scenario Outline: Property kind
      Given a property whose objects are <objects>
      When the analytics are computed
      Then its kind is "<kind>"

      Examples:
        | objects                 | kind              |
        | only literals           | datatype_property |
        | only resources          | object_property   |
        | literals and resources  | mixed             |

    Scenario: Identifier-like property
      Given every instance has exactly one value of a property
      And all values are different
      When the analytics are computed
      Then the property is identifier-like

    Scenario: Enumeration candidate
      Given a property has 5 distinct values and the top values setting is 20
      When the analytics are computed
      Then the property is a candidate for a list of allowed values

    Scenario: Entropy of a single repeated value
      Given every value of a property is the same
      When the analytics are computed
      Then its entropy estimate is 0

    Scenario: Ratios without a denominator are absent
      Given a property with no literal values
      When the analytics are computed
      Then its language coverage and mean length are absent

  Rule: The class hierarchy is declared or implied by the data

    Scenario: Implied parent
      Given every observed "ex:Student" is also typed "ex:Person"
      And no subclass statement is declared
      When the analytics are computed
      Then "ex:Person" is an implied parent of "ex:Student"

    Scenario: Inherited and refined properties
      Given "ex:Student" has the parent "ex:Person"
      And "ex:name" is labelled "exactly_one" on both
      And "ex:email" is labelled "zero_or_one" on "ex:Person" and "exactly_one" on "ex:Student"
      When the analytics are computed
      Then on "ex:Student" "ex:name" is inherited and "ex:email" is refined

    Scenario: Mutually implied classes
      Given every observed "ex:A" is an "ex:B" and every observed "ex:B" is an "ex:A"
      When the analytics are computed
      Then each is an implied parent of the other
      And both have the hierarchy depth they would have without those parents

    Scenario: Parent without instances
      Given "ex:Student" is declared a subclass of "ex:Agent"
      And "ex:Agent" has no instances in the graph
      When the analytics are computed
      Then "ex:Agent" is listed as a declared parent of "ex:Student"
      And every property of "ex:Student" is its own

    Scenario: Hierarchy cycle
      Given the declared subclass statements form a cycle between "ex:A" and "ex:B"
      When the analytics are computed
      Then both classes get a finite hierarchy depth

  Rule: Further indicators summarise classes

    Scenario: Label coverage
      Given 80 of 100 instances of a class have "rdfs:label" and 90 have "skos:prefLabel"
      When the analytics are computed
      Then the class's label coverage is 0.9

  Rule: Every number says whether it is exact

    Scenario: First-N class
      Given a class was read in first-N mode
      When the analytics are computed
      Then the class and all its properties are marked not exact

    Scenario: Presence-only property
      Given a property was found only by the completeness check
      When the analytics are computed
      Then it is marked not exact
      And it has no min, max, mean, confidence or label
