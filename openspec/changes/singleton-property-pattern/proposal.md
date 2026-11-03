# EPIC: Detect and fingerprint resources used as predicates (the singleton property pattern)

> **Status: problem stated, not shaped (2026-11-03).** This EPIC records the problem and the outcome
> wanted. How to detect and fingerprint the pattern is deliberately left open: approach, key
> decisions, appetite and specs are decided in a later shaping round.

**Golden-thread parents:**
- Living spec `openspec/specs/statistics-collection/spec.md` (what the profile collects per property).
- Living spec `openspec/specs/profile-representations/spec.md` (how properties appear in the pattern
  schema, ShExC and the other outputs).
- Change `namespace-filter` (3.3.0): `--exclude-namespace` removes such predicates by namespace; this
  EPIC asks for them to be understood instead.

**Seeds** (secondary, never groomed), under `inputs/`:
- `brainframe-evidence.md`: the motivating case, measured.

## Appetite

To be decided when shaped.

## Why

Some graphs attach information to a statement by giving the statement **its own predicate**. In the
singleton property pattern (Nguyen et al., WWW 2014), each link uses a unique predicate IRI, and that
IRI is a resource in its own right: it names its generic property through `rdf:singletonPropertyOf`
and carries the link's metadata (who made it, when, in which folder).

```turtle
ex:a      ex:rel/42  ex:b .
ex:rel/42 rdf:singletonPropertyOf ex:isRelatedTo ;
          prov:wasAttributedTo    ex:person/7 .
```

rdf-fingerprinter treats each such IRI as an ordinary property. In the brainframe export
(`inputs/brainframe-evidence.md`) that is about 1,000 one-off properties, each profiled on its own.
The profile can neither say that the pattern is there nor say what the links mean. The only remedy
today, `--exclude-namespace`, keeps the outputs small by dropping the links altogether. That is where
the meaning of the data sits: in that export, the link from a control (procedure, policy) to the asset
it mitigates exists only as such predicates. Downstream, an LLM reading the schema cannot find it and
answers "no risk has a control" when the links are there.

The real data is also messier than the textbook pattern, and a solution has to face that:

- only about a quarter of the link triples name a generic property through `rdf:singletonPropertyOf`;
- the others are predicate IRIs typed only `rdf:Property`, sometimes with the meaning in the IRI's
  collection segment (`{data}mitigationImplementationStatus/{id}`), sometimes nowhere;
- some predicate IRIs are shaped like facts of a class (`{data}Procedure/{id}`) without being typed as
  such;
- "singleton" is not strict: one predicate IRI is reused up to 25 times.

## Solution outline

Outcome wanted, not the method: **a fingerprint that recognises resources used as predicates, groups
them into the relations they stand for, and describes those relations like any other property**,
with their subject and object classes, counts and the metadata the links carry, so that a reader (or
an LLM) can query them by meaning instead of by namespace string.

Questions for the shaping round:

1. **Detection.** Which signals mark a predicate as a resource: `rdf:singletonPropertyOf`, the
   predicate having its own triples or type, its namespace role (data, not vocabulary), its number of
   uses, its IRI shape? Which are required, which are hints?
2. **Grouping.** What a relation is when there is no `rdf:singletonPropertyOf`: the predicate's type,
   its IRI's collection segment, the (subject class, object class) pair, or nothing ("unnamed link").
3. **Link metadata.** Whether and how the properties of the predicate resources themselves are
   profiled (creator, folder, label), and at what cost.
4. **Representations.** How the groups appear in the pattern schema, ShExC, the report and
   `profile.json`, and how this sits with `--exclude-namespace` (replace, complement, or both).
5. **Generality.** Which neighbouring patterns are in scope with it, for example RDF reification
   (`rdf:Statement`) or RDF-star annotations, and which stay out.
6. **Cost.** What the detection adds to collection time on large graphs.

## Key decisions

None yet; see the questions above.

## Rabbit-holes

- Treating the brainframe data model as the pattern. The pattern is generic; brainframe is one
  imperfect instance of it, and the brainframe-specific families (fact-shaped predicate IRIs) may not
  generalise.
- Inferring meaning from IRI strings. Collection segments are a convention of one application, not a
  rule of RDF.

## No-gos

- No repair of the data: the fingerprint describes what is there, it does not add the missing
  `rdf:singletonPropertyOf` triples.
- No application-specific rules (no brainframe namespaces or class names in the code).
- No change to how ordinary properties are profiled.

---

## What Changes

To be decided when shaped.

## Capabilities

### New Capabilities
To be decided when shaped.

### Modified Capabilities
Likely `statistics-collection`, `profile-representations` and `fingerprint-report`; to be confirmed
when shaped.

## Impact

To be decided when shaped. Known consumer: `brainframe-mcp`, which today rebuilds a `~>` summary of
these links from `profile.json` by itself and would use the new relations instead.
