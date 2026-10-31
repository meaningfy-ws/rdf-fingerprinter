## ADDED Requirements

### Requirement: Representations derive from the saved profile only
Every generator SHALL render from a profile file and SHALL NOT query any endpoint (EPIC DEC-1). A
generator SHALL re-derive the analytics from the raw run it loads, honouring the acceptance threshold
it is given (DEC-2).

#### Scenario: Rendering without an endpoint
- **WHEN** each generator renders from a `profile.json` while no endpoint is reachable
- **THEN** its output is written and no SPARQL request is made

#### Scenario: Threshold changed without collecting
- **WHEN** the SHACL generator renders the same profile file at thresholds 1.0 and 0.5
- **THEN** a property with label support 0.8 gets its accepted counts only at 0.5, and no request is made

### Requirement: Profile file round-trip
A profile written to `profile.json` and loaded back SHALL equal the original run. A file that is not
valid JSON, does not match the profile model, or is missing SHALL be a usage error (exit 2) whose
message names the file.

#### Scenario: Round-trip
- **WHEN** a profile run is saved and loaded again
- **THEN** the loaded run equals the saved one

#### Scenario Outline: Unusable profile file
- **WHEN** a generator is given <file>
- **THEN** it exits 2 with a message naming the file and writes nothing

  Examples:
    | file                                   |
    | a path that does not exist             |
    | a file that is not JSON                |
    | JSON that does not match the profile   |

### Requirement: Generators share one framework
Each representation SHALL be produced by a generator class derived from one base class modelled on
LinkML's generator (DEC-3): a `serialize` entry point, per-level visit hooks, and shared command
arguments (profile file, output folder, acceptance threshold, template folder). Each generator SHALL
have its own command (SHACL, PlantUML, profile document) and SHALL render through eds4jinja2 from a
packaged template package (DEC-4).

#### Scenario: Custom template package
- **WHEN** a generator is given a template folder of the user's own that reads a constant from its configuration
- **THEN** the output is rendered from that folder and shows the constant

### Requirement: Text outputs are escaped
Generators SHALL emit IRIs and literals so that the output stays valid whatever the data holds:
Turtle IRIs and string literals escaped per Turtle, PlantUML names quoted when they are not plain
identifiers, and the HTML document autoescaped. SHACL output SHALL be parsed before it is written;
a parse failure SHALL be an error (exit 4), never a written file (DEC-4).

#### Scenario Outline: Unusual IRIs stay valid
- **WHEN** the profile holds <iri> as a <where>
- **THEN** the SHACL parses as Turtle, the PlantUML keeps one element per class, and the HTML shows the IRI as text

  Examples:
    | iri                                    | where          |
    | `http://ex.org/q?a=1&b='x'`            | class IRI      |
    | `http://ex.org/ș/ü`                    | property IRI   |

#### Scenario: An IRI that cannot be written is skipped, not broken
- **WHEN** the profile holds the class IRI `http://ex.org/<script>alert(1)</script> x`
- **THEN** that class is absent from the SHACL and PlantUML outputs, a warning is logged, and the document lists it under caveats as text, not markup

### Requirement: SHACL shapes
The SHACL generator SHALL write one Turtle file per profiled graph with an open `sh:NodeShape` per
class (`sh:targetClass`, no `sh:closed`) holding a `sh:PropertyShape` per property, inherited ones
included (DEC-5). Counts SHALL follow the accepted cardinality label; value constraints SHALL follow
the value types (`sh:datatype` for one datatype, `sh:class` for one class, `sh:nodeKind`, `sh:or`
when mixed; a literal without a datatype but with a language counts as `rdf:langString`). Severity
SHALL follow the first matching rule: no cardinality label, or confidence below the acceptance
threshold → `sh:Info`; label support below 1, a class read in first-N mode, or `sh:class` under
`sh:class` when the run looked up object types across graphs, or a class with declared subclasses → `sh:Warning`; otherwise the default `sh:Violation`. Shapes SHALL be annotated with confidence and observed/total instances, and a first-N
class marked as sampled.

#### Scenario Outline: Severity from the threshold
- **WHEN** at threshold 0.8 a property of a class read in <mode> has <usage>
- **THEN** its property shape has severity <severity>

  Examples:
    | mode    | usage                                     | severity               |
    | exact   | presence only, no cardinality label       | sh:Info                |
    | exact   | confidence 0.3, label support 1.0         | sh:Info                |
    | exact   | confidence 1.0, label support 0.9         | sh:Warning             |
    | first-N | confidence 1.0, label support 1.0         | sh:Warning             |
    | exact   | confidence 1.0, label support 1.0         | sh:Violation (default) |

#### Scenario: Language-tagged literals without a datatype
- **WHEN** a store leaves the datatype of language-tagged literals unbound
- **THEN** the property shape allows `rdf:langString`, and the shapes still conform on that data

#### Scenario Outline: Counts from the cardinality label
- **WHEN** a property's accepted label is <label>
- **THEN** its property shape has <counts>

  Examples:
    | label        | counts                         |
    | exactly_one  | `sh:minCount 1`, `sh:maxCount 1` |
    | zero_or_one  | `sh:maxCount 1` only            |
    | one_or_more  | `sh:minCount 1` only            |
    | zero_or_more | neither                         |
    | exactly_n 3  | `sh:minCount 3`, `sh:maxCount 3` |

#### Scenario: Shapes report no violation on their own data
- **WHEN** the shapes generated from the e2e test data validate that same data with a SHACL engine
- **THEN** no result has severity `sh:Violation` (results at `sh:Warning` and `sh:Info` are expected, so `sh:conforms` may be false) (first-N classes and cross-graph types are at most `sh:Warning`)

#### Scenario: Sampled class is marked
- **WHEN** a class was read in first-N mode
- **THEN** its node shape is annotated with the observed and total instance counts and marked as sampled

### Requirement: PlantUML class diagram
The PlantUML generator SHALL write one `.puml` file per profiled graph, between one `@startuml` and
one `@enduml`, with each class once, its own and refined datatype properties as attributes with
multiplicities, its object properties as associations with multiplicities, and a generalisation per
parent — solid for declared, dashed for implied (DEC-6).

#### Scenario: Diagram content
- **WHEN** the diagram is generated for a profile with `ex:Person` (own `ex:name`, exactly one) whose implied parent is `ex:Agent`
- **THEN** the source shows class `ex:Person` once with attribute `ex:name` multiplicity `1` and a dashed generalisation to `ex:Agent`

### Requirement: Application-profile document
The document generator SHALL write one HTML file in the style of SEMIC / EU application profiles
and SHACL Play shacl-doc, with an overview and provenance (endpoint, date, settings), the namespaces
used, a chapter per graph holding its PlantUML source and a section per class (instances, parents,
and a table of property, value type, cardinality and usage), and a caveats section listing first-N
classes and recorded failures.

#### Scenario: Document sections
- **WHEN** the document is generated for the e2e test data profile
- **THEN** it has the overview, namespaces, one chapter per graph with a section per class, and the caveats section

#### Scenario: Failures and samples are flagged
- **WHEN** the profile holds a first-N class and one failure
- **THEN** the caveats section lists both, and the class section shows "first N of M"

### Requirement: Golden outputs
For a fixed profile each generator SHALL produce output equal to a checked-in golden file, so any
change to a representation is visible in review.

#### Scenario: Golden file per format
- **WHEN** each generator renders the fixed test profile
- **THEN** its output equals that format's golden file

### Requirement: The statistics report is unchanged
Adding the generators SHALL NOT change the statistics report, the `fingerprint` command's existing
options and exit codes, or the 1.x library function (DEC-8).

#### Scenario: Report untouched
- **WHEN** the existing report, command-line and library scenarios run with no format selected
- **THEN** they pass unchanged
