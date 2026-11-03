---
kind: seed notes (secondary; superseded by proposal.md, never groomed)
---

# Evidence: resources used as predicates in the brainframe workspace export

Measured 2026-11-03 with SPARQL on the brainframe workspace export (77,635 triples, 13,699
subjects; BlazeGraph). Sanitised: no titles, no identifiers. `{data}` is the application's data
namespace, `{data}{Collection}/{id}`. The export was reached through `brainframe-mcp`, whose
assistant needed these links to answer "which risks have no control?" and could not find them
from the schema.

## Every predicate under `{data}`, by family

| Family | `rdf:singletonPropertyOf` | Typed | Predicates | Triples | Max uses of one predicate |
|---|---|---|---:|---:|---:|
| `{data}RelationId/{id}` | `isRelatedTo` (all) | `RelationId`, `rdf:Property` | 517 | 606 | 5 |
| `{data}RelationId/{id}` | none | `rdf:Property` only | 117 | 329 | |
| `{data}Procedure/{id}` | none | `rdf:Property` only | 249 | 997 | |
| `{data}Policy/{id}` | none | `rdf:Property` only | 75 | 314 | |
| `{data}mitigationImplementationStatus/{id}` | none | `rdf:Property` only | 3 | 60 | |
| five smaller collections | none | `rdf:Property` only | 21 | 67 | |

The 465 predicates without `rdf:singletonPropertyOf` together reach up to 25 uses for one predicate.
All 2,373 triples have an IRI object.

## What the families appear to mean

- **Singleton properties proper** (first row): the statement's own predicate carries metadata (creator,
  editor, folder, a label) and names its generic property. Nearly singleton: a few predicates are
  reused up to 5 times.
- **Predicate-only resources with no generic property** (other `RelationId` rows): typed only
  `rdf:Property`; the link's meaning is not stated anywhere.
- **Named link families** (`mitigationImplementationStatus/{id}`): the collection name carries the
  meaning. These link procedures and policies to assets (services, container images, cloud
  infrastructure, software) — likely the application's "control mitigates asset" link, which is
  invisible in the current profile.
- **Fact-collection IRIs as predicates** (`Procedure/{id}`, `Policy/{id}`): IRIs shaped like facts of a
  class, used as predicates from procedures and policies to untyped objects; the predicate IRIs are
  not themselves typed as facts.

## What the profile shows today

The profile treats each such IRI as an ordinary property: one edge per predicate, about 1,000 of them.
The 3.3.0 namespace filter (`--exclude-namespace {data}`) removes them from the representations, which
keeps outputs small but loses the links. `brainframe-mcp` then rebuilds a summary by itself from
`profile.json`: one `~> (:Target) n triples` line per class pair, with a hard-coded stem and a
`STRSTARTS` filter as the only way to query them. Neither tells a reader which relation a link is,
what metadata a link carries, or that the pattern exists.

## After the EPIC (task 8.4, 2026-11-03)

Store: a throwaway local Oxigraph 0.5.13 (`oxigraph-brainframe`, port 7879) loaded with
`brainframe-mcp/data/workspace-ce705e50b88704fd413497b9af4ff1cf-meaningfy.rdf` (74,007 triples; the
Blazegraph count of 77,635 above includes Blazegraph's own additions). Baseline matches the table
above: 517 predicates with `rdf:singletonPropertyOf`, used in 606 triples, all typed `RelationId`.

```sh
OUT=temp/brainframe-reifications
for i in 1 2; do for mode in on off; do flag=""; [ $mode = off ] && flag="--no-reifications"
  mkdir -p $OUT/$mode-$i
  poetry run fingerprint -e http://localhost:7879/query -o $OUT/$mode-$i $flag
done; done
```

| | reifications on | `--no-reifications` |
|---|---:|---:|
| classes | 51 | 51 |
| ordinary property rows | 1,087 | 1,589 |
| rows of `RelationId/…` predicates | 117 (the unmarked, `rdf:Property`-only ones; Q5 answer A) | 619 |
| marked predicates left as ordinary properties | **0** of 517 | 502 |
| reified relations | 55, all `RelationId` via `resource_as_predicate`, per (subject class, object class) | — |
| reification kinds found | `resource_as_predicate` | — |
| `ProfileRun` duration (two runs) | 1.003 s, 0.989 s | 0.832 s, 0.792 s |

Example relations (pattern notation): `Policy ~> RelationId (:Policy) 86 statements via
resource_as_predicate [reifiers: createdBy 83, singletonPropertyOf 83, label 83, isFactOf 83]`;
`checkList ~> RelationId (:Policy) 64`; `Action ~> RelationId (:RiskScenario) 38`.

**Outcome criterion: met.** The marked predicates fold into relations named by their own type
(`RelationId`, DEC-12), carry their metadata as reifier properties, and leave no ordinary row.

**Cost criterion (< 10 %): not met on this graph** — about +0.18 s on a 0.8 s run (≈ +20 %). The
cost is the fixed set of probes and captures (sequential sum 0.35 s, run concurrently); the largest
single query is `resource_as_predicate` hidden (0.12 s; a rewrite starting from typed predicates
gives the same 517 terms in 0.10 s, not adopted). On a graph this small the fixed probe cost
dominates; `--no-reifications` removes it.
