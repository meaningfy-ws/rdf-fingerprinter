## ADDED Requirements

### Requirement: Every namespace has a prefix
After collection the fingerprinter SHALL give a prefix to the namespace of each profiled graph IRI,
class, property, value type, parent class and linked class. The namespace of an IRI SHALL be:
- the IRI up to and including its last `#`, when no `/` follows that `#`;
- otherwise, up to and including its last `/`;
- for a `urn:` IRI with neither, up to and including its last `:`.

No two namespaces SHALL share a prefix, and the table SHALL be identical for identical inputs (EPIC
DEC-1, DEC-2).

#### Scenario: Unknown vocabulary is named
- **WHEN** a profile uses `https://ontology.brainframe.com/2016/04/brainframe#Person` and no prefix source names that namespace
- **THEN** the namespace table holds the generated prefix `brainframe` for `https://ontology.brainframe.com/2016/04/brainframe#`

#### Scenario: A fragment route is not a hash namespace
- **WHEN** a profile uses `https://my.brainframe.com/#/knowledge/Person/7a08`
- **THEN** its namespace is `https://my.brainframe.com/#/knowledge/Person/`

#### Scenario: Deterministic table
- **WHEN** the same profile is resolved twice with the same prefix sources
- **THEN** both namespace tables are equal

### Requirement: Prefix source precedence
A namespace SHALL take its prefix from the first source that names it, in this order:
1. the user prefix file (`--prefixes FILE`, else `RDF_FINGERPRINTER_PREFIXES_FILE`);
2. the table saved in the profile, when one is being re-resolved;
3. the packaged prefixes;
4. prefix.cc;
5. generation.

The rules for each candidate prefix:
- A prefix already held in the table by another namespace SHALL be skipped. The exception is a user
  prefix: it displaces the holder, and the displaced namespace is resolved again from sources 3–5.
- The names `rdf`, `rdfs`, `owl`, `xsd`, `sh` and `fp` SHALL be accepted only for their standard
  namespaces: `http://www.w3.org/1999/02/22-rdf-syntax-ns#`, `http://www.w3.org/2000/01/rdf-schema#`,
  `http://www.w3.org/2002/07/owl#`, `http://www.w3.org/2001/XMLSchema#`, `http://www.w3.org/ns/shacl#`
  and `https://data.meaningfy.ws/fingerprint/`.
- `shape`, and any prefix ending in `-shape`, SHALL never be accepted from any source.
- A skipped candidate SHALL be logged at DEBUG, and the namespace falls to the next source.
- When a file maps several prefixes to one namespace, the first in file order SHALL win. If that
  first prefix is skipped, the namespace falls to the next source, not to the same source's next
  candidate.
- The case of prefixes from files and from prefix.cc SHALL be kept.

Each table entry SHALL record its source as `user`, `packaged`, `prefix_cc` or `generated`; a saved
entry keeps the source it was saved with (EPIC DEC-1).

#### Scenario Outline: The first source wins
- **WHEN** the namespace `http://xmlns.com/foaf/0.1/` is named by <sources>
- **THEN** its prefix is <prefix> with source <source>

  Examples:
    | sources                                         | prefix          | source    |
    | the user file as `friend`, the packaged file    | friend          | user      |
    | the packaged file as `foaf`, prefix.cc          | foaf            | packaged  |
    | prefix.cc only, as `foaf`                       | foaf            | prefix_cc |
    | none                                            | foaf            | generated |

#### Scenario: Reserved names are not taken from a file
- **WHEN** the user file maps `sh:` to `http://ex.org/sh#` and `bf-shape:` to `http://ex.org/bf/`
- **THEN** neither name is used for those namespaces, and both get prefixes from the later sources

#### Scenario: Bad user file
- **WHEN** `--prefixes` names a file that is not a JSON object of `name:` → IRI
- **THEN** the command exits 2 with a message naming the option and the file, and sends no query

#### Scenario: A user file over a saved table
- **WHEN** `fingerprint-gen-puml --prefixes my.json` renders a saved profile whose table names `http://ex.org/` as `ex` (generated) and `http://ex.org/core/` as `ex-core` (generated), and `my.json` names `http://ex.org/` as `exo`
- **THEN** the diagram uses `exo:` for `http://ex.org/` and still `ex-core:` for `http://ex.org/core/`

#### Scenario: A user prefix displaces a saved one
- **WHEN** a saved table names `http://xmlns.com/foaf/0.1/` as `foaf` (packaged), and the user file maps `foaf:` to `http://ex.org/foaf/`
- **THEN** `http://ex.org/foaf/` gets `foaf` (user), and `http://xmlns.com/foaf/0.1/` is resolved again from the packaged file, prefix.cc and generation, without taking `foaf`

### Requirement: prefix.cc lookup is best effort
The `fingerprint` command SHALL, unless switched off by `--no-prefix-lookup` or by
`RDF_FINGERPRINTER_PREFIX_LOOKUP=false`, fetch prefix.cc's full prefix list (`/popular/all.file.json`), once, and only when some
namespace is named by no file.
- **Transport.** It SHALL first use HTTPS with certificate checks. Only when that fails on
  certificate verification SHALL it fetch the list over plain HTTP, logging at INFO
  `prefix.cc certificate not valid; fetched the prefix list over HTTP` (developer, 2026-10-31).
- **Timeouts.** Each network operation SHALL time out after 10 seconds, with no retry.
- **Use of the list.** The list SHALL be reversed locally, so no namespace of the store is sent.
  When several prefix.cc prefixes share a namespace, the first in the list SHALL be used. A key is
  read as a prefix name (`foaf`, without a colon). Entries with an invalid prefix name or an
  unwritable IRI SHALL be ignored.
- **Failure.** When the fetch fails, or the list cannot be parsed, the run SHALL log one WARNING
  `prefix.cc lookup failed: <reason>; generating prefixes`, generate the missing prefixes, and keep
  its exit status.
- **Settings.** An invalid `RDF_FINGERPRINTER_PREFIX_LOOKUP` value SHALL be a usage error (exit 2).
- The generator commands SHALL never fetch.
- A library caller of `fingerprint_report` SHALL get a fetch only by passing a prefix list source.

#### Scenario: prefix.cc offline
- **WHEN** a run profiles a store while prefix.cc is unreachable
- **THEN** the run exits as it would otherwise, the warning is logged once, and the unnamed namespaces have generated prefixes

#### Scenario: Expired certificate
- **WHEN** prefix.cc's HTTPS certificate fails verification and its HTTP list is reachable
- **THEN** the list is read over HTTP, the INFO line is logged, and no warning is logged

#### Scenario: Lookup switched off
- **WHEN** a run is given `--no-prefix-lookup`
- **THEN** it makes no request to prefix.cc

### Requirement: Generated prefixes
**Path segments.** The path segments of a namespace SHALL be the `/`-separated segments of its IRI
path, followed by those of its fragment when the fragment contains a `/`; empty segments SHALL be
dropped. For `urn:` namespaces they SHALL be the `:`-separated parts after `urn`. Host labels SHALL
exclude the port.

**Order.** Namespaces SHALL be generated in order of depth (host labels plus path segments), then
lexically, so that parents come first. Then:
1. **Base.** The base of a namespace is the namespace without its trailing `#`, `/` or `:`.
2. **Parent.** A parent is a namespace already in the table, or a namespace that a file or prefix.cc
   names and that begins a gathered namespace (such a parent is not saved in the table). It must
   have the same scheme, such that either
   its host and path segments begin the child's, or its host is the child's host without leading
   labels and its path segments are the same. A parent SHALL contribute at least one extra path
   segment or host label: a namespace with the same host and segments is not a parent. When a
   namespace has a parent, its prefix SHALL be
   the prefix of the parent with the most path segments and host labels, then `-`, then the extra
   path segments or leading host labels joined by `-`.
3. **No parent.** Otherwise the prefix SHALL be the last path segment that is not empty, not all
   digits, and does not fully match `v?\d+(\.\d+)*`. Failing that, it SHALL be the rightmost host label
   left after dropping `www`, the top-level label, and a second-level label of at most 3 characters
   when the host has at least 3 labels (`co.uk`, `gov.uk`).
4. **Clean-up.** A generated prefix SHALL be lower-cased. Each run of characters outside `[a-z0-9-]`
   SHALL become `-`, runs of `-` SHALL collapse to one, and leading and trailing `-` SHALL be
   stripped. A leading digit SHALL get `n` in front, and an empty result SHALL become `ns`.
5. **Clashes.** A prefix already in the table (compared case-insensitively, since prefixes reach
   file names), reserved (`rdf`, `rdfs`, `owl`, `xsd`, `sh`, `fp`,
   `shape`), or ending in `-shape`, SHALL take the next free numeric suffix starting at `2`.

#### Scenario Outline: Generated names
- **WHEN** the namespace <namespace> is generated with the table <known>
- **THEN** its prefix is <prefix>

  Examples:
    | namespace                                                 | known                                                                 | prefix         |
    | `https://ontology.brainframe.com/2016/04/brainframe#`     | none                                                                  | brainframe     |
    | `https://ontology.brainframe.com/2016/04/brainframe/sub/` | `brainframe:` → `https://ontology.brainframe.com/2016/04/brainframe#` | brainframe-sub |
    | `https://my.brainframe.com/#/knowledge/RelationId/`       | none                                                                  | relationid     |
    | `http://ex.org/core/`                                     | `ex:` → `http://ex.org/`                                              | ex-core        |
    | `http://data.ex.org/`                                     | `ex:` → `http://ex.org/`                                              | ex-data        |
    | `http://a.b.ex.org/`                                      | `ex:` → `http://ex.org/`                                              | ex-a-b         |
    | `http://ex.org/v2/`                                       | none                                                                  | ex             |
    | `http://other.org/ex/`                                    | `ex:` → `http://ex.org/`                                              | ex2            |
    | `http://www.legislation.gov.uk/`                          | none                                                                  | legislation    |
    | `http://ex.org/My_Vocab.v1/`                              | none                                                                  | my-vocab-v1    |
    | `http://ex.org/2020/`                                     | none                                                                  | ex             |
    | `http://ex.org/sh/`                                       | none                                                                  | sh2            |
    | `http://ex.org/bf/shape/`                                 | `bf:` → `http://ex.org/bf/`                                           | bf-shape2      |
    | `https://ontology.brainframe.com/2016/04/brainframe#blueprint/` | `brainframe:` → `https://ontology.brainframe.com/2016/04/brainframe#` | brainframe-blueprint |
    | `https://ontology.brainframe.com/2016/04/brainframe/`     | `brainframe:` → `https://ontology.brainframe.com/2016/04/brainframe#` | brainframe2    |
    | `http://store.ex.org:9999/`                               | none                                                                  | store          |
    | `http://localhost:8890/`                                  | none                                                                  | ns             |
    | `http://10.0.0.1/`                                        | none                                                                  | n0             |
    | `urn:x:thing:`                                            | none                                                                  | thing          |
    | `http://ex.org/core/`                                     | `EX:` → `http://ex.org/`                                              | ex-core        |

### Requirement: The namespace table is saved with the profile
The namespace table SHALL be written into `profile.json` and read back with it, so the generator
commands use the names the run chose. A profile saved without a table SHALL still load; its table
SHALL then be resolved from the files and by generation, without fetching.

#### Scenario: Offline generators reuse the table
- **WHEN** `fingerprint-gen-puml` renders a saved profile
- **THEN** it uses the saved prefixes and makes no HTTP request

#### Scenario: Old profile
- **WHEN** a profile file without a namespace table is loaded
- **THEN** it loads, and every namespace gets a prefix from the files or by generation

### Requirement: Short names in every output
An IRI SHALL be shortened by the longest namespace in the table that begins it (EPIC DEC-10). The
report and the PlantUML diagrams SHALL show every IRI as `prefix:local`; an IRI equal to its
namespace SHALL be shown as `prefix:`. In Turtle an IRI SHALL be written `<iri>` only when its
local part is not a valid Turtle local name. Each output SHALL declare every prefix it uses.

#### Scenario: Longest namespace wins
- **WHEN** the table holds `ex:` → `http://ex.org/` and `ex-core:` → `http://ex.org/core/`
- **THEN** `http://ex.org/core/Thing` is shown as `ex-core:Thing`

#### Scenario: No long IRIs in the diagram
- **WHEN** the PlantUML output is generated for the readability test profile
- **THEN** no class, attribute, association or package label holds `http://` or `https://`
