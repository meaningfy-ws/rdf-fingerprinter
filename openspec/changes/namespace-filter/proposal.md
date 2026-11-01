# EPIC: Namespace filters that leave out every term of a namespace

## Appetite

**MEDIUM** (developer, round 1, Q16). On the `epic-planning` scale, MEDIUM is "one new capability
with its tests and docs; neighbours touched lightly". The new capability is the term-level
namespace filter, with its matching rule (DEC-6), applied by every output (DEC-2) from one place
(DEC-4). The neighbour `fingerprint-report` is touched lightly: in-page switches for property rows
(DEC-10). It is above SMALL because of the report switches (Q9 b) and the stem/glob matching
(Q13 b). The 3.3.0 release is part of the change (DEC-3).

**Golden-thread parents:**
- Living spec `openspec/specs/profile-representations/spec.md`, "Requirement: Namespace filters"
  (the requirement this change rewrites) and "Representations derive from the saved profile only".
- Living spec `openspec/specs/fingerprint-report/spec.md`, "Requirement: Navigation, search and
  filters" (the in-page namespace switches).
- Archived change `2026-10-31-readable-representations`: DEC-5 (namespace filters are a
  representation option) and DEC-8 (meta vocabularies excluded by default), which this change
  extends from classes to all terms for the namespaces a user names.
- Archived change `2026-10-31-profile-representations`: DEC-1 (every representation is a function
  of the saved profile).
- Change `llm-schema-tools` (3.2.0): the pattern schema and ShExC outputs this change also filters.

**Seeds** (secondary, never groomed), under `inputs/`:
- `developer-request.md`: the request, verbatim, the decisions already taken, and what existed.
- `brainframe-evidence.md`: the motivating case, measured.
- `qa-round-1.md`: the question round, its answers (verbatim) and where each landed.

## Why

The developer asked to "filter out items by their prefix", e.g. turn `relationid` on and off. The
current filter cannot: it leaves out the **classes** of an excluded namespace and nothing else.
The brainframe dataset models relations as singleton properties `relationid:<uuid>`: no class
lives in that namespace, so `--exclude-namespace relationid` hides nothing and logs nothing. Its
619 properties take about 55 % of the 222 KB pattern schema (edges, `via` lists, glossary), the
output meant to fit an LLM's context (`inputs/brainframe-evidence.md`).

## Solution outline

**One rule, applied by every output: a term in an excluded namespace is not written.**

- A namespace named with `--exclude-namespace` loses every term in every output: the report,
  SHACL, ShExC, PlantUML and the pattern schema (DEC-2, DEC-8). The meta vocabularies stay hidden
  at class level only, as today (DEC-7).
- A name can be a prefix, a prefix glob (`'relation*'`) or an IRI stem
  (`'https://my.brainframe.com/#/knowledge/'`), so one option covers a family of namespaces
  (DEC-6).
- The filter is applied when the outputs are rendered. The saved profile keeps every term, so
  switching a namespace on or off is a re-run of `fingerprint-gen-*` on `profile.json`, with no
  endpoint query (DEC-1).
- The rule lives in one place, before any output is built (DEC-4), so the outputs cannot disagree
  about what is hidden.
- Each output says what it left out, and a name that hides nothing is warned about (DEC-9), so a
  reader or an LLM does not take a filtered namespace for missing data.
- The report also gets in-page switches for the property rows of every namespace in use (DEC-10).

**Outcome:** `fingerprint-gen-pattern --exclude-namespace relationid profile.json` writes a pattern
schema of the brainframe workspace graph with no `relationid:` term, at most 100 000 characters
instead of 221 799, and the same option gives the same cut in every other output.

## Key decisions

- **DEC-1** (developer, 2026-11-01): **Filtering happens at output time only.** `profile.json`
  keeps everything; collection does not change; toggling a namespace means regenerating from the
  saved profile without querying. Continues profile-representations DEC-1 and readable-representations
  DEC-5. Rejected: filtering during collection.
- **DEC-2** (developer, 2026-11-01): **Every output applies the filter**: the report, SHACL,
  ShExC, PlantUML and the pattern schema. The pitfall findings are the exception (DEC-11).
  Rejected: a filter for the LLM outputs only.
- **DEC-3** (developer, 2026-11-01): **This change releases 3.3.0**, separately from 3.2.0
  (`llm-schema-tools`), with the SemVer bump and `CHANGELOG.md` entry the release authority in
  `AGENTS.md` requires. Rejected: folding it into 3.2.0.
- **DEC-4**: **One term-level filter, decided in one place, before any output is built**, for the
  outputs rendered through `generate_representations` (the commands, `fingerprint_report` and
  `generate_from_profile_file`). The one place covers the excluded tier (DEC-7); the class-level
  hiding of the meta tier stays where it is. Reason:
  today each generator decides for itself (`Generator.shown()`, the pattern builder's `_shown()`,
  PlantUML's link test), which is how the outputs came to filter different things. Rejected:
  per-generator filtering rules.
- **DEC-5** (round 1, Q14 a): **The options keep their names**, `--exclude-namespace` and
  `--include-namespace` on `fingerprint` and every `fingerprint-gen-*` command, and
  `GeneratorOptions.exclude_namespaces`/`include_namespaces` for library callers; only their reach
  grows. 3.3.0 is MINOR, with a "Changed" CHANGELOG entry: the old class-only reach of a named
  namespace is the defect being fixed. Rejected: new options beside the old ones.
- **DEC-6** (round 1, Q12 and Q13 b; the rule recommended by the planner, as asked): **How a
  filter value is matched.** Each value is matched against the profile's namespace table by the
  first rule that applies:
  1. a value holding `:` is an **IRI stem**: it matches every namespace whose IRI starts with it,
     case-sensitively. A full namespace IRI is a stem too, so it also matches the namespaces under
     it (in 3.2.0 it matched that namespace only). `*` has no special meaning in a stem (an IRI may
     hold `*`);
  2. a value holding `*` is a **prefix glob**: `*` matches any run of characters, possibly none;
     every other character matches itself, case-sensitively; the glob must cover the whole prefix;
  3. any other value is an **exact prefix**.
  Prefixes never hold `:` or `*`, so the three forms never overlap. Include values match by the
  same rule, and a namespace matched by any include value is taken out of both tiers (DEC-7):
  include wins. Warnings are in DEC-9. Rejected: `?` and `[…]` wildcards (they add rules nobody
  asked for); globs over IRIs; exact-IRI-only matching (it cannot cover brainframe's family of
  instance namespaces in one value).
- **DEC-7** (round 1, Q1 a): **Two tiers.**
  - *Hidden*: the meta namespaces `rdf`, `rdfs`, `owl`, `sh`, less any included again. Only their
    **classes** are left out, as today; `rdf:type`, `rdfs:label` and the like stay.
  - *Excluded*: the namespaces matched by `--exclude-namespace` values, less any included again,
    meta ones included. **Every term** of theirs is left out (DEC-8).
  Rejected: one tier, which would remove the most used properties from every output by default.
- **DEC-8** (round 1, Q2, Q3, Q4 a, Q5, Q6 a): **What "every term" means.** No output writes an
  IRI of an excluded namespace as a class, property, object class, co-type, parent, single value,
  glossary term or prefix declaration. In particular:
  - an excluded **property** loses its pattern edge and incoming links, its ShExC triple
    constraint, its SHACL property shape, its PlantUML attribute or link (and its count), and its
    report row;
  - an excluded **object class** of a kept property is dropped from the property's value types;
    its objects count as untyped resources, so the edge stays, written as `IRI`
    (SHACL `sh:nodeKind sh:IRI`);
  - a **merged group** `A&B` with `B` excluded is the group `A`; a `co B` note is dropped; a class
    in a kept namespace stays even when its instances are also typed with an excluded class;
  - **datatypes** are never filtered.
  Rejected: dropping the whole edge for an excluded object class (it hides a kept property).
- **DEC-9** (round 1, Q7 a, Q8): **The outputs say what they left out.** Every per-graph output
  where an excluded namespace hid a term carries one comment line naming each such namespace with
  its counts of hidden classes, properties and values. The report lists the same per graph under
  its caveats. A filter value that matches no namespace logs the existing warning; an exclude value
  that hides no term logs `--exclude-namespace <name>: no term in this namespace; ignored`.
  Rejected: silent filtering.
- **DEC-10** (round 1, Q9 b): **The report.** The filter removes the excluded terms from the
  report as from every other output; the namespace table still lists every prefix and marks the
  excluded ones. The in-page switches grow: one per namespace of a shown class **or property**;
  switching one off hides that namespace's class sections and its property rows in every class.
  The scripted behaviour is checked by hand, as the search and switches are today. Rejected: a
  CLI filter that only turns switches off (the page keeps its size).
- **DEC-11** (round 1, Q10 a): **Pitfall findings are not filtered**, neither the TSV nor the
  report's pitfall part: they are evidence about the data, with counts from the scan. Rejected:
  dropping example rows (the counts would no longer match the rows). *Clarified after the PLAN's
  clarity gate (coordinator, 2026-11-01):* collection failures are not filtered either (design P-12).
- **DEC-12** (round 1, Q11 a): **Filters are given on the command line** (and in
  `GeneratorOptions`) only, not in the `--config` file, which holds collection settings and is
  recorded in the profile. Rejected: filters in the config file.
- **DEC-13** (round 1, Q15): **Namespaces only.** Hiding a single class or property (such as
  `brainframe:RelationId`, which shares its namespace with the real classes) is not part of this
  change.

## Open questions

None at the EPIC level. Round 1 is answered (`inputs/qa-round-1.md`, "Round 1 answers").

## Rabbit-holes

- **Recounting statistics.** A filtered output leaves terms out. Every analysed value stays as
  analysed from the unfiltered profile: instance, triple and subject counts, inheritance, class and
  graph aggregates, pitfall counts. The one exception: a property that lost an object class gets
  its value types, dominant type, type purity and untyped share from its remaining values, because
  the excluded class's objects count as untyped (DEC-8). The full list is design §C.
- **Glob creep.** `'r*'` also matches `rdf` and `rdfs`, and so removes `rdfs:label`; that is the
  rule (DEC-6), and the output's note shows it (DEC-9). Do not special-case meta prefixes in globs.
- **The in-page switches.** Keep them to hiding (`hidden`), as today: no new widget, no state
  kept between visits.

## No-gos

- **No change to collection or to `profile.json`** (DEC-1): no new query, no new field in the
  saved profile, no filtering of what is stored.
- **No filter by class, property or term pattern**, only by namespace (DEC-13).
- **No filters in the config file** (DEC-12).
- **No filtering of pitfall findings** (DEC-11).
- **No work in `llm-schema-server`** (the draft MCP change). Its `fingerprint-mcp` takes
  `--exclude-namespace` "with the meaning it has on the generator commands", so it inherits the
  new reach by reference; nothing is written there.
- **No new runtime dependency.**
- **No break of library callers:** `GeneratorOptions.exclude_namespaces` and
  `include_namespaces` keep their names and types; a profile saved by 3.0 or later still loads and
  renders.

---

## What Changes

- **Changed:** `--exclude-namespace` reaches every term of the namespace, not only its classes
  (DEC-5, DEC-7, DEC-8), in the report, SHACL, ShExC, PlantUML and pattern outputs (DEC-2).
- Filter values can be IRI stems and prefix globs (DEC-6). **Changed:** a full namespace IRI is
  now a stem, so it also matches the namespaces under it (`http://example.org/` used to match that
  namespace only; design P-11).
- The outputs name the excluded namespaces and what they hid; an exclude value that hides
  nothing is warned about (DEC-9).
- The report marks excluded namespaces in its table and gets switches for property rows (DEC-10).
- Help texts, `docs/modules/ROOT/pages/representations.adoc` ("Namespace filters"),
  `report.adoc` and `llm-schema.adoc` describe the new reach.
- The report's golden file is regenerated with `make refresh-golden`.
- Version 3.3.0 with its `CHANGELOG.md` entry, and the release (DEC-3).

## Capabilities

### New Capabilities
None.

### Modified Capabilities
- `profile-representations`: "Requirement: Namespace filters" is rewritten from class-level to
  two tiers with term-level exclusion, the matching rule, the notes and the warnings.
- `fingerprint-report`: "Requirement: Navigation, search and filters" gains property-row switches.

## Impact

- **Code:**
  - `fingerprint/domain/`: the matching rule and the term filter (DEC-4, DEC-6, DEC-8).
  - `fingerprint/service_layer/representations.py`: applies the filter once, before the outputs.
  - `fingerprint/service_layer/generators/`: the note line in every output; the report's table,
    caveats and switches.
  - `fingerprint/entrypoints/cli/main.py`, `generate.py`: help texts.
  - `model/fingerprint_views.yaml`, `model/fingerprint_analytics.yaml`, then `make generate-models`.
    Nothing in `model/fingerprint_stats.yaml` (the saved profile) changes.
  - `fingerprint_report_templates/`: the note line, the report's caveats, table, rows and script.
- **Tests:** Gherkin scenarios for both deltas, on a builder-made filter profile (the canonical
  sample has no property-only namespace); unit tests for the matching rule and the filter; the
  report golden file refreshed.
- **Docs:** `representations.adoc`, `report.adoc`, `llm-schema.adoc`, `CHANGELOG.md`.
- **Release:** 3.3.0 (SemVer MINOR), after 3.2.0.
