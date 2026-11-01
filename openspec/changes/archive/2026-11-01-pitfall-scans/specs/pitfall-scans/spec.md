## ADDED Requirements

### Requirement: Pitfall check contract
A pitfall check SHALL be one SPARQL file holding a single `SELECT` query that returns the variables
`?entity`, `?property` and `?value`, one row per finding. Its leading comment lines (the header, up to the first
line that is not a comment) SHALL give `# id: <id>`, `# title: <text>`,
`# importance: critical|important|minor`, `# scope: schema|data`, `# source: <text>`, and optionally
`# heuristic: true` and `# description: <text>` (one line). A header comment line without a
`key:`, and a blank line, is ignored; an unknown key, or a key given twice, is refused. The id SHALL match `[a-z0-9_]+`
and be unique in the catalogue. The query SHALL have no dataset clause (`FROM`, `FROM NAMED`), and each `PREFIX` or `BASE`
declaration SHALL be on its own line, before the `SELECT`. A file
that breaks the contract SHALL be a usage error (exit 2) naming the file, before any query (EPIC
DEC-1, DEC-7).

#### Scenario: A valid check loads
- **WHEN** the catalogue loads a file whose header gives id `p35_untyped_property`, importance `important`, scope `data`, and whose query selects `?entity ?property ?value`
- **THEN** the check is available under that id, with its title, importance, scope and source

#### Scenario Outline: An invalid check is refused
- **WHEN** a user check file <problem>
- **THEN** the command exits 2 naming the file, and sends no query

  Examples:
    | problem                                         |
    | has no `# id:` line                             |
    | has importance `severe`                         |
    | holds an `INSERT DATA` update                   |
    | selects `?s ?p ?o` instead of the three variables |
    | does not parse as SPARQL                        |
    | has the unknown header key `# severity: high`   |
    | has a `FROM <http://ex.org/g>` clause            |

### Requirement: The packaged catalogue
The fingerprinter SHALL ship a catalogue of checks covering these OOPS! pitfalls: P04, P05, P06, P07, P08,
P10, P11, P12/P30 (by local name), P13, P19, P20, P21, P22, P24 (direct cases), P25, P26, P27,
P28/P29, P32, P33, P34, P35, P36, P38 and P41. It SHALL also ship four checks beyond OOPS!: an IRI used
as a class and as a property, a typed individual used as a predicate, subjects outside a property's
declared domain, and IRI objects outside an object property's declared range. Each check's `source`
SHALL name its OOPS! pitfall code where it has one, and its title and description SHALL be the
fingerprinter's own words (EPIC DEC-12). The catalogue's ids, importance, scope and heuristic flags
SHALL be those of design.md's catalogue table.

#### Scenario: Catalogue size
- **WHEN** the packaged catalogue is loaded
- **THEN** it holds 29 checks, each with a unique id, and every OOPS!-derived check's source names its pitfall code

#### Scenario Outline: Each check finds its pitfall and only it
- **WHEN** check <id> runs over its positive fixture and over its negative fixture
- **THEN** it finds at least one row in the positive fixture, the expected entity among them, and no row in the negative fixture

  Examples:
    | id                                   |
    | every packaged check (one row each)  |

### Requirement: The pitfall scan stage
With `pitfall_scan` on, the collector SHALL scan every profiled graph after profiling it, at any
depth (also `graphs`); each schema graph SHALL be added to the profiled graphs (after them, in the
order given) when it is not already among them. A graph that holds no triple, by
`ASK FROM <graph> { ?s ?p ?o }` over the graph alone (no `FROM` for the default graph), SHALL NOT be
scanned. Which checks
run, and over which dataset:
- **No schema graph given:** every selected check runs over the graph alone: `FROM <graph>` for a
  named graph; the store's default graph, without `FROM`, for the default graph.
- **Schema graphs given:** a graph that is one of the schema graphs runs only the `schema`-scope
  checks, over itself. Every other graph runs only the `data`-scope checks, over `FROM <graph>`
  plus one `FROM <s>` per schema graph (the default graph: without `FROM`, so without the schema
  graphs).

For each check it SHALL send a count query (the check wrapped in `SELECT (COUNT(*) AS ?n)`) and an
example query (the check with `LIMIT pitfall_examples`). It SHALL record the result in
`GraphProfile.pitfalls`, with the check's metadata, the count, the examples, and the seconds both
queries took. With `pitfall_scan` off, no check query SHALL be sent and no `pitfalls` SHALL be
recorded (EPIC DEC-2, DEC-3, DEC-4, DEC-5).

#### Scenario: Scan with a schema graph
- **WHEN** a run profiles graph `ex:data` with `--pitfalls --schema-graph ex:schema`, and `ex:data` uses the predicate `ex:undeclared`, which `ex:schema` does not declare
- **THEN** the profile of `ex:data` holds a `p35_untyped_property` result with count ≥ 1 and an example whose entity is `ex:undeclared`

#### Scenario: Schema checks run once, on the schema graph
- **WHEN** a run profiles `--graph ex:data` with `--pitfalls --schema-graph ex:schema`
- **THEN** `ex:schema` is profiled too, `ex:schema` has results only for schema-scope checks, and `ex:data` only for data-scope checks

#### Scenario: Empty graph not scanned
- **WHEN** the default graph holds no triple and a run uses `--pitfalls`
- **THEN** no check query is sent for the default graph and it has no `pitfalls`

#### Scenario: A check that finds nothing
- **WHEN** a check's count query returns 0
- **THEN** its result has count 0 and no examples, and no example query is sent

#### Scenario: Bounded examples
- **WHEN** a check finds 1,100 rows and `pitfall_examples` is 10
- **THEN** its result has count 1100 and exactly 10 examples

#### Scenario: Scan off
- **WHEN** a run profiles a store without `--pitfalls`
- **THEN** no query of kind `pitfall` is sent, and no graph profile has `pitfalls`

#### Scenario: Failed check
- **WHEN** the count query of one check times out after its retries
- **THEN** a failure of kind `pitfall` naming the check id is recorded, that check has no result, the other checks still run, and the command exits 1

### Requirement: Scan settings and options
The scan settings SHALL be collection settings: `pitfall_scan` (boolean, default false),
`schema_graphs` (IRIs, default none) and `pitfall_examples` (an integer ≥ 1, default 10), settable by CLI option (`--pitfalls`,
`--schema-graph`, `--pitfall-examples`), by environment variable and by configuration, and recorded
in the profile. The `fingerprint` command SHALL also accept:
- `--pitfall-checks DIR`: user checks, added to the catalogue; a user check with a packaged check's
  id replaces it;
- `--skip-pitfall ID` (repeatable): checks left out;
- `--fail-on critical|important|minor`.

An unknown id in `--skip-pitfall`, a missing directory, a schema graph that cannot be written as an
IRI, or `--pitfall-checks`, `--skip-pitfall` or `--fail-on` given while the scan is off SHALL be
usage errors (exit 2) before any query. `--schema-graph` without the scan is accepted and
recorded, with no effect. In the environment, `RDF_FINGERPRINTER_SCHEMA_GRAPHS` is a
comma-separated list (EPIC DEC-8).

#### Scenario: A user check replaces a packaged one
- **WHEN** `--pitfall-checks my/` holds a valid check with id `p22_class_naming`
- **THEN** the run uses the user's query for `p22_class_naming`, and the result's source is the user's

#### Scenario: Scan options need the scan
- **WHEN** the fingerprint command runs with `--fail-on critical` but without `--pitfalls`
- **THEN** it exits 2 naming `--fail-on`, and sends no query

#### Scenario: Skipped check
- **WHEN** a run uses `--pitfalls --skip-pitfall p13_missing_inverse`
- **THEN** no query of check `p13_missing_inverse` is sent and the profile has no result for it

### Requirement: Fail on findings
A run SHALL exit 5 when `--fail-on LEVEL` is given, its outputs were written, it recorded no failure,
and a check of importance LEVEL or higher (`critical` > `important` > `minor`) counted at least one
row in any scanned graph (rows: the sum of the counts, not of the examples). It SHALL log `<rows> findings in <checks> checks at or above <level>` at
WARNING, counting rows and checks over all graphs. A recorded failure SHALL still exit 1 (EPIC
DEC-10).

#### Scenario Outline: Exit status from findings
- **WHEN** a run with `--fail-on <level>` finds only pitfalls of importance <found>, with no failure
- **THEN** it exits <code>

  Examples:
    | level     | found     | code |
    | critical  | important | 0    |
    | important | important | 5    |
    | minor     | critical  | 5    |

### Requirement: Pitfalls TSV format
The `pitfalls` format SHALL write, per profiled graph with a scan result, `pitfalls-<graph slug>.tsv`
with the header `Level`, `Rule Name`, `Subject`, `Property`, `Value`, and one line per example. The
level maps critical → `ERROR`, important → `WARN` and minor → `INFO`; the rule name is the check id;
IRIs are written in full, a blank node as `_:<id>`, a literal as its lexical form (datatype and
language dropped), and an unbound variable as an empty cell. A tab or line break inside a value
SHALL be written as a space.
`fingerprint-gen-pitfalls` SHALL write it from a saved profile. A graph whose checks all counted 0
gets a file with the header only; a graph without scan results, and a profile without any, SHALL
produce no file (EPIC DEC-9).

#### Scenario: ROBOT-style lines
- **WHEN** the TSV is generated for a profile whose `p19_multiple_domains_or_ranges` result has the example (`ex:p`, `rdfs:range`, `2`)
- **THEN** the file holds the line `ERROR	p19_multiple_domains_or_ranges	http://ex.org/p	http://www.w3.org/2000/01/rdf-schema#range	2`

#### Scenario: Offline
- **WHEN** `fingerprint-gen-pitfalls` renders a saved profile with scan results
- **THEN** it writes the TSV files and sends no query
