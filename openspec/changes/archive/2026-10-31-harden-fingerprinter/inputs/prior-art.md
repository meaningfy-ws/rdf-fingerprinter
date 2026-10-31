# Prior art — 2026-10-31 (seed input, not groomed)

Shallow clones in the repos parent folder (`../void-generator`, `../shexer`, `../qse`, `../shacl-play`,
`../LODStats`, `../shaclgen`, `../RDF2Graph`), read but not run. Stars and last push from the GitHub API.

| Tool | ★ | Lang / licence | Last push | Input | Output | Strategy |
|---|---|---|---|---|---|---|
| sparna-git/shacl-play (generate + doc) | 57 | Java / LGPL-3 | 2026-10 | endpoint, file | SHACL + VoID + HTML doc | many small queries, ASK for 0/1 facts, sample on timeout |
| weso/shexer | 51 | Python / Apache-2 | 2026-06 | files, endpoint | ShEx, SHACL, JSON, UML | client-side counting; one query per instance on endpoints |
| AKSW/shaclgen | 30 | Python / Unlicense·MIT | 2026-04 | files only (rdflib) | SHACL | per-property DISTINCT queries; no counts |
| sib-swiss/void-generator | 20 | Java / MIT | 2026-10 | endpoint, Virtuoso JDBC | VoID + SD | global GROUP BYs, then per class×property COUNT; thread pool |
| dkw-aau/qse | 17 | Java / MIT | 2025-11 | N-Triples, GraphDB | SHACL with support/confidence | 2-pass streaming; reservoir sampling + parallel per-entity queries |
| AKSW/LODStats | 11 | Python / GPL-3 | 2026-05 | dumps (stream) | VoID | single streaming pass; SPARQL mode is a stub |
| jessevdam/RDF2Graph | 6 | Java / MIT | 2015 (abandoned) | endpoint | graph, ShEx, OWL | per class×property queries with inner LIMIT caps; thread pool; resumable |

Not found / dropped: Loupe (no public code), ABSTAT (2★, 2016).

## Two families

1. **Push aggregation to the endpoint** — void-generator, SHACL Play, RDF2Graph, QSE-exact, rdf-fingerprinter.
2. **Pull rows, count in the client** — sheXer, QSE-sampled, LODStats, shaclgen.

Every endpoint tool except ours binds the class *inside* the pattern (`?s a <C>`), so the engine
touches only that class's instances. Ours puts `VALUES` outside four whole-graph `GROUP BY`
subqueries. That is the single largest, cheapest fix.

## Where rdf-fingerprinter differs

- **Richer per-property statistics** than all but sheXer: real min/max/avg occurrences per instance.
  SHACL Play, QSE and RDF2Graph only decide 0/1 bounds (min 1? max 1?).
- **Human HTML report is the product**; most others emit SHACL/ShEx/VoID first (SHACL Play also emits HTML).
- **No machine-readable output**, no sampling, no concurrency, no timeout, no resume.
- **Smallest codebase** (templates + 60 lines of Python), pure SPARQL 1.1, any store.

## Techniques worth adopting (ranked by payoff ÷ cost)

1. Bind the class inside the pattern; one class-count `GROUP BY ?class` query per graph (void-generator, QSE).
2. Bounded concurrency across classes with a pooled HTTP session (void-generator, RDF2Graph).
3. Per-query timeout + limited retry with backoff; non-zero exit on failure (sheXer, void-generator).
4. Object types via inner join `?o a ?t` + separate `FILTER(isLiteral) datatype()` query — no OPTIONAL (void-generator).
5. ASK / `LIMIT 1` for yes/no facts (SHACL Play).
6. Degrade on timeout: retry the class on a sample (inner `LIMIT` or `VALUES` batches), mark "sampled, N" (SHACL Play, RDF2Graph).
7. Coverage = subjects-with-property / class instances; derived cardinality 1 / ? / + / * (sheXer, QSE confidence).
8. Optional VoID output (classPartition, propertyPartition, entities, distinctObjects) — standard, cheap (void-generator, SHACL Play).
9. Checkpoint per graph/class so long runs resume (RDF2Graph, void-generator).
10. Store-specific query variants (QLever, Virtuoso) — rabbit hole; only if a target store demands it.

## Class/subclass handling (checked 2026-10-31)

- **RDF2Graph** — loads `rdfs:subClassOf` from the endpoint, marks classes that have instances or
  subclasses with instances, then simplifies: lifts shared property links to the highest common
  ancestor and drops from children what the parent already declares (`simplify/TreeNode.java`).
- **SHACL Play** — counts with `rdf:type/rdfs:subClassOf*` (inferred membership) unless
  `assumeNoSubclassOf`; optional *direct-type* mode counts only instances with no more specific type
  (`FILTER NOT EXISTS { ?uri a ?child . ?child rdfs:subClassOf* $type }`); prunes redundant
  superclasses from `sh:class` by data co-occurrence.
- **sheXer** — `track_hierarchies` builds a hierarchy tree of instance types (details not read).
- **shaclgen** — ontology mode copies `rdfs:subClassOf` onto shapes. **QSE, void-generator, LODStats** — none.
- **rdf-fingerprinter** — none: every asserted type is profiled flat, so a materialised superclass
  repeats all its subclasses' properties.
