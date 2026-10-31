# Capability: namespace-prefixes (openspec/changes/readable-representations/specs/namespace-prefixes)
# Projected from UC-W1 and UC-B2.1 (docs/modules/ROOT/pages/use-cases/).
@uc_w1
Feature: Every namespace has a prefix
  As a data steward
  I want every IRI in the outputs written as prefix:local
  So that the report, the shapes and the diagrams stay readable whatever vocabularies the data uses

  Rule: Prefixes come from the first source that names the namespace

    Scenario Outline: The first source wins
      Given the namespace "http://xmlns.com/foaf/0.1/" is named by <sources>
      When the namespace table is resolved
      Then its prefix is "<prefix>" with source "<source>"

      Examples:
        | sources                                      | prefix | source    |
        | the user file as friend and the packaged file | friend | user      |
        | the packaged file as foaf and prefix.cc       | foaf   | packaged  |
        | prefix.cc only as foaf                        | foaf   | prefix_cc |
        | no source                                     | foaf   | generated |

    Scenario: Reserved names are not taken from a file
      Given the user file maps "sh" to "http://ex.org/sh#" and "bf-shape" to "http://ex.org/bf/"
      When the namespace table is resolved
      Then neither name is used for those namespaces

    Scenario: A user prefix displaces a saved one
      Given a saved table names "http://xmlns.com/foaf/0.1/" as "foaf" and the user file maps "foaf" to "http://ex.org/foaf/"
      When the namespace table is resolved
      Then "http://ex.org/foaf/" is "foaf" from the user file and "http://xmlns.com/foaf/0.1/" is not "foaf"

  Rule: prefix.cc is a best-effort source

    Scenario: prefix.cc offline
      Given prefix.cc is unreachable
      When the namespace table is resolved with the lookup on
      Then one warning names prefix.cc and the unnamed namespaces have generated prefixes

  Rule: Generated prefixes are readable and stable

    Scenario Outline: Generated names
      Given the namespace "<namespace>" with the table "<known>"
      When its prefix is generated
      Then it is "<prefix>"

      Examples:
        | namespace                                                 | known                                                           | prefix         |
        | https://ontology.brainframe.com/2016/04/brainframe#       |                                                                 | brainframe     |
        | https://my.brainframe.com/#/knowledge/RelationId/         |                                                                 | relationid     |
        | http://ex.org/core/                                       | ex=http://ex.org/                                               | ex-core        |
        | http://data.ex.org/                                       | ex=http://ex.org/                                               | ex-data        |
        | http://other.org/ex/                                      | ex=http://ex.org/                                               | ex2            |
        | http://ex.org/sh/                                         |                                                                 | sh2            |

    Scenario: The longest namespace wins
      Given the table names "http://ex.org/" as "ex" and "http://ex.org/core/" as "ex-core"
      Then "http://ex.org/core/Thing" is shown as "ex-core:Thing"

  Rule: The table is saved with the profile

    @uc_b2_1
    Scenario: An old profile still loads
      Given a profile file without a namespace table
      When it is loaded and its diagram generated
      Then every namespace has a prefix and no long IRI is in a label
