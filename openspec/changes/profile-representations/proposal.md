# EPIC: Represent the fingerprint profile as SHACL, PlantUML and an application-profile document

## Appetite

LARGE (developer, 2026-10-31): a generator framework, three formats and a saved-profile file, in
one release (2.1.0). Depends on `harden-fingerprinter` (archived): it renders that EPIC's profile
model (its DEC-7, DEC-8) through eds4jinja2 (its DEC-6).

Seeds: `inputs/shaping-2026-10-31.md` (brief, Q&A, agent calls),
`../archive/2026-10-31-harden-fingerprinter/inputs/prior-art.md`.

## Why

A fingerprint is an application profile inferred from the data, but 2.0 shows it only as a
statistics page, and every view of it costs a full collection against the endpoint. People need the
profile in the forms application profiles are published in: shapes to validate data with, a class
diagram to grasp the model, and a readable specification document in the style of the SEMIC / EU
application profiles. Each is a function of the profile, so none should query the endpoint again.

## Solution outline

**One profile, saved once, rendered by many generators.**

1. **The profile is saved.** `fingerprint` writes the raw profile run to `profile.json` next to the
   report. Every generator reads that file, as LinkML's `gen-*` commands read a schema file;
   generators re-derive the analytics on load, so a different acceptance threshold needs no new
   collection.
2. **Generators mirror LinkML's architecture.** A `Generator` base class over the profile, modelled
   on `linkml.utils.generator.Generator`: one `serialize()` entry point, visit hooks per level
   (graph, class, property) that a subclass may use, shared command-line arguments, and one
   generator class and one command per format, named after LinkML's `gen-*` but never clashing
   with LinkML's own scripts, which users may have installed (the PLAN fixes the names). `fingerprint` can also run chosen generators straight after collecting.
3. **eds4jinja2 is the rendering engine.** Each format is an eds4jinja2 template package beside
   today's `fingerprint_report/` (config + templates), fed the analytics profile, issuing no queries.
   A user can point a generator at their own template package, as the report allows today.
4. **Three formats**, each per the prior art the developer named (SEMIC / EU profiles, SHACL Play):

| Generator | Output | Content |
|---|---|---|
| SHACL | one Turtle file per graph | open `sh:NodeShape` per class (`sh:targetClass`); `sh:PropertyShape` per property: `sh:path`, `sh:minCount`/`sh:maxCount` from the accepted cardinality label, `sh:datatype` / `sh:class` / `sh:nodeKind` from the value types (`sh:or` when mixed); properties below the acceptance threshold at `sh:severity sh:Info`; statistics (confidence, observed/total instances, first-N) as annotations |
| PlantUML | one `.puml` source per graph | classes with datatype properties as attributes and object properties as associations, with multiplicities; generalisations from declared (solid) and implied (dashed) parents; own and refined properties only |
| Profile document | one HTML file | overview and provenance (endpoint, date, settings); namespaces; per graph: the diagram source and a section per class (instances, parents, a property table: property, value type, cardinality, usage); caveats (first-N classes, failures) |

## Key decisions

- **DEC-1**: Every representation is a function of the saved profile; no generator queries the
  endpoint — reason: collection is the expensive step; rejected: collecting per format.
- **DEC-2**: The saved profile is the raw run (`ProfileRun`, the generated LinkML model) as JSON;
  generators derive the analytics on load — reason: the analytics are deterministic and the
  threshold stays adjustable; rejected: saving the analytics.
- **DEC-3**: Mirror LinkML's generator architecture over our profile (base class, `serialize()`,
  visit hooks, one command per format) — developer, 2026-10-31; rejected: converting the profile to
  a LinkML schema and running LinkML's own generators (statistics would survive only as
  annotations, its PlantUML rendering calls a remote server).
- **DEC-4**: eds4jinja2 renders every format, SHACL included (developer, 2026-10-31). Templates that
  emit Turtle or PlantUML escape IRIs and literals through dedicated filters, and SHACL output is
  parsed before it is written; an invalid file is an error, never a silent output — reason: one
  engine, custom templates for every format; rejected: building SHACL as an rdflib graph.
- **DEC-5**: SHACL shapes are open (no `sh:closed`); strength follows the acceptance threshold;
  a shape repeats the properties its class inherits, so validation does not rely on inference
  (developer, 2026-10-31).
- **DEC-6**: PlantUML is written as source only; the document embeds the source, no rendering, no
  Java, no network (developer, 2026-10-31).
- **DEC-7**: Layout: SHACL and PlantUML one file per graph, the document one file with a chapter
  per graph (developer, 2026-10-31).
- **DEC-8**: Today's statistics report, its CLI usage and the 1.x library function keep working
  unchanged; the new outputs are additions.
- **DEC-9**: Meaningfy standard in full, as harden DEC-7: generators live in the service layer and
  adapters over the domain profile (no rendering in `domain`); TDD with golden files per format;
  SHACL checked by a SHACL engine in tests, PlantUML checked for structure.

## Rabbit-holes

- SHACL/ShEx inference beyond the profile: `sh:or` minimisation, supertype pruning, `sh:in` from
  enumeration candidates — only what the analytics already state.
- Diagram layout for hundreds of classes — per-graph files are the only split; no layout tuning.
- eds4jinja2 renders one template per run: per-graph files must not need changes to eds4jinja2
  itself; the PLAN finds the way within its current API.
- Turtle and PlantUML escaping is easy to get almost right: test it with hostile IRIs and literals.

## No-gos

- No endpoint queries from any generator.
- No VoID, JSON/YAML-as-representation, ShEx, OWL or LLM schema cards — further generators, for
  `llm-schema-tools` or a later EPIC.
- No rendered diagrams (SVG/PNG), no PlantUML server, no Java dependency.
- No change to today's statistics report or to `generate_endpoint_fingerprint_report`.
- No editing round-trip: representations are outputs, never read back.
- No new test data: the existing `tests/test_data` and Oxigraph fixtures only (developer, 2026-10-31).

---

## What Changes

- `fingerprint` writes `profile.json` beside the report, and accepts the formats to render after
  collecting.
- New commands, one per format, that read a `profile.json` and write the representation.
- A generator framework (base class, shared arguments) and three generators.
- Three new eds4jinja2 template packages (SHACL, PlantUML, profile document) shipped in the wheel.
- Docs: a page per format; CHANGELOG 2.1.0.

## Capabilities

### New Capabilities
- `profile-representations`: the saved profile file, the generator framework, and the SHACL,
  PlantUML and profile-document representations.

### Modified Capabilities
- `fingerprint-report`: the command also writes the profile file and may render chosen formats
  after collecting.

## Impact

- Code: new generator modules (service layer + adapters), CLI entry points in `pyproject.toml`
  (`[project.scripts]`), `fingerprint_report_templates/` gains three packages.
- Dependencies: a SHACL engine (pySHACL) for tests only; no new runtime dependency expected.
- No change to collection, the endpoint queries or the profile model's meaning.
