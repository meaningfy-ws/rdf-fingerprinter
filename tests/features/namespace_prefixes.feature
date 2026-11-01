# Capability: namespace-prefixes (openspec/specs/namespace-prefixes)
# Projected from UC-W1 and UC-B2.1 (docs/modules/ROOT/pages/use-cases/).
@uc_w1
Feature: Every namespace has a prefix
  As a data steward
  I want every IRI in the outputs written as prefix:local
  So that the report, the shapes and the diagrams stay readable whatever vocabularies the data uses

  Rule: Every namespace has a prefix

    Scenario: Unknown vocabulary is named
      Given a profile uses "https://ontology.brainframe.com/2016/04/brainframe#Person"
      And no prefix source names that namespace
      When the namespace table is resolved
      Then the namespace table holds the generated prefix "brainframe" for "https://ontology.brainframe.com/2016/04/brainframe#"

    Scenario: A fragment route is not a hash namespace
      Given a profile uses "https://my.brainframe.com/#/knowledge/Person/7a08"
      When the namespace table is resolved
      Then its namespace is "https://my.brainframe.com/#/knowledge/Person/"

    Scenario: Deterministic table
      Given a profile using the namespaces "https://ontology.brainframe.com/2016/04/brainframe#" and "http://ex.org/core/"
      When the same profile is resolved twice with the same prefix sources
      Then both namespace tables are equal

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

    Scenario: Bad user file
      Given the prefix option names a file that is not a JSON object of names to IRIs
      When the fingerprint command runs
      Then it exits with 2 and a message naming the option and the file
      And no query is sent

    Scenario: A user file over a saved table
      Given a saved profile whose table names "http://ex.org/" as "ex" and "http://ex.org/core/" as "ex-core", both generated
      And a user file that names "http://ex.org/" as "exo"
      When the diagram generator renders the saved profile
      Then the diagram uses "exo:" for "http://ex.org/" and still "ex-core:" for "http://ex.org/core/"

    Scenario: A user prefix displaces a saved one
      Given a saved table names "http://xmlns.com/foaf/0.1/" as "foaf" and the user file maps "foaf" to "http://ex.org/foaf/"
      When the namespace table is resolved
      Then "http://ex.org/foaf/" is "foaf" from the user file and "http://xmlns.com/foaf/0.1/" is not "foaf"

  Rule: prefix.cc is a best-effort source

    Scenario: prefix.cc offline
      Given prefix.cc is unreachable
      When the namespace table is resolved with the lookup on
      Then one warning names prefix.cc and the unnamed namespaces have generated prefixes

    Scenario: Expired certificate
      Given prefix.cc's HTTPS certificate fails verification and its HTTP list is reachable
      When the namespace table is resolved with the lookup on
      Then the list is read over HTTP, the INFO line is logged and no warning is logged

    Scenario: Lookup switched off
      Given the prefix lookup is switched on by the environment
      When the fingerprint command runs with "--no-prefix-lookup"
      Then prefix.cc is not contacted

  Rule: Generated prefixes are readable and stable

    Scenario Outline: Generated names
      Given the namespace "<namespace>" with the table "<known>"
      When its prefix is generated
      Then it is "<prefix>"

      Examples:
        | namespace                                                 | known                                                           | prefix         |
        | https://ontology.brainframe.com/2016/04/brainframe#       |                                                                 | brainframe     |
        | https://ontology.brainframe.com/2016/04/brainframe/sub/   | brainframe=https://ontology.brainframe.com/2016/04/brainframe#  | brainframe-sub |
        | https://my.brainframe.com/#/knowledge/RelationId/         |                                                                 | relationid     |
        | http://ex.org/core/                                       | ex=http://ex.org/                                               | ex-core        |
        | http://data.ex.org/                                       | ex=http://ex.org/                                               | ex-data        |
        | http://a.b.ex.org/                                        | ex=http://ex.org/                                               | ex-a-b         |
        | http://ex.org/v2/                                         |                                                                 | ex             |
        | http://other.org/ex/                                      | ex=http://ex.org/                                               | ex2            |
        | http://www.legislation.gov.uk/                            |                                                                 | legislation    |
        | http://ex.org/My_Vocab.v1/                                |                                                                 | my-vocab-v1    |
        | http://ex.org/2020/                                       |                                                                 | ex             |
        | http://ex.org/sh/                                         |                                                                 | sh2            |
        | http://ex.org/bf/shape/                                   | bf=http://ex.org/bf/                                            | bf-shape2      |
        | https://ontology.brainframe.com/2016/04/brainframe#blueprint/ | brainframe=https://ontology.brainframe.com/2016/04/brainframe# | brainframe-blueprint |
        | https://ontology.brainframe.com/2016/04/brainframe/       | brainframe=https://ontology.brainframe.com/2016/04/brainframe#  | brainframe2    |
        | http://store.ex.org:9999/                                 |                                                                 | store          |
        | http://localhost:8890/                                    |                                                                 | ns             |
        | http://10.0.0.1/                                          |                                                                 | n0             |
        | urn:x:thing:                                              |                                                                 | thing          |
        | http://ex.org/core/                                       | EX=http://ex.org/                                               | ex-core        |

  Rule: The table is saved with the profile

    Scenario: Offline generators reuse the table
      Given a saved profile whose table names "http://ex.org/" as "zz", generated
      When the diagram generator renders the saved profile with HTTP forbidden
      Then the diagram uses "zz:" for "http://ex.org/"

    @uc_b2_1
    Scenario: Old profile
      Given a profile file without a namespace table
      When it is loaded and its diagram generated
      Then every namespace has a prefix and no long IRI is in a label

  Rule: Every output shortens IRIs

    Scenario: Longest namespace wins
      Given the table names "http://ex.org/" as "ex" and "http://ex.org/core/" as "ex-core"
      Then "http://ex.org/core/Thing" is shown as "ex-core:Thing"

    @uc_b2_1
    Scenario: No long IRIs in the diagram
      Given the readability test profile
      When the PlantUML output is generated
      Then no class, attribute, association or package label holds a full IRI

  Rule: Pitfall findings are named too

    Scenario: Pitfall examples are named
      Given a profile whose pitfall example entity is "http://other.org/vocab#thing"
      When the namespace table is resolved
      Then the table holds a prefix for "http://other.org/vocab#"
