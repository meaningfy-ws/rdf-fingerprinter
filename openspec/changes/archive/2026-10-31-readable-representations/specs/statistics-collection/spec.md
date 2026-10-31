## MODIFIED Requirements

### Requirement: Settings
Every collection parameter SHALL be settable through `resolve_settings`, in this order of
precedence:
1. a CLI option;
2. the environment variable `RDF_FINGERPRINTER_<NAME>`;
3. its `selected_graphs` argument (graphs only);
4. configuration (`--config FILE` for the CLI, the `config` mapping for library callers);
5. the defaults of DEC-12.

The settings used SHALL be recorded in the profile. An unknown configuration key, an unreadable
configuration file or an invalid value SHALL be a usage error raised before any query. The
completeness check SHALL be switchable by configuration property or environment variable. The 1.x
`additional_config["collection"]` route is removed (readable-representations DEC-9).

#### Scenario: Environment variable overrides default
- **WHEN** `RDF_FINGERPRINTER_TIMEOUT_SECONDS=10` is set and no CLI option is given
- **THEN** the recorded settings have `timeout_seconds` 10

#### Scenario: CLI overrides environment
- **WHEN** the environment sets concurrency 2 and the CLI passes `--concurrency 8`
- **THEN** the recorded settings have `concurrency` 8

#### Scenario: Environment overrides the library configuration
- **WHEN** a library caller passes `config` with `top_k` 5 to `resolve_settings` while `RDF_FINGERPRINTER_TOP_K=7` is set
- **THEN** the recorded settings have `top_k` 7

#### Scenario: Unknown configuration key
- **WHEN** the configuration holds the key `colour`
- **THEN** a usage error names `colour` and no query is sent
