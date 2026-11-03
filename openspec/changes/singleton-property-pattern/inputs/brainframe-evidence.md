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
