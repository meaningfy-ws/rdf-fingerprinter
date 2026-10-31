## MODIFIED Requirements

### Requirement: Settings
Every collection parameter SHALL be settable, in this precedence, by CLI option, environment
variable `RDF_FINGERPRINTER_<NAME>`, the `selected_graphs` parameter of
`generate_endpoint_fingerprint_report` (graphs only), configuration (`--config FILE` for the CLI,
`additional_config["collection"]` for the library), and the defaults of DEC-12; the settings used
SHALL be recorded in the profile. An unknown configuration key, an unreadable configuration file or
an invalid value SHALL be a usage error raised before any query. The completeness check SHALL be
switchable by configuration property or environment variable.

#### Scenario: Environment variable overrides default
- **WHEN** `RDF_FINGERPRINTER_TIMEOUT_SECONDS=10` is set and no CLI option is given
- **THEN** the recorded settings have `timeout_seconds` 10

#### Scenario: CLI overrides environment
- **WHEN** the environment sets concurrency 2 and the CLI passes `--concurrency 8`
- **THEN** the recorded settings have `concurrency` 8

#### Scenario: Environment overrides the library configuration
- **WHEN** a library caller passes `additional_config["collection"]` with `top_k` 5 while `RDF_FINGERPRINTER_TOP_K=7` is set
- **THEN** the recorded settings have `top_k` 7

#### Scenario: Unknown configuration key
- **WHEN** the configuration holds the key `colour`
- **THEN** a usage error names `colour` and no query is sent

## ADDED Requirements

### Requirement: Error classes and retries
The SPARQL client SHALL classify every error into one class with one response: transient (HTTP 429,
502, 503, connection failures) retried after 1 s and then 4 s and, if it persists, treated as a
timeout; timeout (the per-query timeout, HTTP 504, or a 500 whose message mentions a time limit);
permanent (other 4xx and 500s, responses that are not SPARQL results), never retried; unreachable
(HTTP 401, 403, 407), which SHALL stop the run only on the first query — on any later query it
SHALL count as permanent.

#### Scenario: Transient error retried
- **WHEN** a query fails once with HTTP 503 and then succeeds
- **THEN** its result is used and no failure is recorded

#### Scenario: Refusal after the start concerns one query
- **WHEN** a per-class query is refused with HTTP 403 after the graphs were listed
- **THEN** that measurement is recorded as a failure with one attempt and the run goes on

### Requirement: Response per collection stage
A failed query SHALL cost only its stage: the graph listing — unreachable or persistently transient
stops the run, a timeout or rejection profiles the default graph only and records a failure (with
graphs chosen, those are profiled and a WARNING is logged); other discovery queries fall back
(classes counted one by one, predicates listed without counts) or are recorded and skipped; a
failure in a class's first wave (instance listing, histograms, value partitions, co-types) escalates
under `auto` on a timeout and otherwise leaves the class out with a recorded failure; a failure in its
second wave (top values, completeness check, incoming links) is recorded and the class is kept. A
class whose IRI cannot be put in a query SHALL be skipped and recorded. A well-formed response
holding a value the collector cannot interpret SHALL end the run as an unexpected error.

#### Scenario: Second-wave failure keeps the class
- **WHEN** the top-values query of a class times out
- **THEN** the class is in the profile without top values, and the only failures recorded are top-values failures (one per property queried)

#### Scenario: Permanent first-wave failure does not escalate
- **WHEN** the histogram query of a class is rejected with HTTP 400
- **THEN** the class is left out, one failure is recorded and no first-N attempt is made
