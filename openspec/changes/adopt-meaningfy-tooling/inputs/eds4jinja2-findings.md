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
