# Q&A record (secondary, never groomed)

Round 1 asked 2026-11-01 through the coordinator. Each question has options, a recommendation (★)
and a one-line trade-off. Answers are recorded below each question when they arrive.

## A. What the filter covers

**Q1. Meta defaults vs named namespaces.** Today `rdf`, `rdfs`, `owl`, `sh` are excluded by default.
If exclusion becomes term-level for them too, `rdf:type`, `rdfs:label`, `rdf:langString`,
`rdf:singletonPropertyOf` vanish from every output by default.
- (a) ★ Two tiers: the meta defaults keep hiding **classes only** (as today); a namespace named
  with `--exclude-namespace` (meta or not) is filtered at **term level**.
- (b) One tier: every excluded namespace, meta defaults included, is filtered at term level.
- Trade-off: (a) adds one rule to explain; (b) silently removes the most used properties from every
  output (a breaking change).

**Q2. Which positions count as "a term of the namespace".**
- ★ Every IRI the outputs write: class, property, edge target class, co-type, `via` link,
  subclass parent, single value IRI (`=v`), glossary entry, prefix declaration; datatypes per Q6.
- Trade-off: complete and simple to state; needs a touch in every generator.

**Q3. An edge whose property is excluded.**
- ★ Dropped everywhere: pattern edge and its `via` entries, ShExC triple constraint, SHACL property
  shape, PlantUML attribute and link (and its count), report row.
- Trade-off: none known; this is the brainframe case.

**Q4. An edge whose property is kept but whose target class is excluded.**
- (a) ★ Drop that class alternative; if no class alternative is left, the edge stays with its value
  kind (`IRI`; SHACL `sh:nodeKind sh:IRI`).
- (b) Drop the whole edge.
- Trade-off: (a) keeps the edge true to the data (shapes still conform); (b) is smaller but hides a
  kept property.

**Q5. Merged co-typed groups and co-types.** A group `A&B` (same instances) where `B` is excluded.
- ★ The group is named by its kept members only (`A`); a group with no kept member is hidden;
  `co C k` notes with an excluded `C` are dropped (today already). A class in a kept namespace
  stays even when all its instances are also typed with an excluded class.
- Trade-off: keeps the class with its statistics; the reader no longer sees the co-typing.

**Q6. Datatypes in an excluded namespace** (a custom datatype namespace, or `--exclude-namespace xsd`).
- (a) ★ Datatypes are never filtered (they describe literals, not the vocabulary).
- (b) Replace with the plain literal kind.
- Trade-off: (a) excluding `xsd` does nothing to datatypes (state it in the docs); (b) loses value
  types for queries and shapes.

## B. Saying what was filtered

**Q7. Do the outputs say what they left out?**
- (a) ★ One comment line per text output naming the excluded namespaces and how many classes and
  properties each hid, e.g. `# excluded namespaces: relationid (0 classes, 619 properties)` (Turtle
  and ShExC `#`, PlantUML `'`); the report caveats extend today's hidden-namespace list with property
  counts. The meta defaults are not listed unless they hid something.
- (b) Silent.
- Trade-off: ~60 chars per file vs a reader or LLM taking the missing terms for absent data.

**Q8. A known name that hides nothing** (today `--exclude-namespace relationid` hid nothing, silently).
- ★ Warn: `--exclude-namespace <name>: no term in this namespace; ignored`, as for unknown names.
- Trade-off: one more log line; catches typos of the right prefix in the wrong profile.

## C. The report

**Q9. Report vs CLI filter vs in-page switches.**
- (a) ★ The CLI filter **removes** the namespace's terms from the report (class sections, property
  rows, TOC); the namespace table still lists every prefix and marks the excluded ones; the in-page
  switches stay as they are (class sections only).
- (b) As (a), and the switches also hide property rows by prefix and exist for every namespace in use.
- (c) The CLI filter only turns switches off by default; content stays in the HTML.
- Trade-off: (a) one rule for all outputs, no new JavaScript; (b) adds scripted behaviour checked by
  hand; (c) leaves the 1.3 MB brainframe page as large and breaks "same filter everywhere".

## D. Pitfalls

**Q10. Is the pitfalls TSV (and the report's pitfall examples) filtered?**
- (a) ★ No: findings are data-quality evidence with counts from the scan; filtering would hide them.
- (b) Drop example rows whose subject, property or value is excluded.
- Trade-off: (a) the TSV may still show `relationid:` IRIs; (b) the counts then disagree with the rows.

## E. How the filter is given

**Q11. Config file.**
- (a) ★ CLI only, repeatable flags, as today (generator options are CLI-only).
- (b) Add `exclude_namespaces`/`include_namespaces` to the `--config` JSON.
- Trade-off: (a) long command lines for many namespaces; (b) mixes render options into the
  collection-settings file, which is recorded in the profile.

**Q12. Precedence.**
- ★ Unchanged: include wins over exclude; `--include-namespace owl` brings back the classes of a
  meta default.
- Trade-off: none known.

**Q13. Matching.**
- (a) ★ Exact namespace only, by prefix or full namespace IRI (as today).
- (b) Also an IRI stem (every namespace under `https://my.brainframe.com/#/knowledge/`) or a prefix glob.
- Trade-off: (a) brainframe's ~10 instance namespaces need ~10 flags; (b) a matching rule to
  specify and test.

**Q14. Option names and SemVer.**
- (a) ★ Keep `--exclude-namespace`/`--include-namespace` with the term-level meaning; new help text;
  3.3.0 MINOR with a "Changed" CHANGELOG entry (the old behaviour is the defect being fixed).
- (b) New options (e.g. `--drop-namespace`) beside the class-only ones.
- Trade-off: (a) outputs of existing `--exclude-namespace` calls shrink; (b) two near-identical
  options to explain.

## F. Scope

**Q15. Hiding single classes** such as `brainframe:RelationId` (same namespace as the real classes).
- ★ No-go for this change (namespace filter only). `--min-instances` does not help (1765 instances).
- Trade-off: the 1765 statement nodes still get a block.

**Q16. Appetite.** ★ SMALL with the recommended answers (one requirement of one capability, applied
in each generator, existing filter structure reused). It grows to MEDIUM with Q9 (b), Q11 (b) or
Q13 (b).

## G. What the change must prove (test-scenario interview)

**Q17. Confirm the scenarios** (★ these, on a builder-derived fixture from the canonical sample
profile, since the sample has no singleton-property namespace):
1. A property namespace excluded: no output writes its properties, `via` links, glossary entries or
   prefix; its classes' other properties stay.
2. Target class excluded, property kept: the edge stays with `IRI` (per Q4).
3. Group `A&B` with `B` excluded is written as `A` (per Q5).
4. Meta defaults still hide classes only: `rdfs:label` stays with no option (per Q1).
5. `--exclude-namespace rdfs` drops `rdfs:label` everywhere.
6. Include wins over exclude.
7. A known name that hides nothing warns (per Q8).
8. Each output carries the "excluded namespaces" line (per Q7).
9. The profile file is unchanged and no endpoint is queried (regeneration from `profile.json`).
10. Acceptance (not a test): the brainframe pattern file shrinks from 221 799 to about 99 000 chars
    with `--exclude-namespace relationid`, recorded in `inputs/brainframe-evidence.md`.

## Round 1 answers (developer, 2026-11-01, relayed by the coordinator; verbatim)

> - Q1: (a) two tiers — meta defaults keep hiding classes only; a namespace named with --exclude-namespace is filtered at term level.
> - Q4: (a) keep the edge, drop the excluded target alternative; none left → IRI (sh:nodeKind sh:IRI).
> - Q9: (b) the CLI filter removes excluded terms from the report, the namespace table lists every prefix and marks the excluded ones, AND new in-page switches hide property rows per namespace in use. (Developer chose this knowing it adds JS checked by hand.)
> - Q13: (b) also an IRI stem / prefix glob, e.g. `--exclude-namespace 'https://my.brainframe.com/#/knowledge/'` or `'relation*'` covering many namespaces. Specify the matching rule precisely (what counts as a stem vs exact IRI, glob syntax on prefixes, interaction with include precedence and the "unknown name"/"hides nothing" warnings); recommend a rule and state it as a DEC.
> - All other questions: take your ★ recommendations (Q2, Q3, Q5, Q6a, Q7a, Q8, Q10a, Q11a, Q12, Q14a, Q15 no-go). Q17 scenarios as listed (adapted to the answers: add glob/stem and report-switch scenarios).
> - Q16 appetite: MEDIUM (Q9b + Q13b).
>
> The branch will be rebased onto master after PR #45 (3.2.0) merges; nothing in the PLAN should depend on unreleased behaviour beyond what feature/llm-schema-tools already holds. The tasks must end with a 3.3.0 release task mirroring llm-schema-tools 1.15 (CHANGELOG "Changed" entry for the new --exclude-namespace reach) and a gate task (check-all, test-e2e, check-mutation ≥ 0.950, brainframe acceptance measurement).

### Where each answer landed

| Question | Answer | Landed in |
|---|---|---|
| Q1 | (a) two tiers | EPIC DEC-7 |
| Q2, Q3, Q4 (a), Q5, Q6 (a) | ★, Q4 (a) | EPIC DEC-8 |
| Q7 (a), Q8 | ★ | EPIC DEC-9 |
| Q9 | (b) | EPIC DEC-10 |
| Q10 | (a) | EPIC DEC-11 |
| Q11 | (a) | EPIC DEC-12 |
| Q12, Q13 (b) | ★, (b) | EPIC DEC-6 (the matching rule, recommended by the planner as asked) |
| Q14 | (a) | EPIC DEC-5 |
| Q15 | no-go | EPIC DEC-13, No-gos |
| Q16 | MEDIUM | EPIC Appetite |
| Q17 | as listed, plus glob/stem and switch scenarios | spec deltas; `tests/features/` |
