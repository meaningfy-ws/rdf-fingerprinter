## ADDED Requirements

### Requirement: One saved profile per server
The `fingerprint-mcp` command SHALL serve exactly one saved `profile.json`, named by its one
argument, over MCP's stdio transport (EPIC DEC-10, DEC-26). It SHALL also take `--ontology`,
`--prefixes`, `--exclude-namespace`, `--include-namespace`, `--min-instances` and `--max-classes`,
with the meaning they have on the generator commands (profile-representations "Term labels and
descriptions in the outputs", "Namespace filters", "Size filters"). It SHALL take no endpoint
option. Before it serves, it SHALL load the profile, the prefix table and the ontology. If any
of them is unusable, it SHALL exit 2 with a message on stderr that names the file. If the `mcp`
package is not installed, the command SHALL exit 2 with a message that names the extra
`rdf-fingerprinter[mcp]`. The server SHALL write nothing to stdout except protocol messages.

#### Scenario: Server started from a saved profile
- **WHEN** `fingerprint-mcp` is started with the sample profile and a client connects over stdio
- **THEN** the client lists exactly the tools `list_graphs`, `list_classes`, `describe_class`, `get_schema`, `search_schema` and `validate_query`, and the resource template `schema://{graph}`

#### Scenario Outline: Unusable start-up file
- **WHEN** `fingerprint-mcp` is started with <file>
- **THEN** it exits 2 before serving, with a message on stderr naming the file

  Examples:
    | file                                         |
    | a profile path that does not exist           |
    | a file that is not a profile                 |
    | an ontology file that cannot be parsed       |

#### Scenario: Server without the mcp extra
- **WHEN** `fingerprint-mcp` is started where the `mcp` package is not installed
- **THEN** it exits 2 with a message naming `rdf-fingerprinter[mcp]`

### Requirement: The server never contacts an endpoint
The server SHALL answer every tool and resource from the loaded profile and ontology alone. It
SHALL open no network connection, run no SPARQL query against any store, and look up no prefix
online (EPIC DEC-3, DEC-9). No tool SHALL run, update or generate a query (DEC-11).

#### Scenario: Every tool answers without a network
- **WHEN** each tool and the resource is called while every network connection fails
- **THEN** each one answers from the profile, and no connection was attempted

#### Scenario: A query given for validation is not executed
- **WHEN** `validate_query` is given `SELECT * WHERE { ?s ?p ?o }`
- **THEN** it returns a report, and no store was asked to evaluate the query

### Requirement: Graphs and classes are listed
Every tool that takes a `graph` SHALL accept the graph's slug (as in the generated file names,
`default` for the default graph) or its IRI. `list_graphs` SHALL return each profiled graph: its
slug, its IRI (absent for the default graph), and its numbers of blocks and of hidden classes.
`list_classes(graph)` SHALL return one entry per merged group of the graph's pattern view
(profile-representations "Pattern view"), those nested as blank nodes included. Each entry SHALL
hold the group's name, its member classes as prefixed names, its instance count, and whether it
is nested. Entries SHALL be ordered by instances, largest first, then by name. Groups that the
filters hide SHALL be absent. An unknown graph SHALL be a tool error whose message lists the known
slugs.

#### Scenario: Graphs of the sample profile
- **WHEN** `list_graphs` is called on the sample profile
- **THEN** it returns the slugs `default`, `continents-214e8f67` and `treaties-3b4301a8` with the IRI of each named graph

#### Scenario: Classes largest first
- **WHEN** `list_classes` is called for `continents-214e8f67`
- **THEN** the entries are `skosxl:Label` 145 (nested), `euvoc:Continent&skos:Concept` 6, `euvoc:XlNotation` 6 (nested) and `owl:Ontology&skos:ConceptScheme` 1, in that order

#### Scenario: Unknown graph
- **WHEN** `list_classes` is called for `nope`
- **THEN** the call returns a tool error naming `nope` and listing the known slugs

### Requirement: A class is described with its links
`describe_class(graph, class, format)` SHALL return the one-class view of the group holding the
class. It SHALL hold the prefix block, the legend and the group's block, with its `via` links and
their triple counts (EPIC DEC-15, rule N6). Every blank-node chain under the block SHALL be
expanded once, under the first edge that reaches it in the view. The glossary SHALL hold the
entries of the terms the view uses. `class` SHALL be a prefixed name of the profile's table or a
full IRI. `format` SHALL be `pattern` (the default) or `shex` (DEC-23). A class nested as a blank
node SHALL be described as a block of its own. An unknown class SHALL be a tool error that suggests
at most 3 close names. A class the filters hide SHALL be a tool error that names the option
showing it again.

#### Scenario: A named class with incoming links
- **WHEN** `describe_class` is called for `continents-214e8f67` and `skos:ConceptScheme`
- **THEN** the block header reads `(:owl:Ontology&skos:ConceptScheme) 1 via (:euvoc:Continent&skos:Concept)-skos:inScheme 6, (:euvoc:Continent&skos:Concept)-skos:topConceptOf 6`, and its `skosxl:prefLabel` edge is followed by the nested edges of `skosxl:Label` instead of `^`

#### Scenario: A class described as ShExC
- **WHEN** `describe_class` is called for `continents-214e8f67`, `euvoc:Continent` and format `shex`
- **THEN** the text parses as ShExC and holds the shape `euvoc:Continent`

#### Scenario: A blank-node class described on its own
- **WHEN** `describe_class` is called for `continents-214e8f67` and `skosxl:Label`
- **THEN** the view's block is `(:skosxl:Label) 145`, with a `via` list naming `euvoc:Continent&skos:Concept` and `owl:Ontology&skos:ConceptScheme` with their counts

#### Scenario: Unknown class with a suggestion
- **WHEN** `describe_class` is called for `continents-214e8f67` and `euvoc:Continant`
- **THEN** the call returns a tool error that suggests `euvoc:Continent`

#### Scenario: Unknown format
- **WHEN** `describe_class` is called with format `turtle`
- **THEN** the call returns a tool error naming the formats `pattern` and `shex`

### Requirement: The whole-graph schema and its resource
`get_schema(graph, format)` SHALL return the text that the pattern generator (format `pattern`,
the default) or the ShExC generator (format `shex`) writes for that graph, with the server's
filters and ontology. The resource `schema://{graph}`, where `{graph}` is a slug, SHALL return
the same text as `get_schema(graph)` in format `pattern`. An unknown graph SHALL be a resource
error.

#### Scenario: Schema equals the generated file
- **WHEN** `get_schema` is called for `treaties-3b4301a8` in each format, and the resource `schema://treaties-3b4301a8` is read
- **THEN** the texts equal the golden files `pattern-treaties-3b4301a8.txt` and `shex-treaties-3b4301a8.shex`, and the resource equals the first

### Requirement: Schema search by string matching
`search_schema(text)` SHALL split `text` on white space into words. It SHALL return the classes
and properties of every graph's filtered pattern view for which each word, compared case-insensitively, occurs in at
least one of these: the term's prefixed name, its full IRI, any of its labels or its description
(EPIC DEC-22). It SHALL use no embedding. Each hit SHALL hold the prefixed name, the IRI, the kind
(`class` or `property`), the slugs of the graphs that use it, the shown label if any, and the
matched field: the first of name, IRI, label and description that holds every word, or `mixed`
when no single field does. Hits SHALL be ordered by matched field in that order, `mixed` last,
then by prefixed name. At most 25 hits SHALL be returned, together with the total number found.
Text with no word SHALL be a tool error.

#### Scenario Outline: Search hits
- **WHEN** `search_schema` is called with <text> on the sample profile
- **THEN** the first hit is <first> of kind <kind>, matched in <field>

  Examples:
    | text            | first              | kind     | field |
    | continent       | euvoc:Continent    | class    | name  |
    | literalform     | skosxl:literalForm | property | name  |
    | skos-xl#label   | skosxl:Label       | class    | IRI   |

#### Scenario Outline: Search finds labels from the ontology
- **WHEN** the server is started with the label fixture ontology and `search_schema` is called with <text>
- **THEN** the first hit is <first>, matched in <field>

  Examples:
    | text         | first           | field       |
    | Date created | dcterms:created | label       |
    | notion       | skos:Concept    | description |

#### Scenario: Empty search text
- **WHEN** `search_schema` is called with only spaces
- **THEN** the call returns a tool error

### Requirement: Queries are validated against the pattern view
`validate_query(sparql)` SHALL parse the query and never run it (EPIC DEC-11, DEC-24). It SHALL
return a report with `valid`, at most one parse error, a list of issues and a list of constructs
not checked. The query is checked against the profile's classes and their properties in every
graph, whatever the filters hide. The report SHALL hold:
- a parse error, with line and column, for text that is not a SPARQL 1.1 query (updates
  included), and for an undeclared prefix, naming the namespace the profile's table gives that
  prefix when it has one;
- `unknown_class` for an IRI in the object of `rdf:type` that is no profiled class;
- `unknown_predicate` for a predicate IRI that no profiled class uses;
- `predicate_not_on_class` for a predicate on a subject variable typed `C` when no class typing
  that variable has the predicate. A variable is typed `C` by `?x a C`, or by being the object of
  an edge whose every target is a class, where the subject of that edge is typed;
- `path_step_not_on_class` for a step of a sequence path `p/q/…` of IRIs that is no property of
  the classes the previous step reaches, when the path's subject is typed.

Only the query's top-level group SHALL be checked. The patterns of `OPTIONAL`, `UNION`, `MINUS`,
subqueries, `FILTER EXISTS` and property paths other than IRI sequences SHALL NOT be checked;
each one found SHALL be listed once under the constructs not checked. `valid` SHALL be true
exactly when there is no parse error and no issue.

#### Scenario: A correct query from the sample facts
- **WHEN** `validate_query` is given `PREFIX euvoc: <http://publications.europa.eu/ontology/euvoc#> PREFIX skosxl: <http://www.w3.org/2008/05/skos-xl#> SELECT ?c ?name WHERE { ?c a euvoc:Continent ; skosxl:prefLabel/skosxl:literalForm ?name }`
- **THEN** the report is valid, with no issue and nothing listed as not checked

#### Scenario Outline: Issues found in a query
- **WHEN** `validate_query` is given the sample prefixes and the pattern <pattern>
- **THEN** the report is not valid and has one issue of kind <kind> naming <term>

  Examples:
    | pattern                                                       | kind                   | term               |
    | `?c a euvoc:Continant`                                        | unknown_class          | euvoc:Continant    |
    | `?c a euvoc:Continent ; euvoc:nope ?x`                        | unknown_predicate      | euvoc:nope         |
    | `?c a euvoc:Continent ; skosxl:literalForm ?x`                | predicate_not_on_class | skosxl:literalForm |
    | `?c a euvoc:Continent ; skos:inScheme ?s . ?s rdf:value ?v`   | predicate_not_on_class | rdf:value          |
    | `?c a euvoc:Continent ; skosxl:prefLabel/rdf:value ?n`        | path_step_not_on_class | rdf:value          |

#### Scenario Outline: Text that is not a query
- **WHEN** `validate_query` is given <text>
- **THEN** the report is not valid and its parse error <says>

  Examples:
    | text                                                     | says                                                   |
    | `SELECT * WHERE { ?s ?p `                                | gives a line and a column                              |
    | `SELECT * WHERE { ?c a euvoc:Continent }`                | names the prefix `euvoc` and its namespace             |
    | `PREFIX ex: <http://ex.org/> INSERT DATA { ex:a ex:b ex:c }` | says only queries are validated                    |

#### Scenario: Unchecked constructs are listed
- **WHEN** `validate_query` is given a query whose top-level group types `?c` as `euvoc:Continent` and that has `OPTIONAL { ?c euvoc:nope ?x }`
- **THEN** the report is valid, and lists `OPTIONAL` as not checked
