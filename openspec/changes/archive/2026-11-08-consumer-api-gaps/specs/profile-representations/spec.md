## ADDED Requirements

### Requirement: Diagram files are described
`describe_diagrams(run, output_location, ...)` SHALL return, for each PlantUML file
`generate_representations` writes for the same arguments, a `DiagramFile` with its path, format,
graph (None for the default graph), kind (`overview` or `module`), module (the namespace prefix, None
for an overview) and part (the number of a split module, else None), and SHALL write nothing
(consumer-api-gaps C-3).

#### Scenario: Each diagram file is described
- **GIVEN** a profile with classes in two vocabularies
- **WHEN** the diagram files are described
- **THEN** one file is the overview and the other two are the modules "ex" and "foaf", each with the graph and no part

#### Scenario: A split module has its part number
- **GIVEN** a profile with five classes of one vocabulary
- **WHEN** the diagram files are described with module size 2
- **THEN** the module "ex" has parts 1, 2 and 3

### Requirement: Formats are documented
The API reference SHALL name every format `fingerprint_report` accepts besides the report itself and
the files each writes (consumer-api-gaps C-4).

#### Scenario: The API reference names every format
- **WHEN** the API reference is read
- **THEN** it names shacl, puml, pattern, shex and pitfalls
