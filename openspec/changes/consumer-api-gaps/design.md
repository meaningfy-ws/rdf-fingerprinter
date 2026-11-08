# Design: consumer-api-gaps

> Derives from: EPIC consumer-api-gaps (`proposal.md`).

## C-1 Bounded endpoint calls (#76)

`SparqlHttpClient._once` reads the body in `read1` chunks. Before each read it checks the deadline,
`timeout_seconds` after the request started, and raises `QueryTimeout`. The answer size is counted
as it is read and the call stops with `AnswerTooLarge` once it exceeds
`config.max_answer_bytes` (`RDF_FINGERPRINTER_MAX_ANSWER_BYTES`, default 268435456).

Bound: a timeout is not retried, a transient error is retried up to `len(backoff)` times. One
attempt ends at the deadline plus at most one more blocked socket read (`timeout_seconds`), so
the worst case is `(retries + 1) x 2 x timeout_seconds + sum(backoff)`. The connect and header phases
are bounded per socket operation by `timeout_seconds`, not by the deadline (urllib offers no
public way to bound them as a whole); the docs say so.

Rejected: `http.client` with a watchdog thread (loses proxy and redirect handling); a thread that is
abandoned at the deadline (leaks a thread per hostile call).

## C-2 Error contract of the listing (#77)

`collection._Collection.listed_graphs` turns a `KeyError` on `row["g"]` into
`PermanentError("... lacks ?g")`. `ConfigurationError(UsageError)` lives in
`service_layer/exceptions.py`; `validate_config` and the environment source of `resolve_settings`
raise it for a `ConfigError`. An invalid URL stays a plain `UsageError`. The CLI maps both to exit 2.
A run that meets the same answer records a failure and profiles the default graph, as for any
`PermanentError` of Q0, instead of crashing with `KeyError`.

## C-3 Diagram descriptions (#75)

`DiagramFile` is a view in `model/fingerprint_views.yaml` (path, format, graph, kind, module,
part). `PlantumlGenerator.describe()` builds the records from the same loop that names the files, so
they cannot drift. `describe_diagrams` in `service_layer/representations.py` shares the preparation
of `generate_representations` (a private helper) and writes nothing. `graph` is the graph IRI, None
for the default graph; `module` is the namespace prefix; `part` is the `~n` number, None unless
the module was split.

Rejected: a manifest written next to the files (changes the file list of every run); documenting
the file naming as the contract (the graph IRI cannot be recovered from a slug).

## C-4 Formats in the reference (#69)

The `formats` row lists the five generators, and a table gives each one's files. A test reads the
page and the registry so a new generator cannot be left out.

## Library dependencies

None.
