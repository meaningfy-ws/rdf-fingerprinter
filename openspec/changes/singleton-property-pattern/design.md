> Derives from: EPIC singleton-property-pattern (`proposal.md`, DEC-1 to DEC-11). Covers **stage 1**
> in full; stages 2–4 are outlined in "Later stages" and planned in detail when stage 1 closes.

## Context

rdf-fingerprinter profiles each graph as classes and their properties (statistics-collection). It
has no notion of reification: every reifier node is an instance of an ordinary class and every
singleton predicate IRI an ordinary property. The EPIC adds a reification stage that probes for each
known kind, captures what it finds as reified relations under their subject class, and hides the
machinery from the ordinary profile.

Current state the plan builds on (paths relative to the repo root):

- `collect()` (`fingerprint/service_layer/collection.py`) runs per graph `profile_graph`: graph
  totals (switch), predicate partitions (switch), class counts, then one `profile_class` per class in
  a thread pool, then term annotations. Blank-node classes are dropped right after class counts.
  `first_wave` gathers each class's property IRIs through `seen()` and builds the `PropertyProfile`
  rows; `second_wave` adds the Q10 completeness rows from the predicate partitions and Q11.
- The pitfall scan (`_PitfallScan`) is the model for an optional, per-graph, catalogue-driven stage:
  an emptiness `ASK`, then per-check queries in parallel, failures through `run.fail(...)`.
- Queries are packaged `.rq` files; the first comment line is the query's name (`query_name`), which
  `FakeSparql` (`tests/fakes.py`) uses to route and record queries. `SparqlPort.ask` exists.
- Settings are LinkML slots (`model/fingerprint_stats.yaml`, mirrored in `SettingsOverride` of
  `model/fingerprint_analytics.yaml`), resolved CLI > env > config file > default; env and config
  need no per-field code.
- `ClassAnalytics` `is_a ClassProfile` and copies every class field but `property_partitions`, so a
  new `ClassProfile` field reaches the analytics without code.
- Every generator walks `visit_class`/`visit_property`/`end_class`/`end_graph`
  (`fingerprint/service_layer/generators/generator.py`); per-class views are LinkML classes in
  `model/fingerprint_views.yaml` (`DocumentClass`, `PatternBlock`, `ShexShape`, `NodeShape`,
  `DiagramClass`).
- `--exclude-namespace` acts at representation time on the analytics
  (`fingerprint/domain/namespace_filter.py`, `exclude_terms`).

## Goals / Non-Goals

**Goals (stage 1):**
- The mechanism: the probe catalogue, the collection stage, the hidden-term filter, the model type,
  the per-class section in every descriptive output and the note in SHACL/ShExC (DEC-2..DEC-6, DEC-11).
- The family-A kinds: `rdf_statement`, `singleton_property`, `resource_as_predicate`, `owl_axiom`,
  `negative_property_assertion`, and the `triple_term` count (DEC-1).
- The removal of pitfall `x_individual_as_predicate` (DEC-10).
- Canonical sample data with one instance of each stage-1 kind, its profile and goldens.

**Non-Goals:**
- Families B, C, D (later stages; templates only, see "Later stages").
- Detecting predicates typed only `rdf:Property` (Q5 answer A, `inputs/shaping-qa.md`): brainframe's 465
  unmarked predicates stay ordinary properties.
- Precision escalation for capture queries (P-9).
- User-supplied templates (DEC-9), SPARQL 1.2 (no-go).

## Decisions

New planning decisions; EPIC decisions are cited, not restated.

- **P-1 One `.rq` file per kind, in sections.** `fingerprint/adapters/queries/reifications/<kind>.rq`
  holds a header and up to five queries, each starting with a line `# REIFY <kind> <section>`
  (sections: `probe`, `relations`, `reifier-properties`, `hidden`, `count`). The section line is the
  query's name for `query_name`/`FakeSparql`. Rejected: a file per query (five files per kind, the
  kind's logic scattered); one SELECT doing everything (cannot be both an `ASK` and a capture).
- **P-2 Fixed result variables per section.** `probe`: `ASK`. `relations`: `?subjectClass ?predicate
  ?objectClass ?statements`. `reifier-properties`: `?subjectClass ?predicate ?objectClass
  ?reifierProperty ?reifiers`. `hidden`: `?term`. `count`: `?count`. The loader rejects anything else,
  as the pitfall loader does (`validate` in `pitfall_catalogue.py`). This keeps the collector generic:
  no per-kind Python.
- **P-3 Depth and order.** `profile_graph` runs the probes first, before any partition query, at
  every depth including `graphs` (DEC-6: every run). The hidden terms of the kinds found are computed
  right after, at every depth, so graph-level predicate partitions (depth `graphs` with
  `graph_statistics`) are filtered too. Relations and reifier properties run from depth `classes`
  on (there are no classes below it).
- **P-4 Hidden terms are applied once, at the earliest point.** The hidden terms of the kinds found form one frozen set on the
  run. Hidden classes are dropped where blank-node classes are dropped; hidden predicates are dropped
  in `first_wave`'s `seen()`, from the predicate partitions used by Q10, from the graph-level
  predicate partitions, from co-types, and from Q11 incoming links. Rejected: filtering at
  representation time like `--exclude-namespace` (the profile and `profile.json` would still carry
  the machinery, contradicting DEC-4).
- **P-5 A hidden class is a class all of whose instances are reifiers.** Fixed reifier classes
  (`rdf:Statement`, `owl:Axiom`, `owl:NegativePropertyAssertion`) are listed in the `hidden` query by
  `VALUES`; the classes of singleton or resource predicates are hidden only when no instance of the
  class is outside the kind (`FILTER NOT EXISTS`). The same dynamic rule applies to the reifier nodes
  of every kind (an `rdf:Statement` node also typed `ex:Claim` hides `ex:Claim` only if every
  `ex:Claim` is a statement). Rejected: hiding every class of a reifier (would hide `rdf:Property`).
- **P-14 A class with reifiers and ordinary instances stays whole.** Such a class (brainframe's
  `rdf:Property`: 517 singletons and 465 ordinary predicates) keeps its instance count and property
  rows, reifiers included. Subtracting reifier instances would change every per-class query's
  scoping (`$cls`), against the no-go "no change to how ordinary properties are profiled".
  Documented; a scenario pins it. Rejected: subtracting.
- **P-6 Relations are sorted at collection.** By statements descending, then predicate, then object
  class; the analytics pass them through unchanged, which satisfies profile-analytics "Class
  analytics carry reified relations".
- **P-7 Statements and subjects that do not fit.** A statement whose subject is untyped or a
  blank-node class has no class to file under and is dropped from the relations (counted in no
  section); a statement whose object is untyped, a literal or a blank node has no object class
  (`object_class` absent). A subject with two classes files the relation under both, as properties
  already are.
- **P-8 Failure handling.** Each section's query runs through the run's existing failure path:
  `QUERY_KIND["REIFY"] = QueryKind.reification` (`collection.py`) and `run.fail("REIFY", message,
  graph=…, check_id=<kind id>)`, reusing `Failure.check_id` for the kind id (no new slot). A failed probe or capture makes that kind
  "not found" for the filter (its machinery stays ordinary; nothing disappears silently) and is
  recorded as a failure, so the run fails as for any other query (statistics-collection "Failures
  are recorded and fail the run").
- **P-15 The reification sample is collected in memory, not in Oxigraph.** The sample profile
  collects every graph of the shared store and the e2e tests assert exactly three graphs
  (`tests/e2e/test_collection.py`), so a fourth graph would change both. `tests/refresh_sample_data.py`
  collects `reified-profile.json` through `FakeSparql` with `reifications-source.ttl` loaded into the
  named graph `http://example.org/reifications`, with the stored profile's settings or, when no
  stored file exists yet (the first run), `Settings(selected_graphs=[that graph])` with every other
  setting at its default (`reifications` on); the profile's `graph` is that IRI; the Makefile is unchanged. Real-engine
  coverage: an e2e test sends every rendered section of every packaged template to Oxigraph and
  asserts it is accepted (no data needed), and the brainframe acceptance runs on Blazegraph.
  Rejected: a fourth graph in the shared store (churns the sample goldens and e2e).
- **P-16 Rendering.** `reification_query(template, section, graph)` in
  `fingerprint/adapters/queries/__init__.py` fills `$graph_open`, `$graph_close` and `$distinct`
  with `render()` (the same substitutions as the packaged queries). Each section is a complete query that carries its own
  `PREFIX` lines after the `# REIFY` line. The loader validates a section by filling it for
  `graph=None` and parsing it with rdflib `prepareQuery`.
- **P-9 No precision escalation.** Captures are `GROUP BY` aggregates; a timeout is a failure (P-8).
  Measured on brainframe at the gate; escalation is planned only if a real graph needs it.
- **P-10 `--exclude-namespace` also drops reified relations** whose predicate or object class is in
  an excluded namespace, inside `exclude_terms`' class removal (same rule as properties). Reifier
  properties in excluded namespaces are dropped from a relation's list.
- **P-11 The pattern notation is `~>`.** In the pattern schema a reified relation is a line
  `~> <property|unnamed> (:<ObjectClass>|(:?)) <n> statements [reifiers: <p1> <n1>, …]` after the
  class's properties, built in `fingerprint/domain/patterns.py` (`block()`); brainframe-mcp already
  uses `~>` for these links. ShExC carries the same text as a `#` comment line inside the shape
  (`fingerprint/domain/shex.py`, `shex_view`); SHACL an `rdfs:comment "Reified relation: …"` on the
  node shape; PlantUML a `-- reified --` compartment in the class box with one line per relation (no
  association arrows, so absent or unprofiled object classes need no rule). `patterns.csv` and the
  glossary are unchanged in stage 1 (one row per property; documented).
- **P-12 Triple terms are a graph-level count.** `triple_term` has `probe`, `count` and `hidden`
  (`rdf:reifies`) sections and no relations; the count of `rdf:reifies` triples lands on `GraphProfile.triple_term_reifications`.
- **P-13 Release.** Stage 1 removes a packaged pitfall id (BREAKING for `--skip-pitfall
  x_individual_as_predicate`); the version bump is the developer's call at release (EPIC Impact).
  Stages 2–4 are MINOR.

## Layering and modules

| Layer | File | Change |
|---|---|---|
| model | `model/fingerprint_stats.yaml` | enum `ReificationKind` (stage-1 values: `rdf_statement`, `singleton_property`, `resource_as_predicate`, `owl_axiom`, `negative_property_assertion`, `triple_term`); classes `ReifiedRelation` (`kind`, `property` optional (the generic predicate; this slot name is in `IRI_FIELDS` of `fingerprint/service_layer/prefixes.py`, so its namespace gets a prefix), `object_class` optional, `statements`, `reifier_properties`) and `ReifierProperty` (`property`, `reifiers`); `ClassProfile.reified_relations`; `GraphProfile.reification_kinds` (optional; left unset, so absent from `profile.json`, when no kind is found, so the existing profiles do not change), `GraphProfile.triple_term_reifications`; slot `reifications` (boolean, `ifabsent: "true"`) in `Settings`; `QueryKind.reification` |
| model | `model/fingerprint_analytics.yaml` | `reifications` in `SettingsOverride` |
| model | `model/fingerprint_views.yaml` | `reified_relations` on `DocumentClass`, `PatternBlock`, `ShexShape`, `NodeShape`, `DiagramClass` (a view class `ReifiedRelationView` with the rendered predicate, object class, count and reifier text) |
| adapters | `fingerprint/adapters/reification_catalogue.py` (new) | `packaged_templates() -> list[ReificationTemplate]`: reads `queries/reifications/*.rq`, splits sections, validates P-2 |
| adapters | `fingerprint/adapters/queries/reifications/*.rq` (new) | six stage-1 templates (§A) |
| adapters | `fingerprint/adapters/queries/pitfalls/x_individual_as_predicate.rq` | deleted |
| adapters | `fingerprint/adapters/queries/__init__.py` | `reification_query` (P-16) |
| service | `fingerprint/service_layer/collection.py` | `_Reifications` stage (§B), the hidden-term filter (P-4), relations attached to class profiles, `QUERY_KIND["REIFY"]` (P-8) |
| domain | `fingerprint/domain/namespace_filter.py` | P-10 |
| service | `fingerprint/service_layer/generators/{document,shacl,plantuml}.py` | build the `reified_relations` views in `end_class` |
| domain | `fingerprint/domain/patterns.py` (`block()`), `fingerprint/domain/shex.py` (`shex_view`) | build the pattern and ShExC views (P-11) |
| templates | `fingerprint_report_templates/*/templates/…` (`main.html`, `patterns.md`, `schema.shex`, `shapes.ttl`, `diagram.puml`) | render them (P-11) |
| tests | `tests/bdd/conftest.py` | `pytest_bdd_apply_tag`: tag `@stage4` → `pytest.mark.skip(reason="stage 4")` |
| tests | `tests/refresh_sample_data.py`, `tests/refresh_golden.py` | the reified profile and goldens (P-15) |
| entrypoints | `fingerprint/entrypoints/cli/main.py` | `--reifications/--no-reifications` |

`ReificationTemplate` is a LinkML class in `fingerprint_stats.yaml` (id, title, family, the section
texts), never a dict (domain-object-model DEC-1).

## Algorithm / approach

### A. The stage-1 templates (abridged; prefixes omitted)

`singleton_property.rq`:

```sparql
# id: singleton_property
# title: Singleton property (rdf:singletonPropertyOf)
# family: statement_identity
# REIFY singleton_property probe
ASK { $graph_open ?s ?sp ?o . ?sp rdf:singletonPropertyOf ?g . $graph_close }
# REIFY singleton_property relations
SELECT ?subjectClass ?predicate ?objectClass (COUNT(*) AS ?statements) WHERE {
  { SELECT $distinct ?s ?sp ?o WHERE { $graph_open ?s ?sp ?o . ?sp rdf:singletonPropertyOf ?g . $graph_close } }
  $graph_open ?sp rdf:singletonPropertyOf ?predicate . ?s a ?subjectClass .
  OPTIONAL { ?o a ?objectClass } $graph_close } GROUP BY ?subjectClass ?predicate ?objectClass
# REIFY singleton_property reifier-properties
SELECT ?subjectClass ?predicate ?objectClass ?reifierProperty (COUNT(DISTINCT ?sp) AS ?reifiers)
WHERE { $graph_open ?s ?sp ?o . ?sp rdf:singletonPropertyOf ?predicate ; ?reifierProperty ?v .
  FILTER(?reifierProperty NOT IN (rdf:singletonPropertyOf, rdf:type)) ?s a ?subjectClass .
  OPTIONAL { ?o a ?objectClass } $graph_close }
GROUP BY ?subjectClass ?predicate ?objectClass ?reifierProperty
# REIFY singleton_property hidden
SELECT DISTINCT ?term WHERE { $graph_open
  { ?sp rdf:singletonPropertyOf ?g . BIND(?sp AS ?term) }
  UNION { VALUES ?term { rdf:singletonPropertyOf } }
  UNION { ?sp rdf:singletonPropertyOf ?g ; a ?term .
          FILTER NOT EXISTS { ?x a ?term FILTER NOT EXISTS { ?x rdf:singletonPropertyOf ?any } } }
  $graph_close }
```

The other five follow the same sections:

| Kind | Probe matches | `?predicate` from | Statement counted | Fixed hidden terms | Dynamic hidden terms |
|---|---|---|---|---|---|
| `rdf_statement` | `?st rdf:subject ?s ; rdf:predicate ?p ; rdf:object ?o` | `rdf:predicate` | distinct `?st` | `rdf:Statement`, `rdf:subject`, `rdf:predicate`, `rdf:object` | classes of `?st` per P-5 |
| `singleton_property` | above | `rdf:singletonPropertyOf` | each `?s ?sp ?o` triple | `rdf:singletonPropertyOf` | each `?sp`; classes of `?sp` per P-5 |
| `resource_as_predicate` | `?s ?p ?o . ?p a ?t`, with `?t` not in `NOT_REIFIER_TYPES` (below), `FILTER NOT EXISTS { ?t rdfs:subClassOf+ rdf:Property }` (user subclasses of `rdf:Property` in the same graph), and no `rdf:singletonPropertyOf` | `?t` (the predicate's type, DEC-7) | each triple | — | each such `?p`; `?t` per P-5 |
| `owl_axiom` | `?ax owl:annotatedSource ?s ; owl:annotatedProperty ?p ; owl:annotatedTarget ?o` | `owl:annotatedProperty` | distinct `?ax` | `owl:Axiom`, `owl:annotatedSource`, `owl:annotatedProperty`, `owl:annotatedTarget` | classes of `?ax` per P-5 |
| `negative_property_assertion` | `?n owl:sourceIndividual ?s ; owl:assertionProperty ?p` | `owl:assertionProperty` | distinct `?n` | `owl:NegativePropertyAssertion`, `owl:sourceIndividual`, `owl:assertionProperty`, `owl:targetIndividual`, `owl:targetValue` | classes of `?n` per P-5 |
| `triple_term` | `?r rdf:reifies ?t` | — (count only, P-12) | `count`: `COUNT(*)` of `rdf:reifies` triples | `rdf:reifies` | — |

`NOT_REIFIER_TYPES` (a `VALUES` list in the template): `rdf:Property`, `rdfs:ContainerMembershipProperty`,
`rdfs:Resource`, `owl:Thing`, `owl:NamedIndividual`, `owl:ObjectProperty`, `owl:DatatypeProperty`,
`owl:AnnotationProperty`, `owl:OntologyProperty`, `owl:DeprecatedProperty`, `owl:FunctionalProperty`,
`owl:InverseFunctionalProperty`, `owl:TransitiveProperty`, `owl:SymmetricProperty`,
`owl:AsymmetricProperty`, `owl:ReflexiveProperty`, `owl:IrreflexiveProperty`. `rdfs:Resource` and
`owl:Thing` are there because a store with inference types every predicate with them.

Counting triples (the singleton and resource kinds) follows the existing rule for union-default
stores: the relations query counts over a subquery `SELECT $distinct ?s ?sp ?o`, so a triple seen
through two graphs counts once.

Reifier properties exclude the kind's own structural predicates and `rdf:type`. A `resource_as_predicate`
predicate with several non-property types yields one relation per type (as P-7 for subjects).

### B. The collection stage (`_Reifications`)

```text
profile_graph(graph):
    kinds   = [t for t in templates if ask(t.probe)]              # first, every depth (P-3)
    profile.reification_kinds = [t.id for t in kinds]
    run.hidden = union(select(t.hidden) for t in kinds)            # parallel; every depth
    count   = select(triple_term.count) if triple_term in kinds
    totals, predicates (as today, minus run.hidden)
    if depth < classes: return
    relations = merge(select(t.relations), select(t.reifier_properties)) per kind
    classes = class_counts(graph)
    drop blank-node classes and hidden classes from classes         # P-4, P-5
    profile_class(...) with run.hidden                              # seen(), Q10, co-types, Q11
    attach relations to their subject class, sorted (P-6); drop those of classes not profiled (P-7)
```

`settings.reifications` off: none of this runs and `run.hidden` is empty, so the profile equals
today's except the settings block, which records `"reifications": false`. Every operation is a read-only query; the stage is idempotent and safe to
retry like every other collection query.

### C. Worked example (the canonical reification sample, §D)

Data (graph `…/reifications`):

```turtle
ex:alice a ex:Person .  ex:bob a ex:Person .  ex:acme a ex:Org .
ex:alice ex:rel1 ex:acme .  ex:bob ex:rel2 ex:acme .
ex:rel1 rdf:singletonPropertyOf ex:worksFor ; a ex:Link ; prov:wasAttributedTo ex:hr .
ex:rel2 rdf:singletonPropertyOf ex:worksFor ; a ex:Link .
ex:st1 a rdf:Statement ; rdf:subject ex:alice ; rdf:predicate ex:knows ; rdf:object ex:bob ;
       dct:source ex:survey .
```

Profile of class `ex:Person`: no property `ex:rel1`, `ex:rel2` or anything from `rdf:`; reified
relations, in this order:
1. `singleton_property`, `ex:worksFor` → `ex:Org`, 2 statements, reifiers `prov:wasAttributedTo` 1.
2. `rdf_statement`, `ex:knows` → `ex:Person`, 1 statement, reifiers `dct:source` 1.

No class `ex:Link` (every instance is a singleton predicate, P-5), no class `rdf:Statement`.
`reification_kinds` = `[rdf_statement, singleton_property]`. Pattern line:
`~> ex:worksFor (:Org) 2 statements [reifiers: prov:wasAttributedTo 1]`.

### D. Canonical data

`tests/test_data/reifications-source.ttl` holds one instance of each stage-1 kind (§C extended
with `owl:Axiom`, `owl:NegativePropertyAssertion`, a resource-as-predicate typed `ex:Procedure`, one
typed only `rdf:Property` that must stay ordinary, and an `rdf:reifies` triple whose object is an IRI
standing in for a triple term: rdflib cannot parse RDF 1.2 triple terms, and the probe only needs the
predicate). It is collected in memory (P-15) by `make refresh-sample-profile` into
`tests/test_data/profiles/reified-profile.json`, rendered by `make refresh-golden` into
`tests/test_data/golden/reified/`, and its named facts go in `tests/sample_data.py` (`REIFIED_*`).
The existing sample and scanned profiles gain only `"reifications": true` in their settings: the
sample through `make refresh-sample-profile`, the scanned one by hand, since no make target refreshes
it (the one hand edit, justified against the "regenerate, never by hand" rule). Their golden outputs
must not change (profile-representations "No section when none"); the stage-1 probes find nothing in
the continents and treaties data (checked with rdflib in the gate review).

### Anti-patterns

| Don't | Do instead | Why |
|---|---|---|
| Write Python per kind | Put every per-kind rule in its `.rq` sections | Stages 2–4 must be templates only (EPIC appetite) |
| Match IRI strings or namespaces to find reifiers | Use the kind's marker or the predicate's type | DEC-7 |
| Filter the machinery in the generators | Filter in collection (P-4) | `profile.json` would still carry it (DEC-4) |
| Hide a class because some instance is a reifier | Hide only classes all of whose instances are (P-5) | Hiding `rdf:Property` would hide declared vocabularies |
| Build dicts of relations keyed by class | Build `ReifiedRelation` objects and group with a module-level helper | domain-object-model DEC-1 (guard test) |
| Treat a failed probe as "absent" silently | Record the failure and leave the machinery ordinary (P-8) | Nothing may disappear without a trace |

## Test case specifications

Each spec scenario is a Gherkin scenario of the same title in the capability's feature file
(lean-test-suite DEC-1), written first (task 0.1, so `tests/guards/test_traceability.py` is green
from the start) and bound to `FakeSparql` loaded with `reifications-source.ttl` or a builder variant.
`FakeSparql` routes on the first token of the query name (`REIFY`), so tests that make one section
fail pass `when=` to match the kind and section. Scenarios stay red from task 0.1 until the task that
binds them (tasks.md names it); `@stage4` is skipped by the conftest hook.

| Spec delta → scenario | Feature file |
|---|---|
| statistics-collection: Kind absent; Switch off; A class with reifiers and ordinary instances stays whole; Singleton properties of one generic property; RDF reification; Resource used as predicate with no marker; A predicate typed only as a property is ordinary; Relation through a blank node (stage 4, `@stage4` skipped until then); RDF-star is counted only; Singleton predicates leave the property rows; rdf:Statement leaves the classes | `tests/features/statistics_collection.feature` |
| profile-analytics: Relations follow their class | `tests/features/profile_analytics.feature` |
| profile-representations: Section present; No section when none; Shapes note reifications without constraining them | `tests/features/profile_representations.feature` |
| fingerprint-report: Kinds found are named | `tests/features/fingerprint_report.feature` |
| pitfall-scans: Catalogue size (28); Each check finds its pitfall and only it | `tests/features/pitfall_scans.feature` (existing, updated) |

Unit tests (branches the scenarios do not reach): `tests/unit/adapters/test_reification_catalogue.py`
(section split; each P-2 rejection: missing probe, probe not `ASK`, wrong variables, `FROM` clause,
unknown section); `tests/unit/service_layer/test_reifications.py` (depth `graphs` runs probes only;
failed probe → failure recorded, machinery kept; failed `hidden` → kind not filtered; relation of an
unprofiled class dropped; untyped subject dropped; two-class subject filed twice; sort order P-6);
`tests/unit/domain/test_namespace_filter.py` (P-10 cases). Golden tests cover every output for the
reified profile. e2e: `tests/e2e/`
sends every rendered section of every packaged template to Oxigraph and asserts each is accepted
(P-15).

## Error matrix

| Failure mode | How it is detected | Expected handling |
|---|---|---|
| Malformed packaged template | `packaged_templates()` validation at load | Raises at startup; a unit test loads the packaged catalogue, so CI catches it |
| Probe times out or errors | the query port raises | `run.fail("REIFY", …, check_id=<kind>)`; kind treated as absent; run fails (P-8) |
| `hidden` fails after the probe found the kind | port raises | failure recorded; the kind's machinery stays ordinary; its relations are still attached if their queries succeeded |
| `relations` / `reifier-properties` fails | port raises | failure recorded; the kind's relations omitted; hidden terms still applied (the machinery is known) |
| Endpoint rejects `rdf:reifies` objects (1.1 store with triple terms) | probe raises | as a failed probe; the docs name `--no-reifications` as the way round |
| Capture slow on a large graph | duration in the run log | no escalation (P-9); measured at the gate |
| Reifier with a non-IRI generic predicate (literal in `rdf:singletonPropertyOf`) | `?predicate` not an IRI | the relation is unnamed (`property` absent) |
| Retry of a timed-out query | existing retry policy | safe: read-only, no state written before all queries of a graph return |

## Exit criteria (stage 1)

`make check-all` green; `make oxigraph-load-test-data` + `make test-e2e` green; `make check-mutation`
at or above the stored score; `openspec validate --all --strict`; the brainframe acceptance (task
8.4): with defaults, the 517 marked singleton predicates appear as one relation `isRelatedTo` per
(subject class, object class) and as no ordinary property, the 465 `rdf:Property`-only predicates are
unchanged, and the reification stage costs under 10 % of collection time, measured as the
difference in `ProfileRun` duration (finished − started) between a default run and a
`--no-reifications` run of the same settings, each run twice, the faster of each pair compared.

## Risks / Trade-offs

- [Brainframe gains less than hoped: only the marked quarter folds (Q5 answer A)] → stated in the
  docs and in the brainframe evidence; option B/C stays a possible later change.
- [`FILTER NOT EXISTS` in P-5 is slow on large classes] → it runs only for kinds found; measured at
  the gate; fallback is to hide only the fixed classes.
- [Hidden-term set large (thousands of singleton IRIs)] → a Python frozenset; never sent back to the
  endpoint as `VALUES`.
- [Mixed classes still carry reifiers (P-14), e.g. brainframe's `rdf:Property`] → documented in the
  docs page and pinned by a scenario; subtraction is a possible later change.
- [Untyped subjects' reified statements vanish from the profile (P-7)] → documented; a graph-level
  count is a possible later addition.
- [Golden churn] → the existing goldens must not change (§D); any diff is a defect.

## Later stages (outline; planned in detail when stage 1 closes)

| Stage | Kinds (new `ReificationKind` values) | New beyond templates |
|---|---|---|
| 2 | `graph_statement` (one triple per named graph, graph described), `nanopublication` | none expected; the probe must run over all graphs, so the template uses `GRAPH ?g` instead of `$graph_open` |
| 3 | `prov_qualified`, `dcat_qualified`, `schema_role`, `wikibase_statement`, `cidoc_property_of_property`, `skosxl_label` | none |
| 4 | `blank_nary`, `structured_value` (`rdf:value`) | none; the `@stage4` scenario of statistics-collection is bound |

Each stage: templates, sample data in `reifications-source.ttl`, scenarios, refreshed reified
profile and goldens, docs rows, release.

## Open Questions

None blocking stage 1.
