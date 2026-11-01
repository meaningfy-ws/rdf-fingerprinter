# Brainframe: ROBOT quality report

**Run:** 2026-11-01, ROBOT v1.9.10 (`obolibrary/robot:v1.9.10` in Docker, `-Xmx8G`).
**Inputs:** `../../../../brainframe-mcp/data/`:

| Input | File | Triples |
|---|---|---|
| Ontology | `workspace-brainframe-root-ontolofy.owl` | 5,335 |
| Data | `workspace-ce705e50b88704fd413497b9af4ff1cf-meaningfy.rdf` | 74,007 |
| Merged | `robot merge` of the two | — |

**Commands** (for each input; the merged runs use `robot merge -i ONT -i DATA` and chain the command):
- `robot report --fail-on none --output <x>-report.tsv` (and `--format html`): ROBOT's default report profile;
- `robot validate-profile --profile DL`;
- `robot reason --reasoner HermiT` (and `ELK`).

## Verdict

The ontology is **logically sound**: consistent, with no unsatisfiable class, alone and together with
the data. It is **not OWL 2 DL**, and its **labelling and metadata are poor**. The data is consistent
with the ontology. Most of the data's findings are missing, duplicate or placeholder labels, plus a
relation pattern that OWL cannot read (1,765 triples).

## Results

| Check | Ontology | Data alone | Ontology + data |
|---|---|---|---|
| `report`, ERROR | 309 | 12,313 | 12,633 |
| `report`, WARN | 531 | 8,830 | 9,339 |
| `report`, INFO | 3 | 0 | 3 |
| OWL 2 DL profile | not in profile (3 violations) | not in profile (68,186 violations, mostly terms undeclared in the data file alone) | not in profile |
| HermiT / ELK | consistent; no unsatisfiable class | — | consistent; no unsatisfiable class; **1,765 triples not parsed as OWL** |

The data file carries no declarations, so its standalone profile result mostly reflects checking it in
isolation. Use the merged column for the data.

## Ontology, by rule

| Level | Rule | Count | What it is |
|---|---|---|---|
| ERROR | `missing_label` | 301 | 293 brainframe terms, 2 `prv:` terms, `skos:altLabel`, `foaf:mbox` with no `rdfs:label` |
| ERROR | `duplicate_label` | 4 | `PrivacyStandard` and `QualityStandard` are both "Privacy standard"@en (likely copy-paste); `blueprint/BrainframeId_Bin` and `blueprint/ContextId_Bin` are both "Bin"@en |
| ERROR | `missing_ontology_title` / `_license` / `_description` | 3 | `https://ontology.brainframe.com/2016/04/brainframe` has none of the three |
| ERROR | `illegal_use_of_built_in_vocabulary` | 1 | `brainframe:singletonPropertyOf rdfs:subPropertyOf rdf:type` |
| WARN | `missing_definition` | 529 | ROBOT looks for `IAO:0000115` (an OBO convention); not meaningful for brainframe, and should be switched off in a brainframe profile |
| WARN | `annotation_whitespace` | 2 | leading or trailing spaces |
| INFO | `missing_superclass` | 3 | three root classes |

**OWL 2 DL violations (all 3):**
- `brainframe:enableLanguage` is used as an annotation property without being declared;
- `brainframe:label_translated` is used as an annotation property without being declared (its values are JSON strings);
- reserved vocabulary: `brainframe:singletonPropertyOf` is a sub-property of `rdf:type`.

## Data (ontology + data), by rule

| Level | Rule | Count | What it is |
|---|---|---|---|
| ERROR | `missing_label` | 8,849 | 6,148 `SOARequirementLinkControl/…`, 1,374 `SOARequirement/…`, 669 `QuestionRisk/…`, 180 `DocumentPropertyFormQuestion/…` |
| ERROR | `duplicate_label` | 3,322 | placeholder labels: "…"@en (1,073), "…" (537); HTML template text (39 copies of one template); system messages ("Added link to: …") |
| ERROR | `label_formatting` | 133 | labels containing line breaks or markup |
| ERROR | `multiple_labels` | 6 | terms with several labels in one language |
| WARN | `missing_definition` | 8,785 | as above: not meaningful here |
| WARN | `annotation_whitespace` | 45 | leading or trailing spaces |

**Not readable as OWL:** 1,765 triples `<…/RelationId/<uuid>> rdf:singletonPropertyOf brainframe:isRelatedTo`.
They use the RDF singleton-property pattern, where each relation instance is its own predicate.
The reasoner ignores them.

## Files

| File | Content |
|---|---|
| `ontology-report.{tsv,html}`, `data-report.{tsv,html}`, `merged-report.tsv` | every finding: `Level, Rule Name, Subject, Property, Value` |
| `*-profile-DL.txt` | the OWL 2 DL profile violations |
| `*-reason-hermit.log` | reasoner output (the unparsed triples) |
| `ontology-reasoned.owl`, `merged-reasoned-{elk,hermit}.owl` | the input plus inferred axioms (large; safe to delete) |

## Reproduce

```bash
D=../brainframe-mcp/data Q=temp/brainframe-fingerprint/quality
R="docker run --rm -u $(id -u):$(id -g) -e ROBOT_JAVA_ARGS=-Xmx8G -v $D:/in:ro -v $PWD/$Q:/out obolibrary/robot:v1.9.10 robot"
$R report --input /in/workspace-brainframe-root-ontolofy.owl --fail-on none --output /out/ontology-report.tsv
$R merge --input /in/workspace-brainframe-root-ontolofy.owl --input /in/workspace-…-meaningfy.rdf \
   reason --reasoner HermiT --output /out/merged-reasoned-hermit.owl
```

The OOPS!-derived SPARQL checks, and the modelling analysis, are in `modelling-analysis.md`.
