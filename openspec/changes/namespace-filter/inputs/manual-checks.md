# Manual checks (secondary; filled in by task 1.6 and task 1.10)

The `@manual` scenarios of `fingerprint-report › Navigation, search and filters` and the brainframe
acceptance (design IT-4) are checked by hand on the brainframe data. The checks below are the plan;
each gets a result line (date, browser, pass/fail, notes) when run.

## Data and commands

- Saved profile (the input; no endpoint query is needed to render it):
  `/home/lps/work/repos/rdf-fingerprinter-nsfilter/temp/brainframe-llm-schema/profile.json` (a git-ignored copy of `/home/lps/work/repos/rdf-fingerprinter-llm/temp/brainframe-llm-schema/profile.json`).
- The store it came from: `http://localhost:7879/query`. Use it only if the profile has to be
  collected again:
  `poetry run fingerprint -e http://localhost:7879/query -o /home/lps/work/repos/rdf-fingerprinter-nsfilter/temp/brainframe-namespace-filter/collected`.
- Output folders (git-ignored `temp/`), in the worktree `/home/lps/work/repos/rdf-fingerprinter-nsfilter`:

```sh
P=/home/lps/work/repos/rdf-fingerprinter-nsfilter/temp/brainframe-llm-schema/profile.json
OUT=/home/lps/work/repos/rdf-fingerprinter-nsfilter/temp/brainframe-namespace-filter
mkdir -p "$OUT/all" "$OUT/no-relationid"
for cmd in doc pattern shex; do
  poetry run fingerprint-gen-$cmd "$P" -o "$OUT/all"
  poetry run fingerprint-gen-$cmd "$P" -o "$OUT/no-relationid" --exclude-namespace relationid
done
```

The report is `$OUT/all/main.html` (no filter) and `$OUT/no-relationid/main.html` (filtered).

## Checks

Before each check, note `<T>`, the number of class sections, from the count shown with an empty
search (`<T> shown, 0 hidden` on `$OUT/all/main.html`).

| # | Scenario | Page | Steps | Expected |
|---|---|---|---|---|
| M-1 | Search narrows the classes | `$OUT/all/main.html` | type `risk` | only classes and rows whose names or IRIs contain `risk` stay shown; the count updates |
| M-2 | Namespace switched off | `$OUT/all/main.html` | clear the search; switch off `brainframe` | every `brainframe:` class section and contents entry is hidden; typing `risk` still filters the rest |
| M-3 | Property namespace switched off | `$OUT/all/main.html` | clear the search; switch off `relationid` | every `relationid:` row is hidden in every class; the count stays `<T> shown, 0 hidden`; typing `label` still filters the remaining rows |
| M-4 | Search and a property switch combine | `$OUT/all/main.html` | all switches on; type `2822a123`; then switch off `relationid` | after typing: `brainframe:CloudInfrastructure` alone, with its one `relationid:2822a123-…` row, count `1 shown, <T−1> hidden`; after the switch: no class shown, count `0 shown, <T> hidden` |
| M-5 | Filtered page | `$OUT/no-relationid/main.html` | open; look at the switches, the namespace table and the caveats | no `relationid` switch; `relationid` marked `excluded` in the table; the caveats show `relationid (classes 0, properties 619, values <v>)` for the workspace graph |

## Acceptance measurement (task 1.10, recorded in `brainframe-evidence.md`)

```sh
wc -m "$OUT"/all/pattern-workspace-*.txt "$OUT"/no-relationid/pattern-workspace-*.txt
wc -m "$OUT"/all/shex-workspace-*.shex "$OUT"/no-relationid/shex-workspace-*.shex
wc -m "$OUT"/all/main.html "$OUT"/no-relationid/main.html
grep -c 'relationid:' "$OUT"/no-relationid/pattern-workspace-*.txt   # expected 0
grep '^# excluded namespaces' "$OUT"/no-relationid/pattern-workspace-*.txt
```

Expected: the filtered pattern file is at most 100 000 characters (221 799 before).

## Results

Run 2026-11-01 on branch `feature/namespace-filter` at 247a08e+ (pages regenerated with the commands
above), in HeadlessChrome 156.0.8078.4 (Playwright's chrome-headless-shell) driven by puppeteer-core:
real `input` and `change` events on `#q` and the switch checkboxes, no page errors and no failed
requests. The Claude in Chrome extension was not connected, so no headed browser was used.
T = 52 classes.

| # | Result | Observed |
|---|---|---|
| M-1 | pass | `risk`: `3 shown, 49 hidden`; every shown class matches by name or IRI, or has a matching row |
| M-2 | pass | `brainframe` off: `0 shown, 52 hidden`, no `brainframe:` contents entry visible; with `risk` still `0 shown`. Every class of this graph is `brainframe:`, so "typing still filters the rest" is shown only as nothing reappearing |
| M-3 | pass | `relationid` off: `52 shown, 0 hidden`; 619 `relationid:` rows, 0 visible; with `label`: `46 shown, 6 hidden`, 50 rows visible, all matching `label`, 0 `relationid:` |
| M-4 | pass | `2822a123`: `brainframe:CloudInfrastructure` alone with one `relationid:` row, `1 shown, 51 hidden`; `relationid` off: `0 shown, 52 hidden` |
| M-5 | pass | 14 switches, no `relationid`; the table row `relationid` is marked `excluded`; caveat `graph:workspace: relationid (classes 0, properties 619, values 0)` |

Acceptance (`wc -c` of the regenerated files): pattern workspace 221,799 → 98,587 bytes; ShExC
250,121 → 110,810; report 1,336,056 → 821,816. The filtered pattern file holds no `relationid:`.
