# RDF Fingerprinter

[![PyPI version](https://img.shields.io/pypi/v/rdf-fingerprinter?color=teal&label=pypi)](https://pypi.org/project/rdf-fingerprinter/)
[![Python versions](https://img.shields.io/pypi/pyversions/rdf-fingerprinter)](https://pypi.org/project/rdf-fingerprinter/)
[![Downloads](https://static.pepy.tech/badge/rdf-fingerprinter/month)](https://pepy.tech/project/rdf-fingerprinter)
[![License](https://img.shields.io/pypi/l/rdf-fingerprinter?color=green)](https://github.com/meaningfy-ws/rdf-fingerprinter/blob/master/LICENSE)
[![CI](https://github.com/meaningfy-ws/rdf-fingerprinter/actions/workflows/ci.yml/badge.svg)](https://github.com/meaningfy-ws/rdf-fingerprinter/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/meaningfy-ws/rdf-fingerprinter/branch/master/graph/badge.svg)](https://codecov.io/gh/meaningfy-ws/rdf-fingerprinter)
[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://meaningfy-ws.github.io/rdf-fingerprinter/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

**See the structure of an RDF dataset at a glance.** RDF Fingerprinter profiles a SPARQL endpoint
and reconstructs the data shapes its data actually follow — its *application profile* — as an HTML
report, SHACL, ShEx, PlantUML diagrams and compact schemas for language models.

![One read-only pass over a SPARQL endpoint saves profile.json once; from it come outputs for people (HTML report, PlantUML diagrams, pitfalls), for agents (query-writing schema, glossary, ShExC) and for machines (JSON profile, SHACL, CSV tables, pitfall TSV, exit status)](https://raw.githubusercontent.com/meaningfy-ws/rdf-fingerprinter/master/docs/modules/ROOT/images/outputs.png)

An [application profile](https://en.wikipedia.org/wiki/Application_profile) is the set of
[data shapes](https://www.w3.org/2014/data-shapes/wiki/Main_Page) that constrain how data are
instantiated for a purpose, and so can validate them. *Fingerprinting* infers that profile from the
data: for each class in the dataset, it reconstructs the shape its instances share. Compare two
fingerprints to spot how two datasets differ in structure.

**Who it's for:** data stewards, modellers and reviewers who need to know what a dataset really
contains; language models that write SPARQL; and validators, pipelines and CI jobs that check data
against its profile.

**Documentation:** <https://meaningfy-ws.github.io/rdf-fingerprinter/> ·
**The story behind 3.5:** [A fingerprint you can trust on a large graph](https://meaningfy.lu/rdf-fingerprinter-3-5/)

## Features

- **Profiles any SPARQL 1.1 endpoint, read-only**, class by class with bounded queries, and says how
  precise every number is (exact, or first N of M when a class is too big).
- **Writes** an HTML report and a saved `profile.json`, from which SHACL shapes, enriched ShExC,
  PlantUML diagrams and a pattern schema for language models are generated without querying again.
- **Scans for modelling pitfalls** (`--pitfalls`, 28 SPARQL checks, most from the OOPS! catalogue)
  and fails a CI job on them (`--fail-on`).
- **Recognises reifications** (`rdf:Statement`, singleton properties, `owl:Axiom`, PROV, Wikibase,
  RDF 1.2 triple terms, …) and shows the relations they stand for.

How it compares with SHACL Play, sheXer, void-generator, QSE and others:
[Comparison](https://meaningfy-ws.github.io/rdf-fingerprinter/rdf-fingerprinter/comparison.html).

## Why you can trust the results

RDF Fingerprinter began in 2024 as report templates and about sixty lines of Python. On large
graphs its queries timed out, and the run still reported success. It has since been rewritten around
one idea: **a fingerprint you can trust on a large graph.**

- **It never writes to your store.** It sends only `SELECT` and `ASK` queries.
- **Every number says how precise it is:** exact, or the first N of M instances when a class is too
  big. A failed measurement is recorded, not hidden: a run neither stops at the first timeout nor
  hides it.
- **The facts are collected once; the judgements can be redone.** Raw counts are saved in
  `profile.json`, and every output is regenerated from it offline, with different thresholds or
  filters, without touching the endpoint again.
- **Generated SHACL is graded by confidence:** `sh:Violation`, `sh:Warning` or `sh:Info`, according
  to how strongly the data support each constraint.
- **Exit codes tell automation what happened:** 0 all measured, 1 written with failures, 2–5 usage
  error, endpoint unreachable, unexpected error, or pitfalls at the `--fail-on` level.

It is built and tested like the infrastructure it is meant to be: 1,300+ unit tests, 191 end-to-end
tests against a real triple store, property-based tests, mutation testing after every release
(score 0.969 at 3.5), layer boundaries enforced by import-linter, and
[12 recorded architecture decisions](https://meaningfy-ws.github.io/rdf-fingerprinter/rdf-fingerprinter/decisions.html).

## Installation

```shell
pip install rdf-fingerprinter
```

Requires Python 3.12 or later (tested on 3.12, 3.13 and 3.14).

**Upgrading from 0.3 or 1.x?** The library was rewritten in 2.0 and has grown since. Read the
breaking changes per release in the
[CHANGELOG](https://github.com/meaningfy-ws/rdf-fingerprinter/blob/master/CHANGELOG.md) and the
[Getting Started](https://meaningfy-ws.github.io/rdf-fingerprinter/rdf-fingerprinter/getting-started.html)
upgrade notes.

## Quick start

Point `fingerprint` at a SPARQL endpoint and an output folder (output folders must exist):

```shell
mkdir -p out shapes diagrams
fingerprint -e https://my.sparql.endpoint/query -o out
```

It writes `out/main.html` (the report) and `out/profile.json` (the raw profile). Generate other
representations from the saved profile, without querying the endpoint again:

```shell
fingerprint-gen-shacl out/profile.json -o shapes/
fingerprint-gen-puml  out/profile.json -o diagrams/
```

Run `fingerprint --help` for every option (depth, precision, graphs, timeouts, pitfalls, …), and
see [Getting Started](https://meaningfy-ws.github.io/rdf-fingerprinter/rdf-fingerprinter/getting-started.html)
for exit codes and configuration files. To use the library from Python, see the
[API Reference](https://meaningfy-ws.github.io/rdf-fingerprinter/rdf-fingerprinter/api-reference.html).

### Schemas for LLMs

To give a language model the shape of your data before it writes SPARQL, render the saved profile as
a **pattern schema**: five files per graph (`prefixes-*.md`, `patterns-*.md`, `patterns-*.csv`,
`glossary-*.md`, `glossary-*.csv`) with compact `(:Class)-property-> (:Target)` lines, statistics,
and labels, alt labels, definitions and notes. Or as **enriched ShExC** (the same content as ShEx
shapes):

```shell
fingerprint-gen-pattern out/profile.json -o llm/ --ontology vocab.ttl --max-classes 30
fingerprint-gen-shex    out/profile.json -o llm/ --min-instances 10
```

Give a model that writes SPARQL `patterns-*.md` and `prefixes-*.md`; filter the CSV files with grep
or DuckDB. On the test data, the patterns Markdown of a graph is about five times smaller than its
SHACL shapes (2,081 against 10,950 characters).
See [Schemas for LLMs](https://meaningfy-ws.github.io/rdf-fingerprinter/rdf-fingerprinter/llm-schema.html).

### Namespace filters

Leave out whole namespaces in every output (report, SHACL, ShExC, PlantUML, pattern schema) by
prefix, prefix glob or IRI stem; repeat the option to combine them, and use `--include-namespace` to
bring one back:

```shell
fingerprint-gen-pattern profile.json -o llm/ --exclude-namespace relationid --exclude-namespace 'prv*'
fingerprint-gen-doc     profile.json -o out/ --exclude-namespace 'https://my.brainframe.com/#/knowledge/'
```

The report keeps every namespace in its table, marks the excluded ones, and has a switch per
namespace that hides its classes and property rows on the page. See
[Namespace filters](https://meaningfy-ws.github.io/rdf-fingerprinter/rdf-fingerprinter/representations.html#filters).

## Development

Requires Poetry, Docker and (for `make check-spec`) Node.js.

```shell
make install                    # Poetry env with the test and lint groups
make check-all                  # lint, types, layers, OpenSpec, parallel tests with coverage floors — the gate CI runs
make check-release              # check-all + release tests + random properties + e2e; before a release
make oxigraph-load-test-data    # in-memory Oxigraph on :7878 with the test graphs
make test-e2e                   # end-to-end tests against it (local only)
```

See [Development](https://meaningfy-ws.github.io/rdf-fingerprinter/rdf-fingerprinter/development.html).

## Contributing

Contributions are welcome. Before you change something, please discuss it with the maintainers in a
[GitHub issue](https://github.com/meaningfy-ws/rdf-fingerprinter/issues). We follow the
[Apache code of conduct](https://www.apache.org/foundation/policies/conduct); please follow it in all
your interactions on the project.

## License

Licensed under the [Apache License 2.0](https://github.com/meaningfy-ws/rdf-fingerprinter/blob/master/LICENSE).
Maintained by [Meaningfy](https://meaningfy.ws).
