# Brainframe: modelling analysis of the fingerprint

**Sources:**
- the fingerprint report `../main.html` (rdf-fingerprinter 3.0.0; 52 class sections, 1,601 property rows);
- the ROBOT run (`robot-report.md`);
- ten OOPS!-style SPARQL checks (`oops-queries/`, results in `oops-results/`), run on the raw RDF in
  Oxigraph;
- a few direct queries to confirm patterns.

**Data:** the ontology (5,335 triples) and one workspace export (74,007 triples), dated 2026-10-29.

**Scope:** this analysis reads structure, not meaning. Where a finding depends on what brainframe's
application intends, it says so.

## Summary

The schema is consistent and every property has a domain and a range. The modelling problems are
elsewhere:
- in **how relations and versions are represented**: as predicates minted per instance;
- in **typing**: 68% of the subjects are untyped, and 6 classes are used but never declared;
- in **schema and data drift**: the data uses 108 brainframe predicates that the ontology doesn't
  declare, and the ontology declares 262 classes but the data instantiates 45;
- in **application concerns stored as knowledge**: presentation flags, HTML, placeholders, IDs.

| # | Pitfall | Severity | Evidence |
|---|---|---|---|
| 1 | Relation instances minted as predicates (singleton properties) | critical | 619 `relationid:` predicates in the report; 1,765 `RelationId` nodes; OWL cannot read them |
| 2 | Versions of an instance used as predicates | critical | 249 `procedure:<uuid>-<timestamp>`, 75 `policy:…`, 10 `youtube:…` predicates |
| 3 | Data uses schema terms the ontology doesn't declare | critical | 108 brainframe predicates, 37,135 triples, undeclared; 6 classes used, undeclared |
| 4 | Most subjects untyped; typing is inconsistent within one kind | important | 8,785 of 12,926 subjects untyped; `SOARequirement/…`: 552 typed, 1,374 not |
| 5 | Superclasses act as tags; nothing is inherited | important | 45 of 51 classes have parents; 0 of 1,589 property rows are inherited or refined |
| 6 | One IRI used as a class and as a property | important | `brainframe:factActivity`: 500 instances, and a predicate in 8,138 triples |
| 7 | Multiple domains or ranges (an intersection, probably meant as a union) | critical (OOPS! P19) | `isParentOf` (domain and range), `isFactOf` (range), `isContextOf` (domain) |
| 8 | Built-in vocabulary redefined | critical | `brainframe:singletonPropertyOf rdfs:subPropertyOf rdf:type` |
| 9 | Placeholder, HTML and duplicate labels | important | 8,849 missing, 3,322 duplicate, "…" on every `RelationId`; HTML tables as labels |
| 10 | Application and UI state in the knowledge graph | important | `factFontSize` (15 classes), `isMarkdownFormat`, `onlyOfficeCache`, `requestUpload`, `KanbanType`, `WorkspaceVariable` |
| 11 | Instance IRIs are client-side routes | important | `https://my.brainframe.com/#/knowledge/<Class>/<uuid>[-<timestamp>]` |
| 12 | Naming conventions mixed | minor (OOPS! P22) | 15 classes start lower-case (`factActivity`, `checkList`, `pa_dataRetentionPolicy`, `brainframeAccount`, …); typo `originNamesapce` (100 triples) |
| 13 | Very sparse, long-tail profile | minor | 17 of 51 classes have at most 2 instances; 711 property rows are used by under 5% of a class's instances; 77% of properties are 0..1 |
| 14 | Metadata missing; overlapping vocabularies | minor | no ontology title, licence or description; instances carry `rdfs:label` (45 classes) and `dcterms:title` (42 classes) side by side; `prv:` (2009 provenance vocabulary) next to `dcterms:` |

## Findings

### 1. Relation instances minted as predicates

The report shows `brainframe:Policy` with 296 property rows, 175 of them from the `relationid:`
namespace; `checkList` has 117 and `ServiceFunctionOrProcess` 69. Each of those predicates is one
relation instance:

```turtle
<…/RelationId/06aed3bf…>  a brainframe:RelationId ;
    rdf:singletonPropertyOf brainframe:isRelatedTo ;
    rdfs:label "..." ;
    prv:createdBy <…/Person/7a08…> ;
    brainframe:isFactOf <…/ContextId/3457…> .
<…/Action/…>  <…/RelationId/06aed3bf…>  <…/RiskScenario/…> .
```

This is the RDF singleton-property pattern, used to attach metadata (creator, context) to an edge.
It has four costs:
- **The schema grows with the data.** There are 619 predicates for a single relation type,
  `isRelatedTo`. Every new link adds a predicate. This is why the `Procedure` and `Policy` boxes
  are unreadable in the diagrams, and why the profile has 1,212 predicate partitions.
- **OWL cannot read it.** ROBOT drops the 1,765 `rdf:singletonPropertyOf` triples. A reasoner never
  sees that these edges are `isRelatedTo`.
- **Simple queries fail.** "What is related to X?" needs a join through `rdf:singletonPropertyOf`;
  `?s brainframe:isRelatedTo ?o` finds nothing.
- **Punning.** The same IRI is an individual (`a brainframe:RelationId`) and a predicate.
  `extra_individual_as_predicate` finds 518 such IRIs.

**Better:**
- Write the plain edge `?s brainframe:isRelatedTo ?o`.
- Put the edge metadata on a qualified-relation node, `brainframe:Relation`, with `source`,
  `target`, `createdBy` and `context`, or use RDF 1.2 / RDF-star triple terms
  (`<< ?s :isRelatedTo ?o >> prv:createdBy …`).
- Keep the plain edge either way, so that the simple query and OWL reasoning work.

### 2. Versions used as predicates

There are 249 predicates in the `procedure:` namespace, 75 in `policy:` and 10 in `youtube:`. Each
is the IRI of one version of a document:

```turtle
<…/Procedure/3f1d…-20261026085236>  <…/Procedure/3f1d…-20250226094300>  <…/factDistribution/97a5…> .
```

A newer version of a procedure points to a `factDistribution` node, and the predicate is an older
version of the same procedure. Each is used by 2–5 subjects. A version is an individual, not a
relation, so this is a category error. It also inflates the schema the same way finding 1 does.

**Better:** a version-of relation, with the distribution as a property of the version:
- `<v2> brainframe:previousVersion <v1>`, or `prov:wasRevisionOf` / `dcterms:isVersionOf`;
- `<v1> brainframe:hasDistribution <factDistribution/…>`.

The existing `brainframe:versions` and `brainframe:currentVersion` (used by 34 and 33 classes)
suggest the application already models versions properly in some places.

### 3. Schema and data drift

`oops_p35_untyped_property` on the merged graph finds 1,100 predicates that are not declared as any
kind of property. Finding 1 accounts for 634 of them and finding 2 for 334. The other **108 are in
the brainframe namespace**, used in 37,135 triples:

| Predicate | Triples |
|---|---|
| `factActivity` | 8,138 |
| `SOARequirementLinkControlId` / `…Type` / `…TypeId` | 6,148 each |
| `SOAId` | 1,068 |
| `languages`, `isMarkdownFormat` | about 690 each |
| `RiskValue`, `RiskTitle`, `RiskOrder` | 669 each |

`oops_p34_untyped_class` finds classes used in `rdf:type` but not declared: `SOARequirement`, `SOA`,
`DocumentForm`, `DocumentPropertyForm`, `GroupRole` and `brainframeAccount`.

In the other direction, the ontology declares 262 classes and the data instantiates only 45 of them
(17%).

Read together, the ontology describes an older or different slice of the model than the one the
application writes. The upper-case `RiskValue`, `RiskTitle` and `SOAId` read like database column
names.

**Better:** generate the ontology from the application's model, or check exports against it in CI.
The SHACL shapes the fingerprinter just generated are a ready baseline for that check.

### 4. Untyped subjects and inconsistent typing

The fingerprint's caveats report 8,785 of 12,926 workspace subjects with no `rdf:type`:
- `SOARequirementLinkControl` 6,148;
- `SOARequirement` 1,374;
- `QuestionRisk` 669;
- `DocumentPropertyFormQuestion` 180;
- `brainfactTagsReplyTypeValues` 96;
- `Ratings` 90.

Their class is written into the IRI (`…/knowledge/QuestionRisk/<uuid>`), but not into the data.
`SOARequirement` IRIs are typed 552 times and untyped 1,374 times, so the same kind of thing is typed
in some places and not in others. Untyped resources are invisible to class-based queries, to SHACL
targets and to the fingerprinter's own class profiles, which cover only 4,141 of the 12,926 subjects.

**Better:** type every resource the application creates. Don't rely on the IRI path to carry the type.

### 5. Superclasses that act as tags

45 of the 51 classes declare parents: `BrainFactId` (12), `Digital` (10), `GraphResource` (10),
`Operations` (9), `DataRecord` (6) and `Security` (5). Many classes have two or three of them, for
example `AuditReport` ⊑ `BrainFactId`, `DataRecord` and `Operations`.

Yet **every one of the 1,589 property rows is `own`**: no class shares a property with a parent, in
the profile's sense. So the hierarchy carries no structure. It mixes three kinds of grouping:
- system roles: `GraphResource`, `BrainFactId`, `DataRecord`;
- business areas: `Operations`, `Security`;
- technology kinds: `Digital`.

That is faceted tagging expressed as `rdfs:subClassOf`. It is not wrong in OWL, but every facet
multiplies inferred types, and it hides the real taxonomy.

**Better:**
- Keep `rdfs:subClassOf` for genuine is-a relations (`Database` ⊑ `Software`, if that is meant).
- Express facets as SKOS concepts or annotation values, for example `brainframe:area :Operations`.

### 6. One IRI as a class and as a property

`brainframe:factActivity` is a class with 500 instances, and it is also the most-used undeclared
predicate (8,138 triples). This is OWL 2 punning. It is legal, but confusing, and the fingerprint
lists it both as a class section and as a property. The lower-case class name suggests the class use
is the accident.

**Better:** split it into `brainframe:FactActivity` (the class) and `brainframe:hasFactActivity`
(the property).

### 7. Multiple domains or ranges

`oops_p19` finds the following:
- `brainframe:isParentOf` has two domains and two ranges;
- `isFactOf` has two ranges;
- `isContextOf` has two domains.

In OWL, two `rdfs:domain` statements mean the subject is an instance of **both** classes, an
intersection. Two ranges mean the same for the object. These are almost certainly meant as "either",
a union. With the current axioms, a reasoner will type every subject of `isParentOf` as both
classes.

**Better:** one domain or range that is a union (`owl:unionOf`), or a common superclass.

### 8. Built-in vocabulary redefined

`brainframe:singletonPropertyOf rdfs:subPropertyOf rdf:type` gives a standard term new meaning. It is
ROBOT's only `illegal_use_of_built_in_vocabulary` finding, and one of the three reasons the ontology
is not OWL 2 DL. It probably exists to make finding 1 "type" its edges, and it goes away with that
fix.

### 9. Labels

- **Missing:** 8,849 instances, mainly the untyped kinds from finding 4.
- **Placeholders:** every `RelationId` is labelled "...", 1,073 resources are "…"@en and 537 are "…".
- **Content as labels:** one HTML project-charter template appears as the label of 39 resources.
  System messages ("Added link to: …") are labels too. ROBOT counts 133 `label_formatting` errors.
- **Schema:** 301 terms have no label, and 4 labels are duplicated. `PrivacyStandard` and
  `QualityStandard` are both "Privacy standard", which reads like a copy-paste error.
  `label_translated` holds JSON strings (`{"en": …}`) instead of language-tagged literals, although
  the page shows the data does use `rdf:langString` in 38 rows.

**Better:**
- Labels should name things. Use body properties (`dcterms:description`, `brainframe:content`) for
  text and HTML.
- Leave a label out rather than write "…".
- Use `"…"@en` / `"…"@nl` instead of JSON.

### 10. Application state in the knowledge graph

The data and schema include UI and storage concerns:
- `factFontSize` (on 15 classes), `isMarkdownFormat`, `onlyOfficeCache`, `requestUpload`;
- `KanbanType`, `WorkspaceVariable`, `IntegrationCredential`;
- identifier classes: `BrainframeId`, `ContextId` and `GraphResource` (the blueprint `…_Bin` terms).

They make the domain model hard to see; `IntegrationCredential` in an exported graph also deserves a
security look. `oops_p22` also flags `onlyOfficeCache` and `requestUpload` as classes with lower-case
names, which suggests they are settings rather than concepts.

**Better:** separate the domain ontology from an application or configuration vocabulary, in a
different namespace or graph, and leave the latter out of knowledge exports.

### 11. IRIs that are client-side routes

Instance IRIs look like `https://my.brainframe.com/#/knowledge/Procedure/3f1d…-20261026085236`. This
causes three problems:
- **Not dereferenceable one by one.** Everything after `#` stays in the browser, so every instance
  is the same HTTP resource, `https://my.brainframe.com/`, and the IRIs can't be looked up
  individually.
- **The IRI changes when anything about the instance changes.** It carries the class and, for
  versions, a timestamp, so it changes when the type or the version does.
- **Tooling has to guess.** The fingerprinter had to split namespaces at the route (`…/Procedure/`),
  giving the prefixes `procedure`, `policy`, `relationid`, `youtube` and so on.

**Better:** stable, opaque, dereferenceable IRIs (`https://data.brainframe.com/id/<uuid>`), with the
type in `rdf:type` and the version in data.

### 12–14. Smaller things

- **Naming.** Class names start with a capital, except 15 (`factActivity`, `checkList`,
  `documentTemplate`, `brainframeAccount`, `pa_dataRetentionPolicy`, the `pa_*` family, …). There is
  a typo in `originNamesapce`, used 100 times.
- **Sparsity.** 17 classes have at most 2 instances. 711 of 1,589 property rows are used by under 5%
  of their class's instances, and 77% of properties are `zero_or_one`. That fits a forms-driven
  application, but it means the generated shapes are mostly `sh:Info` or `sh:Warning`, and the
  classes are thin.
- **Metadata.** The ontology has no title, licence or description, and the version IRI is `…/2.0.0`
  while the namespace is `…/2016/04/brainframe`.
- **Overlapping vocabularies.** Instances of 45 classes carry `rdfs:label` and of 42 carry
  `dcterms:title`, two naming properties side by side. `prv:`
  (2009) is used for `createdBy` and `changedBy`, where PROV-O (`prov:wasAttributedTo`) is the
  standard.

## What the checks did not find

These came back clean:
- **Consistency:** the ontology alone, and with the data, is consistent under HermiT and ELK, with
  no unsatisfiable classes.
- **OOPS! P11:** every object and datatype property has a domain and a range.
- **OOPS! P04:** no completely unconnected classes.
- **OOPS! P38:** there is an `owl:Ontology` declaration.

## Priorities

1. Replace singleton properties and version predicates with plain edges plus qualified nodes or
   triple terms (findings 1, 2, 8). This removes 953 predicates, most of the OWL 2 DL violations and
   most of the diagram noise.
2. Declare every term the application writes, type every resource, and check exports against the
   ontology or the generated SHACL shapes in CI (findings 3, 4).
3. Fix the multiple domains and ranges and the `factActivity` pun (findings 6, 7).
4. Move UI and application state out of the domain model, and clean the labels (findings 9, 10).
5. Add ontology metadata and align the naming (findings 12–14).

## OOPS! pitfalls as SPARQL: the inventory

OOPS! (`../../../../OOPS`, cloned at commit `11572ea`, 2025-07-01) has no SPARQL to borrow: each of its
33 pitfalls is Java code over a Jena `OntModel` (`src/main/java/es/upm/fi/oeg/oops/checkers/`).
Nobody has published the catalogue as SPARQL either. The closest SPARQL collection is RDFUnit's
data-quality test patterns; RDFUnit is unmaintained (last push over two years ago).

From the Java checkers' logic I wrote **27 OOPS! pitfalls and four extra checks** as SPARQL, in
`oops-queries/`. They ran on the raw RDF in Oxigraph; results are in `oops-results/`, and every
query finished in under 2 s.

| Query | OOPS! (importance) | Ontology | Ont. + data | Notes |
|---|---|---|---|---|
| `oops_p04_unconnected_class` | P04 (minor) | 0 | 0 | |
| `oops_p05_wrong_inverse` | P05 (critical) | 1 | 1 | the domain of one does not match the range of its inverse |
| `oops_p06_class_cycle` | P06 (critical) | 0 | 0 | |
| `oops_p07_merged_concepts` | P07 (minor, name heuristic) | 22 | 22 | `…AndDeployment…`, `…OrPreventive…`; many are deliberate |
| `oops_p08_missing_label_or_comment` | P08 (minor) | 282 | 282 | no `rdfs:comment` |
| `oops_p10_no_disjointness` | P10 (important) | 1 | 1 | no disjointness axiom anywhere |
| `oops_p11_missing_domain_or_range` | P11 (important) | 0 | 0 | |
| `oops_p12_p30_same_name_not_equivalent` | P12/P30 (approximation) | 2 | 2 | same local name in two namespaces, not equivalent |
| `oops_p13_missing_inverse` | P13 (suggestion) | 148 | 148 | object properties without an inverse; a suggestion only |
| `oops_p19_multiple_domains_or_ranges` | P19 (critical) | 4 | 4 | `isParentOf`, `isFactOf`, `isContextOf` |
| `oops_p20_label_longer_than_comment` | P20 (minor, heuristic) | 2 | 2 | |
| `oops_p21_miscellaneous_class` | P21 (minor, name heuristic) | 0 | 0 | |
| `oops_p22_class_naming` | P22 (minor) | 15 | 15 | lower-case class names |
| `oops_p24_recursive_definition` | P24 (important; direct cases) | 0 | 0 | |
| `oops_p25_inverse_of_itself` | P25 (important) | 0 | 0 | |
| `oops_p26_inverse_of_symmetric` | P26 (important) | 0 | 0 | |
| `oops_p27_wrong_equivalent_properties` | P27 (critical) | 4 | 4 | equivalent properties with different domains or ranges |
| `oops_p28_p29_wrong_symmetric_or_transitive` | P28/P29 (critical) | 0 | 0 | |
| `oops_p32_classes_same_label` | P32 (minor) | 2 | 2 | `PrivacyStandard` and `QualityStandard` |
| `oops_p33_single_property_chain` | P33 (minor) | 0 | 0 | |
| `oops_p34_untyped_class` | P34 (minor) | 0 | 6 | classes used but never declared |
| **`oops_p35_untyped_property`** | **P35 (important)** | 2 | **1,100** | **relations used but never defined**; see below |
| `oops_p36_iri_with_file_extension` | P36 (minor) | 0 | 0 | |
| `oops_p38_no_ontology_declaration` | P38 (important) | 0 | 0 | |
| `oops_p41_no_license` | P41 (important) | 1 | 1 | |
| `extra_individual_as_predicate` | — | 0 | 518 | typed individuals used as predicates (singleton properties) |
| `extra_punning_class_and_property` | — | 0 | 1 | `factActivity` |
| `data_domain_violation` | RDFUnit-style | 3 | 28 (p, domain) pairs | e.g. 2,861 subjects of `isFactOf` are not `MeetingNote`: the P19 intersection |
| `data_range_violation` | RDFUnit-style | 1 | 5 pairs | e.g. 52 objects of `isParentOf` are not `MeetingNote` |

### Relations used but never defined

`oops_p35_untyped_property` is the check for relations that are used but never defined. On
ontology plus data it finds **1,100 predicates** declared neither as `owl:ObjectProperty`,
`owl:DatatypeProperty`, `owl:AnnotationProperty` nor `rdf:Property`:
- 634 `relationid:*` singleton properties (finding 1);
- 334 version IRIs used as predicates (finding 2);
- **108 brainframe properties**, in 37,135 triples, such as `factActivity` (8,138) and
  `SOARequirementLinkControl*` (6,148 each), finding 3;
- some `dcterms:` and other external terms.

The data checks add the other half: relations that are defined but used against their definition.

### What SPARQL cannot cover

- **Lexical heuristics:** P02 (synonyms), P31 (wrong equivalent classes) and full P12/P30 need
  WordNet-style synonym checks. P07 and P21 are approximated here from names only.
- **Judgement calls:** P10 (missing disjointness) beyond "none at all", and P13 (inverses) are
  suggestions.
- **HTTP checks of the namespace:** P37 (ontology not available on the Web), P39 (ambiguous
  namespace) and P40 (namespace hijacking) need an HTTP client.

### Two ways to run them

- **Directly on a store**, as here (`curl … --data-urlencode query@file.rq`). This sees the raw RDF,
  including the non-OWL triples.
- **Through ROBOT:** `robot report --profile oops-profile.txt` (`LEVEL<TAB>file:./oops-queries/<name>.rq`;
  each query returns `?entity ?property ?value`). This was checked on the ontology: 4 ERROR and
  298 WARN, in `ontology-oops-report.tsv`. ROBOT reads through the OWL API, so it drops the 1,765
  non-OWL triples and part of the punning. Run P35 and `extra_*` on the store, or use
  `robot report --tdb true`.
