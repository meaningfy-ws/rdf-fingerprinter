# Capability: pitfall-scans (openspec/changes/pitfall-scans/specs/pitfall-scans)
# Projected from UC-W1 and UC-B2.1 (docs/modules/ROOT/pages/use-cases/).
@uc_w1
Feature: Scanning a fingerprinted store for modelling pitfalls
  As a data steward
  I want the fingerprint to report modelling pitfalls next to the statistics
  So that I see what is wrong with how the data is modelled, not only what it holds

  Background:
    Given a store whose graph "data" uses an undeclared relation and whose graph "schema" holds the ontology

  Rule: Checks follow a contract and are read-only

    Scenario: A valid check loads
      When the packaged catalogue is loaded
      Then check "p35_untyped_property" has importance "important", scope "data" and source "OOPS! P35"

    Scenario Outline: An invalid check is refused
      Given a user check file that <problem>
      When the fingerprint command runs with --pitfalls and that check folder
      Then it exits with 2 naming the file
      And no query was sent

      Examples:
        | problem                             |
        | has no id                           |
        | has importance severe               |
        | holds an INSERT DATA update         |
        | selects ?s ?p ?o                    |
        | does not parse                      |
        | has the unknown header key severity |
        | has a FROM clause                   |

    Scenario: Catalogue size
      When the packaged catalogue is loaded
      Then it holds 29 checks with unique ids, each OOPS!-derived one naming its pitfall code

  Rule: The scan stage

    Scenario: Scan with a schema graph
      When the fingerprint command runs with --pitfalls on graph "data" with schema graph "schema"
      Then it exits with 0
      And the profile of "data" has a "p35_untyped_property" result whose example entity is "ex:undeclared"

    Scenario: Schema checks run once, on the schema graph
      When the fingerprint command runs with --pitfalls on graph "data" with schema graph "schema"
      Then the graph "schema" is profiled too
      And the profile of "schema" has results only for schema checks
      And the profile of "data" has results only for data checks

    Scenario: The default graph runs without the schema
      Given the default graph holds data too
      When the fingerprint command runs with --pitfalls on every graph with schema graph "schema"
      Then a warning says the default graph's data checks ran without the schema graphs
      And the report's caveats say so

    Scenario: Checks run on the worker pool
      When graph "data" is scanned with concurrency 4
      Then at most 4 check queries were in flight at once, more than one at some point, and the results are in catalogue order

    Scenario: Empty graph not scanned
      When the fingerprint command runs with --pitfalls on every graph
      Then the default graph has no pitfall results and no check query was sent for it

    Scenario: A check that finds nothing
      When the fingerprint command runs with --pitfalls on graph "data" with schema graph "schema"
      Then the "p25_inverse_of_itself" result of "schema" has count 0 and no examples, and no example query was sent for it

    Scenario: Bounded examples
      When the fingerprint command runs with --pitfalls and --pitfall-examples 1 on graph "data"
      Then every result has at most 1 example

    Scenario: Scan off
      When the fingerprint command runs without --pitfalls on graph "data"
      Then no pitfall query was sent
      And no graph profile has pitfall results

    Scenario: Failed check
      Given the count query of "p35_untyped_property" times out
      When the fingerprint command runs with --pitfalls on graph "data" with schema graph "schema"
      Then it exits with 1
      And a failure of kind pitfall names "p35_untyped_property"

  Rule: Options

    Scenario: A user check replaces a packaged one
      Given a valid user check with the id "p22_class_naming"
      When the fingerprint command runs with --pitfalls and that check folder on graph "schema"
      Then the "p22_class_naming" result's source names the user's file

    Scenario: Scan options need the scan
      When the fingerprint command runs without --pitfalls but with --fail-on critical
      Then it exits with 2 naming "--fail-on"
      And no query was sent

    Scenario: Skipped check
      When the fingerprint command runs with --pitfalls and --skip-pitfall "p13_missing_inverse" on graph "schema"
      Then no query of check "p13_missing_inverse" was sent

  Rule: Fail on findings

    Scenario Outline: Exit status from findings
      When the fingerprint command runs with --pitfalls and --fail-on <level and graphs>
      Then it exits with <code>

      Examples:
        | level and graphs                                    | code |
        | critical on graph "data"                            | 0    |
        | critical on graph "data" with schema graph "schema" | 5    |
        | important on graph "data"                           | 5    |
        | minor on graph "data" with schema graph "schema"    | 5    |

  Rule: The TSV format

    Scenario: ROBOT-style lines
      Given a profile whose "p19_multiple_domains_or_ranges" result has the example "http://ex.org/p", "http://www.w3.org/2000/01/rdf-schema#range", "2"
      When the pitfalls TSV is generated
      Then the file holds the line "ERROR	p19_multiple_domains_or_ranges	http://ex.org/p	http://www.w3.org/2000/01/rdf-schema#range	2"

    Scenario: Offline
      When the fingerprint command runs with --pitfalls and --format pitfalls on graph "data" with schema graph "schema"
      Then fingerprint-gen-pitfalls writes the same files from the saved profile without a query
