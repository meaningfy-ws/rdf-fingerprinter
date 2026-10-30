# eds4jinja2 findings and decision (2026-10-30)

Measured in a throwaway Python 3.12 venv against the current `requirements.txt`.

## Evidence

- `eds4jinja2~=0.2.0` does not install on 3.12: it pins `pandas~=2.0.3`, which has no 3.12 wheel;
  the sdist build fails with `ModuleNotFoundError: No module named 'pkg_resources'`.
- `eds4jinja2` 1.0.4 (latest, `Requires-Python >=3.11`) installs on 3.12, but pins
  `numpy~=1.26` and `pandas~=2.2.0`; numpy 1.26 has no 3.13/3.14 wheels, so 1.0.4 is 3.12-only.
- 1.0 moved `ReportBuilder`: `eds4jinja2.builders.report_builder` →
  `eds4jinja2.services.report_builder`. Our only use is `fingerprint/service_layer/handlers.py:15`;
  the constructor arguments we pass (`target_path`, `additional_config`, `output_path`) still exist.
  Template rendering under 1.0 is unverified (needs the Fuseki suites).
- Usage surface: one `ReportBuilder` call in Python; the templates call `from_endpoint` /
  `from_statement` (16), `.with_query` (6), `.fetch_tabular` (6), `.fetch_tree` (1), and use the
  results as pandas DataFrames (`.loc` 15, `.itertuples` 4, `.empty` 5, `.columns` 2, `.iterrows` 1).

## Debate: drop vs keep

- **Drop** — ~100 lines of Jinja2 + SPARQLWrapper (already deps) would replace it and remove
  pandas/numpy/openpyxl/xlrd/pydantic/bs4. Cost: every template is rewritten off DataFrames, which
  changes report output (a No-go of this EPIC), and the code becomes a private fork of shared logic.
- **Keep** — the blocker is two version pins, not the design; a fix upstream helps every consumer.
- **Speed** — not measured. Likely dominated by SPARQL endpoint latency, not eds4jinja2; pandas
  import is a ~1 s one-off. 1.0 ships a `parallel_executor` worth evaluating. Measure first.

## Decision

Keep eds4jinja2 (developer, 2026-10-30). The developer first releases an eds4jinja2 with loosened
pins (target `numpy>=1.26,<3`, `pandas>=2.2,<3`, so 3.12–3.14 install); this change resumes on that
release. Performance work on eds4jinja2 is a separate, measurement-led effort.

## Update: eds4jinja2 2.0.0 measured (2026-10-30)

The developer released **eds4jinja2 2.0.0** on PyPI instead of a pin-loosening 1.x. Its
`pyproject.toml`: `requires-python >=3.12,<4.0` (classifiers 3.12–3.14), major-version ranges
`pandas>=3.1,<4`, `numpy>=2.5.4,<3`, `rdflib>=7.6,<8`, `click>=8.5,<9`, `SPARQLWrapper>=2.0,<3`,
`Jinja2>=3.1.6,<4`, plus `pydantic`, `requests`, `PyYAML`, `python-calamine`; optional `oxigraph`
extra. It no longer installs `xlrd`, `openpyxl`, `toml`, `py-singleton`, `beautifulsoup4`.

Measured in throwaway uv venvs, the code with only the `ReportBuilder` import moved to
`eds4jinja2.services.report_builder`, against a local Fuseki loaded with `tests/test_data`
(continents + treaties graphs and the default graph):

| Run | Python | eds4jinja2 / pandas / numpy | `pytest tests` | report all graphs | report treaties graph |
|---|---|---|---|---|---|
| baseline | 3.11 | 0.2.x / 2.0.3 / 1.x | 6 passed | 5.4 s | 13.3 s |
| upgrade | 3.12 | 2.0.0 / 3.1.0 / 2.5.4 | 6 passed | 5.9 s | 14.5 s |
| upgrade | 3.13 | 2.0.0 / 3.1.0 / 2.5.4 | 6 passed | — | — |
| upgrade | 3.14 | 2.0.0 / 3.1.0 / 2.5.4 | 6 passed | 5.8 s | 15.6 s |

- **Report output is byte-identical** (`main.html` md5 equal across baseline, 3.12 and 3.14 for
  both runs), so the report-output No-go holds. The `float` branch in `macros/renderers.html` is
  exercised (rounded decimals appear); pandas 3 `str` dtype changes nothing visible.
- **Speed**: single runs, about 8–17 % slower, within noise of SPARQL latency; not a blocker.
  Performance work stays a separate, measurement-led effort.
- `beautifulsoup4` is only a test dependency here, already declared in `requirements-dev.txt`;
  it moves to the Poetry test group.
- Effective lower bounds rise through eds4jinja2 (`rdflib>=7.6`, `click>=8.5`); our own
  constraints may stay as written, the resolver picks the compatible versions.
- Seen while testing, out of scope: `fingerprint/__init__.py` runs `logging.config.fileConfig('logging.conf')`
  relative to the CWD, so importing the package outside the repo root fails (the known
  logging-on-import defect); `handlers.py` uses the legacy `importlib.resources.path(package, name)` (aliased
  `pkg_resources`), which warns as deprecated on 3.12 only (3.13 un-deprecated it); the
  `importlib_resources` fallback branch is dead on 3.12+ and `importlib-resources` can be dropped.
- Oxigraph 0.5.13 as a SPARQL server (same test data): the first run rendered `nan` in the
  object/property type columns — the templates `GROUP_CONCAT` IRIs, an error in strict SPARQL 1.1
  that Fuseki tolerates. Wrapping the arguments in `STR()` fixes Oxigraph and leaves the Fuseki
  report byte-identical. What still differs is spec-legal: decimal lexical form (`1` vs `1.0`)
  and `GROUP_CONCAT` order. Oxigraph rendered the treaties report in 8.6 s vs 13.3 s on Fuseki.
  eds4jinja2's in-process `oxigraph` engine is not used: the fingerprinter talks HTTP to an endpoint.
- Coverage's default tracer slowed the report tests ~12× (174 s vs 14 s); `core = sysmon` fixes it.

**Decision confirmed**: depend on `eds4jinja2>=2.0,<3`; minimum Python 3.12 (DEC-7, DEC-8).
