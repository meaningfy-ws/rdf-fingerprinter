## MODIFIED Requirements

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
page, each shapes file, the overview and each module diagram), so any change to a representation
is visible in review.

#### Scenario: Golden file per output
- **WHEN** each generator renders the fixed test profile
- **THEN** every written file equals its golden file, and no golden file is left unmatched

## ADDED Requirements

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
Every generator and the report SHALL leave out the classes of the excluded namespaces. The excluded
set SHALL start from the meta namespaces `http://www.w3.org/1999/02/22-rdf-syntax-ns#`,
`http://www.w3.org/2000/01/rdf-schema#`, `http://www.w3.org/2002/07/owl#` and
`http://www.w3.org/ns/shacl#`. Each `--exclude-namespace` SHALL add a namespace to it, and each
`--include-namespace` SHALL take one out; include wins over exclude. Either option SHALL take a
prefix from the table or a namespace IRI. A name matching nothing in the table SHALL log the warning
`--exclude-namespace <name>: no such namespace; ignored` (or the same for include) and be ignored.
Properties of the shown classes SHALL stay, whatever their value types. Collection SHALL NOT change
(EPIC DEC-5, DEC-8).

#### Scenario: Meta vocabularies hidden by default
- **WHEN** shapes and diagrams are generated with no filter option for a profile holding `owl:Ontology` and `ex:Person`
- **THEN** `ex:Person` has a node shape and a box, and `owl:Ontology` has neither

#### Scenario: Included again
- **WHEN** they are generated with `--include-namespace owl`
- **THEN** `owl:Ontology` has a node shape and a box

#### Scenario: Excluded by option
- **WHEN** they are generated with `--exclude-namespace ex`
- **THEN** no `ex:` class has a node shape, a box or a report section

#### Scenario: Unknown name
- **WHEN** `--exclude-namespace nope` is given and no namespace has the prefix or IRI `nope`
- **THEN** a warning names `nope`, and the outputs are as without the option

### Requirement: No files for empty graphs
A profiled graph with no shown class SHALL produce no SHACL or PlantUML file; the report SHALL still
list it, as empty.

#### Scenario: Empty default graph
- **WHEN** the shapes and diagrams are generated for a profile whose default graph is empty
- **THEN** no `shapes-default.ttl` and no `diagram-default*.puml` is written, and the report lists the default graph as empty

## REMOVED Requirements

### Requirement: The statistics report is unchanged
**Reason**: This change redesigns the report on purpose, merges the profile document into it and
removes the 1.x library API (EPIC DEC-3, DEC-9).
**Migration**: The report is now specified by `fingerprint-report` "Report content", "One
self-contained page" and "Navigation, search and filters". The exit codes stay as they are, the new
options are additive, and the library migration is in `fingerprint-report`'s removal of "Public
function keeps its signature".
