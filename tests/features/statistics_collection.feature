# Capability: statistics-collection (openspec/specs/statistics-collection)
# Error rows: openspec/changes/archive/2026-10-31-harden-fingerprinter/design.md "Error matrix". Step definitions are written during implementation.
Feature: Collecting raw statistics from a knowledge graph
  As a data steward
  I want the structure of every class in my knowledge graph measured from its data
  So that I can see the application profile the data actually follows, even on large graphs

  Background:
    Given a SPARQL endpoint holding a knowledge graph
    And the default collection settings

  Rule: Graphs and classes are discovered cheaply first

    Scenario: The default graph and every named graph are profiled
      Given the endpoint holds data in the default graph and in two named graphs
      And no graph is selected
      When the knowledge graph is fingerprinted
      Then the profile contains three graphs
      And the default graph comes first

    Scenario: Only the selected graphs are profiled
      Given the endpoint holds data in the default graph and in two named graphs
      And only the named graph "http://example.org/graph/a" is selected
      When the knowledge graph is fingerprinted
      Then the profile contains exactly that graph

    Scenario: Class counts fall back to counting class by class
      Given counting all classes of a graph at once times out
      When the knowledge graph is fingerprinted
      Then each class is counted on its own
      And the instance counts equal those of a single count

    Scenario Outline: The list of named graphs cannot be obtained
      Given the endpoint answers the named-graph listing with <problem>
      And <selection>
      When the knowledge graph is fingerprinted
      Then <graphs profiled>
      And <failure>

      Examples:
        | problem              | selection                                  | graphs profiled                        | failure                                    |
        | a rejection          | no graph is selected                       | only the default graph is profiled     | a failure about listing graphs is recorded |
        | a timeout            | no graph is selected                       | only the default graph is profiled     | a failure about listing graphs is recorded |
        | a rejection          | the named graph "http://example.org/g" is selected | only that graph is profiled    | no failure is recorded                     |

  Rule: Every class is measured on its own instances only

    Scenario: The class is bound inside the measurement
      When the statistics of class "http://example.org/Person" are measured
      Then every measurement for that class reads only instances of "http://example.org/Person"

    Scenario: Type statements are not reported as properties
      Given every instance of "ex:Student" is also typed "ex:Person"
      When the knowledge graph is fingerprinted
      Then no property of "ex:Student" is "rdf:type"
      And the other types of "ex:Student" list "ex:Person"

  Rule: Raw statistics record what was observed

    Scenario: Cardinality histogram per property
      Given class "ex:Person" has 4 instances
      And their numbers of "ex:name" values are 1, 1, 2 and 0
      When the knowledge graph is fingerprinted
      Then the histogram of "ex:name" on "ex:Person" is:
        | values per instance | instances |
        | 1                   | 2         |
        | 2                   | 1         |
      And 4 instances of "ex:Person" were observed

    Scenario: Literal values are split by datatype and language
      Given the "ex:name" values of "ex:Person" are "Ann"@en, "Bo"@en and "Carl"
      When the knowledge graph is fingerprinted
      Then the literal value groups of "ex:name" are:
        | datatype        | language | statements | shortest | longest |
        | rdf:langString  | en       | 2          | 2        | 3       |
        | xsd:string      |          | 1          | 4        | 4       |

    Scenario: Untyped objects are counted
      Given "ex:knows" on "ex:Person" points to one resource typed "ex:Person" and one resource without a type
      When the knowledge graph is fingerprinted
      Then the object groups of "ex:knows" record 1 object of class "ex:Person" and 1 untyped object

    Scenario Outline: Where object types are looked up
      Given an object of "ex:knows" is typed "ex:Person" only in another named graph
      And object types are looked up in <scope>
      When the knowledge graph is fingerprinted
      Then that object is counted as <result>

      Examples:
        | scope          | result                                         |
        | the same graph | untyped                                        |
        | any graph      | of class "ex:Person", typed in the other graph |

  Rule: Precision escalates only when the endpoint cannot answer

    Scenario: A class is read exactly
      Given every measurement of a class answers within the timeout
      When the knowledge graph is fingerprinted
      Then the class is marked "exact"
      And its observed instances equal its instance count

    Scenario: A class too big for an exact read falls back to the first N instances
      Given a class with 50000 instances
      And the exact read of that class times out
      And the first N setting is 10000
      When the knowledge graph is fingerprinted
      Then the class is marked "first 10000 of 50000"
      And its instance count is still 50000

    Scenario: A first-N read uses one sample for every measurement
      Given a class is read in first-N mode
      When its statistics are measured
      Then every measurement of that class uses the same listed instances

    Scenario: A first-N read of a small class equals an exact read
      Given a class with fewer instances than the first N setting
      When it is fingerprinted once with policy "exact" and once with policy "first_n"
      Then both reads give the same histograms, value groups and distinct counts

    Scenario: Blank-node instances weaken the first-N sample
      Given a class whose listed instances include blank nodes
      And the class is read in first-N mode
      When the knowledge graph is fingerprinted
      Then the class is marked as having a sample that may differ between measurements

    Scenario Outline: A forced policy uses only its mode
      Given the precision policy is "<policy>"
      And the exact read of a class times out
      When the knowledge graph is fingerprinted
      Then <outcome>

      Examples:
        | policy  | outcome                                          |
        | exact   | the class is recorded as a failure               |
        | first_n | the class is marked "first N" without an exact try |

  Rule: Failures are visible and never silent

    Scenario: One class fails and the others are still profiled
      Given every read of class "ex:Big" fails
      And all other classes answer
      When the knowledge graph is fingerprinted
      Then the profile contains every other class
      And one failure names "ex:Big", the failed measurement and the number of attempts

    Scenario Outline: Failures in optional measurements keep the class
      Given the <measurement> of a class fails
      When the knowledge graph is fingerprinted
      Then the class is still profiled
      And a failure for the <measurement> is recorded

      Examples:
        | measurement             |
        | top values              |
        | property presence check |
        | incoming links          |

    Scenario: The endpoint rejects a query as malformed
      Given the endpoint rejects a class's measurement as malformed
      When the knowledge graph is fingerprinted
      Then the failure is recorded without retrying
      And the other classes are still profiled

    Scenario: A transient endpoint error is retried
      Given the endpoint answers a measurement with "service unavailable" once
      When the knowledge graph is fingerprinted
      Then the measurement is retried
      And no failure is recorded

    Scenario: An IRI unusable in a query is skipped
      Given a class IRI contains a space
      When the knowledge graph is fingerprinted
      Then that class is skipped with a failure naming the IRI
      And the other classes are still profiled

    Scenario: A first-N query too large for the endpoint
      Given the endpoint rejects queries listing 10000 instances as too large
      When a class falls back to first-N mode
      Then a failure for that class suggests lowering the first N setting

  Rule: Settings are explicit, layered and recorded

    Scenario Outline: Setting precedence
      Given the default timeout is 60 seconds
      And <environment>
      And <command line>
      When the knowledge graph is fingerprinted
      Then the recorded timeout is <timeout> seconds

      Examples:
        | environment                          | command line                     | timeout |
        | no environment variable is set       | no command-line option is given  | 60      |
        | the environment sets the timeout to 10 | no command-line option is given | 10      |
        | the environment sets the timeout to 10 | the command line sets it to 30  | 30      |

    Scenario: A configuration file sets collection options
      Given a configuration file setting concurrency to 2
      When the knowledge graph is fingerprinted with that file
      Then the recorded concurrency is 2

    Scenario: An acceptance threshold of zero is refused
      Given the acceptance threshold is set to 0
      When the knowledge graph is fingerprinted
      Then the run is refused as a usage error

  Rule: Depth and switches decide what is measured

    Scenario Outline: Measurements per depth
      Given the depth is "<depth>"
      When the knowledge graph is fingerprinted
      Then the profile contains <present>
      And the profile contains no <absent>

      Examples:
        | depth       | present                                     | absent                       |
        | classes     | instance counts, hierarchy and other types  | property histograms          |
        | properties  | property histograms                         | value groups                 |
        | values      | value groups and object classes             | top values or incoming links |
        | rich_values | top values                                  | incoming links               |
        | links       | incoming links                              | graph totals                 |

    Scenario: Graph totals are measured only on request
      Given graph statistics are switched on
      When the knowledge graph is fingerprinted
      Then each graph records its statements, distinct subjects, distinct objects, predicates and untyped subjects

    Scenario: A rare property is found by the completeness check
      Given a class is read in first-N mode
      And the completeness check is switched on
      And only an instance outside the first N uses "ex:rare"
      When the knowledge graph is fingerprinted
      Then "ex:rare" is listed on that class as present, without statistics
