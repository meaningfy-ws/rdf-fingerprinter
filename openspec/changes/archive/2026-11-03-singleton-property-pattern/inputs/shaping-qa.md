---
kind: shaping Q&A record (secondary; superseded by proposal.md, never groomed)
---

# Shaping round 1 (2026-11-03)

## Catalogue: reification patterns and what SPARQL 1.1 can detect

| # | Pattern | Shape | SPARQL 1.1 detection |
|---|---|---|---|
| 1 | Singleton property (Nguyen 2014) | `?s ?sp ?o . ?sp rdf:singletonPropertyOf ?p` | fixed marker, cheap |
| 1b | Resource used as predicate | predicate IRI has own triples/type, no `singletonPropertyOf` | structural (predicate set ⋈ subject set); today flagged by pitfall `x_individual_as_predicate` |
| 2 | RDF reification | `?st a rdf:Statement ; rdf:subject ; rdf:predicate ; rdf:object` | fixed marker; asserted vs unasserted checkable |
| 3 | OWL axiom annotation, negative assertions | `owl:Axiom ; owl:annotatedSource/Property/Target`; `owl:NegativePropertyAssertion` | fixed marker, mostly schema level |
| 4 | RDF-star / RDF 1.2 | `?r rdf:reifies <<( s p o )>>` | presence count only; decomposition needs SPARQL 1.2 |
| 5 | Named graph as statement id, nanopublications | `GRAPH ?g { s p o }` + `?g` described; `np:hasAssertion` | fixed marker (nanopub) or structural (graph IRI as subject) |
| 6 | Qualified relations of known vocabularies | PROV `prov:qualifiedX` (+ `prov:unqualifiedForm`), DCAT `dcat:qualifiedRelation`, `schema:Role`, Wikidata `p:`/`ps:`/`pq:` | per-vocabulary rule |
| 7 | Generic n-ary relation (W3C note) | intermediate node | no signal with IRIs; structural with blank nodes (see below) |

Two families: statement identity (#1–5: one output, subject class → generic predicate → object class +
reifier metadata) and relation-through-a-node (#6–7).

Tension noted: pitfall `x_individual_as_predicate` scores #1/#1b as critical; this EPIC wants them
understood.

## Q1 — Which patterns are in scope?

**Answer (developer):** all of #1–#6, plus "any blank node reification constructs".

Reading of "blank node reification constructs" (to confirm): reifiers that are blank nodes —
`rdf:Statement`, `owl:Axiom`, PROV qualified influences and `schema:Role` written as `[ … ]` — and
generic n-ary relations through a blank node (#7), which become structurally detectable: a blank
node that is the object of exactly one triple and has its own outgoing triples.

## Q2 — Direction (developer, 2026-11-03, verbatim intent)

"how many types of reifications do you know? can you add one proper type, and then if such templates
are found, extend the fingerprinting to capture those. by default filter out reifications from the
default standard fingerprinting, and if any available then those shall be in separate section (under
each class)"

Recorded as DEC-1..DEC-5 in `proposal.md`. Reading of "templates": detection templates (one SPARQL
pattern per reification kind), not report templates — to confirm.

## Q3 — Appetite and readings (developer, 2026-11-03)

- One EPIC, delivered in stages (option a).
- "Templates" are probing templates: queries that ask whether such constructs are present.
- A relation through a blank node is filed under the class of the node that points to the blank node.
- "Proceed to shaping this epic change."

The agent then proposed DEC-6..DEC-11 in `proposal.md` (switch, grouping without IRI strings, reifier
metadata by name and count, packaged templates only, pitfall kept, no SHACL/ShEx constraints).

## Q4 — Decision review (developer, 2026-11-03)

- `reifications` on means: probed for at every run; only if present, move on to detect the reified
  relations and fingerprint them (DEC-6 reworded).
- "shall we eliminate that pitfall template?" — agent recommended yes: its query is the
  resource-as-predicate probe and, as critical, it makes `--fail-on critical` exit 5 on the supported
  pattern. Recorded as DEC-10 (removal).
- SHACL/ShEx could add a note on reified relations (DEC-11 amended: note, never constrain).
- Yes to the other decisions. "go ahead, continue shaping".

## Q5 — Signal for "resource used as predicate" (developer, 2026-11-03)

Options: (A) the predicate has an `rdf:type` other than the property types; (B) A or it carries
triples outside rdf/rdfs/owl/skos/sh; (C) B or a rarely-used statistical signal.
**Answer: A.** No false positives on vocabularies. Consequence: brainframe's 465 predicates typed
only `rdf:Property` (the unmarked `RelationId`, `Procedure`, `Policy`, `mitigationImplementationStatus`
families) stay ordinary properties; only the 517 marked singletons fold into `isRelatedTo`.

## Q6 — Re-shape: singleton properties are not standard (developer, 2026-11-03, during apply)

Developer: "note that those singleton templates are made up, they are not standard constructs, they
are made up. so do not normalise them, just capture the generic antipattern".

Options offered: (1) one generic kind — drop `singleton_property`; any predicate with a non-property
type is `resource_as_predicate`, named by that type, `rdf:singletonPropertyOf` only a reifier
property; (2) the same but never named; (3) the same with a wider signal (reverses Q5).
**Answer: (1).** Recorded as DEC-12 (EPIC re-shape, amends DEC-1 and DEC-7). Consequence for
brainframe: the 517 marked predicates (typed `RelationId` and `rdf:Property`) form relations named
`RelationId`, not `isRelatedTo`.

## Q7 — SKOS-XL and name mappings (developer, 2026-11-03, during apply)

Stage 3 hid `skosxl:Label` by default and named the relations `skos:prefLabel`; the canonical EU
sample's class counts dropped (16 → 13). Developer: "no that folding is wrong skos: is skos: and
skosxl: is skosxl: stay precise no compressions please; we shall fingerprint correctly and if the
class had a skos: and a skosxl: property then we shall show both".
Recorded as DEC-13: drop `skosxl_label`; name every relation by the predicate in the data (PROV,
DCAT, Wikibase included); P-19 superseded.
