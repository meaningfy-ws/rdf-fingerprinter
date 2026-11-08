"""Errors the service layer reports to its callers."""


class UsageError(ValueError):
    """A setting value the user must correct (the CLI's exit 2)."""


class ConfigurationError(UsageError):
    """An `RDF_FINGERPRINTER_*` value that cannot be used: the operator's to correct, not the user's input.

    A `UsageError`, so callers that catch that keep working; an invalid endpoint URL stays a plain `UsageError`."""
