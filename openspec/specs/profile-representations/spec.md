# profile-representations Specification

## Purpose
The saved profile file and the representations generated from it without querying: the LinkML-shaped generator framework, SHACL shapes graded by what the profile observed, PlantUML class diagrams, the report page as the document, namespace filters and modular diagrams, and their commands (UC-W2).
## Requirements
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
have its own command (SHACL, PlantUML, profile document, pattern schema, ShExC) and SHALL render
through eds4jinja2 from a packaged template package (DEC-4).

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
The SHACL generator SHALL write one Turtle file per profiled graph with a shown class, with an
open `sh:NodeShape` per shown class (see "Namespace filters"), named by the "Shape IRI policy"
(`sh:targetClass`, no `sh:closed`) holding a `sh:PropertyShape` per property, inherited ones
included (archived change 2026-10-31-profile-representations, DEC-5). Counts SHALL follow the accepted cardinality label; value constraints SHALL follow
the value types (`sh:datatype` for one datatype, `sh:class` for one class, `sh:nodeKind`, `sh:or`
when mixed; a literal without a datatype but with a language counts as `rdf:langString`). Severity
SHALL follow the first matching rule: no cardinality label, or confidence below the acceptance
threshold → `sh:Info`; label support below 1, a class read in first-N mode, `sh:class` when the run looked up object
types across graphs, or a class with declared subclasses → `sh:Warning`; otherwise the default `sh:Violation`. Shapes SHALL be annotated with confidence and observed/total instances, and a first-N
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

#### Scenario: A class with declared subclasses is graded at most Warning
- **WHEN** a class with a declared subclass has a property that every instance has
- **THEN** its property shape has severity `sh:Warning`

### Requirement: PlantUML class diagram
The PlantUML generator SHALL write, for each non-empty profiled graph, an overview diagram
`diagram-<graph slug>.puml` and one diagram per module, `diagram-<graph slug>--<module>.puml`. Each
file SHALL get its own view, marked as an overview or a module, together with the graph's label and
slug. Each
diagram SHALL lie between one `@startuml` and one `@enduml`.

The overview SHALL show a package for each namespace with a shown class, labelled with its prefix
and its number of shown classes. It SHALL also show a package, marked `referenced`, for each other
namespace that is not hidden and holds a link target. For each ordered pair of different packages
it SHALL show one arrow, labelled with the number of links from the first to the second. A link is
an association (a shown class, an object property and its single value class) or a generalisation
to a parent, counted once each. Links to hidden classes SHALL NOT be drawn or counted.

A module SHALL be a namespace's shown classes, or, when there are more of them than the module size
(`--module-size`, default 15), one cluster of them. A module's name SHALL be the prefix, with `~1`,
`~2`, … added for clusters (`~` never occurs in a prefix, so module names cannot collide). Every shown class SHALL be in exactly one module. Clusters SHALL be built
deterministically:
1. The weight of a pair of classes is the number of links between them, in either direction.
2. **Seed.** Among the unassigned classes linked to at least one other unassigned class, seed a
   cluster with the one whose weights to the unassigned classes sum highest (ties: by short name).
3. **Grow.** While the cluster is smaller than the module size, add the unassigned class whose
   weights to the cluster's members sum highest, if that sum is above 0 (ties: by short name).
4. **Repeat.** Go back to step 2 while some unassigned class is linked to another unassigned class.
5. **Rest.** Chunk the classes still unassigned into clusters of at most the module size, in short
   name order.
6. **Naming.** Number the clusters `~1`, `~2`, … in the order they were made.

In a module each class SHALL appear once, with its own and refined properties only. An object
property with exactly one value class and no untyped objects SHALL be an association, with its
multiplicity, to that class, whether or not the class is profiled; any other property SHALL be an
attribute listing its value types, with its multiplicity. Each shown parent SHALL get a
generalisation: solid when declared, dashed when implied. The overview SHALL count exactly these
associations and generalisations, minus those to hidden classes. A class outside the
module, or an unprofiled class, SHALL appear as a reference box without members. A generalisation to a hidden class SHALL be
left out; an association to a hidden class SHALL keep the class as a reference box. No diagram SHALL
be generated per class (EPIC DEC-7).

#### Scenario: Diagram content
- **WHEN** the diagram is generated for a profile with `ex:Person` (own `ex:name`, exactly one) whose implied parent is `ex:Agent`
- **THEN** the `ex` module shows class `ex:Person` once, with attribute `ex:name` of multiplicity `1` and a dashed generalisation to `ex:Agent`

#### Scenario: Clusters of a small namespace
- **WHEN** namespace `ex` holds classes A–G with links A–B (2), B–C (1), C–D (1) and E–F (1), G unlinked, and the module size is 3
- **THEN** the modules are `ex~1` = {A, B, C}, `ex~2` = {E, F} and `ex~3` = {D, G}, while a namespace prefixed `ex-1` is the module `ex-1` (file `…--ex-1.puml`)

#### Scenario: Big namespace is split
- **WHEN** a graph's namespace holds 40 classes and the module size is 15
- **THEN** that namespace yields at least three module diagrams of at most 15 classes each, every class is in exactly one of them, and the file set and contents are the same on every run

#### Scenario: Overview
- **WHEN** the diagrams are generated for a profile where 3 `ex:` classes have object properties whose values are `foaf:Person`
- **THEN** the overview has the package `ex`, the package `foaf` marked `referenced` (when no `foaf:` class is profiled), and one arrow from `ex` to `foaf` labelled `3`

### Requirement: Application-profile document
The document generator SHALL write the report page `main.html` from a saved profile. The page and
its content are specified by `fingerprint-report` "Report content", "One self-contained page" and
"Navigation, search and filters" (EPIC DEC-3).

#### Scenario: Document written from a profile file
- **WHEN** `fingerprint-gen-doc` renders a saved profile into an empty folder
- **THEN** the folder holds `main.html` and no `profile.html`

#### Scenario: Failures and samples are flagged
- **WHEN** the profile holds a first-N class and one failure
- **THEN** the collection section lists the failure, the caveats list the first-N class, and the class section shows "first N of M"

### Requirement: Golden outputs
Every file each generator writes for a fixed profile SHALL equal a checked-in golden file (the
page, each shapes file, the overview and each module diagram, each pattern schema and each ShExC
file), so any change to a representation is visible in review.

#### Scenario: Golden file per output
- **WHEN** each generator renders the fixed test profile
- **THEN** every written file equals its golden file, and no golden file is left unmatched

### Requirement: Shape IRI policy
The shapes base of a class SHALL be its namespace without the trailing `#`, `/` or `:`, followed by
`/shape/`, or by `:shape:` for a `urn:` namespace. It SHALL be declared under the prefix
`<class prefix>-shape`. A node shape SHALL be named `<shapes base><local>`, and its property shapes
`<shapes base><local>-<property prefix>-<property local>`. With a shapes namespace given, every
shape SHALL be in it, declared as `shape:`, and named `<class prefix>-<local>`, with property shapes
named `<class prefix>-<local>-<property prefix>-<property local>`. A class or property equal to
its namespace SHALL use the local name `_`. Collisions are counted per shapes IRI, whatever prefix
writes it. When two shapes of one file get the same IRI, those after
the first in class and property IRI order SHALL get `-2`, `-3`, ….
Shape IRIs SHALL be the same on every run (EPIC DEC-6).

#### Scenario Outline: Shape names
- **WHEN** shapes are generated for class <class> (prefix `bf`) and property `bf:name`, with shapes namespace <given>
- **THEN** the node shape is <node> and the property shape is <property>

  Examples:
    | class                                                      | given                   | node                                                                                | property                                                     |
    | `https://ontology.brainframe.com/2016/04/brainframe#Asset` | none                    | `https://ontology.brainframe.com/2016/04/brainframe/shape/Asset` (`bf-shape:Asset`) | `bf-shape:Asset-bf-name`                                     |
    | `https://ontology.brainframe.com/2016/04/brainframe#Asset` | `http://ex.org/shapes/` | `http://ex.org/shapes/bf-Asset` (`shape:bf-Asset`)                                  | `shape:bf-Asset-bf-name`                                     |
    | `urn:x:Asset` (prefix `x`)                                 | none                    | `urn:x:shape:Asset` (`x-shape:Asset`)                                               | `x-shape:Asset-bf-name`                                      |

#### Scenario: Colliding shape names
- **WHEN** the profile holds both `http://ex.org/a#Thing` and `http://ex.org/a/Thing`
- **THEN** their node shapes are `…/a/shape/Thing` and `…/a/shape/Thing-2`, in IRI order

### Requirement: Namespace filters
The rules below SHALL hold for outputs rendered through `generate_representations`, the path of the
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
    | *lx                     | `relx`                                           |
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
    | pattern schema | the line `Excluded namespaces: rel (classes 0, properties 2, values 0).` in every patterns Markdown file (llm-schema-split) |
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

### Requirement: No files for empty graphs
A profiled graph with no shown class SHALL produce no SHACL, PlantUML, pattern-schema or ShExC
file; the report SHALL still list it, as empty.

#### Scenario: Empty default graph
- **WHEN** the shapes, diagrams, pattern schema and ShExC are generated for a profile whose default graph is empty
- **THEN** no `shapes-default.ttl`, no `diagram-default*.puml`, none of `prefixes-default.md`, `patterns-default.md`, `patterns-default.csv`, `glossary-default.md`, `glossary-default.csv` and no `shex-default.shex` is written, and the report lists the default graph as empty

### Requirement: Pattern view
The pattern schema and the enriched ShExC SHALL both render from one pattern view per graph. The
view SHALL be built from the profile's analytics and term annotations only, and SHALL add no
query (EPIC DEC-2, DEC-14, DEC-18). It SHALL follow rules N1–N9 of the EPIC's
`inputs/pattern-schema-option.md`, "Refined format" (DEC-13), made exact as follows:
1. **Merged groups (N2).** Two classes of a graph SHALL be in one group when the co-type count of
   one for the other equals both of their instance counts; grouping is transitive. A group's name
   SHALL be its members' prefixed names, sorted, joined by `&`. Its properties SHALL be the union
   of its members' properties; for a property more than one member has, the first member in name
   order that has it supplies the profile. Its instance count is any member's.
2. **Nested groups (N7).** A group SHALL be nested, with no block of its own, when the objects
   that reach it are all blank nodes and at least one is, and the distinct blank-node objects
   reaching it, summed once per source group and property, are at least its instance count.
   Otherwise it is a named group.
3. **Blocks (N1).** Each named group with at least one member that the filters show
   ("Namespace filters", "Size filters") SHALL get one block. The block's name SHALL list every
   member, hidden ones included. A named group with no shown member SHALL get no block, and its
   classes count as hidden. A nested group that no edge of the view reaches (it is reached only
   from groups without a block, or only from itself) SHALL count as hidden too, so no class
   disappears unreported.
4. **Edges (N3).** A block SHALL hold one edge per property, ordered by prefixed name. The
   edge's target SHALL list its alternatives in this order:
   - the target groups, by name, inside one `(:…|…)`, hidden groups included;
   - the literal datatypes, by name; a literal with a language and no datatype counts as
     `rdf:langString`, and one with neither as `xsd:string`;
   - `IRI` for untyped IRI objects;
   - `BNODE` for untyped blank-node objects.
   A property without value partitions SHALL have the target `.`. A group typed in another
   graph SHALL be written `T @<graph IRI>`, the graph always the full `<iri>`; a class typed in a
   graph whose IRI cannot be written SHALL be written without the graph and the graph reported as skipped.
5. **Incoming links (N6).** A block's `via` list SHALL name every pair of a source group with a
   block or nested in the view and a property whose objects are in the group, ordered by source
   name, then property. It SHALL write names only; each link's triple count is printed once, on
   the source's outgoing edge.
6. **Chains (N7).** A hop is one edge. Edges SHALL sit at levels 1 to 3: level 1 holds the
   block's own edges, and an expanded nested group's edges sit one level below the edge that
   reaches it, so a chain holds at most 3 edges (class → blank node → blank node → target). An
   edge at level 1 or 2 into a nested group SHALL be expanded when it is that group's chosen edge.
   Each nested group SHALL be expanded under exactly one edge of the view, chosen level by level
   from the top. Among the edges at the shallowest level reaching it, the chosen edge is the one
   with the most triples into the group, then the smallest source name, then the smallest
   property name. Every other edge into an expanded group SHALL end in ` ^`. An edge into a
   nested group that is not expanded anywhere, because every edge reaching it is at level 3,
   SHALL end in ` …`. A group SHALL NOT be expanded inside its own expansion. An edge into several nested groups SHALL
   expand only the first of the groups chosen for it, by name (the others go to their next best edge),
   so that no property begins two edges at the same place; it SHALL end in ` …` when another of its nested targets is expanded
   nowhere.
7. **Names (DEC-16).** Every IRI SHALL be written as `prefix:local` from the profile's prefix
   table when the local part is a safe Turtle local name, and as `<IRI>` otherwise. An IRI that
   fails the IRIREF guard SHALL be left out of both outputs and reported as skipped.

#### Scenario: A chain deeper than three hops
- **WHEN** a profile has `ex:A` with `ex:p` to blank nodes of `ex:B`, `ex:B` with `ex:q` to blank nodes of `ex:C`, `ex:C` with `ex:r` to blank nodes of `ex:D`, and `ex:D` with `ex:s` to blank nodes of `ex:E`
- **THEN** the `ex:A` block holds `-ex:p->` at level 1, `ex:B`'s `-ex:q->` at level 2 and `ex:C`'s `-ex:r-> (:ex:D) bn …` at level 3, which ends the chain, and neither `ex:D` nor `ex:E` has a block

#### Scenario: A blank-node cycle is expanded once
- **WHEN** a profile has `ex:List` blank nodes whose `ex:rest` points to blank nodes of `ex:List`, reached from `ex:A` by `ex:items`
- **THEN** `ex:List` is expanded once under `-ex:items->`, and its nested `-ex:rest-> (:ex:List) bn ^` is not expanded

#### Scenario: A class with unreached instances keeps its block
- **WHEN** blank nodes of `ex:Note` are reached by 3 distinct objects and `ex:Note` has 5 instances
- **THEN** `ex:Note` has a block of its own, and the edges into it end without nesting

#### Scenario: An object type from another graph
- **WHEN** a profile collected with `any_graph` records `ex:knows` objects of class `ex:Person` typed in graph `http://ex.org/people`
- **THEN** the edge target is written `(:ex:Person @<http://ex.org/people>)`

### Requirement: Pattern schema output
The pattern generator SHALL write five files for each graph with a block, through the
`fingerprint-gen-pattern` command and `--format pattern` (llm-schema-split DEC-1, DEC-8):
`prefixes-<graph slug>.md` ("Prefix file"), `patterns-<graph slug>.md` (below),
`patterns-<graph slug>.csv` ("Patterns CSV"), `glossary-<graph slug>.md` and
`glossary-<graph slug>.csv` ("Term labels and descriptions in the outputs", "Glossary CSV"). It
SHALL NOT write `pattern-<graph slug>.txt`. All five SHALL render from the graph's one pattern
view through one template package.

`patterns-<graph slug>.md` SHALL hold, in this order:
1. the line `# Patterns of <graph label>`;
2. the line ``Prefixes: `prefixes-<graph slug>.md` · glossary: `glossary-<graph slug>.md` ``;
3. the line `Legend: (:A&B) n: classes with the same n instances · ~m first_n: statistics over the first m read · co C k: k also typed C · via (:S)-p: incoming links · -p-> (:T|U) object classes · IRI, BNODE untyped · . not collected · deeper indent: a blank node's own edges, statistics over all its instances, up to 3 hops · ^ expanded under another edge · … deeper than 3 hops · k/n instances having p (omitted: all) · ×a-b values per instance (omitted: 1) · bn blank nodes · @n languages, @tag one language · =v one value · lo..hi range · dN distinct values (omitted: all differ) · presence found, not measured`;
4. `Hidden: <n> classes.` when n > 0 classes are hidden ("Pattern view" rule 3), and
   `Excluded namespaces: <note>.` when the namespace filter hid something;
5. per block, by instances, largest first, then by name: the heading `## <group name>`, then a
   fenced code block, with the info string `text` and a fence of three backticks, holding the
   block header and its edge lines.
It SHALL hold no prefix declarations and no glossary.

A block header SHALL be `(:<group>) <instances>`, followed by ` ~<observed> first_n` for a group
read in first-N mode, then ` co <class> <k>` for each co-type that is not merged, joined by `, `,
then ` via ` and the `via` list joined by `, `. An edge line SHALL be two spaces per level,
`-<property>-> <target>`, then its statistics, each after one space, in this order (N4, N5):
- `k/n`, when k, the instances with the property, is below n, the observed instances;
- `×a` or `×a-b`, the fewest and most values per instance that has the property, unless both
  are 1;
- `bn`, when some objects are blank nodes;
- `@<tag>` for one language, `@<n>` for n > 1 languages;
- for a property with one literal datatype other than `rdf:langString` and a known range,
  `=v` when its lowest and highest values are equal, else `lo..hi`;
- `=<name>`, for a property whose objects are all IRIs, with one distinct object, when the
  profile holds its top values (depth `rich_values` or deeper): the IRI written as a name by
  rule 7 of "Pattern view" (DEC-16). Without top values nothing is printed for it, and no query
  is added (DEC-14);
- `d<N>`, when the distinct objects are fewer than the triples and no `=v` or `=<name>` is
  written;
- `presence`, for a property found only by the completeness check, with no other statistic.

A value SHALL be written bare when it is not empty, holds no white space and no `"`, and has no
`..`. Otherwise, or when it is longer than 64 characters, it SHALL be written as a JSON string. A
longer value SHALL be cut to 64 characters and end in `…` inside the quotes.

#### Scenario Outline: Lines of the continents pattern schema
- **WHEN** the pattern schema is generated from the sample profile
- **THEN** `patterns-continents-214e8f67.md` holds the line <line>

  Examples:
    | line                                                                                                                                         |
    | `(:euvoc:Continent&skos:Concept) 6`                                                                                                          |
    | `  -euvoc:startDate-> xsd:date =1952-07-24`                                                                                                  |
    | `  -euvoc:status-> IRI d1`                                                                                                                   |
    | `  -skosxl:prefLabel-> (:skosxl:Label) ×24 bn`                                                                                               |
    | `    -lvont:script-> IRI 12/145 d2`                                                                                                          |
    | `    -skosxl:literalForm-> rdf:langString @24`                                                                                               |
    | `    -rdf:value-> xsd:string AFRICA..OCEANIA`                                                                                                |
    | `(:owl:Ontology&skos:ConceptScheme) 1 via (:euvoc:Continent&skos:Concept)-skos:inScheme, (:euvoc:Continent&skos:Concept)-skos:topConceptOf` |
    | `  -skosxl:prefLabel-> (:skosxl:Label) bn ^`                                                                                                 |
    | `## euvoc:Continent&skos:Concept`                                                                                                            |

#### Scenario: Five files per graph
- **WHEN** the pattern schema is generated from the sample profile
- **THEN** for each of `continents-214e8f67`, `treaties-3b4301a8` and `default` exactly `prefixes-<slug>.md`, `patterns-<slug>.md`, `patterns-<slug>.csv`, `glossary-<slug>.md` and `glossary-<slug>.csv` are written, and no `.txt` file

#### Scenario: One block per class group and one edge per property
- **WHEN** the pattern schema is generated from the sample profile
- **THEN** in every `patterns-<slug>.md` no group name begins two blocks, no property begins two edges at the same place, `skosxl:Label`, `euvoc:XlNotation` and `euvoc:XlNote` begin no block, and every prefix of the matching `prefixes-<slug>.md` is used in it

#### Scenario Outline: Values that need quotes
- **WHEN** a literal property's lowest and highest values are both <value>
- **THEN** its edge ends in <written>

  Examples:
    | value                     | written                                                                |
    | `Treaty of Rome`          | `="Treaty of Rome"`                                                    |
    | `1..2`                    | `="1..2"`                                                              |
    | the empty string          | `=""`                                                                  |
    | 70 times the letter `a`   | `="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa…"` |

#### Scenario: A single IRI value is written as a prefixed name
- **WHEN** a profile collected at depth `rich_values` has `ex:status` whose objects are all the one IRI `http://ex.org/status/active`, recorded as its top value, and the prefix table maps `exs` to `http://ex.org/status/`
- **THEN** the edge is `-ex:status-> IRI =exs:active`, the prefix file lists `exs`, and the same profile without top values gives `-ex:status-> IRI d1`

#### Scenario: A class read in first-N mode
- **WHEN** a profile has `ex:Big` with 50000 instances, 10000 of them read in first-N mode, and `ex:name` on 9000 of those
- **THEN** its block header is `(:ex:Big) 50000 ~10000 first_n`, and its `ex:name` edge holds `9000/10000`

#### Scenario: Unusual IRIs in the LLM outputs
- **WHEN** the profile holds the class IRI `http://ex.org/q?a=1&b='x'`
- **THEN** the patterns Markdown and CSV write it as `<http://ex.org/q?a=1&b='x'>`, and the ShExC leaves it out, lists it after `# skipped:`, and parses

### Requirement: Enriched ShExC output
The ShExC generator SHALL write `shex-<graph slug>.shex` for each graph with a block, through the
`fingerprint-gen-shex` command and `--format shex`. It SHALL render the same pattern view (EPIC
DEC-18 amendment, DEC-27), with this mapping:
- one `PREFIX` line per prefix used; then the legend line
  `# comments use the pattern schema's legend: k/n instances having p (omitted: all) · ×a-b values per instance (omitted: 1) · bn blank nodes · @n languages, @tag one language · =v one value · lo..hi range · dN distinct values (omitted: all differ) · presence found, not measured · … deeper than 3 hops`;
  then `# hidden: <n> classes` when n > 0 classes are hidden ("Pattern view" rule 3); then the `# skipped:` line (below), if any;
- per block, the comment `# ` plus the pattern block header, then a shape labelled with the
  first member of the group, in name order, that the filters show and whose IRI holds no `=`. A group
  with no such member gets no shape, and a reference to it is `IRI`. A file is written for each
  graph with a pattern block, even when every shape is dropped (the header and the glossary only);
- per edge, a triple constraint `<property> <value> <cardinality> ;`, followed by two spaces and
  `# <comment>` if and only if the comment is non-empty. The comment is, joined by single spaces:
  the pattern target text when a target alternative is a class group; then the edge's statistic
  tokens (`=<name>` included); then `… deeper than 3 hops` for an edge into a group expanded nowhere. It is
  empty when none of these applies (for example `owl:imports IRI ;`);
- value: a group with a shape in the file is `@<shape>`; any other class (hidden, from another
  graph, or not profiled) is `IRI`; a datatype is itself; untyped objects are `IRI` or `BNODE`;
  `.` stays `.`. Two or more alternatives SHALL be joined as `(a OR b …)`, without duplicates;
- a nested group expanded nowhere in the pattern view (every edge reaching it is at level 3)
  SHALL get no shape, whatever the number of edges reaching it; each of those edges SHALL be
  `BNODE`, with `… deeper than 3 hops` in its comment. This case wins over the next two, but only
  for that group: a hidden or other class on the same edge stays `IRI` (`(BNODE OR IRI)`);
- an expanded nested group SHALL be written inline when exactly one edge of the view reaches it:
  `<indent><property> BNODE {`, then `  # <comment>` if it is non-empty, then its constraints one
  level deeper, then `<indent>}`, the cardinality if any (`} {0,2}`), and ` ;`. The indent is two
  spaces per level, with triple constraints at levels 1 to 3 as in the pattern view. When more
  than one edge reaches it, it SHALL be one shape `<label> BNODE { … }`, after the block shapes,
  referenced as `BNODE @<label>` from every edge reaching it, whose own constraints start again at
  level 1;
- cardinality: `?` for 0–1, nothing for exactly 1, `{a}` for exactly a > 1, `{a,b}` otherwise.
  The minimum is 0 when some instances lack the property. A property with no histogram is `*`;
- the glossary at the end: the line `# glossary: none` when it has no entry, else the line
  `# glossary` followed by each glossary line ("Term labels and descriptions in the outputs")
  after `# `;
- a term whose IRI holds `=` SHALL be left out and listed on one `# skipped: <IRI> …` line, after
  the legend and the hidden line, because PyShExC rejects `=` in an IRI.
Every ShExC file SHALL parse with PyShExC, its `parse` returning a `Schema`.

#### Scenario: The ShExC output parses
- **WHEN** the ShExC is generated from the sample profile
- **THEN** each of the three files parses with PyShExC

#### Scenario Outline: Lines of the continents ShExC
- **WHEN** the ShExC is generated from the sample profile
- **THEN** `shex-continents-214e8f67.shex` holds the line <line>

  Examples:
    | line                                                                             |
    | `euvoc:Continent {`                                                              |
    | `  euvoc:startDate xsd:date ;  # =1952-07-24`                                    |
    | `  euvoc:xlNotation BNODE {  # (:euvoc:XlNotation) bn`                           |
    | `  skosxl:prefLabel BNODE @skosxl:Label {24} ;  # (:skosxl:Label) ×24 bn`        |
    | `  skos:inScheme @skos:ConceptScheme ;  # (:owl:Ontology&skos:ConceptScheme) d1` |
    | `skosxl:Label BNODE {`                                                           |
    | `  lvont:script IRI ? ;  # 12/145 d2`                                            |

### Requirement: Term labels and descriptions in the outputs
Classes and properties SHALL get labels, alt labels, descriptions and notes from two sources
(llm-schema-tools DEC-6; llm-schema-split DEC-5):
- the `--ontology FILE` option of `fingerprint-gen-pattern` and `fingerprint-gen-shex`, read at
  render time with the same predicates and selection as statistics-collection "Term labels and
  descriptions are collected";
- the profile's stored term annotations.

Per term and per field (labels, alt labels, descriptions, notes), the ontology's values SHALL be
used when it has any, else the data's; the two are never merged (llm-schema-tools DEC-7). A file
that is missing, unreadable or not RDF in a format rdflib reads by its extension SHALL be a usage
error (exit 2) that names the file, and nothing SHALL be written.

The glossary SHALL list, sorted by prefixed name, each term the output uses that has a label, an
alt label or a description (N9), one line each:
`<name> <kind>[ "<label>"[@<lang>]][ alt: "<a>" | "<b>" …][: <description>]` (llm-schema-split
DEC-7, DEC-10):
- the kind SHALL be the term's kind codes ("Glossary CSV"), several joined by `/`;
- the label SHALL be the shown label; a term with no label SHALL show its shown alt label instead;
- `alt:` SHALL list, JSON-quoted and joined by ` | `, the term's alt labels in the language of
  the label shown, except the one shown as the label; it is left out when none remain;
- the description SHALL be the shown description, its white space collapsed to single spaces,
  cut to 200 characters ending in `…`.
The text shown SHALL be the untagged value if there is one, else `en`, else the smallest language
tag. Notes SHALL NOT appear in the glossary lines.

`glossary-<graph slug>.md` SHALL hold the line `# Glossary of <graph label>`, then either each
glossary line after `- `, or, with no entry, the line
`No term of this graph has a label or a description.` A profile saved before term annotations
existed SHALL load, and SHALL render as a profile with no annotations.

#### Scenario: Labels from an ontology file
- **WHEN** the pattern schema is generated from the sample profile with the label fixture ontology
- **THEN** `glossary-continents-214e8f67.md` holds `- skos:Concept C "Concept"@en alt: "Notion": An idea or notion; a unit of thought.` and `- skosxl:prefLabel oP "preferred label"@en`, and has no line for `euvoc:Continent`

#### Scenario: A term with only alt labels
- **WHEN** the pattern schema is generated from the sample profile with the label fixture ontology
- **THEN** `glossary-treaties-3b4301a8.md` holds the line `- skosxl:altLabel oP "alternative label"@en`

#### Scenario: A term with notes only
- **WHEN** a term the output uses has the note `"Internal"@en` and no label, alt label or description
- **THEN** `glossary-<slug>.csv` has its row with `notes` `Internal`, and the glossary Markdown and the ShExC have no line for it

#### Scenario: Alt labels in another language are not shown
- **WHEN** a term has the label `"Concept"@en` and the alt labels `"Begriff"@de` and `"Notion"@en`
- **THEN** its glossary line holds `"Concept"@en alt: "Notion"` and not `Begriff`

#### Scenario: The ontology wins for the fields it gives
- **WHEN** the data labels `ex:Person` `"Persoon"@nl` with the description `"Iemand"@nl`, and the ontology labels it `"Person"@en` with no description
- **THEN** the glossary line of the class `ex:Person` is `ex:Person C "Person"@en: Iemand`

#### Scenario Outline: The label shown
- **WHEN** a term's labels are <labels>
- **THEN** the glossary shows <shown>

  Examples:
    | labels                                  | shown             |
    | `"Begriff"@de`, `"Concept"@en`, `"C"`   | `"C"`             |
    | `"Begriff"@de`, `"Concept"@en`          | `"Concept"@en`    |
    | `"Begriff"@de`, `"Concept"@fr`          | `"Begriff"@de`    |

#### Scenario: Unreadable ontology file
- **WHEN** `fingerprint-gen-pattern` is given `--ontology` naming a file that is not RDF
- **THEN** it exits 2 with a message naming the file and writes nothing

#### Scenario: A profile saved before term annotations
- **WHEN** the pattern schema is generated from a profile saved before 3.2, with no term annotations
- **THEN** it is written, `glossary-<slug>.md` holds `No term of this graph has a label or a description.`, and `glossary-<slug>.csv` holds its header row only

### Requirement: Size filters
The pattern and ShExC generators SHALL take `--min-instances N` and
`--max-classes K`, each at least 1 (EPIC DEC-22). After the namespace filters, a named group with
fewer than N instances SHALL be hidden. Of the named groups left, only the K with the most
instances SHALL be shown, ties broken by name. Hidden groups SHALL behave as namespace-hidden
ones: no block, still named as edge targets, and absent from `via` lists. A value below 1 SHALL
be a usage error (exit 2).

#### Scenario: Small classes hidden
- **WHEN** the pattern schema of the sample profile is generated with `--min-instances 2`
- **THEN** `patterns-treaties-3b4301a8.md` has no `(:owl:Ontology&skos:ConceptScheme)` block and holds `Hidden: 2 classes.`, and the edge `-skos:inScheme-> (:owl:Ontology&skos:ConceptScheme) d1` is still there

#### Scenario: Only the largest classes
- **WHEN** the pattern schema of the sample profile is generated with `--max-classes 1`
- **THEN** each `patterns-<slug>.md` has one block, the largest named group of its graph, and each `patterns-<slug>.csv` one row of depth 0

### Requirement: Prefix file
`prefixes-<graph slug>.md` SHALL hold the line `# Prefixes of <graph label>`, then a Markdown table
with the header `| prefix | namespace | classes | properties | instances | triples |` and one row
per prefix of the IRIs the graph's pattern view writes, sorted by prefix (llm-schema-split DEC-3).
The namespace SHALL be written `<namespace IRI>`, with any `|` written `\|`. Counted over the
view only, for the namespace of the prefix:
- `classes`: the distinct class IRIs among the members of the groups with a block and of the
  expanded nested groups;
- `properties`: the distinct property IRIs of the edges written, at any depth;
- `instances`: the sum of the instance counts of those classes, each class once;
- `triples`: the sum of the triple counts of the edges written whose property is in it.
A prefix used only for a datatype or a value SHALL have the count 0 in every column.

#### Scenario: Prefix counts of the continents graph
- **WHEN** the pattern schema is generated from the sample profile
- **THEN** `prefixes-continents-214e8f67.md` has a row for `euvoc` whose `classes` cell is `2` (`euvoc:Continent`, `euvoc:XlNotation`) and a row `| xsd | <http://www.w3.org/2001/XMLSchema#> | 0 | 0 | 0 | 0 |`

### Requirement: CSV cells
Every CSV file of the pattern schema SHALL follow RFC 4180 with a header row, UTF-8 and `\n` line
ends (llm-schema-split DEC-2). A cell SHALL be empty for an absent value, `true` or `false` for a
flag, the digits for a number, and, for several values, their texts joined by ` | ` (DEC-6). A
cell holding `,`, `"`, a carriage return, a line feed, or a leading or trailing space SHALL be
quoted with `"`, each `"` inside doubled.

#### Scenario Outline: Cell quoting
- **WHEN** a cell's value is <value>
- **THEN** it is written <written>

  Examples:
    | value                          | written                   |
    | the text `a, b`                | `"a, b"`                  |
    | the text `say "hi"`            | `"say ""hi"""`            |
    | the texts `Body` and `Human`   | `Body \| Human`           |
    | no value                       | the empty cell            |
    | the flag true                  | `true`                    |

#### Scenario: Every CSV parses
- **WHEN** the pattern schema is generated from the sample profile with the label fixture ontology
- **THEN** every `.csv` file reads with Python's `csv.DictReader`, its header is the column list of its requirement, and every row has as many cells as the header

### Requirement: Patterns CSV
`patterns-<graph slug>.csv` SHALL have the columns `graph, block, owner, path, depth, property,
targets, target_kinds, ending, instances, subjects, triples, per_min, per_max, blank_nodes,
languages, min_value, max_value, single_value, distinct, presence_only, first_n, via`
(llm-schema-split DEC-4). It SHALL hold, per block in the order of `patterns-<graph slug>.md`, one
block row and then one row per edge line of the block, in line order:
- **block row:** `graph` the graph IRI (empty for the default graph), `block` and `owner` the
  group name, `depth` `0`, `instances` the group's instances, `first_n` the instances read when
  read in first-N mode, `via` each incoming link as `<source>-<property>`; every other cell
  empty;
- **edge row:** `block` the block it sits in; `owner` the group whose profile gives the edge (the
  nested group for a nested edge); `path` the property names of the edges above it joined by `/`
  (empty at depth 1); `depth` its level, 1 to 3; `property` its prefixed name; `targets` its
  target alternatives in the order of "Pattern view" rule 4, each written as in the patterns
  Markdown but a group without `(:` and `)`; `target_kinds` the kind of each, `group`,
  `datatype`, `iri`, `blank_node` or `unknown`; `ending` empty, `^` or `…` (no space before it); `instances` the
  owner's observed instances; `subjects` the instances having it; `triples` its triples;
  `per_min` and `per_max` its fewest and most values per instance; `blank_nodes` whether some
  objects are blank nodes; `languages` its language tags, sorted; `min_value` and `max_value`
  its lowest and highest value when "Pattern schema output" writes `lo..hi` or `=v`, and
  `single_value` the value when it writes `=v` and the name of the IRI when it writes
  `=<name>`; all three not cut and not JSON-quoted; `distinct` its distinct objects; `presence_only` whether it was found only by the
  completeness check; `first_n` and `via` empty.
A value the profile does not hold SHALL be an empty cell.

#### Scenario Outline: Rows of the continents patterns CSV
- **WHEN** the pattern schema is generated from the sample profile
- **THEN** `patterns-continents-214e8f67.csv` has a row whose <columns> are <cells>

  Examples:
    | columns                                                        | cells                                                                                         |
    | `block, depth, property, instances`                            | `euvoc:Continent&skos:Concept, 0, (empty), 6`                                                 |
    | `depth, property, targets, target_kinds, single_value`         | `1, euvoc:startDate, xsd:date, datatype, 1952-07-24`                                          |
    | `owner, path, depth, property, subjects, instances, distinct`  | `skosxl:Label, skosxl:prefLabel, 2, lvont:script, 12, 145, 2`                                  |
    | `owner, depth, property, min_value, max_value`                 | `euvoc:XlNotation, 2, rdf:value, AFRICA, OCEANIA`                                             |
    | `block, depth, via`                                            | `owl:Ontology&skos:ConceptScheme, 0, euvoc:Continent&skos:Concept-skos:inScheme \| euvoc:Continent&skos:Concept-skos:topConceptOf` |

### Requirement: Glossary CSV
`glossary-<graph slug>.csv` SHALL have the columns `term, iri, kind, language, pref_label,
alt_labels, definition, notes` (llm-schema-split DEC-5). It SHALL hold, for each term the
output uses that has a label, an alt label, a description or a note, sorted by prefixed name, one
row per language that
any of its labels, alt labels, descriptions or notes has, the untagged language first (an empty
`language` cell), then by tag:
- `term` the prefixed name, `iri` the full IRI;
- `kind` the term's kind codes: `C` a class; `dP` a property whose objects are literals;
  `oP` a property whose objects are IRIs, classes or blank nodes; `P` a property with no
  collected objects; `D` a datatype (llm-schema-split DEC-10); a term with several codes has them
  joined by ` | `, in the order `C`, `dP`, `oP`, `P`, `D`;
- `pref_label` and `definition` the term's label and description in that language, or empty;
- `alt_labels` and `notes` all its alt labels and notes in that language, in full, joined by
  ` | `.

#### Scenario: Rows per language
- **WHEN** the pattern schema is generated from the sample profile with the label fixture ontology
- **THEN** `glossary-continents-214e8f67.csv` has for `skos:Concept` a row with `language` `de`, `pref_label` empty and `alt_labels` `Begriff`, and a row with `language` `en`, `kind` `C`, `pref_label` `Concept`, `alt_labels` `Notion`, `definition` `An idea or notion; a unit of thought.` and `notes` `Also a SKOS class. | Use for concepts of a scheme.`

#### Scenario: A description is not cut in the CSV
- **WHEN** the pattern schema is generated from the sample profile with the label fixture ontology
- **THEN** the `definition` of `dcterms:type` in `glossary-continents-214e8f67.csv` is the whole comment of the fixture, longer than 200 characters, with no `…`

### Requirement: Reified relations per class
A descriptive output SHALL show each class's reified relations in a separate section after its
properties, when it lists properties per class (profile document, pattern view and schema, PlantUML
diagram), each with kind, the predicate that names it (or "unnamed"), object class, statement count
and reifier properties. A class with none SHALL show no section. SHACL and ShExC outputs SHALL note
each reified relation under the class's shape (an annotation in SHACL, a comment in ShExC) and SHALL
NOT constrain it.

#### Scenario: Section present
- **GIVEN** a profile where class A has a reified relation `ex:isRelatedTo` to B
- **WHEN** the profile document is generated
- **THEN** A's entry has a reified-relations section naming `ex:isRelatedTo`, B and the count

#### Scenario: No section when none
- **GIVEN** a profile with no reified relations
- **WHEN** any output is generated
- **THEN** it equals the output for the same profile before this change

#### Scenario: Shapes note reifications without constraining them
- **GIVEN** a profile where class A has a reified relation `ex:isRelatedTo` to B
- **WHEN** SHACL shapes and ShExC are generated
- **THEN** A's shape notes `ex:isRelatedTo` to B, and has no property shape or triple constraint for
  the relation or its reifier properties

