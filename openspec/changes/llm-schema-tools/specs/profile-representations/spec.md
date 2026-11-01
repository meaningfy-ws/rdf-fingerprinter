## ADDED Requirements

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
   graph SHALL be written `T @<graph name>`.
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
   SHALL end in ` …`. A group SHALL NOT be expanded inside its own expansion.
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
The pattern generator SHALL write `pattern-<graph slug>.txt` for each graph with a block, through
the `fingerprint-gen-pattern` command and `--format pattern`. The file SHALL hold, in this
order (N8):
1. one `PREFIX p: <ns>` line per prefix the file uses, sorted by prefix;
2. the legend line `# (:A&B) n: classes with the same n instances · ~m first_n: statistics over the first m read · co C k: k also typed C · via (:S)-p: incoming links · -p-> (:T|U) object classes · IRI, BNODE untyped · . not collected · deeper indent: a blank node's own edges, statistics over all its instances, up to 3 hops · ^ expanded under another edge · … deeper than 3 hops · k/n instances having p (omitted: all) · ×a-b values per instance (omitted: 1) · bn blank nodes · @n languages, @tag one language · =v one value · lo..hi range · dN distinct values (omitted: all differ) · presence found, not measured`;
3. `# hidden: <n> classes` when n > 0 classes are hidden ("Pattern view" rule 3);
4. the blocks, by instances, largest first, then by name;
5. the glossary ("Term labels and descriptions in the outputs").

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
- **THEN** `pattern-continents-214e8f67.txt` holds the line <line>

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
    | `# glossary: none`                                                                                                                           |

#### Scenario: One block per class group and one edge per property
- **WHEN** the pattern schema is generated from the sample profile
- **THEN** in every file no group name begins two blocks, no property begins two edges at the same place, `skosxl:Label`, `euvoc:XlNotation` and `euvoc:XlNote` begin no block, and every declared prefix is used

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
- **THEN** the edge is `-ex:status-> IRI =exs:active`, `PREFIX exs:` is declared, and the same profile without top values gives `-ex:status-> IRI d1`

#### Scenario: A class read in first-N mode
- **WHEN** a profile has `ex:Big` with 50000 instances, 10000 of them read in first-N mode, and `ex:name` on 9000 of those
- **THEN** its block header is `(:ex:Big) 50000 ~10000 first_n`, and its `ex:name` edge holds `9000/10000`

#### Scenario: Unusual IRIs in the LLM outputs
- **WHEN** the profile holds the class IRI `http://ex.org/q?a=1&b='x'`
- **THEN** the pattern schema writes it as `<http://ex.org/q?a=1&b='x'>`, and the ShExC leaves it out, lists it after `# skipped:`, and parses

### Requirement: Enriched ShExC output
The ShExC generator SHALL write `shex-<graph slug>.shex` for each graph with a block, through the
`fingerprint-gen-shex` command and `--format shex`. It SHALL render the same pattern view (EPIC
DEC-18 amendment, DEC-27), with this mapping:
- one `PREFIX` line per prefix used; then the legend line
  `# comments use the pattern schema's legend: k/n instances having p (omitted: all) · ×a-b values per instance (omitted: 1) · bn blank nodes · @n languages, @tag one language · =v one value · lo..hi range · dN distinct values (omitted: all differ) · presence found, not measured · … deeper than 3 hops`;
  then `# hidden: <n> classes` as in the pattern schema; then the `# skipped:` line (below), if any;
- per block, the comment `# ` plus the pattern block header, then a shape labelled with the
  first member of the group, in name order, that the filters show;
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
  `BNODE`, with `… deeper than 3 hops` in its comment. This case wins over the next two;
- an expanded nested group SHALL be written inline when exactly one edge of the view reaches it:
  `<indent><property> BNODE {`, then `  # <comment>` if it is non-empty, then its constraints one
  level deeper, then `<indent>}`, the cardinality if any (`} {0,2}`), and ` ;`. The indent is two
  spaces per level, with triple constraints at levels 1 to 3 as in the pattern view. When more
  than one edge reaches it, it SHALL be one shape `<label> BNODE { … }`, after the block shapes,
  referenced as `BNODE @<label>` from every edge reaching it, whose own constraints start again at
  level 1;
- cardinality: `?` for 0–1, nothing for exactly 1, `{a}` for exactly a > 1, `{a,b}` otherwise.
  The minimum is 0 when some instances lack the property. A property with no histogram is `*`;
- the glossary at the end, each line commented with `# `;
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
Classes and properties SHALL get labels and one description from two sources (EPIC DEC-6, DEC-17,
DEC-20):
- the `--ontology FILE` option of `fingerprint-gen-pattern` and `fingerprint-gen-shex`, read at
  render time with the same predicates and selection as statistics-collection "Term labels and
  descriptions are collected";
- the profile's stored term annotations.

Per term and per field, labels or description, the ontology's values SHALL be used when it has
any, else the data's; the two are never merged (DEC-7). A file that is missing, unreadable or not
RDF in a format rdflib reads by its extension SHALL be a usage error (exit 2) that names the file,
and nothing SHALL be written.

The glossary SHALL list, sorted by prefixed name, each term the output uses that has a label or a
description (N9): `<name> "<label>"[@<lang>][: <description>]`, or `<name>: <description>` with no
label. When there are none, it SHALL be the line `# glossary: none`, else the line `# glossary`
followed by the entries. The label and description shown SHALL each be the untagged value if
there is one, else `en`, else the smallest language tag. A description SHALL have its white space
collapsed to single spaces, and be cut to 200 characters ending in `…`. A profile saved before
term annotations existed SHALL load, and SHALL render as a profile with no annotations.

#### Scenario: Labels from an ontology file
- **WHEN** the pattern schema is generated from the sample profile with the label fixture ontology
- **THEN** the glossary holds `skos:Concept "Concept"@en: An idea or notion; a unit of thought.` and `skosxl:prefLabel "preferred label"@en`, and has no line for `euvoc:Continent`

#### Scenario: The ontology wins for the fields it gives
- **WHEN** the data labels `ex:Person` `"Persoon"@nl` with the description `"Iemand"@nl`, and the ontology labels it `"Person"@en` with no description
- **THEN** the glossary line is `ex:Person "Person"@en: Iemand`

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
- **THEN** it is written, and its glossary is `# glossary: none`

### Requirement: Size filters
The pattern and ShExC generators SHALL take `--min-instances N` and
`--max-classes K`, each at least 1 (EPIC DEC-22). After the namespace filters, a named group with
fewer than N instances SHALL be hidden. Of the named groups left, only the K with the most
instances SHALL be shown, ties broken by name. Hidden groups SHALL behave as namespace-hidden
ones: no block, still named as edge targets, and absent from `via` lists. A value below 1 SHALL
be a usage error (exit 2).

#### Scenario: Small classes hidden
- **WHEN** the pattern schema of the sample profile is generated with `--min-instances 2`
- **THEN** `pattern-treaties-3b4301a8.txt` has no `(:owl:Ontology&skos:ConceptScheme)` block and holds `# hidden: 2 classes`, and the edge `-skos:inScheme-> (:owl:Ontology&skos:ConceptScheme) d1` is still there

#### Scenario: Only the largest classes
- **WHEN** the pattern schema of the sample profile is generated with `--max-classes 1`
- **THEN** each file has one block, the largest named group of its graph

## MODIFIED Requirements

### Requirement: Generators share one framework
Each representation SHALL be produced by a generator class derived from one base class modelled on
LinkML's generator (DEC-3): a `serialize` entry point, per-level visit hooks, and shared command
arguments (profile file, output folder, acceptance threshold, template folder). Each generator SHALL
have its own command (SHACL, PlantUML, profile document, pattern schema, ShExC) and SHALL render
through eds4jinja2 from a packaged template package (DEC-4).

#### Scenario: Custom template package
- **WHEN** a generator is given a template folder of the user's own that reads a constant from its configuration
- **THEN** the output is rendered from that folder and shows the constant

### Requirement: Golden outputs
Every file each generator writes for a fixed profile SHALL equal a checked-in golden file (the
page, each shapes file, the overview and each module diagram, each pattern schema and each ShExC
file), so any change to a representation is visible in review.

#### Scenario: Golden file per output
- **WHEN** each generator renders the fixed test profile
- **THEN** every written file equals its golden file, and no golden file is left unmatched

### Requirement: No files for empty graphs
A profiled graph with no shown class SHALL produce no SHACL, PlantUML, pattern schema or ShExC
file; the report SHALL still list it, as empty.

#### Scenario: Empty default graph
- **WHEN** the shapes, diagrams, pattern schema and ShExC are generated for a profile whose default graph is empty
- **THEN** no `shapes-default.ttl`, no `diagram-default*.puml`, no `pattern-default.txt` and no `shex-default.shex` is written, and the report lists the default graph as empty
