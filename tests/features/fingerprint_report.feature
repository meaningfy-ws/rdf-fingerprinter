# Capability: fingerprint-report (openspec/specs/fingerprint-report)
# Projected from UC-W1, UC-B1.1, UC-B1.2 and UC-B2.2 (docs/modules/ROOT/pages/use-cases/).
@uc_w1
Feature: The fingerprint report and the command line
  As a data steward
  I want a readable report and an honest exit status
  So that I can read the profile and automate fingerprinting safely

  Rule: The report renders the analytics and never queries

    Scenario: No queries during rendering
      Given an analytics profile
      And an endpoint that fails on any query
      When the report is rendered
      Then the report is written
      And the endpoint was never queried

  Rule: The offline page equals the run's page

    Scenario: Offline page equals the run's page
      Given every class is profiled
      When the fingerprint command runs
      And the document is rendered again from the saved profile file
      Then the two pages are equal

  Rule: The report shows each class honestly

    Scenario: First N class is labelled
      Given a class read in first-N with 10000 of 50000 instances observed
      When the report is rendered
      Then its section shows "first 10000 of 50000"

    Scenario: Exact class is labelled
      Given a class read in exact with 120 of 120 instances observed
      When the report is rendered
      Then its section shows "exact"

    Scenario: The property columns
      Given the report is generated for the test data
      Then every class table has the columns property, subjects, min, max, avg, kind, distinct values and value types
      And every class table has the columns confidence, cardinality, inheritance and language coverage

    Scenario: Absent value is a dash
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
    Scenario: Clean run
      Given every class is profiled
      When the fingerprint command runs
      Then it exits with 0
      And the report is written

    @uc_b1_1
    Scenario: Partial failure
      Given one class fails and the others are profiled
      When the fingerprint command runs
      Then it exits with 1
      And the report is written
      And it logs the number of failures

    @uc_b1_1
    Scenario Outline: Endpoint unreachable
      Given <situation>
      When the fingerprint command runs
      Then it exits with 3
      And no report is written
      And it logs that the endpoint cannot be reached

      Examples:
        | situation                           |
        | the endpoint refuses connections    |
        | the endpoint requires authentication |

    @uc_b1_1
    Scenario Outline: Usage error
      Given <situation>
      When the fingerprint command runs
      Then it exits with 2
      And no report is written

      Examples:
        | situation                          |
        | the output folder does not exist   |
        | a setting is invalid               |
        | the prefix file is malformed       |

    @uc_b1_1
    Scenario: Unexpected error
      Given an unexpected error occurs
      When the fingerprint command runs
      Then it exits with 4
      And no report is written

  Rule: Credentials never leave the endpoint address

    Scenario: Credentials are redacted
      Given the endpoint address "https://user:pw@host:8890/sparql?key=abc"
      When the fingerprint command runs
      Then no output file and no log line holds the user info "user:pw@" or the query string "key=abc"
      And the outputs and logs show "https://host:8890/sparql"

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
    Scenario: Profile file beside the report
      Given every class is profiled
      When the fingerprint command runs
      Then the output folder holds the report and the profile file
      And the profile file holds a namespace table

    @uc_b1_1
    Scenario: Partial failures are saved too
      Given one class fails and the others are profiled
      When the fingerprint command runs
      Then the profile file lists that failure
      And it exits with 1

    @uc_b1_1
    Scenario: Profile kept when the report fails
      Given every class is profiled
      And the report template raises an error
      When the fingerprint command runs
      Then the output folder holds the profile file
      And it exits with 4

  Rule: Representations can be rendered in the same run

    @uc_b2_2
    Scenario: Report plus SHACL in one run
      Given every class is profiled
      When the fingerprint command runs with the format "shacl"
      Then the output folder holds the report, the profile file and one shapes file per non-empty profiled graph

    @uc_b2_2
    Scenario: The document is the report
      Given every class is profiled
      When the fingerprint command runs with the format "doc"
      Then the output folder holds the report and no profile.html

    @uc_b2_2
    Scenario: Unknown format
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

  Rule: Pitfalls in the report

    Scenario: Section and badge
      Given the scanned test profile
      When the report is rendered
      Then the Pitfalls section lists "p34_untyped_class" with its count and examples
      And a class section that the check names shows a badge linking to it

    Scenario: Values are escaped
      Given a scanned profile whose example value is "<script>alert(1)</script>"
      When the report is rendered
      Then the page shows the value as text and has no script element with it

    Scenario: No scan, no section
      Given the readability test profile
      When the report is rendered
      Then the page has no Pitfalls section and no pitfall badge

  Rule: Pitfall scans in the command

    Scenario: Pitfalls found with fail-on
      Given a store whose graph "data" uses an undeclared relation and whose graph "schema" holds the ontology
      When the fingerprint command runs with --pitfalls and --fail-on critical on graph "data" with schema graph "schema"
      Then it exits with 5
      And it logs the findings at or above "critical"

    Scenario: An update in a user check is refused
      Given a store whose graph "data" uses an undeclared relation and whose graph "schema" holds the ontology
      And a user check file that holds a DELETE WHERE update
      When the fingerprint command runs with --pitfalls and that check folder
      Then it exits with 2 naming the file
      And no query was sent

    Scenario: Pitfalls format in the run
      Given a store whose graph "data" uses an undeclared relation and whose graph "schema" holds the ontology
      When the fingerprint command runs with --pitfalls and --format pitfalls on graph "data" with schema graph "schema"
      Then the output folder holds one pitfalls TSV per scanned graph
