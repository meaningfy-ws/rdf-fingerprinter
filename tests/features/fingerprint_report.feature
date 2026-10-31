# Capability: fingerprint-report (openspec/specs/fingerprint-report)
# Projected from UC-W1, UC-B1.1, UC-B1.2 and UC-B2.2 (docs/modules/ROOT/pages/use-cases/).
@uc_w1
Feature: The fingerprint report and the command line
  As a data steward
  I want a readable report and an honest exit status
  So that I can read the profile and automate fingerprinting safely

  Rule: The report renders the analytics and never queries

    Scenario: No queries while rendering
      Given an analytics profile
      And an endpoint that fails on any query
      When the report is rendered
      Then the report is written
      And the endpoint was never queried

  Rule: The report shows each class honestly

    Scenario Outline: Precision is shown per class
      Given a class read in <mode> with <observed> of <instances> instances observed
      When the report is rendered
      Then its section shows "<label>"

      Examples:
        | mode    | observed | instances | label                |
        | exact   | 120      | 120       | exact                |
        | first-N | 10000    | 50000     | first 10000 of 50000 |

    Scenario: The property columns
      Given the report is generated for the test data
      Then every class table has the columns property, subjects, min, max, avg, kind, distinct values and value types
      And every class table has the columns confidence, cardinality, inheritance and language coverage

    Scenario: Absent values are shown as a dash
      Given a property whose language coverage is absent
      When the report is rendered
      Then its language coverage cell shows "—"

    Scenario: Failure listed
      Given the profile contains one failure for class "ex:Big"
      When the report is rendered
      Then the collection section lists "ex:Big" with the failed measurement and the error message
      And the collection section lists the settings used

    Scenario: Short names only
      Given the readability test profile
      When the report is rendered
      Then no visible text outside the namespace table, the endpoint, the settings, the failures and the caveats holds a full IRI

    Scenario: Hidden namespaces are listed
      Given the readability test profile
      When the report is rendered
      Then the caveats list "owl" as hidden with 1 class
      And no "owl:" class section exists

  Rule: The report is one self-contained page

    Scenario: No external resources
      Given the readability test profile
      When the report is rendered
      Then the page has no external stylesheet, script, image or CSS url

    Scenario: Content outside the script
      Given the readability test profile
      When the report is rendered
      Then without its scripts the page still has the table of contents, every class section and every table

    Scenario: Search data is present
      Given the readability test profile
      When the report is rendered
      Then each class section carries its prefix and a search text with its short name and full IRI

    @manual
    Scenario: Search narrows the classes
      Given the brainframe report open in a browser
      When the reader types "risk" in the search box
      Then only the classes and property rows whose names or IRIs contain "risk" stay shown, and the shown count updates

    @manual
    Scenario: Namespace switched off
      Given the brainframe report open in a browser
      When the reader switches off a namespace
      Then its class sections and contents entries are hidden, and the search still applies to the rest

  Rule: The exit status tells what happened

    @uc_b1_1
    Scenario Outline: Exit status
      Given <situation>
      When the fingerprint command runs
      Then it exits with <code>
      And <report>

      Examples:
        | situation                                   | code | report                    |
        | every class is profiled                     | 0    | the report is written     |
        | one class fails and the others are profiled | 1    | the report is written     |
        | the endpoint refuses connections            | 3    | no report is written      |
        | the endpoint requires authentication        | 3    | no report is written      |
        | the output folder does not exist            | 2    | no report is written      |
        | a setting is invalid                        | 2    | no report is written      |
        | the prefix file is malformed                | 2    | no report is written      |
        | an unexpected error occurs                  | 4    | no report is written      |

  Rule: Library callers call fingerprint_report

    @uc_b1_2
    Scenario: Minimal call
      When the library is called with an endpoint, an output folder and default settings
      Then it returns the path of the main report document

    @uc_b1_2
    Scenario: Custom template package
      Given a custom template package that prints the number of graphs
      When the report is generated with that package
      Then the page shows that number

  Rule: The profile is saved with the report

    @uc_b1_1
    Scenario: The profile file sits beside the report
      Given every class is profiled
      When the fingerprint command runs
      Then the output folder holds the report and the profile file
      And the profile file holds a namespace table

    @uc_b1_1
    Scenario: Recorded failures are saved too
      Given one class fails and the others are profiled
      When the fingerprint command runs
      Then the profile file lists that failure
      And it exits with 1

    @uc_b1_1
    Scenario: The profile is kept when the report fails
      Given every class is profiled
      And the report template raises an error
      When the fingerprint command runs
      Then the output folder holds the profile file
      And it exits with 4

  Rule: Representations can be rendered in the same run

    @uc_b2_2
    Scenario: Report plus shapes in one run
      Given every class is profiled
      When the fingerprint command runs with the format "shacl"
      Then the output folder holds the report, the profile file and one shapes file per non-empty profiled graph

    @uc_b2_2
    Scenario: The document is the report
      Given every class is profiled
      When the fingerprint command runs with the format "doc"
      Then the output folder holds the report and no profile.html

    @uc_b2_2
    Scenario: An unknown format is refused
      Given every class is profiled
      When the fingerprint command runs with the format "void"
      Then it exits with 2
      And the message names the known formats
      And the endpoint was never queried

    @uc_b2_2
    Scenario: A failing representation keeps the report
      Given every class is profiled
      And the shapes fail to render
      When the fingerprint command runs with the format "shacl"
      Then the output folder holds the report and the profile file
      And it exits with 4
