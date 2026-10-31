# Seed: developer remarks after the brainframe application test (2026-10-31)

Seed input; keep it as written, do not edit or tidy it. It feeds the EPIC `readable-representations` (`proposal.md`, not
yet written).

## The test

- Data: `../brainframe-mcp/data/` — `workspace-…-meaningfy.rdf` (37 MB, 74,007 triples) and
  `workspace-brainframe-root-ontolofy.owl` (5,335 triples), each loaded into its own named graph in a
  dedicated Oxigraph 0.5.13 (port 7879).
- Run: `fingerprint --depth links --precision exact --completeness --graph-stats --format doc
  --format puml --format shacl`; exit 0, no failures. Outputs in `temp/brainframe-fingerprint/` (git-ignored).
- Timing: 18.8 s wall, 172 MB max RSS. Collection 3.3 s (232 queries, 58 classes); rendering 13.6 s,
  of which `main.html` alone 10.8 s.

## Remarks (verbatim)

> * add a new requrement, always have prefixes defined for each URI, nameaspcae so that when it is
>   rendered in dcuments and diagrams,
> * the html template looks horrible, put a simple modern design to it, and increase its usability
>   (feel free to use an ui/ux designing skill to decide how to make it better), increase usability
>   and readability (including having no long URI, always all uris must be in short form:
>   prefix:localsegment ); there was some logic somewhere to detect the namespaces from prefix.cc,
>   and then to generate automaticaly new prefixes when none avalable (including subnamespace
>   logics, based on additional segments or subdomains)
> * We shall have a mechanism to filter out groups of classes, per prefix/namespace.
> * the profile.htm and the main.html do the same job (if they belong to different generators,
>   merge and improve usability with toc, search and filet, all in a static html)
> * the logic of generating shapes namespace, shall be borrowed from the model2owl (if you can reach
>   it), otherwise adopt a robust simple uri policy when generating shack shapes.
> * the diagram-workspace, is unreadable, an dunusable. What can be done to incerase its
>   readability/usability? (any way of breaking down per ... something, like simple modularisation
>   approach)

## Remarks restated, with what the test showed

| # | Remark | Evidence in the test output / codebase |
|---|---|---|
| R1 | **Every IRI gets a prefix.** Each namespace seen in the data SHALL have a prefix, so documents and diagrams never show a full IRI. | No prefix exists for `https://ontology.brainframe.com/2016/04/brainframe#` or `https://my.brainframe.com/#/knowledge/…`; `diagram-workspace-*.puml` contains 1,382 `https://` occurrences. Prefixes today come only from the static `fingerprint_report_templates/fingerprint_report/templates/prefixes.json` (`load_prefixes`, `fingerprint/adapters/template_renderer.py:26`). |
| R2 | **Prefix discovery and generation.** Resolve namespaces from prefix.cc; when none is known, generate one, including sub-namespaces (extra path segments, subdomains). | Earlier work exists only in git history: commit `51b68a4` (2020, "add namespace inventory fom prefix.cc", `tests/poc/prefixes.json`, an `ns1:`/`ns2:` numbering, `invert_dict` and `replace_strings_in_tabular` helpers). It is not in the current code. |
| R3 | **A modern, usable HTML report.** Simple modern design; short `prefix:local` forms everywhere; use a UI/UX design skill to decide the layout. | `main.html` is 1.4 MB and slow to render (10.8 s). |
| R4 | **One HTML document.** `profile.html` (profile-document generator, `--format doc`) and `main.html` (the report) do the same job; merge them into one static HTML with a table of contents, search and filters. | Both are written on every `--format doc` run (636 KB + 1.4 MB). |
| R5 | **Filter class groups by prefix/namespace.** Classes can be filtered out by namespace (in the HTML at least, and possibly at collection time; still to decide). | The workspace graph has 51 classes and 1,212 predicate partitions across several vocabularies. |
| R6 | **A SHACL shape IRI policy.** Borrow model2owl's shape-naming logic if it can be reached; otherwise adopt a simple, robust IRI policy. | Shapes today are `<urn:fingerprint:shape:https%3A%2F%2Fontology.brainframe.com%2F2016%2F04%2Fbrainframe%23AccountingSystem>`: a percent-encoded URN, impossible to read and with no prefix. model2owl is not checked out next to this repo (`~/work/repos`); it would have to be fetched (OP-TED / meaningfy-ws on GitHub). |
| R7 | **A readable diagram.** `diagram-workspace-*.puml` (158 KB, one diagram for 51 classes) is unusable; break it down, e.g. one diagram per namespace or per class neighbourhood, plus an overview. | One `.puml` per graph, with no modularisation. |

## Side findings (not remarks, noticed in the same run)

- The empty default graph reports `declared_subclass_edges: 318`; the count seems to be taken across
  all graphs, not per graph. Possible bug, cause not checked.
- 8,785 of 12,926 workspace subjects are untyped; the report could make this more prominent.
- Empty graphs still produce `shapes-default.ttl` / `diagram-default.puml` files with no content.

## Open questions for shaping

1. R2: should the prefix.cc lookup be online at run time, or a vendored snapshot refreshed by a make target?
2. R5: filter only in the HTML (client side), or also an `--exclude-namespace` option that skips collection?
3. R4: keep `--format doc` as a separate artifact, or is the merged report the only HTML?
4. R6: fetch model2owl to read its naming convention, or decide our own policy now?
5. R7: which way to modularise: per namespace, per class neighbourhood (ego diagrams), or both?
