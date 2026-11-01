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

    Scenario: Mixed presence
      Given 4 observed instances of a class
      And the histogram of a property is 1:2, 2:1
      When the analytics are computed
      Then min is 0, max is 2, mean is 1.0 and confidence is 0.75
      And the mean when present is 1.33

  Rule: A cardinality label is accepted only above the threshold

    Scenario: Mandatory single value
      Given 100 observed instances of a class
      And the histogram of a property is 1:97, 2:3
      And the acceptance threshold is 0.95
      When the analytics are computed
      Then the label is "exactly_one" with support 0.97
      And the rejected alternatives are ""

    Scenario: Below threshold
      Given 4 observed instances of a class
      And the histogram of a property is 1:2, 2:1
      And the acceptance threshold is 0.95
      When the analytics are computed
      Then the label is "zero_or_more" with support 1.0
      And the rejected alternatives are "one_or_more, zero_or_one"

  Rule: Value profiles describe what a property points to

    Scenario: Mixed property kind
      Given a property whose objects are literals and resources
      When the analytics are computed
      Then its kind is "mixed"

    Scenario: Identifier-like property
      Given every instance has exactly one value of a property
      And all values are different
      When the analytics are computed
      Then the property is identifier-like

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

    Scenario: Parent without a profile
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

    Scenario: Entropy of a single value
      Given every value of a property is the same
      When the analytics are computed
      Then its entropy estimate is 0

  Rule: Every number says whether it is exact

    Scenario: First N class
      Given a class was read in first-N mode
      When the analytics are computed
      Then the class and all its properties are marked not exact

    Scenario: Presence-only property
      Given a property was found only by the completeness check
      When the analytics are computed
      Then it is marked not exact
      And it has no min, max, mean, confidence or label
