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
    Scenario: Threshold changed without collecting
      Given a saved profile with a property whose label support is 0.8
      And an endpoint that fails on any query
      When the shapes are generated at threshold 1.0 and again at 0.5
      Then the property has its accepted counts only at threshold 0.5
      And the endpoint was never queried

    Scenario: Round-trip
      Given a profile run
      When it is saved and loaded again
      Then the loaded run equals the saved one

    @uc_b2_1
    Scenario Outline: Unusable profile file
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
    Scenario: Custom template package
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

    Scenario Outline: Counts from the cardinality label
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

    Scenario Outline: Severity from the threshold
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

    Scenario: Sampled class is marked
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

    Scenario: Document written from a profile file
      Given a saved profile of the test data
      When the document command renders it into an empty folder
      Then the folder holds the report and no profile.html
      And it has an overview, the namespaces, one chapter per graph with a section per class, and caveats

    Scenario: Clusters of a small namespace
      Given the namespace "ex" holds the classes A to G, with A and B linked twice, B and C, C and D, and E and F once, and G linked to none
      When the diagrams are generated with module size 3
      Then the module "ex~1" holds A, B and C
      And the module "ex~2" holds E and F
      And the module "ex~3" holds D and G

    Scenario: Big namespace is split
      Given the namespace "ex" holds 40 classes, each linked to the next
      When the diagrams are generated with module size 15
      Then there are at least 3 module diagrams of at most 15 classes each
      And every class is in exactly one of them
      And generating again gives the same files with the same contents

    Scenario: Overview
      Given 3 classes of "ex" have object properties whose values are "foaf:Person", and no "foaf" class is profiled
      When the diagrams are generated
      Then the overview has the package "ex" and the package "foaf" marked referenced
      And one arrow from "ex" to "foaf" is labelled 3

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
        | class                                                    | property                                                | given                 | node                                                         | shape                                                                       |
        | https://ontology.brainframe.com/2016/04/brainframe#Asset | https://ontology.brainframe.com/2016/04/brainframe#name | none                  | https://ontology.brainframe.com/2016/04/brainframe/shape/Asset | https://ontology.brainframe.com/2016/04/brainframe/shape/Asset-brainframe-name |
        | https://ontology.brainframe.com/2016/04/brainframe#Asset | https://ontology.brainframe.com/2016/04/brainframe#name | http://ex.org/shapes/ | http://ex.org/shapes/brainframe-Asset                        | http://ex.org/shapes/brainframe-Asset-brainframe-name                       |
        | urn:x:Asset                                              | urn:x:name                                              | none                  | urn:x:shape:Asset                                            | urn:x:shape:Asset-x-name                                                    |

    Scenario: Colliding shape names
      Given a profile holding both the classes "http://ex.org/a#Thing" and "http://ex.org/a/Thing"
      When the shapes are generated
      Then the node shapes are "http://ex.org/a/shape/Thing" and "http://ex.org/a/shape/Thing-2", in class IRI order

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
      When the shapes, the diagram, the pattern schema and the ShExC are generated with no filter option
      Then no shapes, diagram, pattern schema or ShExC file is written for it

  Rule: Every format is checked into a golden file

    Scenario Outline: Golden file per output
      Given the fixed test profile
      When the <format> is generated from it
      Then it equals its golden file

      Examples:
        | format         |
        | shapes         |
        | diagram        |
        | document       |
        | pattern schema |
        | ShExC          |

  # llm-schema-tools: the pattern schema (primary) and the enriched ShExC (secondary), one pattern view.
  Rule: The pattern view follows the profile's links, one hop and through blank nodes

    @uc_b2_1
    Scenario: A chain deeper than three hops
      Given a profile where "ex:A" reaches blank nodes of "ex:B" by "ex:p", "ex:B" those of "ex:C" by "ex:q", "ex:C" those of "ex:D" by "ex:r", and "ex:D" those of "ex:E" by "ex:s"
      When the pattern schema is generated from it
      Then the "ex:A" block holds "-ex:p->" at level 1, "-ex:q->" at level 2 and "-ex:r-> (:ex:D) bn …" at level 3
      And no line lies below level 3
      And neither "ex:D" nor "ex:E" begins a block

    @uc_b2_1
    Scenario: A blank-node cycle is expanded once
      Given a profile where "ex:A" reaches blank nodes of "ex:List" by "ex:items", and "ex:List" reaches blank nodes of "ex:List" by "ex:rest"
      When the pattern schema is generated from it
      Then "ex:List" is expanded once, under "-ex:items->"
      And its nested line "-ex:rest-> (:ex:List) bn ^" is followed by no deeper line

    @uc_b2_1
    Scenario: A class with unreached instances keeps its block
      Given a profile where 3 distinct blank nodes of "ex:Note" are reached and "ex:Note" has 5 instances
      When the pattern schema is generated from it
      Then "ex:Note" begins a block
      And the edges into "ex:Note" are not followed by nested lines

    @uc_b2_1
    Scenario: An object type from another graph
      Given a profile collected across graphs where "ex:knows" points to "ex:Person" typed in graph "http://ex.org/people"
      When the pattern schema is generated from it
      Then the "ex:knows" edge target is "(:ex:Person @<http://ex.org/people>)"

  Rule: The pattern schema is compact and reads like triple patterns

    @uc_b2_1
    Scenario Outline: Lines of the continents pattern schema
      Given the fixed test profile
      When the pattern schema is generated from it
      Then "pattern-continents-214e8f67.txt" holds, at level <level>, the line "<line>"

      Examples:
        | level | line                                                                                                                                       |
        | 0     | (:euvoc:Continent&skos:Concept) 6                                                                                                          |
        | 1     | -euvoc:startDate-> xsd:date =1952-07-24                                                                                                    |
        | 1     | -euvoc:status-> IRI d1                                                                                                                     |
        | 1     | -skosxl:prefLabel-> (:skosxl:Label) ×24 bn                                                                                                 |
        | 2     | -lvont:script-> IRI 12/145 d2                                                                                                              |
        | 2     | -skosxl:literalForm-> rdf:langString @24                                                                                                   |
        | 2     | -rdf:value-> xsd:string AFRICA..OCEANIA                                                                                                    |
        | 0     | (:owl:Ontology&skos:ConceptScheme) 1 via (:euvoc:Continent&skos:Concept)-skos:inScheme, (:euvoc:Continent&skos:Concept)-skos:topConceptOf |
        | 1     | -skosxl:prefLabel-> (:skosxl:Label) bn ^                                                                                                   |
        | 0     | # glossary: none                                                                                                                           |

    @uc_b2_1
    Scenario: One block per class group and one edge per property
      Given the fixed test profile
      When the pattern schema is generated from it
      Then in every file no group name begins two blocks and no property begins two edges at the same place
      And "skosxl:Label", "euvoc:XlNotation" and "euvoc:XlNote" begin no block
      And every declared prefix is used

    @uc_b2_1
    Scenario Outline: Values that need quotes
      Given a profile where the lowest and highest values of a literal property are both <value>
      When the pattern schema is generated from it
      Then the property's edge ends in <written>

      Examples:
        | value                   | written                                                              |
        | "Treaty of Rome"        | ="Treaty of Rome"                                                    |
        | "1..2"                  | ="1..2"                                                              |
        | the empty string        | =""                                                                  |
        | 70 times the letter "a" | ="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa…" |

    @uc_b2_1
    Scenario: A single IRI value is written as a prefixed name
      Given a profile collected at depth "rich_values" where every object of "ex:status" is the IRI "http://ex.org/status/active", recorded as its top value
      And the prefix table maps "exs" to "http://ex.org/status/"
      When the pattern schema is generated from it
      Then the "ex:status" edge is "-ex:status-> IRI =exs:active"
      And the prefix "exs" is declared
      And the same profile without top values gives the edge "-ex:status-> IRI d1"

    @uc_b2_1
    Scenario: A class read in first-N mode
      Given a profile where "ex:Big" has 50000 instances, 10000 of them read in first-N mode, and "ex:name" on 9000 of those
      When the pattern schema is generated from it
      Then the "ex:Big" block header is "(:ex:Big) 50000 ~10000 first_n"
      And its "ex:name" edge holds "9000/10000"

    @uc_b2_1
    Scenario: Unusual IRIs in the LLM outputs
      Given a profile whose class IRI is "http://ex.org/q?a=1&b='x'"
      When the pattern schema and the ShExC are generated from it
      Then the pattern schema writes the class as "<http://ex.org/q?a=1&b='x'>"
      And the ShExC lists "http://ex.org/q?a=1&b='x'" after "# skipped:"
      And the ShExC parses

  Rule: The enriched ShExC says the same, where ShExC can

    @uc_b2_1
    Scenario: The ShExC output parses
      Given the fixed test profile
      When the ShExC is generated from it
      Then each of the three files parses with PyShExC

    @uc_b2_1
    Scenario Outline: Lines of the continents ShExC
      Given the fixed test profile
      When the ShExC is generated from it
      Then "shex-continents-214e8f67.shex" holds, at level <level>, the line "<line>"

      Examples:
        | level | line                                                                         |
        | 0     | euvoc:Continent {                                                            |
        | 1     | euvoc:startDate xsd:date ;  # =1952-07-24                                    |
        | 1     | euvoc:xlNotation BNODE {  # (:euvoc:XlNotation) bn                           |
        | 1     | skosxl:prefLabel BNODE @skosxl:Label {24} ;  # (:skosxl:Label) ×24 bn        |
        | 1     | skos:inScheme @skos:ConceptScheme ;  # (:owl:Ontology&skos:ConceptScheme) d1 |
        | 0     | skosxl:Label BNODE {                                                         |
        | 1     | lvont:script IRI ? ;  # 12/145 d2                                            |

  Rule: Terms carry labels and one description, the ontology first

    @uc_b2_1
    Scenario: Labels from an ontology file
      Given the fixed test profile
      And the label fixture ontology
      When the pattern schema is generated from it with that ontology
      Then the glossary holds the line 'skos:Concept "Concept"@en: An idea or notion; a unit of thought.'
      And the glossary holds the line 'skosxl:prefLabel "preferred label"@en'
      And the glossary has no line for "euvoc:Continent"

    @uc_b2_1
    Scenario: The ontology wins for the fields it gives
      Given a profile whose data labels "ex:Person" '"Persoon"@nl' with the description '"Iemand"@nl'
      And an ontology that labels "ex:Person" '"Person"@en' with no description
      When the pattern schema is generated from it with that ontology
      Then the glossary holds the line 'ex:Person "Person"@en: Iemand'

    @uc_b2_1
    Scenario Outline: The label shown
      Given a profile whose data labels "ex:Person" <labels>
      When the pattern schema is generated from it
      Then the glossary line of "ex:Person" shows <shown>

      Examples:
        | labels                              | shown          |
        | "Begriff"@de, "Concept"@en, "C"     | "C"            |
        | "Begriff"@de, "Concept"@en          | "Concept"@en   |
        | "Begriff"@de, "Concept"@fr          | "Begriff"@de   |

    @uc_b2_1
    Scenario: Unreadable ontology file
      Given the fixed test profile
      And an ontology file that is not RDF
      When the pattern schema is generated from it with that ontology
      Then it exits 2 with a message naming the ontology file
      And nothing is written

    @uc_b2_1
    Scenario: A profile saved before term annotations
      Given a profile saved before 3.2, with no term annotations
      When the pattern schema is generated from it
      Then it is written
      And its glossary is "# glossary: none"

  Rule: Size filters prune the largest outputs

    @uc_b2_1
    Scenario: Small classes hidden
      Given the fixed test profile
      When the pattern schema is generated from it with "--min-instances 2"
      Then "pattern-treaties-3b4301a8.txt" has no block "(:owl:Ontology&skos:ConceptScheme)"
      And it holds the line "# hidden: 2 classes"
      And it still holds the line "-skos:inScheme-> (:owl:Ontology&skos:ConceptScheme) d1"

    @uc_b2_1
    Scenario: Only the largest classes
      Given the fixed test profile
      When the pattern schema is generated from it with "--max-classes 1"
      Then each file has one block, the largest named group of its graph
