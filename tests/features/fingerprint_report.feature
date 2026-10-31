# Capability: fingerprint-report (openspec/specs/fingerprint-report)
# Step definitions are written during implementation.
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

    Scenario: The 1.x columns survive
      Given the report is generated for the test data
      Then every class table has the columns property, subjects, min, max, avg, kind, distinct values and value types
      And every class table has the columns confidence, cardinality and inheritance

    Scenario: Absent values are shown as a dash
      Given a property whose language coverage is absent
      When the report is rendered
      Then its language coverage cell shows "—"

    Scenario: Failures and settings are reported
      Given the profile contains one failure for class "ex:Big"
      When the report is rendered
      Then the collection section lists "ex:Big" with the failed measurement and the error message
      And the collection section lists the settings used

  Rule: The exit status tells what happened

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
        | an unexpected error occurs                  | 4    | no report is written      |

  Rule: Library callers keep the 1.x call

    Scenario: A 1.x call still works
      When the library is called with only an endpoint and an output folder
      Then it returns the path of the main report document

    Scenario: Custom template constants survive
      Given a custom template that reads a constant from the additional configuration
      When the report is generated with that constant
      Then the constant appears in the report
