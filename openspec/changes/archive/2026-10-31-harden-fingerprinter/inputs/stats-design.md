> **SUPERSEDED** by `design.md` (2026-10-31): kept as a seed, not groomed. Final queries, settings and rules are in `design.md`.

# Statistics collection — design draft (2026-10-31, under discussion, not decided)

Parameters: `$G` graph IRI (default graph → no `GRAPH` wrapper), `$C` class, `$P` property,
`$CAP` instances per class (first N, harden DEC-3), `$K` enumeration limit.
`SAMPLE(C)` ≡ `{ SELECT ?s { GRAPH $G { ?s a $C } } LIMIT $CAP }`.

## Statistics catalogue, by depth

| Depth | Statistic | Query | Feeds |
|---|---|---|---|
| L0 graph | named graphs | Q0 | all |
| L0 graph | triples per graph | Q1 | VoID |
| L0 graph | triples per predicate (property partition) | Q2 | VoID, "complete" mode |
| L1 class | instances per class (exact) | Q3 | all |
| L1 class | declared `rdfs:subClassOf` edges | Q4 | UML, SHACL, report |
| L1 class | co-occurring types (sample) → implied C ⊑ D | Q8 | UML, report |
| L2 class×property | cardinality histogram: subjects with exactly n values (sample) | Q5 | all |
| L2 derived | subjects, triples, min, max, mean, confidence, label 1/?/+/*/{n} + alternatives, own/inherited | — (domain) | report, SHACL, UML |
| L3 values | per (C,p): node kind, datatype, language, triples, distinct objects | Q6 | report, SHACL, VoID |
| L3 values | per (C,p): object classes (+ untyped) with counts | Q7 | report, SHACL `sh:class`, UML associations |
| L3 rich | value enumeration where distinct objects ≤ K | Q9 | SHACL `sh:in` |
| L3 complete | properties used by C but absent from its sample | Q10 | completeness when C > CAP |
| L4 links | incoming (subject class, property) per class | Q11 | UML, report |

## Query templates

```sparql
# Q0 graphs
SELECT DISTINCT ?g { GRAPH ?g { } }

# Q1 triples
SELECT (COUNT(*) AS ?triples) { GRAPH $G { ?s ?p ?o } }

# Q2 property partitions (one scan; fallback: DISTINCT ?p, then COUNT per p)
SELECT ?p (COUNT(*) AS ?triples) { GRAPH $G { ?s ?p ?o } } GROUP BY ?p

# Q3 class partitions — COUNT without DISTINCT: (s rdf:type c) triples are unique in a graph
SELECT ?c (COUNT(?s) AS ?instances) { GRAPH $G { ?s a ?c } } GROUP BY ?c
#    fallback on timeout: SELECT DISTINCT ?c …  then  SELECT (COUNT(?s) AS ?n) { … ?s a $C }

# Q4 declared hierarchy (schema-sized; any graph)
SELECT DISTINCT ?sub ?sup { ?sub rdfs:subClassOf ?sup FILTER(isIRI(?sup)) }

# Q5 cardinality votes (one query per class, all properties)
SELECT ?p ?n (COUNT(?s) AS ?subjects) {
  { SELECT ?s ?p (COUNT(*) AS ?n) { SAMPLE($C) GRAPH $G { ?s ?p ?o } } GROUP BY ?s ?p }
} GROUP BY ?p ?n

# Q6 value kinds / datatypes / languages
SELECT ?p ?kind ?dt ?lang (COUNT(*) AS ?triples) (COUNT(DISTINCT ?o) AS ?distinct) {
  SAMPLE($C) GRAPH $G { ?s ?p ?o }
  BIND(IF(isLiteral(?o), "literal", IF(isBlank(?o), "bnode", "iri")) AS ?kind)
  BIND(IF(isLiteral(?o), datatype(?o), ?none) AS ?dt)
  BIND(IF(isLiteral(?o), lang(?o), ?none) AS ?lang)
} GROUP BY ?p ?kind ?dt ?lang

# Q7 object classes — inner join, untyped via UNION, no OPTIONAL
SELECT ?p ?t (COUNT(DISTINCT ?o) AS ?objects) {
  SAMPLE($C) GRAPH $G { ?s ?p ?o FILTER(!isLiteral(?o)) }
  { GRAPH $G { ?o a ?t } } UNION { FILTER NOT EXISTS { GRAPH $G { ?o a ?any } } BIND(fp:Untyped AS ?t) }
} GROUP BY ?p ?t

# Q8 co-types (implied hierarchy: count == sample size ⇒ C ⊑ D in the data)
SELECT ?d (COUNT(?s) AS ?subjects) { SAMPLE($C) GRAPH $G { ?s a ?d FILTER(?d != $C) } } GROUP BY ?d

# Q9 enumeration (only pairs with distinct ≤ K from Q6)
SELECT ?o (COUNT(*) AS ?triples) { SAMPLE($C) GRAPH $G { ?s $P ?o } } GROUP BY ?o LIMIT $K+1

# Q10 completeness (only when instances > CAP; P from Q2 not seen in Q5) — ASK stops at first hit
ASK { GRAPH $G { ?s a $C ; $P [] } }

# Q11 incoming links
SELECT ?sc ?p (COUNT(*) AS ?triples) { SAMPLE($C) GRAPH $G { ?x ?p ?s . ?x a ?sc } } GROUP BY ?sc ?p
```

## Algorithm

1. Per graph, in parallel: Q3, Q4 (once), Q1/Q2 if depth needs them. Fallbacks on timeout.
2. Per class, biggest first, bounded concurrency K: Q5, Q6, Q7, Q8 are independent (all only
   need `SAMPLE(C)`) → submitted together.
3. Second wave, data-pruned: Q9 for pairs with few distinct values; Q10 for big classes vs Q2
   predicates; Q11 if L4.
4. Timeout on a per-class query → retry with `CAP/10` (min floor), mark the class "first N";
   below the floor → record the failure in the profile, non-zero exit at the end.
5. Cost bound: each per-class query touches ≤ CAP subjects and their out-edges, so total work
   ≈ Σ_C min(|C|, CAP) × out-degree — independent of graph size beyond the caps; queries
   ≈ graphs × 4 + classes × 4 (+ pruned second wave).

## Profile model (sketch)

```
ProfileRun        endpoint, started/finished, tool version, settings(cap, threshold, depth,
                  concurrency, timeout), failures[]
└ GraphProfile    iri | default, triples?, predicate_triples{p: n}?
  └ ClassProfile  iri, instances (exact), sample_size, sampled (bool), declared_supers[],
                  cotypes{class: subjects}, incoming[(class, p, triples)]?
    └ PropertyProfile  iri, histogram{n: subjects} (n=0 included)          ← stored
                       subjects, triples, min, max, mean, confidence,      ← derived (domain)
                       label + alternatives, own|inherited
      └ ValueProfile   kind(iri|bnode|literal), datatype?, language?, class? | untyped,
                       triples, distinct_objects, enumeration{value: n}?
```

Stored = raw counts only; everything else derived in `domain`, so representations never disagree.

## Depth → representation

| Representation | Needs |
|---|---|
| VoID | L0 + L1 (+ L2 nested partitions, L3 distinct objects) |
| HTML statistics report | L1 + L2 + L3 |
| PlantUML | L1 + hierarchy + L2 label + L3 object classes (+ L4) |
| SHACL simple | L1 + L2 label + L3 kind/datatype/class |
| SHACL rich | + Q9 `sh:in`, languages, severity by confidence, Q10 |
| ReSpec document | L1–L3 (+ L4) |

## Developer feedback (2026-10-31)

- **Q7 across graphs**: object types MAY be looked up in any graph — a setting
  (`same-graph` | `any-graph`); `any-graph` replaces `GRAPH $G { ?o a ?t }` with `?o a ?t` over the
  whole dataset (`GRAPH ?any { ?o a ?t }` where the default graph is not the union).
- **Q10**: on/off via configuration property or environment variable.
- **Sampling is an optimisation, not a goal.** Precision is the default; see "Precision modes".

## Precision modes (proposed)

| Mode | How | Precise? | Cost / risk |
|---|---|---|---|
| `exact` (default) | Q5–Q8 per class with no `LIMIT` (`SAMPLE(C)` = all instances) | yes | one query touches all of C; giant classes may time out |
| `batched` (fallback 1) | stream C's instance IRIs once, run Q5–Q7 per `VALUES` batch (e.g. 2 000), merge client-side | yes for histograms, triples, types (additive); distinct objects need a client-side set (memory) or become approximate | many small queries; memory for distinct sets |
| `first-n` (fallback 2) | `LIMIT $CAP` | no — labelled "first N of M" | bounded cost; biased to store row order; max and rare properties underestimated (Q10 restores presence) |

Escalation on timeout: exact → batched → first-n → recorded failure. Instance counts (Q3) are
always exact. The mode actually used is stored per class in the profile.

## One algorithm, not parallel implementations (decided in draft, 2026-10-31)

The precision mode changes only **the subject source** spliced into every per-class query:

| Mode | Subject source |
|---|---|
| exact | `GRAPH $G { ?s a $C }` |
| batched | `VALUES ?s { …batch… }` (instance IRIs streamed once by `SELECT ?s { ?s a $C }`) |
| first_n | `{ SELECT ?s { GRAPH $G { ?s a $C } } LIMIT $N }` |

Every statistic is a **mergeable** partial result: histogram bins, triples, lengths (min/max/sum)
and value ranges merge by sum/min/max, so exact and first_n are "one batch" and batched is "many
batches + merge". The only non-additive figure is distinct objects; see trade-off T2.

## Trade-offs — explicit choices

- **T1 default policy `auto`**: exact first, escalate on timeout. Precision wherever the endpoint
  can answer; bounded cost only where it cannot. `exact`/`batched`/`first_n` can be forced.
- **T2 distinct objects in batched mode**: exact via a client-side set up to `distinct_limit`
  (default 1 000 000 per class×property); beyond that the count is a lower bound and
  `distinct_objects_exact = false`. No sketch library (HyperLogLog) — no new dependency.
- **T3 lexical statistics** (lengths, value ranges, languages, datatypes) are folded into Q6 as
  extra aggregates — no extra query, and they follow the class's precision mode. No separate
  literal sampling switch: the precision policy is the switch.
- **T4 diversity**: distinct ratio from Q6 (free); top-K values from Q9 per class×property in the
  second wave, only at depth `rich_values` (it groups by value — the costliest per-pair query).
- **T5 untyped subjects** (LODStats, RDF2Graph): one optional graph-level query at depth `graphs`;
  it is a full scan, so it runs only when asked.
- **T6 cross-graph object types**: `object_type_scope` setting (developer); `any_graph` also
  records the graph that supplied the type (linkset evidence, void-generator).
- **T7 completeness check (Q10)**: configuration property / environment variable (developer).

### Q6 with lexical aggregates

```sparql
SELECT ?p ?kind ?dt ?lang (COUNT(*) AS ?triples) (COUNT(DISTINCT ?o) AS ?distinct)
       (MIN(STRLEN(STR(?o))) AS ?minLen) (MAX(STRLEN(STR(?o))) AS ?maxLen)
       (SUM(STRLEN(STR(?o))) AS ?sumLen) (MIN(?o) AS ?minVal) (MAX(?o) AS ?maxVal) {
  $SUBJECTS GRAPH $G { ?s ?p ?o }
  BIND(IF(isLiteral(?o), "literal", IF(isBlank(?o), "bnode", "iri")) AS ?kind)
  BIND(IF(isLiteral(?o), datatype(?o), ?none) AS ?dt)
  BIND(IF(isLiteral(?o), lang(?o), ?none) AS ?lang)
} GROUP BY ?p ?kind ?dt ?lang
```
Lengths and ranges are kept only for literal groups.

### Q9 top-K values

```sparql
SELECT ?o (COUNT(*) AS ?n) { $SUBJECTS GRAPH $G { ?s $P ?o } } GROUP BY ?o ORDER BY DESC(?n) LIMIT $K
```

## Where every statistic comes from (catalogue → model)

Raw → `model/fingerprint_stats.yaml`; computed → `model/fingerprint_analytics.yaml`.

| Statistic | Today's template | Other tools | Model |
|---|---|---|---|
| graphs | ✓ | all | `GraphProfile.graph` |
| triples per graph | | void-gen, LODStats, SHACL Play | `GraphProfile.triples` |
| triples per predicate | | void-gen, LODStats | `PredicatePartition` |
| distinct subjects / objects (graph) | | void-gen, LODStats | `GraphProfile.distinct_*` |
| untyped subjects | | LODStats, RDF2Graph | `GraphProfile.untyped_subjects` |
| classes + instances | ✓ (`class_instance_count`) | all | `ClassProfile.instances` |
| declared subclass edges | | RDF2Graph, SHACL Play, LODStats | `SubclassEdge` |
| co-types / implied parents | | SHACL Play | `CoTypeCount` → `ParentClass` |
| subjects using property | ✓ (`subject_count`) | QSE support, void-gen | histogram → `subjects_with_property` |
| min / max / avg per instance | ✓ | sheXer, RDF2Graph (0/1 only) | histogram → `min`, `max`, `mean` |
| cardinality votes / label | | sheXer, QSE, SHACL Play | `CardinalityBin` → `cardinality_label` |
| confidence | | QSE, sheXer | → `confidence` |
| property kind (object/datatype) | ✓ (`property_types`) | SHACL Play nodeKind | `ValuePartition.node_kind` → `property_kind` |
| object classes / datatypes | ✓ (`object_types`) | all | `ValuePartition.object_class`, `.datatype` |
| untyped objects | ✓ (`rdfs:Resource`) | RDF2Graph | `ValuePartition` without class → `untyped_object_ratio` |
| distinct objects | ✓ (`object_count`) | void-gen, SHACL Play | `ValuePartition.distinct_objects` |
| languages | | SHACL Play, LODStats | `ValuePartition.language` |
| literal lengths | | LODStats (avg string length) | `min/max/total_length` → `mean_length` |
| value ranges | | — | `min_value`, `max_value` |
| value enumeration / top values | | SHACL Play (`sh:in`, histograms) | `ValueCount` → `is_enumeration_candidate`, `entropy_estimate` |
| incoming links / reverse | | RDF2Graph, sheXer inverse paths | `IncomingLink` |
| cross-graph links | | void-gen linksets | `object_class_graph` → `cross_graph_object_types` |
| vocabularies used | | LODStats | → `GraphAnalytics.vocabularies` |
| labelled subjects | | LODStats | → `ClassAnalytics.label_coverage` |
| in/out degree | | LODStats | → `mean_out_degree`; incoming links |
| hierarchy depth | | LODStats | → `hierarchy_depth` |
| own / inherited property | | RDF2Graph | → `inheritance` |
| owl:sameAs count | | LODStats | predicate partition of `owl:sameAs` (no own slot) |

Not taken: LODStats' RDF-syntax/vocabulary-definition counters (about ontology files, not data);
QSE support/confidence pruning *thresholds* (an output choice for SHACL, not a statistic).
