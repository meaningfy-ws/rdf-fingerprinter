## ADDED Requirements

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
- `kind` how the view writes the IRI: `class`, `property` or `datatype`, several joined by ` | `;
- `pref_label` and `definition` the term's label and description in that language, or empty;
- `alt_labels` and `notes` all its alt labels and notes in that language, in full, joined by
  ` | `.

#### Scenario: Rows per language
- **WHEN** the pattern schema is generated from the sample profile with the label fixture ontology
- **THEN** `glossary-continents-214e8f67.csv` has for `skos:Concept` a row with `language` `de`, `pref_label` empty and `alt_labels` `Begriff`, and a row with `language` `en`, `kind` `class`, `pref_label` `Concept`, `alt_labels` `Notion`, `definition` `An idea or notion; a unit of thought.` and `notes` `Also a SKOS class. | Use for concepts of a scheme.`

#### Scenario: A description is not cut in the CSV
- **WHEN** the pattern schema is generated from the sample profile with the label fixture ontology
- **THEN** the `definition` of `dcterms:type` in `glossary-continents-214e8f67.csv` is the whole comment of the fixture, longer than 200 characters, with no `…`

## MODIFIED Requirements

### Requirement: No files for empty graphs
A profiled graph with no shown class SHALL produce no SHACL, PlantUML, pattern-schema or ShExC
file; the report SHALL still list it, as empty.

#### Scenario: Empty default graph
- **WHEN** the shapes, diagrams, pattern schema and ShExC are generated for a profile whose default graph is empty
- **THEN** no `shapes-default.ttl`, no `diagram-default*.puml`, none of `prefixes-default.md`, `patterns-default.md`, `patterns-default.csv`, `glossary-default.md`, `glossary-default.csv` and no `shex-default.shex` is written, and the report lists the default graph as empty

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
`<name>[ "<label>"[@<lang>]][ alt: "<a>" | "<b>" …][: <description>]` (llm-schema-split DEC-7):
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
- **THEN** `glossary-continents-214e8f67.md` holds `- skos:Concept "Concept"@en alt: "Notion": An idea or notion; a unit of thought.` and `- skosxl:prefLabel "preferred label"@en`, and has no line for `euvoc:Continent`

#### Scenario: A term with only alt labels
- **WHEN** the pattern schema is generated from the sample profile with the label fixture ontology
- **THEN** `glossary-treaties-3b4301a8.md` holds the line `- skosxl:altLabel "alternative label"@en`

#### Scenario: A term with notes only
- **WHEN** a term the output uses has the note `"Internal"@en` and no label, alt label or description
- **THEN** `glossary-<slug>.csv` has its row with `notes` `Internal`, and the glossary Markdown and the ShExC have no line for it

#### Scenario: Alt labels in another language are not shown
- **WHEN** a term has the label `"Concept"@en` and the alt labels `"Begriff"@de` and `"Notion"@en`
- **THEN** its glossary line holds `"Concept"@en alt: "Notion"` and not `Begriff`

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

