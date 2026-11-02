# Pattern schema: a two-part representation (term dictionary + structural patterns) — 2026-11-01 (seed input, not groomed)

This note works out option 8 of [`schema-representation-options.md`](schema-representation-options.md)
(Cypher-style path patterns) as a richer, two-part representation. The developer asked for it as
follows: "explore the option with Cypher-style patterns, enriched with additional annotations and
statistics. The schema representation has two parts: (1) for each term, class or property, a set of
labels, comments and definitions; (2) — very important — the structural patterns that can be used,
along with the statistics."

Nothing here is decided. Every number comes from `tests/test_data/profiles/sample-profile.json`,
unless a line is marked *illustrative*.

## 1. The idea

- **Part A: the term dictionary.** One entry per class and per property. Each entry gives the
  term's prefixed name, its full IRI, its labels per language, and its comments and definitions,
  each tagged with the source it came from.
- **Part B: the structural patterns.** For each class, every pattern the data actually contains
  (outgoing, incoming, co-types, and paths worth showing), each with the statistics an LLM needs to
  write the query: coverage, values per instance, distinct objects, node kind, value range and
  precision.
- **The arrows are a notation, not a query language.** `(:euvoc:Continent)-[:skosxl:prefLabel]->(:skosxl:Label)`
  stands for the SPARQL triple pattern `?c a euvoc:Continent ; skosxl:prefLabel ?l . ?l a skosxl:Label`.
  This is **not** Cypher or Gremlin support. Nothing parses or runs Cypher, so the Q13 no-go
  (SPARQL and RDF only) still holds.
- **Evidence.** The arrow form is the static schema format of the Text2Cypher studies (Ozsoy 2025;
  the Neo4j blog). Adding statistics follows the research seed's method 3, "enrich the schema with
  data-derived facts", which is the idea behind Neo4j's "enhanced schema" (property value samples
  and ranges). Fitch & Kurtz found that labels and comments mattered more than model choice, and
  that motivates Part A. All of these are from `llm-schema-research.md`. No study in the seed tests
  this exact two-part layout.

## 2. Part A: the term dictionary

### Entry layout

```text
<prefixed name>  <full IRI>  <class|property>
  label@<lang>       "<text>"   [<source>]
  comment@<lang>     "<text>"   [<source>]
  definition@<lang>  "<text>"   [<source>]
```

- `<source>` is `ontology` (the `--ontology` file) or `data` (the label query, stored in the
  profile). By DEC-7, the ontology wins for a term it labels, and the data fills in the terms it
  does not.
- A term with no entry falls back to its prefixed name, so it needs no line at all.

### The F2 predicates mapped to fields (proposed list, from `qa-round-1.md`)

| Field | Predicates, in priority order |
|---|---|
| `label` | `skos:prefLabel`, `skosxl:prefLabel`/`skosxl:literalForm`, `rdfs:label`, `dcterms:title` |
| `altLabel` (shown only when no `label` exists) | `skos:altLabel` |
| `definition` | `skos:definition` |
| `comment` | `rdfs:comment`, `dcterms:description`, `skos:scopeNote` |

Splitting `definition` from `comment` is new in this note. In `qa-round-1.md` F2, both are
"comment".

### What the sample data has

- **No class or property in the sample data has a label, comment or definition.** Any Part A
  entry for a term therefore comes from an `--ontology` file or a test fixture.
- The data does label **instances**. All 6 continents and the scheme
  `<http://publications.europa.eu/resource/authority/continent>` carry SKOS-XL labels (the scheme's
  is `"Continent"@en`), and the `owl:Ontology` with the same IRI has `rdfs:comment "Continent"`.
  These are values, not schema terms. Part A as asked covers classes and properties only. Whether
  it should also cover value IRIs is question P5.

### Example entries

The first four are **illustrative: they would come from the `--ontology` file**. The texts are the
published labels of SKOS, SKOS-XL and DCMI Terms as I recall them. They are not profile facts, and
the wording must be checked against the published files before it goes into a fixture.

```text
skos:Concept  <http://www.w3.org/2004/02/skos/core#Concept>  class
  label@en       "Concept"                                [ontology]   # illustrative
  definition@en  "An idea or notion; a unit of thought."  [ontology]   # illustrative

skosxl:Label  <http://www.w3.org/2008/05/skos-xl#Label>  class
  label@en       "Label"                                  [ontology]   # illustrative
  definition@en  "A special class of lexical entities."   [ontology]   # illustrative

skosxl:prefLabel  <http://www.w3.org/2008/05/skos-xl#prefLabel>  property
  label@en       "preferred label"                        [ontology]   # illustrative

dcterms:created  <http://purl.org/dc/terms/created>  property
  label@en       "Date Created"                           [ontology]   # illustrative
  definition@en  "Date of creation of the resource."      [ontology]   # illustrative

euvoc:Continent  <http://publications.europa.eu/ontology/euvoc#Continent>  class
  (no entry in the sample data and no ontology given: shown as euvoc:Continent)
```

## 3. Part B: structural patterns with statistics

### Pattern layout

```text
## <class>  <instances> instances · <precision> · graph <graph>
co   <class> <subjects>/<observed>                               # co-types
out  (:C)-[:p]->(:Target|Target2)   <stats>                      # object properties
out  (:C)-[:p]->(xsd:type)          <stats> · <min>..<max>       # literal properties
out  (:C)-[:p]->(IRI)               <stats>                      # objects with no type
in   (:Other)-[:p]->(:C)            <triples>                    # incoming links
path (:C)-[:p]->(:T)-[:q]->(<type>) <stats of the last hop>      # a path worth showing
```

`<stats>` is `with/observed · values per instance · distinct objects · node kind`:
- `with/observed`: instances that have the property / instances observed, so `56/104` is 54% coverage.
- Values per instance: `1` when every instance has exactly one; `23–24` for a range; `mean 3.43`
  when it varies; a histogram (`24×97, 23×7`, meaning 97 instances have 24 values and 7 have 23)
  when there are few bins.
- Distinct objects: `distinct_objects` of the property.
- Node kind: `blank`, `iri` or `literal`.
- `<min>..<max>`: the smallest and largest values in SPARQL order (`min_value`/`max_value`).
- Top-K values: shown as `top: …` when the profile has them. The sample profile has none (see §4).

Precision: `exact`, or `first_n 10000 of 120000` with a `~` before every number that is a lower
bound. The sample profile has **only exact classes**, so no example below shows the marker.

### Example: euvoc:Continent (graph continents)

```text
## euvoc:Continent  6 instances · exact · graph <http://publications.europa.eu/resources/authority/continents>
co   skos:Concept 6/6
out  (:euvoc:Continent)-[:skosxl:prefLabel]->(:skosxl:Label)                     6/6 · 24 · 144 distinct · blank
out  (:euvoc:Continent)-[:euvoc:xlNotation]->(:euvoc:XlNotation)                 6/6 · 1 · 6 distinct · blank
out  (:euvoc:Continent)-[:skos:inScheme]->(:skos:ConceptScheme|owl:Ontology)     6/6 · 1 · 1 distinct · iri
out  (:euvoc:Continent)-[:skos:topConceptOf]->(:skos:ConceptScheme|owl:Ontology) 6/6 · 1 · 1 distinct · iri
out  (:euvoc:Continent)-[:euvoc:status]->(IRI)                                   6/6 · 1 · 1 distinct · iri
out  (:euvoc:Continent)-[:euvoc:startDate]->(xsd:date)                           6/6 · 1 · 1 distinct · 1952-07-24
out  (:euvoc:Continent)-[:dcterms:created]->(xsd:date)                           6/6 · 1 · 1 distinct · 2014-10-10
in   none
path (:euvoc:Continent)-[:skosxl:prefLabel]->(:skosxl:Label)-[:skosxl:literalForm]->(rdf:langString)  1 per label · 24 languages
path (:euvoc:Continent)-[:euvoc:xlNotation]->(:euvoc:XlNotation)-[:rdf:value]->(xsd:string)          1 · AFRICA..OCEANIA
```

**How the two paths are built.** Each path joins the Continent pattern with the target class's own
profile in the same graph. The last-hop figures (24 languages; `AFRICA..OCEANIA`) describe **all**
instances of the target class, not only those reached from a continent. `skosxl:Label` has 145
instances: 144 reached from the continents and 1 from the scheme. Path-level statistics are not in
the profile (see §4).

### Example: euvoc:Treaty (graph treaties), 11 of its 24 properties

```text
## euvoc:Treaty  104 instances · exact · graph <http://publications.europa.eu/resources/authority/treaties>
co   skos:Concept 104/104
out  (:euvoc:Treaty)-[:skosxl:prefLabel]->(:skosxl:Label)                    104/104 · 24×97, 23×7 · 2489 distinct · blank
out  (:euvoc:Treaty)-[:skosxl:altLabel]->(:skosxl:Label)                     56/104 · 1–74 · 2040 distinct · blank
out  (:euvoc:Treaty)-[:euvoc:xlNotation]->(:euvoc:XlNotation)                104/104 · 1–6, mean 3.43 · 357 distinct · blank
out  (:euvoc:Treaty)-[:dcterms:replaces]->(:euvoc:Treaty|skos:Concept)       22/104 · 1 · 22 distinct · iri
out  (:euvoc:Treaty)-[:dcterms:isReplacedBy]->(:euvoc:Treaty|skos:Concept)   22/104 · 1 · 22 distinct · iri
out  (:euvoc:Treaty)-[:euvoc:signatureLocation]->(IRI)                       74/104 · 1×72, 2×2 · 13 distinct · iri
out  (:euvoc:Treaty)-[:lemon:context]->(IRI)                                 104/104 · 2×101, 1×3 · 2 distinct · iri
out  (:euvoc:Treaty)-[:eli:date_document]->(xsd:date)                        83/104 · 1 · 30 distinct · 1951-04-18..2012-02-02
out  (:euvoc:Treaty)-[:euvoc:officialJournalSeries]->(xsd:string)            92/104 · 1 · 3 distinct · literal
out  (:euvoc:Treaty)-[:euvoc:endDate]->(xsd:date)                            22/104 · 1 · 13 distinct · literal
out  (:euvoc:Treaty)-[:euvoc:status]->(IRI)                                  104/104 · 1 · 3 distinct · iri
in   (:euvoc:Treaty)-[:dcterms:replaces]->(:euvoc:Treaty)      22
in   (:euvoc:Treaty)-[:dcterms:isReplacedBy]->(:euvoc:Treaty)  22
```

### Example: skosxl:Label (graph continents): incoming links and per-language values

```text
## skosxl:Label  145 instances · exact · graph <http://publications.europa.eu/resources/authority/continents>
out  (:skosxl:Label)-[:skosxl:literalForm]->(rdf:langString)  145/145 · 1 · 145 distinct · 24 languages (en 7, others 6 each)
out  (:skosxl:Label)-[:lexvo:script]->(IRI)                   12/145 · 1 · 2 distinct · iri
out  (:skosxl:Label)-[:dcterms:type]->(IRI)                   145/145 · 1 · 1 distinct · iri
in   (:euvoc:Continent)-[:skosxl:prefLabel]->(:skosxl:Label)    144
in   (:skos:Concept)-[:skosxl:prefLabel]->(:skosxl:Label)       144   # the same 144 triples: every continent is also a skos:Concept
in   (:skos:ConceptScheme)-[:skosxl:prefLabel]->(:skosxl:Label)   1
in   (:owl:Ontology)-[:skosxl:prefLabel]->(:skosxl:Label)         1   # the same subject IRI as the scheme
```

**Where the incoming lines come from.** They are derived by reversing the other classes' outgoing
patterns (`object_class` of their value partitions), not by a query. Because a subject is counted
under each of its classes, co-typed classes repeat the same triples. The comments mark this; a
renderer must state it too (see the cons in §7).

### Cross-graph object types

The sample profile was collected with `object_type_scope: same_graph`, so it has no cross-graph
types. With `any_graph`, a target type asserted in another graph would be written
`(:C)-[:p]->(:T @<graph>)`, from `object_class_graph`. This is notation only; there is no
example in the sample data.

## 4. Field mapping: what the profile carries today

Field paths are on `ProfileRun` (`fingerprint/domain/profile.py`) and on the analytics classes
derived from it on load (`ClassAnalytics`, `PropertyAnalytics`, in the same file and computed in
`fingerprint/domain/analytics.py`).

| Part | Field | Carried today by | Status |
|---|---|---|---|
| A | full IRI | `ClassProfile.class_iri`, `PropertyProfile.property` | present |
| A | prefixed name | `ProfileRun.namespaces` plus prefix resolution (namespace-prefixes spec) | present. The sample profile's `namespaces` is empty, so its prefixes are resolved at render time. |
| A | label / altLabel / comment / definition, per language | — | **MISSING**: the F2 data query (statistics-collection and the model) plus `--ontology` at render time (DEC-6) |
| A | source of each text | — | **MISSING**: same change; must record `ontology` or `data` per text |
| A | labels of value IRIs (e.g. a status IRI) | — | **MISSING**, and out of the current scope (P5) |
| B | instances, observed instances | `ClassProfile.instances`, `observed_instances` | present |
| B | precision marker | `precision_mode`, `sample_shared`, `ClassAnalytics.is_exact`, `sample_ratio`, `distinct_objects_exact` | present |
| B | co-types | `ClassProfile.co_types` (`CoTypeCount`) | present |
| B | coverage | `PropertyAnalytics.confidence`, `subjects_without_property` | present (derived) |
| B | values per instance | `PropertyProfile.cardinality_histogram`; `min`, `max`, `mean`, `median`, `cardinality_label` | present |
| B | target class, datatype, node kind | `ValuePartition.object_class`, `datatype`, `node_kind`; `PropertyAnalytics.value_types`, `property_kind` | present |
| B | languages | `ValuePartition.language`; `PropertyAnalytics.languages` | present |
| B | value range | `ValuePartition.min_value`, `max_value` | present |
| B | distinct objects | `PropertyProfile.distinct_objects` | present |
| B | top-K sample values | `PropertyProfile.top_values`, `top_values_exact` | **in the model, not in a default run.** Collected only at depth `rich_values` or deeper; the sample profile (depth `values`) has none. |
| B | incoming links (collected) | `ClassProfile.incoming_links` (`IncomingLink`) | **in the model, not in a default run.** Collected only at depth `links`. |
| B | incoming links (derived) | reverse of other classes' `ValuePartition.object_class` | derivable now, same graph only, with co-type repeats |
| B | multi-hop path | join with the target class's profile | derivable now, class-level statistics only |
| B | path-level statistics | — | **MISSING**, and new queries would be needed; propose it as a rabbit hole |
| B | cross-graph object types | `ValuePartition.object_class_graph` with `object_type_scope: any_graph` | present when that scope is set |

## 5. Variants worth comparing

**a. ASCII Cypher arrows (§3, as above).**
```text
(:euvoc:Continent)-[:skosxl:prefLabel]->(:skosxl:Label)  6/6 · 24 · 144 distinct · blank
```

**b. SPARQL triple patterns.** This is the closest to what the model must write, and every line is
a valid SPARQL basic graph pattern.
```sparql
?s a euvoc:Continent ; skosxl:prefLabel ?o . ?o a skosxl:Label .   # 6/6 · 24 · 144 distinct · blank
?s a euvoc:Continent ; euvoc:startDate ?o .   # xsd:date · 6/6 · 1 · 1952-07-24
```

**c. One line per pattern, no class repeated.** This saves tokens, but each line no longer stands
alone. Shown in full for Continent, so it can be measured in §6.
```text
euvoc:Continent 6 exact | co skos:Concept 6 | in none
  skosxl:prefLabel  -> skosxl:Label                     6/6 ×24 d144 blank
  euvoc:xlNotation  -> euvoc:XlNotation                 6/6 ×1  d6   blank
  skos:inScheme     -> skos:ConceptScheme|owl:Ontology  6/6 ×1  d1   iri
  skos:topConceptOf -> skos:ConceptScheme|owl:Ontology  6/6 ×1  d1   iri
  euvoc:status      -> IRI                              6/6 ×1  d1   iri
  euvoc:startDate   -> xsd:date                         6/6 ×1  d1   1952-07-24
  dcterms:created   -> xsd:date                         6/6 ×1  d1   2014-10-10
```

**d. How Parts A and B link.**
- By reference: Part B uses prefixed names only, and a client gets Part A from `search_schema` or a
  separate dictionary. Each part is smaller, and the dictionary is sent once.
- Inline: the label follows the name on first use, as in
  `(:euvoc:Continent "Continent"@en)-[:skosxl:prefLabel "preferred label"@en]->…` (the labels here
  are illustrative). It is one self-contained answer, but it repeats labels for every pattern.

## 6. Size

I counted the Unicode code points of each code block, with Python `len()`, for `euvoc:Continent`. The ShEx and Markdown
counts are for the snippets in `schema-representation-options.md` (§1 and §2).

| Representation of `euvoc:Continent` | Characters |
|---|---|
| ShEx compact (options §1) | 350 |
| Markdown class card (options §2) | 548 |
| Pattern schema, Part B, variant a (§3 above, without the two `path` lines) | 920 |
| Pattern schema, Part B, variant a (§3 above, full, with paths) | 1,170 |
| Pattern schema, Part B, variant c (§5c, all 7 properties) | 583 |
| SHACL Turtle (golden file, all Continent shapes) | 2,274 |

Part A adds nothing for Continent on the sample data, because no labels exist. With the
illustrative ontology entries, each labelled term adds about 60–130 characters. The counts are for
these hand-written snippets; a generator's output would differ slightly. F4 measures whole outputs,
not snippets.

## 7. How it fits the EPIC

**Replace or join DEC-5's two formats?** Three readings, none decided:
1. **Join.** Part B becomes a third LLM format next to ShEx-compact and the Markdown card, and the
   F4 size rule picks among all three.
2. **Replace the Markdown card.** Part B carries the card's statistics, in a form that reads more
   like a query. ShEx-compact stays as the parseable, standard option.
3. **Part A is shared in any case.** The term dictionary is a function of the labels (DEC-6,
   DEC-7), not of a format. Every format can draw on it: ShEx comments, Markdown card cells, SHACL
   `sh:name`, and the pattern schema.

**MCP fit.**
- `describe_class(class)` returns Part B for the class, plus the Part A entries of the terms it
  mentions.
- `search_schema(text)` searches Part A: names, labels and comments. That is where the words of a
  question meet the schema.
- `validate_query` checks a query's triple patterns against Part B. Whether a triple pattern
  matches an `out` pattern is the same check as Q11's "predicate used on a class whose profile
  lacks it", and the patterns give the target class needed for the next variable.

**Pros**
- It reads like the triple patterns the model must write. Ozsoy 2025 and Neo4j use the arrow form
  as a schema format for Cypher.
- It carries more of the profile than ShEx (coverage, distinct counts, ranges, co-types, incoming
  links), which is the research seed's method 3.
- Part A gives labels one home for every format, and is what `search_schema` needs.
- Validation can reuse it directly.

**Cons**
- It has no standard and no parser of its own. Variant b is valid SPARQL; variant a is not.
- It is larger than ShEx-compact (1,170 or 920 characters against 350 for Continent). If the F4
  size rule alone picked the default, Part B variant a would lose, and variant c (583 characters)
  would still lose to ShEx and the Markdown card (548).
- Derived incoming links and paths repeat triples across co-types and give class-level, not
  path-level, statistics. Both need care in the notation, or the model is misled.
- Arrow notation may lead a model to write Cypher. The research seed has no evidence either way.
  That is a risk to measure, not a reason to drop it.

**Recommendation (not a decision).** Adopt **Part A as a shared term dictionary** for every format
and for `search_schema`. Treat **Part B as a candidate third format** in the F3 evaluation,
preferably as variant b (SPARQL patterns) or c (compact), rather than replacing the Markdown card
before anything is measured.

## 8. Questions this raises

- P1: Does Part B join DEC-5 as a third format, replace the Markdown card, or stay a candidate for
  the evaluation only?
- P2: Which variant: a (arrows), b (SPARQL patterns) or c (compact)? And by reference or inline
  labels?
- P3: Should the default collection depth rise to `rich_values` (top-K values) or `links`
  (collected incoming links)? Or is deriving incoming links from outgoing patterns enough?
- P4: Paths: show one hop beyond the class (class-level statistics, labelled as such), or none?
- P5: Should Part A also cover value IRIs (status, type and scheme IRIs), whose labels the data
  often carries?
- P6: Should F2 keep `definition` separate from `comment`, as this note does?


## Refined format (after round 3, revised after round 4)

This section applies the developer's round-3 answers (`qa-round-1.md`, "Round 3 answers"):
- arrows (variant a);
- a glossary below the patterns;
- as little redundancy as possible;
- no depth increase;
- links between classes in both directions; one hop, but up to 3 hops through blank nodes (round 4);
- value IRIs written as prefixed names.

The renderings below were produced from `tests/test_data/profiles/sample-profile.json` by a
throw-away prototype script (`render2.py` in the session scratchpad). The script stays outside the repository; it is not product code. So
every number is the profile's.

### a) Non-redundancy rules

Each rule is a check a test can make on the output.

| # | Rule | Testable as |
|---|---|---|
| N1 | **Group by subject.** A class is written once, as a block header `(:C) n`, with its edges indented below as `-p-> target`. | No class name begins two blocks. |
| N2 | **Merge classes that have the same instances.** Two classes whose co-type count equals both of their instance counts become one block `(:A&B)`, names sorted, so their shared patterns are written once. Partial co-types stay as a `co C n` note on the header. | `euvoc:Continent` and `skos:Concept` (6 = 6 = 6) are one block, as are `owl:Ontology` and `skos:ConceptScheme`. |
| N3 | **One edge per property.** Target classes are joined with `\|` (alternatives); a merged group inside a target keeps `&`. Literal targets are written as the datatype; untyped IRI targets as `IRI`. | No property appears twice in a block. |
| N4 | **Defaults are omitted.** No coverage when every instance has the property; no `×1`; no distinct count when all values differ; no node kind except `bn` for blank nodes; no precision when exact. | `-euvoc:startDate-> xsd:date =1952-07-24` carries no `6/6`, `×1` or `d1`. |
| N5 | **A literal with one value shows it.** `=v` replaces both the distinct count and the range. Otherwise `lo..hi` shows the range, with `dN` when values repeat. | `=2014-10-10` and not `d1 2014-10-10..2014-10-10`. |
| N6 | **Both directions, every number printed once.** Every named-class block shows its outgoing edges and one `via` list of its incoming links, as `(:Source)-p`. In the whole-graph view the `via` list carries **names only**: the triple count is printed on the source's outgoing edge and nowhere else. In the one-class view (`describe_class`), `via` adds the count, because the source block is absent there. | `(:owl:Ontology&skos:ConceptScheme) 1 via (:euvoc:Continent&skos:Concept)-skos:inScheme, …` carries no `6`; the `6` is not repeated. |
| N7 | **Blank nodes are see-through; otherwise one hop.** A class whose instances are reached only as blank nodes gets no block of its own. Its edges are nested under the edge that reaches it, recursively, up to 3 hops from the named class, until a named class, an IRI or a literal is reached; a class already on the chain is not expanded again. A blank-node class reached from several edges is expanded once, under the edge with the most links (ties broken by name). Its other edges end in `^` ("expanded under another edge"). Nested statistics cover all the blank-node class's instances, as the legend says. Edges to named classes are one hop: they end at the target's name. | `skosxl:Label` is nested under `euvoc:Continent`'s `skosxl:prefLabel` (144 links) and the scheme's `skosxl:prefLabel` ends in `bn ^`. |
| N8 | **One prefix block and one legend line.** The prefix block comes first and lists only the prefixes used; value IRIs are written with them (P5). The legend is one comment line. | Each `PREFIX` is used at least once. |
| N9 | **The glossary lists only the labelled terms the output uses.** A term without a label is absent; its prefixed name is its name. | No glossary line for `euvoc:Continent` on the sample profile. |

### b) Full rendering of the continents graph (the final form)

This is the graph `http://publications.europa.eu/resources/authority/continents` in the
whole-graph view. The order is prefix block → legend → named-class blocks (largest first) →
glossary. `skosxl:Label` and `euvoc:XlNotation` have no blocks of their own: every instance of
either is a blank node, so N7 nests their edges.

```text
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX euvoc: <http://publications.europa.eu/ontology/euvoc#>
PREFIX lvont: <http://lexvo.org/ontology#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX skosxl: <http://www.w3.org/2008/05/skos-xl#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
# (:A&B) n: classes with the same n instances · via: incoming links · -p-> (:T|U) object classes · IRI untyped · deeper indent: a blank-node object's own edges (stats over all its instances; up to 3 hops) · ^ expanded under another edge · k/n instances having p (omitted: all) · ×a-b values per instance (omitted: 1) · bn blank nodes · @n languages · =v one value · lo..hi range · dN distinct (omitted: all differ)
(:euvoc:Continent&skos:Concept) 6
  -dcterms:created-> xsd:date =2014-10-10
  -euvoc:startDate-> xsd:date =1952-07-24
  -euvoc:status-> IRI d1
  -euvoc:xlNotation-> (:euvoc:XlNotation) bn
    -dcterms:created-> xsd:date =2014-10-10
    -dcterms:type-> IRI d1
    -euvoc:startDate-> xsd:date =1952-07-24
    -euvoc:status-> IRI d1
    -rdf:value-> xsd:string AFRICA..OCEANIA
  -skos:inScheme-> (:owl:Ontology&skos:ConceptScheme) d1
  -skos:topConceptOf-> (:owl:Ontology&skos:ConceptScheme) d1
  -skosxl:prefLabel-> (:skosxl:Label) ×24 bn
    -dcterms:created-> xsd:date =2014-10-10
    -dcterms:type-> IRI d1
    -euvoc:startDate-> xsd:date 1952-07-24..2014-10-10 d2
    -euvoc:status-> IRI d1
    -lvont:script-> IRI 12/145 d2
    -skosxl:literalForm-> rdf:langString @24
(:owl:Ontology&skos:ConceptScheme) 1 via (:euvoc:Continent&skos:Concept)-skos:inScheme, (:euvoc:Continent&skos:Concept)-skos:topConceptOf
  -dcterms:created-> xsd:date =2014-10-10
  -dcterms:identifier-> xsd:string =http://publications.europa.eu/resource/authority/continent
  -euvoc:startDate-> xsd:date =2014-10-10
  -euvoc:status-> IRI
  -owl:imports-> IRI
  -rdfs:comment-> rdfs:Literal =Continent
  -skosxl:prefLabel-> (:skosxl:Label) bn ^
# glossary: empty (the sample profile has no labels or comments)
```

**What a blank-node chain renders like.** These are the two chains in the sample data, each two
hops from `euvoc:Continent` to a literal:
- Continent → `euvoc:xlNotation` (a blank node, `euvoc:XlNotation`) → `rdf:value` (`xsd:string`,
  `AFRICA..OCEANIA`). This is the second indent level under `-euvoc:xlNotation->`. As SPARQL it is
  `?c euvoc:xlNotation/rdf:value ?code`.
- Continent → `skosxl:prefLabel` (a blank node, `skosxl:Label`, 24 per continent) →
  `skosxl:literalForm` (`rdf:langString` in 24 languages). As SPARQL it is
  `?c skosxl:prefLabel/skosxl:literalForm ?name`.

The sample data has no chain longer than two hops, so the 3-hop limit is not exercised here.

**Glossary entries the sample profile cannot supply.** These lines are **illustrative only: they
would come from the `--ontology` file**, and their wording must be checked against the published
files. They use the single description field of DEC-17.

```text
# glossary
skos:Concept "Concept"@en: An idea or notion; a unit of thought.
skosxl:Label "Label"@en: A special class of lexical entities.
skosxl:prefLabel "preferred label"@en
dcterms:created "Date Created"@en: Date of creation of the resource.
```

**The one-class view of a named class with incoming links,
`describe_class(skos:ConceptScheme)`.** The `via` list carries counts here, and the blank-node
`skosxl:Label` is expanded in full, because no other edge in the view expands it. Prefixes and
legend are omitted below.

```text
(:owl:Ontology&skos:ConceptScheme) 1 via (:euvoc:Continent&skos:Concept)-skos:inScheme 6, (:euvoc:Continent&skos:Concept)-skos:topConceptOf 6
  -dcterms:created-> xsd:date =2014-10-10
  -dcterms:identifier-> xsd:string =http://publications.europa.eu/resource/authority/continent
  -euvoc:startDate-> xsd:date =2014-10-10
  -euvoc:status-> IRI
  -owl:imports-> IRI
  -rdfs:comment-> rdfs:Literal =Continent
  -skosxl:prefLabel-> (:skosxl:Label) bn
    -dcterms:created-> xsd:date =2014-10-10
    -dcterms:type-> IRI d1
    -euvoc:startDate-> xsd:date 1952-07-24..2014-10-10 d2
    -euvoc:status-> IRI d1
    -lvont:script-> IRI 12/145 d2
    -skosxl:literalForm-> rdf:langString @24
# glossary: empty (the sample profile has no labels or comments)
```

`describe_class(euvoc:Continent)` renders exactly the Continent block of the graph view above. No
link points at Continent, so it has no `via` list.

### c) Size

These are Unicode code points, counted with `wc -m` and Python `len()`.

| Rendering | Characters |
|---|---|
| Continents graph, whole view (above), with prefix block, legend and empty glossary | 2,154 |
| — of which the prefix block and legend | 872 |
| — of which the class blocks and glossary line | 1,282 |
| Continent block alone, with both blank-node chains nested (no prefixes, no legend) | 772 |
| `describe_class(euvoc:Continent)`, with prefixes and legend | 1,709 |
| Illustrative glossary (4 entries) | 245 |
| ShEx compact snippet, Continent (options §1; no blank-node chains) | 350 |
| Markdown card snippet, Continent (options §2; no blank-node chains) | 548 |
| Round-3 rendering of the whole graph, for comparison (one hop, `bn via` only) | 2,149 |

The whole-graph output stays the same size (2,154 against 2,149): the blank-node classes moved
into the blocks that reach them, so each is written once either way. The Continent block grows from
351 to 772 characters because it now carries the two blank-node chains. The ShEx and Markdown
snippets leave those chains out; they would need their own `euvoc:XlNotation` and `skosxl:Label`
shapes or cards to say the same.

### d) Grammar sketch (EBNF-like)

```ebnf
output    ::= prefix* legend block* glossary
prefix    ::= "PREFIX " PNAME_NS " <" IRI ">" NL
legend    ::= "# " TEXT NL
block     ::= header NL edge*
header    ::= "(:" group ") " INT [" ~" INT " " MODE] [" co " pair (", " pair)*] [" via " link (", " link)*]
link      ::= "(:" group ")-" name [" " INT]                 (* INT only in the one-class view *)
edge      ::= INDENT "-" name "-> " target stat* [" ^"] NL edge*   (* INDENT = 2 × depth, depth 1..3 *)
target    ::= "(:" group ("|" group)* ")" | name ("|" name)* | "IRI"
group     ::= name ("&" name)*                               (* & binds tighter than | *)
pair      ::= name " " INT
stat      ::= " " ( INT "/" INT | "×" INT ["-" INT] | "bn" | "@" INT | "=" VALUE | VALUE ".." VALUE | "d" INT )
glossary  ::= "# glossary" (": " TEXT NL | NL (name " " STRING ["@" LANG] [": " TEXT] NL)*)
name      ::= PNAME | "<" IRI ">"
VALUE     ::= a lexical form without spaces or ".." | a JSON-quoted string otherwise
```

`validate_query` reads `header` and `edge`. For a triple pattern `?x p ?y` with `?x` typed `C`,
block `C` (or the merged group containing it) must have an edge `p` at depth 1. A pattern on an
untyped `?y` reached through a blank-node edge is checked against the nested edges, so the
property path `?c skosxl:prefLabel/skosxl:literalForm ?n` is valid and
`?c skosxl:prefLabel/rdf:value ?n` is not. The prototype does not yet quote `VALUE`s; the grammar
requires it.


## Secondary form: enriched ShEx-compact (after round 5)

In round 5 the developer said "yes, pattern mainly, with compact and enriched shex as a secondary
form" (`qa-round-1.md`, Round 5 answers; proposal DEC-18 as amended). The enriched ShExC renders
from the same profile and the same glossary as the pattern schema. It says the same things where
ShExC can say them:

| Pattern schema | Enriched ShExC |
|---|---|
| Edge target class or datatype | value expression: `@shape`, a datatype, `IRI` |
| `×n`, `×a-b`, `k/n` coverage | ShEx cardinality: `{n}`, `{a,b}`, `?` or `*` when some instances lack the property |
| `bn` and blank-node chains (DEC-15) | `BNODE { … }` nested inline shapes, up to 3 hops. A blank-node class reached from several edges becomes one named shape, referenced as `BNODE @C` (the pattern's `^`). |
| Statistics: `=v`, `lo..hi`, `dN`, `@n`, counts, co-types, `via` | `#` comments with the pattern legend's tokens, so they cost no syntax |
| Glossary (labels; one description, DEC-17) | `# label: …` comment lines above each shape. There are none on the sample profile. |
| Prefixes (DEC-16) | one `PREFIX` block |
| Merged co-typed classes `(:A&B)` | the shape is labelled with the first class and the comment names the other; targets refer to that shape |

### Example: euvoc:Continent

From `tests/test_data/profiles/sample-profile.json`, graph `…/continents`. Every number is the
profile's.

```shex
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX euvoc: <http://publications.europa.eu/ontology/euvoc#>
PREFIX lvont: <http://lexvo.org/ontology#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX skosxl: <http://www.w3.org/2008/05/skos-xl#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
# comments use the pattern legend: k/n having p · bn · @n languages · =v one value · lo..hi · dN distinct
# euvoc:Continent 6, also skos:Concept 6 (same instances); via none
euvoc:Continent {
  dcterms:created xsd:date ;          # =2014-10-10
  euvoc:startDate xsd:date ;          # =1952-07-24
  euvoc:status IRI ;                  # d1
  euvoc:xlNotation BNODE {            # euvoc:XlNotation
    dcterms:created xsd:date ;        # =2014-10-10
    dcterms:type IRI ;                # d1
    euvoc:startDate xsd:date ;        # =1952-07-24
    euvoc:status IRI ;                # d1
    rdf:value xsd:string              # AFRICA..OCEANIA
  } ;
  skos:inScheme @skos:ConceptScheme ;     # also owl:Ontology; d1
  skos:topConceptOf @skos:ConceptScheme ; # also owl:Ontology; d1
  skosxl:prefLabel BNODE {            # skosxl:Label, stats over all 145
    dcterms:created xsd:date ;        # =2014-10-10
    dcterms:type IRI ;                # d1
    euvoc:startDate xsd:date ;        # 1952-07-24..2014-10-10 d2
    euvoc:status IRI ;                # d1
    lvont:script IRI ? ;              # 12/145 d2
    skosxl:literalForm rdf:langString # @24
  } {24}
}
```

**Parse check.** The snippet parses with PyShExC 0.10.3.post1 (`pyshexc.parser_impl.generate_shexj.parse`
returns a `Schema`). When one closing brace is removed, the same call reports
`line 32:0 missing '}' at '<EOF>'` and returns `None`. PyShExC is already in `poetry.lock` (a
dependency of `linkml`, in the dev group). On PyPI, PyShExC 0.10.3.post1 (2026-05-01) requires
Python ≥3.10 and lists 3.11–3.14. Its dependencies (`antlr4-python3-runtime~=4.9.3`, `pyjsg`,
`shexjsg`, `rdflib-shim`) are already locked too.

**Size (Unicode code points, `wc -m`).**

| Rendering of `euvoc:Continent` | Characters |
|---|---|
| Enriched ShExC above, everything included | 1,521 |
| — without the prefix block and the legend comment | 1,056 |
| Pattern schema Continent block, with the same chains (§c above) | 772 |
| Plain ShExC snippet, without chains or statistics (options §1) | 350 |

The enriched ShExC costs about 37% more than the pattern block (1,056 against 772) for the same
facts. That fits its role as the secondary form.
