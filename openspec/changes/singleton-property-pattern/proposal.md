# EPIC: Detect reifications and fingerprint them as relations of their class

> **Status: shaped (2026-11-03).** Scope, approach and every decision confirmed by the developer in
> four rounds (`inputs/shaping-qa.md`).

**Golden-thread parents:**
- Living spec `openspec/specs/statistics-collection/spec.md` (what the profile collects; queries
  selected by depth and switches).
- Living spec `openspec/specs/profile-representations/spec.md` (how classes and properties appear in
  the outputs).
- Living spec `openspec/specs/fingerprint-report/spec.md` (the report's per-class content).
- Living spec `openspec/specs/pitfall-scans/spec.md`: its packaged `.rq` catalogue is the model for
  the probe catalogue (DEC-3).
- Change `namespace-filter` (3.3.0): `--exclude-namespace` drops such predicates by namespace; this
  EPIC makes them understood instead.

**Seeds** (secondary, never groomed), under `inputs/`:
- `brainframe-evidence.md`: the motivating case, measured.
- `shaping-qa.md`: the catalogue of reification kinds and the developer's answers.

## Appetite

**VERY LARGE**, delivered in stages within this one EPIC (developer, round 2). Stage 1 builds the
whole mechanism (type, probes, filter, per-class section) with the statement-identity kinds; every
later stage only adds probe templates, their sample data and tests. If a later stage needs more than
templates, cut it, do not grow the mechanism.

## Why

Many graphs say something about a statement: who asserted a link, when, with what confidence, in
which role. RDF has no single way to do that, so graphs **reify**: they give the statement, or the
relation, a node of its own. The singleton property pattern (Nguyen et al., WWW 2014) is one way:
each link uses a unique predicate IRI that names its generic property and carries the link's metadata.

```turtle
ex:a      ex:rel/42  ex:b .
ex:rel/42 rdf:singletonPropertyOf ex:isRelatedTo ;
          prov:wasAttributedTo    ex:person/7 .
```

rdf-fingerprinter profiles every reification as ordinary classes and properties. In the brainframe
export (`inputs/brainframe-evidence.md`) that is about 1,000 one-off properties, each profiled on its
own; with `rdf:Statement` it would be a class of nodes with `rdf:subject/predicate/object`, which says
nothing about the relation they stand for. The profile can neither say that the pattern is there nor
what the links mean. The only remedy today, `--exclude-namespace`, drops the links altogether, and
with them the meaning: in that export, the link from a control to the asset it mitigates exists only
as such predicates, and an LLM reading the schema answers "no risk has a control" when the links are
there.

## Solution outline

A fingerprint that **probes for every known reification construct, folds what it finds into the
relations they stand for, and shows those relations per class, apart from the ordinary properties**.

1. **Probe.** A packaged catalogue holds one SPARQL `ASK` template per reification kind. The
   collector asks each one; a kind found in the graph gets its capture query run, a kind not found
   costs one `ASK`.
2. **Capture.** For each kind found, a capture query returns the reified relations: subject class,
   generic predicate, object class, how many statements, and which properties the reifiers carry.
3. **Filter.** The nodes and predicates that implement the reification (singleton predicate IRIs,
   `rdf:subject/predicate/object`, reifier classes such as `rdf:Statement`, the qualifying nodes)
   leave the ordinary classes and properties.
4. **Show.** Each class gets a "reified relations" section, next to its properties, in the profile
   and in every output that lists properties per class.

The kinds come in four families (`inputs/shaping-qa.md` has the full catalogue):

| Family | Kinds | Stage |
|---|---|---|
| A. The statement has its own identity | `rdf:Statement`; `rdf:singletonPropertyOf`; resource used as predicate without the marker; `owl:Axiom` / `owl:Annotation`; `owl:NegativePropertyAssertion`; RDF-star / RDF 1.2 `rdf:reifies` (counted only) | 1 |
| B. A named graph is the statement's id | one triple per graph with the graph described; nanopublications | 2 |
| C. A relation qualified through a node, by vocabulary | PROV-O qualified forms; DCAT qualified relations; `schema:Role`; Wikibase statements; CIDOC-CRM properties of properties; SKOS-XL labels | 3 |
| D. Through a blank node, no vocabulary | n-ary relation through a blank node; structured values through `rdf:value` | 4 |

## Key decisions

DEC-1..DEC-5 are the developer's; DEC-6..DEC-11 were proposed by the agent and confirmed or amended
by the developer in round 4.

- **DEC-1 Scope: every reification kind SPARQL 1.1 can detect** (the four families above). RDF-star /
  RDF 1.2 triple terms are counted only, at graph level: SPARQL 1.1 cannot take a triple term apart,
  so they have no subject class. Rejected: the singleton pattern alone (too narrow for one mechanism).
- **DEC-2 One domain type.** A reified relation is one LinkML class (working name `ReifiedRelation`:
  kind, subject class, generic predicate, object class, statement count, reifier properties) with a
  `ReificationKind` enum. Rejected: a class per kind.
- **DEC-3 Probing templates.** Each kind is an `ASK` probe plus a capture query in a packaged `.rq`
  catalogue with a header, the way pitfall checks are (`fingerprint/adapters/pitfall_catalogue.py`).
  Capture runs only for kinds whose probe answers true. Rejected: one large query for all kinds (cost
  paid on every graph, one failure loses all kinds).
- **DEC-4 Filtered out of the standard fingerprint by default.** What implements a reification found
  by a probe does not appear as ordinary classes or properties. Rejected: showing both.
- **DEC-5 A separate section under each class.** A reified relation is filed under its subject's
  class; for a relation through a blank node, under the class of the node that points to the blank
  node. Rejected: one graph-level list of reifications.
- **DEC-6 One switch, on by default: probe every run, capture only what is present.** With the
  `reifications` setting on (the default, like `pitfall_scan`), every run asks every probe, at every
  depth; only for a kind whose probe answers true does it go on to capture that kind's relations and
  filter its machinery. Off gives today's fingerprint exactly. Rejected: separate switches for
  probing and filtering (a filter without detection has nothing to filter).
- **DEC-7 Grouping never reads IRI strings.** The generic predicate comes from what the kind states
  (`rdf:singletonPropertyOf`, `rdf:predicate`, `owl:annotatedProperty`, `prov:unqualifiedForm`, the
  incoming predicate of a qualifying node). When nothing states it, the predicate resource's own type
  (other than `rdf:Property` and the OWL property types) names the relation; otherwise it is an
  unnamed relation per (subject class, object class). Rejected: collection segments of IRIs (one
  application's convention).
- **DEC-8 Reifier metadata is profiled by name and count.** For each reified relation, the properties
  its reifiers carry and how many reifiers carry each; no values. Rejected: full property profiles of
  reifiers (cost; values belong to a deeper depth if ever wanted).
- **DEC-9 Packaged templates only.** No user-supplied probe directory in this EPIC. Rejected: a
  `--reification-templates` folder like `--pitfall-checks` (not asked for; the catalogue loader keeps
  it cheap to add later).
- **DEC-10 The pitfall `x_individual_as_predicate` is removed** from the packaged catalogue (29 → 28
  checks). Its query is the "resource used as predicate" probe, and as a critical finding it would make
  `--fail-on critical` exit 5 on the very pattern this EPIC supports. A user who still wants it as a
  defect can supply it through `--pitfall-checks`. Rejected: keeping it (contradicts DEC-4/DEC-5);
  silencing it for predicates a probe explains (couples the pitfall scan to collection).
- **DEC-11 Validation shapes note reified relations, never constrain them.** SHACL and ShEx outputs
  add a note under the class's shape (a comment in ShExC, an `rdfs:comment`-style annotation in SHACL)
  naming each reified relation; no property shape or constraint. The descriptive outputs (report,
  profile document, pattern schema and view, diagram, `profile.json`) carry the full section.
  Rejected: shapes for reifiers (each kind would need its own shape idiom); silence (a reader of the
  shapes would not know the links exist).

## Rabbit-holes

- **Structural probes on large graphs.** "Resource used as predicate" and "one triple per named
  graph" join large sets. Probes stop at the first match; captures follow the existing precision
  escalation and failure rules. Measure on the brainframe export and one large public graph before
  stage 1 closes.
- **Inferring meaning from IRI strings.** Ruled out by DEC-7.
- **Treating brainframe as the pattern.** It is one imperfect instance; fact-shaped predicate IRIs
  (`{data}Procedure/{id}`) may stay unnamed relations, and that is a correct answer.
- **"Singleton" is not strict.** A predicate IRI reused 25 times is still a reifier; probes and
  captures must not assume one use.
- **Blank nodes that are not reifications.** A blank node pointed to once with outgoing triples is
  also an RDF list, an OWL restriction or a plain nested description. The D probes exclude list and
  OWL vocabulary nodes and report the rest as n-ary relations; nothing deeper.
- **Nested reification** (a reifier of a reifier, `owl:Annotation` on `owl:Axiom`) is reported one
  level down at most.

## No-gos

- No repair of the data: the fingerprint describes what is there; it adds no missing
  `rdf:singletonPropertyOf` or other triples.
- No application-specific rules: no brainframe namespaces or class names in code or templates.
- No change to how ordinary properties are profiled, and none at all with `reifications` off.
- No SPARQL 1.2: triple terms are counted, not decomposed.
- No n-ary relations through IRI nodes (W3C note pattern, events, 4D fluents) and no Web Annotation:
  nothing in the data tells them from ordinary classes.
- No user-supplied probe templates (DEC-9).

---

## What Changes

- A packaged probe catalogue: per kind, an `ASK` probe and a capture query, with a header (id, kind,
  family, stage).
- A collection stage that probes, captures the reified relations, and records what it filtered.
- The profile model gains `ReifiedRelation` and `ReificationKind`; each class profile carries its
  reified relations; the graph profile carries the RDF-star count.
- The ordinary classes and properties of the profile exclude the reification machinery found.
- The report, profile document, pattern view and schema, PlantUML diagram and `profile.json` show a
  reified-relations section per class; SHACL and ShExC note the relations under the class's shape.
- **BREAKING (pitfall catalogue):** the packaged check `x_individual_as_predicate` is removed; runs
  with `--skip-pitfall x_individual_as_predicate` now fail with "unknown check".
- A `reifications` setting, on by default. **Behaviour change:** with the default, graphs that use
  reification get smaller ordinary sections and a new per-class section.

## Capabilities

### New Capabilities
None: the reification stage belongs to `statistics-collection`.

### Modified Capabilities
- `statistics-collection`: probes, capture, filter, the switch.
- `profile-analytics`: reified relations carried into the class analytics.
- `profile-representations`: the per-class section in the descriptive outputs; a note in SHACL/ShEx.
- `fingerprint-report`: the per-class section in the report.
- `pitfall-scans`: the packaged catalogue loses `x_individual_as_predicate`.

## Impact

- Code: `fingerprint/adapters/queries/` (new `reifications/` catalogue), the collection service, the
  LinkML model (`model/fingerprint_stats.yaml`, `make generate-models`), the generators and report
  templates.
- Test data: a canonical sample graph with one instance of each kind of the stage; golden outputs
  refreshed (`make refresh-sample-profile`, `make refresh-golden`).
- Known consumer: `brainframe-mcp`, which rebuilds a `~>` summary of these links from `profile.json`
  by itself and would read the reified relations instead.
- Release: MAJOR under strict SemVer, because a packaged pitfall id disappears (`--skip-pitfall
  x_individual_as_predicate` stops working); otherwise additive. The developer decides at release.
- Pitfall removal touches `tests/unit/adapters/test_pitfall_checks.py`,
  `tests/unit/service_layer/test_pitfall_scan.py`, `tests/bdd/steps/pitfalls.py`, the scanned golden
  profile and report, and `docs/modules/ROOT/pages/pitfalls.adoc`.
