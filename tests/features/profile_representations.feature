# Capability: profile-representations (openspec/changes/profile-representations)
# Projected from UC-W2, UC-B2.1 and UC-B2.2 (docs/modules/ROOT/pages/use-cases/).
@uc_w2
Feature: Publishing a fingerprint as an application profile
  As a data steward
  I want SHACL shapes, a class diagram and a profile document from a fingerprint
  So that I can validate, grasp and publish the structure of a knowledge graph without querying it again

  Rule: Representations come from the saved profile alone

    @uc_b2_1
    Scenario: Rendering without an endpoint
      Given a saved profile of the test data
      And an endpoint that fails on any query
      When every representation is generated from the saved profile
      Then the shapes, the diagram and the document are written
      And the endpoint was never queried

    @uc_b2_1
    Scenario: The threshold changes without collecting again
      Given a saved profile with a property whose label support is 0.8
      And an endpoint that fails on any query
      When the shapes are generated at threshold 1.0 and again at 0.5
      Then the property has its accepted counts only at threshold 0.5
      And the endpoint was never queried

    Scenario: A saved profile loads back unchanged
      Given a profile run
      When it is saved and loaded again
      Then the loaded run equals the saved one

    @uc_b2_1
    Scenario Outline: An unusable profile file is refused
      Given <file>
      When the shapes are generated from it
      Then the command exits with 2
      And the message names the file
      And nothing is written

      Examples:
        | file                                     |
        | a profile path that does not exist       |
        | a profile file that is not JSON          |
        | a JSON file that does not match a profile |

    @uc_b2_1
    Scenario: A custom template package
      Given a custom template package that reads a constant from its configuration
      When the shapes are generated with that template package
      Then the output shows the constant

  Rule: Outputs stay valid whatever the data holds

    Scenario Outline: Unusual IRIs stay valid
      Given a profile whose <where> is <iri>
      When every representation is generated
      Then the shapes parse as Turtle
      And the diagram declares each class once
      And the document shows "<iri>" by its short name, with the full IRI as its title

      Examples:
        | where        | iri                        |
        | class IRI    | http://ex.org/q?a=1&b='x'  |
        | property IRI | http://ex.org/ș/ü          |

    Scenario: An IRI that cannot be written is skipped, not broken
      Given a profile whose class IRI is "http://ex.org/<script>alert(1)</script> x"
      When every representation is generated
      Then that class is absent from the shapes and the diagram
      And a warning names the skipped IRI
      And the document lists the IRI under caveats as text

  Rule: Shapes say no more than the profile observed

    Scenario Outline: Counts follow the cardinality label
      Given a property whose accepted label is <label>
      When the shapes are generated
      Then its property shape has minimum count <min> and maximum count <max>

      Examples:
        | label         | min  | max  |
        | exactly one   | 1    | 1    |
        | zero or one   | none | 1    |
        | one or more   | 1    | none |
        | zero or more  | none | none |
        | exactly 3     | 3    | 3    |

    Scenario Outline: Severity follows what the profile knows
      Given at threshold 0.8 a property of a class read in <mode> with <usage>
      When the shapes are generated
      Then its property shape has severity <severity>

      Examples:
        | mode    | usage                                  | severity     |
        | exact   | presence only                          | Info         |
        | exact   | confidence 0.3 and label support 1.0   | Info         |
        | exact   | confidence 1.0 and label support 0.9   | Warning      |
        | first-N | confidence 1.0 and label support 1.0   | Warning      |
        | exact   | confidence 1.0 and label support 1.0   | Violation    |

    Scenario: A class with declared subclasses is graded at most Warning
      Given a class with a declared subclass and a property every instance has
      When the shapes are generated
      Then its property shape has severity Warning

    Scenario: Language-tagged literals without a datatype
      Given a property whose literals carry a language but no datatype
      When the shapes are generated
      Then its property shape allows language-tagged strings

    Scenario: A sampled class is marked
      Given a class read from its first 10 of 50 instances
      When the shapes are generated
      Then its node shape records 10 observed of 50 instances and the first-N mode

    Scenario: Shapes report no violation on their own data
      Given the shapes generated from the profile of the test data
      When the test data is validated against them
      Then no result has severity Violation

  Rule: The diagram and the document show the model

    Scenario: Diagram content
      Given a profile with class "ex:Person" whose own property "ex:name" has exactly one value and whose implied parent is "ex:Agent"
      When the diagram is generated
      Then the diagram declares "ex:Person" once with attribute "ex:name" of multiplicity "1"
      And it draws a dashed generalisation from "ex:Person" to "ex:Agent"

    Scenario: Document sections
      Given a saved profile of the test data
      When the document is generated
      Then it has an overview, the namespaces, one chapter per graph with a section per class, and caveats

    Scenario: Failures and samples are flagged
      Given a profile with a class read from its first 10 of 50 instances and one recorded failure
      When the document is generated
      Then the collection section lists the failure and the caveats list the sampled class
      And the class section shows "first 10 of 50"

  Rule: Shapes have readable names

    Scenario Outline: Shape names
      Given a profile with the class "<class>" and its property "<property>"
      When the shapes are generated with the shapes namespace "<given>"
      Then the node shape is "<node>" and the property shape is "<shape>"

      Examples:
        | class                                                    | property                                                | given                 | node                                                            | shape                                                                       |
        | https://ontology.brainframe.com/2016/04/brainframe#Asset | https://ontology.brainframe.com/2016/04/brainframe#name | http://ex.org/shapes/ | http://ex.org/shapes/brainframe-Asset                           | http://ex.org/shapes/brainframe-Asset-brainframe-name                       |

  Rule: Namespace filters choose the classes shown

    Scenario: Meta vocabularies hidden by default
      Given a profile holding the classes "http://example.org/Person" and "http://www.w3.org/2002/07/owl#Ontology"
      When the shapes and the diagram are generated with no filter option
      Then "ex:Person" has a node shape and a box
      And "owl:Ontology" has neither

    Scenario: Included again
      Given a profile holding the classes "http://example.org/Person" and "http://www.w3.org/2002/07/owl#Ontology"
      When the shapes and the diagram are generated with include "owl"
      Then "owl:Ontology" has a node shape and a box

    Scenario: Excluded by option
      Given a profile holding the classes "http://example.org/Person" and "http://www.w3.org/2002/07/owl#Ontology"
      When the shapes and the diagram are generated with exclude "ex"
      Then "ex:Person" has neither

    Scenario: Unknown name
      Given a profile holding the classes "http://example.org/Person" and "http://www.w3.org/2002/07/owl#Ontology"
      When the shapes and the diagram are generated with exclude "nope"
      Then a warning names "nope"
      And "ex:Person" has a node shape and a box

    Scenario: Empty default graph
      Given a profile whose default graph is empty
      When the shapes and the diagram are generated with no filter option
      Then no shapes or diagram file is written for it

  Rule: Every format is checked into a golden file

    Scenario Outline: Golden output
      Given the fixed test profile
      When the <format> is generated from it
      Then it equals its golden file

      Examples:
        | format   |
        | shapes   |
        | diagram  |
        | document |
