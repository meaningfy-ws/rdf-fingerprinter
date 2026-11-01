## MODIFIED Requirements

### Requirement: Namespace filters
This requirement holds for outputs rendered through `generate_representations`, the path of the
`fingerprint` command, every `fingerprint-gen-*` command, `fingerprint_report` and
`generate_from_profile_file`. A `Generator` built directly from analytics SHALL apply the hidden set
and hide the classes of the excluded set only.

Each `--exclude-namespace` and `--include-namespace` value (repeatable; `GeneratorOptions.exclude_namespaces`
and `include_namespaces` for library callers) SHALL be matched against the profile's namespace table
by the first rule that applies (EPIC DEC-6):
1. a value holding `:` SHALL match every namespace whose IRI starts with the value,
   case-sensitively (an IRI stem; a full namespace IRI also matches the namespaces under it);
2. a value holding `*` SHALL match every prefix it covers whole, `*` standing for any run of
   characters, possibly none, and every other character for itself, case-sensitively (a prefix glob);
3. any other value SHALL match the namespace with exactly that prefix.

The filters SHALL form two sets (EPIC DEC-7):
- **hidden**: the meta namespaces `http://www.w3.org/1999/02/22-rdf-syntax-ns#`,
  `http://www.w3.org/2000/01/rdf-schema#`, `http://www.w3.org/2002/07/owl#` and
  `http://www.w3.org/ns/shacl#`, less those matched by an include value. Every generator and the
  report SHALL leave out their classes, and only their classes;
- **excluded**: the namespaces matched by an exclude value, less those matched by an include value
  (include wins). No output SHALL write an IRI of an excluded namespace as a class, property, object
  class, co-type, parent, single value or glossary term (EPIC DEC-8). An output SHALL declare an
  excluded namespace's prefix only while a position it keeps still uses the namespace (a datatype,
  or SHACL's fixed prefixes `sh`, `xsd`, `rdf`, `rdfs`, `fp`); the report's namespace table SHALL
  list it anyway (below):
  - an excluded property SHALL have no pattern edge or incoming link, no ShExC triple constraint, no
    SHACL property shape, no PlantUML attribute, link or link count, and no report row;
  - an excluded object class SHALL be dropped from the value types of the property; its objects
    SHALL count as untyped resources, so the edge is written as `IRI` in the pattern schema and the
    ShExC, with `sh:nodeKind sh:IRI` and no `sh:class` for it in SHACL, and as `resource` in PlantUML;
  - classes merged by equal instances SHALL be merged from their kept classes only, and a co-type
    note SHALL name kept classes only; a class of a kept namespace SHALL stay whatever its co-types;
  - datatypes SHALL NOT be filtered, and neither SHALL pitfall findings (the TSV and the report's
    pitfall part, EPIC DEC-11) nor collection failures (the report's collection section).

The filter SHALL be applied once, to the analysed profile, before any output is built (EPIC DEC-4).
Every analysed value SHALL stay as analysed from the unfiltered profile, except that the excluded
terms are removed and that a property which lost an object class SHALL have its value types,
dominant value type, type purity and untyped share derived from its remaining value partitions. In
particular instance, triple and subject counts SHALL NOT change, and a property inherited from an
excluded parent SHALL stay inherited. Collection and the saved profile SHALL NOT change (EPIC DEC-1).

Every per-graph output where an excluded namespace hid an IRI in that graph SHALL carry one comment
line `excluded namespaces: <prefix> (classes <c>, properties <p>, values <v>)`, one entry per such
namespace in prefix order, joined by `; `, where `<c>`, `<p>` and `<v>` count the distinct IRIs of
the namespace hidden in that graph from class positions (classes, object classes, co-types,
parents), property positions and single-value positions. The comment SHALL start with `#` in the
pattern schema, the ShExC and the SHACL shapes, and with `'` in every PlantUML file of the graph.
The report SHALL list the same line per graph under its caveats, SHALL list every prefix of the
table with the excluded ones marked `excluded` and every namespace's uses counted on the unfiltered
profile, and SHALL NOT call a graph empty when its classes were excluded (EPIC DEC-9, DEC-10).

A value matching no namespace SHALL log `--exclude-namespace <name>: no such namespace; ignored` (or
the same for include). An exclude value that matches a namespace still excluded, but whose excluded
namespaces hide no IRI in any graph, SHALL log `--exclude-namespace <name>: no term in this
namespace; ignored`. An exclude value whose every namespace is included again SHALL log nothing.
Each warning SHALL be logged once per run (EPIC DEC-9).

#### Scenario: Meta vocabularies hidden by default
- **WHEN** shapes and diagrams are generated with no filter option for a profile holding `owl:Ontology` and `ex:Person`
- **THEN** `ex:Person` has a node shape and a box, and `owl:Ontology` has neither

#### Scenario: Meta properties kept by default
- **WHEN** every output is generated with no filter option for the filter test profile, where `ex:Person` has `rdfs:label`
- **THEN** every output still writes `rdfs:label` for `ex:Person`

#### Scenario: A meta namespace excluded by name
- **WHEN** every output is generated with `--exclude-namespace rdfs` for the filter test profile
- **THEN** no output writes `rdfs:label`

#### Scenario: Included again
- **WHEN** they are generated with `--include-namespace owl`
- **THEN** `owl:Ontology` has a node shape and a box

#### Scenario: Excluded by option
- **WHEN** the shapes, the diagram and the report are generated with `--exclude-namespace ex` for a profile holding `owl:Ontology` and `ex:Person` with the property `ex:name`
- **THEN** no `ex:` class has a node shape, a box or a report section, and no output writes an `ex:` property

#### Scenario Outline: Properties of an excluded namespace
- **WHEN** the <output> is generated with `--exclude-namespace rel` for the filter test profile, where `ex:Person` has `ex:name` and the singleton properties `rel:r1` and `rel:r2` pointing to `ex:Person`
- **THEN** it holds no `rel:` name, and still writes `ex:name` for `ex:Person`

  Examples:
    | output         |
    | pattern schema |
    | ShExC          |
    | shapes         |
    | diagram        |
    | report         |

#### Scenario Outline: An edge to an excluded class
- **WHEN** the <output> is generated with `--exclude-namespace org` for the filter test profile, where `ex:memberOf` points from `ex:Person` to `org:Unit`
- **THEN** `ex:memberOf` is written as <written>

  Examples:
    | output         | written                                                        |
    | pattern schema | an edge `-ex:memberOf-> IRI`                                   |
    | ShExC          | the triple constraint `ex:memberOf IRI`                        |
    | shapes         | a property shape with `sh:nodeKind sh:IRI` and no `sh:class`   |
    | diagram        | the attribute `ex:memberOf : resource`, with no link            |
    | report         | a row whose value types do not name `org:Unit`                 |

#### Scenario: A merged class loses its excluded member
- **WHEN** the pattern schema is generated with `--exclude-namespace org` for a profile where all 5 `ex:Agent` instances are also the 5 `org:Member` instances
- **THEN** the block is headed `(:ex:Agent) 5`, with no `org:` name, where without the option it is headed `(:ex:Agent&org:Member) 5`

#### Scenario Outline: Matching a filter value
- **WHEN** the outputs are generated with `--exclude-namespace <value>` for a profile with the namespaces `ex` (`http://example.org/`), `rel` (`http://example.org/rel/`), `relx` (`http://example.org/relx/`) and `org` (`http://org.example/`)
- **THEN** the excluded namespaces are <excluded>

  Examples:
    | value                   | excluded                                         |
    | rel                     | `rel`                                            |
    | rel*                    | `rel` and `relx`                                 |
    | *x                      | `relx`                                           |
    | http://example.org/rel/ | `rel`                                            |
    | http://example.org/     | `ex`, `rel` and `relx`                           |
    | Rel*                    | none, and a warning says `Rel*` is no namespace  |

#### Scenario: Include wins over exclude
- **WHEN** the outputs are generated with `--exclude-namespace http://example.org/` and `--include-namespace ex` for the filter test profile
- **THEN** `ex:Person` and `ex:name` are written, and no `rel:` name is

#### Scenario: Unknown name
- **WHEN** `--exclude-namespace nope` is given and no namespace has the prefix or IRI `nope`
- **THEN** a warning names `nope`, and the outputs are as without the option

#### Scenario: A name that hides nothing
- **WHEN** the outputs are generated with `--exclude-namespace foaf` for the filter test profile, whose prefix table names `foaf` but which has no `foaf:` term
- **THEN** one warning says `--exclude-namespace foaf: no term in this namespace; ignored`, and the outputs are as without the option

#### Scenario Outline: Excluded namespaces are noted
- **WHEN** the <output> is generated with `--exclude-namespace rel` for the filter test profile
- **THEN** it carries <note>, and without the option it carries none

  Examples:
    | output         | note                                                                                    |
    | pattern schema | the line `# excluded namespaces: rel (classes 0, properties 2, values 0)`               |
    | ShExC          | the line `# excluded namespaces: rel (classes 0, properties 2, values 0)`               |
    | shapes         | the line `# excluded namespaces: rel (classes 0, properties 2, values 0)`               |
    | diagram        | the line `' excluded namespaces: rel (classes 0, properties 2, values 0)` in every file  |
    | report         | the same text for the graph under its caveats, and `rel` marked excluded in its table   |

#### Scenario: Datatypes are not filtered
- **WHEN** every output is generated with `--exclude-namespace xsd` for the filter test profile, where `ex:name` holds `xsd:string` literals
- **THEN** every output still gives `ex:name` the type `xsd:string`, and a warning says `xsd` hides no term

#### Scenario: Pitfall findings are not filtered
- **WHEN** the pitfalls file and the report are generated with `--exclude-namespace rel` for a scanned profile whose finding names `rel:r1` as an example
- **THEN** both still list that example

#### Scenario: Every class of a graph excluded
- **WHEN** the outputs are generated with `--exclude-namespace org` for a profile whose graph holds only `org:` classes
- **THEN** no shapes, diagram, pattern schema or ShExC file is written for that graph, and the report says its classes are hidden, not that it is empty

#### Scenario: The saved profile keeps excluded terms
- **WHEN** the pattern schema is generated from a saved profile with `--exclude-namespace rel`, then again without it
- **THEN** the profile file is unchanged, the first output holds no `rel:` name and the second holds `rel:r1`
