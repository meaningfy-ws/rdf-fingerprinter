# Seeds and Q&A, round 1 (2026-11-02) — secondary, never groomed

## Seed (developer, verbatim)

> now lets extend this epic slightly, I want the schema files be split into two: one only with
> structural templates, in an .md (and in an index .json or .csv (so that tools can simply search
> and filetr with tools)); and a second one with the glossary similarely in .md and in indexed
> .json or .csv (to allow simple and quick filters and search with tools)
>
> can you do that? so basically we abandon the idea of a single .txt file; note that prefix
> definition must be in both ... so then, lets put those prefixes (with stats) into another file,
> so now we will have in fact 3 files one .md fith prefixes, and then two pairs of files with
> distinct glossary definitions and structureal patterns
>
> what do you think? this will allow better cntrol on what schema prts to get

"This epic" was `llm-schema-tools`, already released as 3.2.0. Agent's proposal: archive it and
open a follow-up change; the index rows carry the facts (not pointers into the .md); CSV over JSON.

## Answers

- **R1-1 Format and release** (developer): "yes, go with csv and 3.x+1.y, archive first". Read as:
  CSV indexes; release 4.0.0 (MAJOR, the `.txt` output is dropped); archive `llm-schema-tools`
  first (done: `archive/2026-11-02-llm-schema-tools`).
- **R1-2 llm-schema-server** (developer): "llm schema server is likely to be closed not sure what
  is it about". Not touched by this change.
- **R1-3 Prefix statistics**: per prefix, classes, properties, instances of its classes, triples of
  its properties (option "Terms + volume").
- **R1-4 Edge CSV**: typed columns, one row per edge (option "Typed columns").
- **R1-5 Glossary CSV** (developer, verbatim): "for each uri, and a row per language, we will have
  several columns, one column with pref label, then anotehr colun with multiple alt labels
  separated by "semicolon" ;, and the definition of the uri; and then additional notes
  concatenated with semicolon."
- **R1-6 CLI**: one command writes all files (option "One command").

## Round 2 answers (follow-ups to R1-5)

R1-5 needs alt labels and notes, which the 3.2 collection does not keep (one label and one
description per language, `skos:altLabel` only as a fallback).

- **R2-1 Definition vs notes**: definition = first of `skos:definition`, `rdfs:comment`,
  `dcterms:description`, one value per language. Notes = every value of `skos:scopeNote`,
  `skos:note`, `skos:example`, `skos:editorialNote`, `skos:historyNote`, `skos:changeNote`, plus
  the `rdfs:comment` / `dcterms:description` values not used as the definition.
- **R2-2 Alt labels**: `skos:altLabel` and `skosxl:altLabel`/`skosxl:literalForm`. The pref label
  comes only from the pref predicates and is empty when there is none; the `.md` line falls back
  to the first alt label.
- **R2-3 Glossary .md**: compact, one language per term as in 3.2, plus `alt: a | b`; notes only in
  the CSV.
- **R2-4 Separator**: multi-valued cells are joined with ` | ` (developer chose it over `; `).

## Round 3 (2026-11-02, after the PLAN gate, before implementation)

- **R3-1 Term type in the glossary** (developer, verbatim): "oh we shall also indicate in teh
  glossary the term type (class data property or object propperty, but encoded minimally e.g. C,
  dP, oP)". Recorded as DEC-10. The agent added `D` (datatype) and `P` (no objects collected) for
  the two cases the three codes leave out, and `dP/oP` for a property with both kinds of object.

## Round 4 (2026-11-02, during implementation)

- **R4-1 Version** (developer, verbatim): "we do not 4.x.x, we stay on 3.x.x". DEC-1 amended: the
  release is 3.4.0, its breaking output change marked **BREAKING** in the CHANGELOG.
- **R4-2 Gate** (developer): "of course with checks and QA (not mutmut however, we want a
  relatively quick implementation and release)", then "lets do check all quick only and a
  mandatory requirement and only ocasionally mutmut and hypothesis". The gate of this change is
  `make check-all` (now the fast gate, without Hypothesis and coverage), e2e, spec validation and
  a code review; `make check-all-deep` and `make check-mutation` are occasional.
