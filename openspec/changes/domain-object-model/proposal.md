# EPIC: Domain objects everywhere — no composed dicts, one typed config, rdflib for SPARQL, eds4jinja2's own document building

## Appetite

LARGE (developer, 2026-10-31): a refactoring across every layer of 2.0 and 2.1, with one upstream
change to eds4jinja2. Lands on top of PR #40 before it merges; 2.1.0 ships with it. Depends on
`profile-representations` (archived) and on an eds4jinja2 release that adds what DEC-7 needs.

Seeds: `inputs/review-2026-10-31.md` (the developer's review, the assessment, the decisions).

## Why

The 2.0/2.1 code models the profile in LinkML but then works on plain dicts: analytics helpers hand
dicts to each other and validate once at the end, collection builds raw dicts for the model, the
generators pass untyped view dicts to templates, and SPARQL results arrive as dicts of strings. A dict
has no names a reader can follow, no types a checker can verify, and no single definition a custom
template can rely on. Configuration is scattered: some values read the environment through an ad-hoc
module, others are module constants nobody can change. And rendering bypasses eds4jinja2's own
document building because it could not name per-graph files or check output before writing.

## Solution outline

**The concepts are the code.** Every value that crosses a function boundary is an instance of a
LinkML-generated Pydantic class or enum.

1. **Domain objects, never composed dicts** (DEC-1). Collection builds `ClassProfile`,
   `PropertyProfile`, `ValuePartition`… directly; analytics builds `PropertyAnalytics`,
   `ClassAnalytics`… directly; the generators build view objects from a new LinkML schema
   `model/fingerprint_views.yaml` (node and property shapes, diagram classes, document sections,
   caveats) and their enums (representation format, shape severity). A check fails the gate on new
   dict construction or `dict[str, Any]` in the code.
2. **One home for the generated model** (DEC-3): `fingerprint/domain/generated/` disappears; the
   generated profile module and its JSON Schema sit in `fingerprint/domain/`.
3. **SPARQL results through rdflib** (DEC-5): the adapter sends each query with the standard library
   (timeout, retries, failure classification) and rdflib parses the answer into typed result rows
   (`URIRef`, `Literal`, `BNode`); SPARQLWrapper and the hand-written row parser go.
4. **One typed configuration** (DEC-6): a config class in `fingerprint/__init__.py` reading
   environment variables through an `env_property` resolver (the Meaningfy settings pattern, as in
   ted-sws and mapping-workbench); every operational constant becomes a variable with its default.
5. **eds4jinja2 builds the documents** (DEC-7): eds4jinja2 gains a per-render output name and a
   check before writing; the template renderer adapter then calls its document building instead of
   rendering through its Jinja environment.

Behaviour does not change: the golden files and every scenario are the safety net (DEC-8).

## Key decisions

- **DEC-1**: No composed dicts in `fingerprint/` — reason: names, types and one definition per
  concept (developer, 2026-10-31). A dict is never a value that is passed, returned or stored.
  Allowed, each visible in the code: keyword arguments to a model constructor or `model_copy` (the
  construction syntax of an object, not a value); immutable module-level lookup tables keyed by enum
  members (a registry is a table, not a value); and dicts at an external library's boundary inside an
  adapter (eds4jinja2's configuration, JSON being parsed into a model), built there from a typed
  object and marked `# dict-ok: <reason>`. Rejected: hand-written dataclasses for the views (two
  modelling languages).
- **DEC-2**: The representation views are a LinkML schema, generated like the profile model — reason:
  custom templates rely on the view shape, so it is a contract and gets a schema; rejected: Pydantic
  written by hand.
- **DEC-3**: The generated model lives in `fingerprint/domain/` (no `generated/` folder); the import
  path `fingerprint.domain.generated.profile` breaks, the version stays 2.1.0 (developer: not used in
  production yet).
- **DEC-4**: Exceptions and IRI rules stay code — reason: LinkML generates data classes, and an
  exception must subclass `Exception`; failure *data* is already modelled (`Failure`). Rejected:
  modelling exceptions in LinkML.
- **DEC-5**: SPARQLWrapper goes; rdflib parses the results into typed terms (developer, 2026-10-31).
  *Amended while planning (logged in `inputs/review-2026-10-31.md`):* the developer chose rdflib's
  `SPARQLConnector`, but in rdflib 7.6.0 it calls `urlopen` without a timeout (and returns a tuple on a
  POST HTTP error), so it cannot carry the per-query timeout collection relies on. The query is sent
  with the standard library (`urlopen(…, timeout=…)`, form-encoded POST as today) and the answer is
  parsed with `rdflib.query.Result.parse`. Rejected: `SPARQLConnector` (no timeout); SPARQLWrapper.
  Pending the developer's confirmation; the alternative is contributing a timeout to rdflib.
- **DEC-6**: Configuration follows the Meaningfy settings pattern: an `env_property` resolver
  (adapter) and one config class in `fingerprint/__init__.py`. Operational constants (profile file
  name, retry backoff, timeout markers, error excerpt length, shapes namespace, default-graph label,
  prefixes file, collection-setting defaults) become `RDF_FINGERPRINTER_*` variables with their current
  values as defaults; standard vocabulary IRIs and protocol lookup tables stay constants. Precedence
  stays CLI > environment > config file > default. Importing the package stays side-effect free.
- **DEC-7**: eds4jinja2 is extended upstream (developer, 2026-10-31) with an output file name per
  render and a check before writing, released as a minor version; rdf-fingerprinter requires it and
  renders through its document building. Rejected: keeping the `template_env` workaround.
- **DEC-8**: No behaviour change: every 2.1 scenario and golden file holds; the CLI, the library
  function and `profile.json` stay as specified.

## Rabbit-holes

- Over-modelling the views: one class per thing a template iterates over, no deeper.
- rdflib's connector raises urllib errors, not SPARQLWrapper's: the failure classification must be
  re-mapped and re-tested row by row (the error-class table in How it works).
- Config read at import time would break "import has no side effects": values resolve on access.
- eds4jinja2's parallel pre-fetch path must keep working for its other users.
- Enum members versus their stored string values (`use_enum_values`): compare to members, never to
  free strings.

## No-gos

- No new representation, no new collection measurement, no change of output.
- No change to the meaning of the profile model; only where its generated code lives.
- No configuration file format beyond what exists (`--config` JSON); no secrets handling.
- No changes to eds4jinja2 beyond what DEC-7 needs, and no breaking change there.
- No new runtime dependency (SPARQLWrapper is removed; eds4jinja2's lower bound rises).

---

## What Changes

- Collection, analytics and generators construct generated model objects; new
  `model/fingerprint_views.yaml`; a dict-construction check in the gate; AGENTS.md rule.
- `fingerprint/domain/generated/` folded into `fingerprint/domain/` (**BREAKING** import path,
  within 2.x by decision).
- SPARQL adapter on rdflib's `SPARQLConnector`; SPARQLWrapper removed from the dependencies.
- `fingerprint/__init__.py` config with `RDF_FINGERPRINTER_*` variables; `settings_sources.py` removed.
- eds4jinja2 minor release; the template renderer adapter calls its document building.

## Capabilities

### New Capabilities
<!-- none: the representations, collection and report keep their requirements -->

### Modified Capabilities
- `developer-tooling`: generated models (location, views schema), the dict-construction check, the
  configuration pattern.
- `statistics-collection`: settings read from the environment through the config; operational
  constants configurable.

## Impact

- Code: every layer (`domain`, `adapters`, `service_layer`, `entrypoints`), templates where view
  names change, `model/`, `Makefile` (`generate-models`), `.importlinter`, `pyproject.toml`.
- Dependencies: SPARQLWrapper removed; `eds4jinja2` lower bound raised to the release with DEC-7.
- A second repository: `../eds4jinja2` gets its own OpenSpec change and release.
