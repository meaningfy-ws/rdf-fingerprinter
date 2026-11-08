# Seed: the developer's request (secondary, never groomed)

Received 2026-11-01, relayed by the coordinator. Verbatim:

> request for a correction. Not sure what the current "namespaces" filter is for, but it is
> definitely not filtering out items by their prefix (that is what I meant by namespace). I shall be
> able to filter out some prefixes/namespaces (e.g. relationid - on\off), and also I shall be able to
> use this sort of filtering in the output artefacts (e.g. in the shacls, shex, puml, that .txt for
> llms etc), fix this and add new capability

## Already decided by the developer (relayed by the coordinator, 2026-11-01)

- Ships as **3.3.0**, separately from 3.2.0 (`llm-schema-tools`). The release is part of this
  change, as in `llm-schema-tools` task 1.15.
- Filtering applies at **output time only**. `profile.json` keeps everything; every output (report
  and profile document, SHACL, ShExC, PlantUML, pattern `.txt`, the pitfalls TSV if relevant) leaves
  the namespace's terms out. Toggling a prefix on or off means regenerating from the saved profile,
  with no endpoint query.

## What exists today (verified in code and spec, worktree at `fda27d8`)

- `openspec/specs/profile-representations/spec.md`, "Requirement: Namespace filters": every
  generator and the report leave out only the **classes** of the excluded namespaces. The set starts
  from the meta namespaces `rdf`, `rdfs`, `owl`, `sh`; `--exclude-namespace` adds, `--include-namespace`
  removes, include wins; prefix or IRI; unknown names warn and are ignored.
- `fingerprint/service_layer/generators/generator.py`: `META_NAMESPACES`, `excluded_namespaces()`,
  `Generator.shown()` (class test only), `Generator.hidden` (namespace → hidden classes, listed in
  the report caveats via `HiddenNamespace`).
- `fingerprint/domain/patterns.py`: `_Builder._shown()` filters class groups and co-type notes only.
  Properties, edge targets, `via` links, value IRIs, glossary entries and prefixes of an excluded
  namespace are still written. An edge to an excluded class still names that class (ShExC writes it
  as `IRI` since `f2e5ef8`).
- `fingerprint/service_layer/generators/plantuml.py`: links to hidden classes are not drawn or
  counted; hidden parents are left out; property attributes are not filtered.
- `fingerprint/service_layer/generators/pitfalls.py`: no filtering at all.
- `fingerprint_report_templates/fingerprint_report/templates/main.html`: one in-page switch per
  namespace **with classes** (`data-switch`), hiding class sections only.
- Generator options are CLI-only (`fingerprint` and `fingerprint-gen-*`); `--config` holds
  collection settings only.

So `--exclude-namespace relationid` on the brainframe profile hides nothing: no class lives in
`relationid`, and no warning is logged because the prefix is known.
