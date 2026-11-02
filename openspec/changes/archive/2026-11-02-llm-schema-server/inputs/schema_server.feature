# Seed input — carried over from llm-schema-tools PLAN, not gated (llm-schema-tools DEC-28, 2026-11-01).
# It was tests/features/schema_server.feature; it moves back there when this change is planned.
# Capability: schema-server (openspec/changes/llm-schema-server/specs/schema-server/spec.md)
# Projected from UC-W3 (inputs/ucw3.adoc). Step definitions are written during implementation.
@uc_w3
Feature: Serving a fingerprint's schema to an agent
  As an agent that writes SPARQL for a knowledge graph
  I want the graph's classes, links and labels, and a check of my query, from a saved fingerprint
  So that my queries use terms the data really has, without loading the endpoint

  Rule: One server serves one saved profile and nothing else

    Scenario: Server started from a saved profile
      Given the schema server is started with the sample profile
      When a client connects over stdio
      Then the client lists exactly the tools "list_graphs, list_classes, describe_class, get_schema, search_schema, validate_query"
      And the client lists the resource template "schema://{graph}"

    Scenario Outline: Unusable start-up file
      Given <file>
      When the schema server is started with it
      Then it exits 2 before serving, with a message on stderr naming the file

      Examples:
        | file                                   |
        | a profile path that does not exist     |
        | a file that is not a profile           |
        | an ontology file that cannot be parsed |

    Scenario: Server without the mcp extra
      Given the mcp package is not installed
      When the schema server is started with the sample profile
      Then it exits 2 with a message naming "rdf-fingerprinter[mcp]"

  Rule: The server never contacts an endpoint

    Scenario: Every tool answers without a network
      Given the schema server is serving the sample profile
      And every network connection fails
      When each tool and the schema resource is called
      Then each one answers from the profile
      And no network connection was attempted

    Scenario: A query given for validation is not executed
      Given the schema server is serving the sample profile
      When "validate_query" is given "SELECT * WHERE { ?s ?p ?o }"
      Then it returns a report
      And no store was asked to evaluate the query

  Rule: Graphs and classes are listed, largest first

    Scenario: Graphs of the sample profile
      Given the schema server is serving the sample profile
      When "list_graphs" is called
      Then it returns the slugs "default, continents-214e8f67, treaties-3b4301a8" with the IRI of each named graph

    Scenario: Classes largest first
      Given the schema server is serving the sample profile
      When "list_classes" is called for "continents-214e8f67"
      Then the entries are, in order:
        | name                            | instances | nested |
        | skosxl:Label                    | 145       | yes    |
        | euvoc:Continent&skos:Concept    | 6         | no     |
        | euvoc:XlNotation                | 6         | yes    |
        | owl:Ontology&skos:ConceptScheme | 1         | no     |

    Scenario: Unknown graph
      Given the schema server is serving the sample profile
      When "list_classes" is called for "nope"
      Then the call returns a tool error naming "nope" and listing the known slugs

  Rule: A class is described with its links in both directions

    Scenario: A named class with incoming links
      Given the schema server is serving the sample profile
      When "describe_class" is called for "continents-214e8f67" and "skos:ConceptScheme"
      Then the block header reads "(:owl:Ontology&skos:ConceptScheme) 1 via (:euvoc:Continent&skos:Concept)-skos:inScheme 6, (:euvoc:Continent&skos:Concept)-skos:topConceptOf 6"
      And its "skosxl:prefLabel" edge is followed by the nested edges of "skosxl:Label"

    Scenario: A class described as ShExC
      Given the schema server is serving the sample profile
      When "describe_class" is called for "continents-214e8f67" and "euvoc:Continent" in format "shex"
      Then the text parses as ShExC
      And it holds the shape "euvoc:Continent"

    Scenario: A blank-node class described on its own
      Given the schema server is serving the sample profile
      When "describe_class" is called for "continents-214e8f67" and "skosxl:Label"
      Then the block header begins with "(:skosxl:Label) 145 via"
      And its via list names "euvoc:Continent&skos:Concept" and "owl:Ontology&skos:ConceptScheme" with their counts

    Scenario: Unknown class with a suggestion
      Given the schema server is serving the sample profile
      When "describe_class" is called for "continents-214e8f67" and "euvoc:Continant"
      Then the call returns a tool error suggesting "euvoc:Continent"

    Scenario: Unknown format
      Given the schema server is serving the sample profile
      When "describe_class" is called for "continents-214e8f67" and "euvoc:Continent" in format "turtle"
      Then the call returns a tool error naming the formats "pattern" and "shex"

  Rule: The whole-graph schema is the generated file

    Scenario: Schema equals the generated file
      Given the schema server is serving the sample profile
      When "get_schema" is called for "treaties-3b4301a8" in each format, and the resource "schema://treaties-3b4301a8" is read
      Then the texts equal the golden files "pattern-treaties-3b4301a8.txt" and "shex-treaties-3b4301a8.shex"
      And the resource equals the pattern schema

  Rule: The schema is searched by plain string matching

    Scenario Outline: Search hits
      Given the schema server is serving the sample profile
      When "search_schema" is called with "<text>"
      Then the first hit is "<first>" of kind "<kind>", matched in "<field>"

      Examples:
        | text          | first              | kind     | field |
        | continent     | euvoc:Continent    | class    | name  |
        | literalform   | skosxl:literalForm | property | name  |
        | skos-xl#label | skosxl:Label       | class    | IRI   |

    Scenario Outline: Search finds labels from the ontology
      Given the schema server is serving the sample profile with the label fixture ontology
      When "search_schema" is called with "<text>"
      Then the first hit is "<first>", matched in "<field>"

      Examples:
        | text         | first           | field       |
        | Date created | dcterms:created | label       |
        | notion       | skos:Concept    | description |

    Scenario: Empty search text
      Given the schema server is serving the sample profile
      When "search_schema" is called with "   "
      Then the call returns a tool error

  Rule: A query is checked against the pattern view, never run

    Scenario: A correct query from the sample facts
      Given the schema server is serving the sample profile
      When "validate_query" is given the query:
        """
        PREFIX euvoc: <http://publications.europa.eu/ontology/euvoc#>
        PREFIX skosxl: <http://www.w3.org/2008/05/skos-xl#>
        SELECT ?c ?name WHERE { ?c a euvoc:Continent ; skosxl:prefLabel/skosxl:literalForm ?name }
        """
      Then the report is valid, with no issue and nothing listed as not checked

    Scenario Outline: Issues found in a query
      Given the schema server is serving the sample profile
      When "validate_query" is given the sample prefixes and the pattern "<pattern>"
      Then the report is not valid and has one issue of kind "<kind>" naming "<term>"

      Examples:
        | pattern                                                     | kind                   | term               |
        | ?c a euvoc:Continant                                        | unknown_class          | euvoc:Continant    |
        | ?c a euvoc:Continent ; euvoc:nope ?x                        | unknown_predicate      | euvoc:nope         |
        | ?c a euvoc:Continent ; skosxl:literalForm ?x                | predicate_not_on_class | skosxl:literalForm |
        | ?c a euvoc:Continent ; skos:inScheme ?s . ?s rdf:value ?v   | predicate_not_on_class | rdf:value          |
        | ?c a euvoc:Continent ; skosxl:prefLabel/rdf:value ?n        | path_step_not_on_class | rdf:value          |

    Scenario Outline: Text that is not a query
      Given the schema server is serving the sample profile
      When "validate_query" is given "<text>"
      Then the report is not valid and its parse error <says>

      Examples:
        | text                                                        | says                                       |
        | SELECT * WHERE { ?s ?p                                      | gives a line and a column                  |
        | SELECT * WHERE { ?c a euvoc:Continent }                     | names the prefix "euvoc" and its namespace |
        | PREFIX ex: <http://ex.org/> INSERT DATA { ex:a ex:b ex:c }  | says only queries are validated            |

    Scenario: Unchecked constructs are listed
      Given the schema server is serving the sample profile
      When "validate_query" is given the query:
        """
        PREFIX euvoc: <http://publications.europa.eu/ontology/euvoc#>
        SELECT ?c WHERE { ?c a euvoc:Continent . OPTIONAL { ?c euvoc:nope ?x } }
        """
      Then the report is valid
      And it lists "OPTIONAL" as not checked
