# Schema representation options for an LLM tool — 2026-11-01 (seed input, not groomed)

The question asked: "if we were to decide what would be a graph schema representation suitable for
an LLM tool, what options do we have? Give a few short descriptions and an example snippet for
each." This note lists nine options. Every evidence claim comes from
[`llm-schema-research.md`](llm-schema-research.md); where that file has no evidence for an option,
the option says so.

## The class every example shows

Every snippet shows the same class, so the options can be compared side by side. The facts are
taken from the canonical sample profile `tests/test_data/profiles/sample-profile.json`, graph
`http://publications.europa.eu/resources/authority/continents`; `tests/sample_data.py` names the
same class as `CONTINENTS`.

- `euvoc:Continent`: **6 instances**, read exactly (`precision_mode: exact`). All 6 instances are
  also typed `skos:Concept`.
- The class has seven properties. Each instance has exactly 1 value for six of them and exactly 24
  values for `skosxl:prefLabel`.

| Property | Values per instance | Value | Distinct objects |
|---|---|---|---|
| `euvoc:startDate` | 1 | literal, `xsd:date` (all `1952-07-24`) | 1 |
| `euvoc:status` | 1 | IRI, no type | 1 |
| `euvoc:xlNotation` | 1 | blank node, `euvoc:XlNotation` | 6 |
| `dcterms:created` | 1 | literal, `xsd:date` (all `2014-10-10`) | 1 |
| `skos:inScheme` | 1 | IRI, typed both `skos:ConceptScheme` and `owl:Ontology` | 1 |
| `skos:topConceptOf` | 1 | IRI, typed both `skos:ConceptScheme` and `owl:Ontology` | 1 |
| `skosxl:prefLabel` | 24 | blank node, `skosxl:Label` | 144 |

**Labels.** The sample data has no `rdfs:label` or `rdfs:comment` on `euvoc:Continent` or on its
properties. Its only `rdfs:comment` is on the `owl:Ontology` instance (the value is `"Continent"`).
Where a format has a label slot, the snippet leaves it empty. A real label would have to come from
an `--ontology` file or a test fixture.

**Prefixes.** All snippets use the prefixes from the profile and the shipped SHACL output:
`euvoc:`, `skos:`, `skosxl:`, `dcterms:`, `owl:` and `xsd:`. Except where shown, snippets leave out
the prefix block.

## 1. ShEx compact (ShExC)

One shape per class, listing the predicates the class's instances use, with their target class or
datatype and a cardinality (no marker means exactly one). SPARQL-LLM and Emonet et al. derive these
shapes from VoID partitions. They chose ShEx over OWL because its syntax is closer to SPARQL, and
SPARQL-LLM placed first at TEXT2SPARQL 2026 (research seed, *SPARQL / RDF*). The token cost is low.
ShEx is a W3C Community Group standard and parseable, so a validator can read it back. A shape
carries cardinality but no counts or labels unless they are added as comments.

```shex
# 6 instances (exact); also skos:Concept (6)
euvoc:Continent {
  euvoc:startDate   xsd:date ;
  euvoc:status      IRI ;
  euvoc:xlNotation  @euvoc:XlNotation ;
  dcterms:created   xsd:date ;
  skos:inScheme     @skos:ConceptScheme OR @owl:Ontology ;
  skos:topConceptOf @skos:ConceptScheme OR @owl:Ontology ;
  skosxl:prefLabel  @skosxl:Label {24}
}
```

## 2. Markdown class card

One heading and one table per class, with prefixed names, counts, values per instance, value types
and labels. No study in the research seed tests this format directly. The support is indirect:
Fitch & Kurtz found that readable names and labels mattered more than model choice, and Rasheed &
Aguado found that a plain list did as well as Turtle at a fraction of the tokens. The token cost is
low to medium. It is the easiest format to read and to fit to the profile, including counts, sample
values and labels. It follows no standard and is not machine-parseable for validation, so a
validator would read the profile instead.

```markdown
### euvoc:Continent: 6 instances (exact)
Also typed: skos:Concept (6). Label: none.

| Property | Per instance | Value | Distinct |
|---|---|---|---|
| euvoc:startDate | 1 | xsd:date, e.g. 1952-07-24 | 1 |
| euvoc:status | 1 | IRI | 1 |
| euvoc:xlNotation | 1 | → euvoc:XlNotation (blank node) | 6 |
| dcterms:created | 1 | xsd:date, e.g. 2014-10-10 | 1 |
| skos:inScheme | 1 | → skos:ConceptScheme, owl:Ontology | 1 |
| skos:topConceptOf | 1 | → skos:ConceptScheme, owl:Ontology | 1 |
| skosxl:prefLabel | 24 | → skosxl:Label (blank node) | 144 |
```

## 3. SHACL Turtle (already ships)

This is the existing `fingerprint-gen-shacl` output: one node shape per class and one property shape
per property, with `sh:minCount`/`sh:maxCount`, `sh:class` or `sh:datatype`, `sh:nodeKind`, and
`fp:` annotations for counts and confidence. The research seed lists SHACL shapes among the static
baselines and groups them with ShEx as "shape-style" descriptions. It is a W3C Recommendation and
parseable. The token cost is the highest of the nine: the shapes for `euvoc:Continent` alone take
2,274 characters in `tests/test_data/golden/shapes-continents-214e8f67.ttl`. The snippet below is an
excerpt from that file (the node shape and one of its seven property shapes).

```turtle
euvoc-shape:Continent a sh:NodeShape ;
    sh:targetClass euvoc:Continent ;
    fp:instances 6 ;
    fp:observedInstances 6 ;
    fp:precisionMode "exact" ;
    sh:property euvoc-shape:Continent-skosxl-prefLabel ;   # … and six more
.
euvoc-shape:Continent-skosxl-prefLabel a sh:PropertyShape ;
    sh:path skosxl:prefLabel ;
    sh:minCount 24 ;
    sh:maxCount 24 ;
    sh:class skosxl:Label ;
    sh:nodeKind sh:BlankNode ;
    fp:confidence 1.0 ;
    fp:labelSupport 1.0 ;
.
```

## 4. VoID class and property partitions

The W3C VoID vocabulary states, per class, the number of entities and, per property, the number of
triples and distinct objects. SPARQL-LLM consumes VoID; `void-generator` (Java) produces it
(research seed, *Relevance* and prior art). The profile model is already VoID-aligned:
`GraphProfile` is `void:Dataset` and `class_partitions` is `void:classPartition`. The token cost is
medium. It is a standard, parseable, and carries counts. It has no per-instance cardinality and no
labels. Target classes need the SIB extension terms used by void-generator, which this note has not
checked, so the snippet leaves them out. VoID suits a pipeline that builds its own prompt from it
better than a prompt read directly by an LLM.

```turtle
<#continents> a void:Dataset ;
  void:classPartition <#continents-Continent> .
<#continents-Continent>
  void:class euvoc:Continent ;
  void:entities 6 ;
  void:propertyPartition
    [ void:property skosxl:prefLabel ;  void:triples 144 ; void:distinctObjects 144 ] ,
    [ void:property euvoc:xlNotation ;  void:triples 6 ;   void:distinctObjects 6 ] ,
    [ void:property skos:inScheme ;     void:triples 6 ;   void:distinctObjects 1 ] .
    # … four more, each with 6 triples
```

## 5. Profile JSON (or its JSON Schema)

This is the saved `profile.json` (the `ProfileRun` model), either whole or cut down to one class.
The model's JSON Schema, `fingerprint/domain/profile_run.schema.json`, describes its structure. The
research seed has no study of JSON as a schema format. Neo4j's "enhanced schema" (property value
samples and ranges) is the nearest evidence, but it concerns *what* is included, not the format.
The token cost is high: full IRIs and nesting. It is exact, complete, and parseable by any client.
The model reads it as data, not as triple patterns.

```json
{"class_iri": "http://publications.europa.eu/ontology/euvoc#Continent",
 "instances": 6, "precision_mode": "exact",
 "property_partitions": [
  {"property": "http://www.w3.org/2008/05/skos-xl#prefLabel", "distinct_objects": 144,
   "cardinality_histogram": [{"values_per_subject": 24, "subjects": 6}],
   "value_partitions": [{"triples": 144, "distinct_objects": 144,
     "object_class": "http://www.w3.org/2008/05/skos-xl#Label", "node_kind": "blank_node"}]}]}
```

## 6. Plain vocabulary list

A bare list of classes and the properties each one uses, with no types or counts. This is the
Rasheed & Aguado baseline: on 20 RINF questions, Gemini scored 85% with the list, the same as short
Turtle and better than detailed Turtle (75%) (research seed, *SPARQL / RDF*). The token cost is the
lowest of the nine. It reads easily but carries no target types or cardinality and has no standard
syntax, so it gives a validator only names to check.

```text
euvoc:Continent (6): euvoc:startDate, euvoc:status, euvoc:xlNotation, dcterms:created,
  skos:inScheme, skos:topConceptOf, skosxl:prefLabel
```

## 7. Reduced OWL/RDFS Turtle

The class and its properties as `owl:Class` and `owl:ObjectProperty`/`owl:DatatypeProperty`, with
`rdfs:domain`/`rdfs:range` taken from the profile. In Fitch & Kurtz, OWL beat SQL DDL as schema
context; for Rasheed & Aguado, short Turtle matched the plain list and detailed Turtle scored lower
(research seed). The token cost is medium to high. It is a standard and parseable. Counts and
cardinality need OWL restrictions, which add many tokens, so the snippet leaves them out.
`rdfs:domain` also says more than the data shows: other classes use the same properties too.

```turtle
euvoc:Continent a owl:Class .
skosxl:prefLabel  a owl:ObjectProperty ;   rdfs:domain euvoc:Continent ; rdfs:range skosxl:Label .
euvoc:xlNotation  a owl:ObjectProperty ;   rdfs:domain euvoc:Continent ; rdfs:range euvoc:XlNotation .
skos:inScheme     a owl:ObjectProperty ;   rdfs:domain euvoc:Continent ; rdfs:range skos:ConceptScheme .
euvoc:startDate   a owl:DatatypeProperty ; rdfs:domain euvoc:Continent ; rdfs:range xsd:date .
# … dcterms:created, skos:topConceptOf, euvoc:status
```

## 8. Cypher-style path patterns

One `(:Class)-[:predicate]->(:Class)` line per link, plus a property list for literal values. This is
the static schema format of the Text2Cypher studies (Ozsoy 2025; the Neo4j blog). The research seed
lists it for property graphs, not for SPARQL. The token cost is low. It is close to the
triple-pattern shape of a query, and models have seen a great deal of Cypher. It has no RDF
standard, carries no counts unless they are added, and would need a parser of our own for
validation.

```text
(:euvoc:Continent {euvoc:startDate: xsd:date, dcterms:created: xsd:date, euvoc:status: IRI})
(:euvoc:Continent)-[:skosxl:prefLabel]->(:skosxl:Label)          // 24 per instance
(:euvoc:Continent)-[:euvoc:xlNotation]->(:euvoc:XlNotation)
(:euvoc:Continent)-[:skos:inScheme]->(:skos:ConceptScheme|owl:Ontology)
(:euvoc:Continent)-[:skos:topConceptOf]->(:skos:ConceptScheme|owl:Ontology)
```

## 9. Typed signature (TypeScript- or Pydantic-like)

The class written as a record type: one field per property, with its value type and arity. **The
research seed has no evidence for this format**; it is listed only because code-style declarations
are familiar to models. The token cost is low. Cardinality reads well (`T`, `T | None`,
`list[T]`), and labels can go in docstrings. A predicate IRI must be shortened to a field name,
which loses the exact name the query needs unless it is kept in a comment. It has no RDF standard.

```python
class Continent:  # euvoc:Continent, 6 instances
    startDate: date                       # euvoc:startDate
    status: IRI                           # euvoc:status
    xlNotation: XlNotation                # euvoc:xlNotation
    created: date                         # dcterms:created
    inScheme: ConceptScheme | Ontology    # skos:inScheme
    topConceptOf: ConceptScheme | Ontology  # skos:topConceptOf
    prefLabel: list[Label]                # skosxl:prefLabel, exactly 24
```

## Comparison

"Tokens" is relative to the other options here; nobody has measured it yet (see the evaluation
question in the Q&A record). "Parseable" means a standard parser exists that a validator could read
the format back with. "Labels" means the format has a place for `rdfs:label`/`rdfs:comment`.

| Option | Tokens | Reads like SPARQL | Standard | Parseable for validation | Cardinality / counts | Labels |
|---|---|---|---|---|---|---|
| 1 ShEx compact | low | yes | W3C CG | yes | cardinality; counts only as comments | comments only |
| 2 Markdown card | low–medium | partly | no | no (validate from the profile) | both | yes |
| 3 SHACL Turtle | highest | no | W3C Rec | yes | both (`fp:` annotations) | yes (`sh:name`, `rdfs:comment`) |
| 4 VoID | medium | no | W3C IG Note | yes | counts only | no |
| 5 Profile JSON | high | no | own schema | yes (JSON Schema) | both | only if the model adds them |
| 6 Vocabulary list | lowest | no | no | names only | counts optional | optional |
| 7 Reduced OWL/RDFS | medium–high | partly | W3C Rec | yes | only through restrictions | yes |
| 8 Cypher patterns | low | yes (as patterns) | no (for RDF) | no | as comments | no |
| 9 Typed signature | low | no | no | no | cardinality | docstrings |

Every option is a function of the saved profile. None needs an endpoint query, so DEC-2 holds for
each.
