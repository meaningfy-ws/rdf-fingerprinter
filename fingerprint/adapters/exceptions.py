"""Errors raised by the adapters; the service layer maps them to its outcomes."""


class SparqlError(Exception):
    """A query that could not be answered; the message is meant for the log and the report."""

    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


class QueryTimeout(SparqlError):
    """The endpoint did not answer in time; the caller escalates or falls back."""


class RetriesExhausted(QueryTimeout):
    """A transient error that persisted through every retry."""


class TransientError(SparqlError):
    """A failure worth retrying (overload, dropped connection)."""


class PermanentError(SparqlError):
    """The endpoint rejected the query; retrying cannot help."""


class EndpointUnreachable(SparqlError):
    """The endpoint cannot be used at all (no connection, authentication required)."""


class ConfigFileError(ValueError):
    """A configuration file that cannot be read or is not a JSON object."""


class TemplatePackageError(ValueError):
    """A template package whose `config.json` lacks what rendering needs."""


class GeneratedOutputError(ValueError):
    """A generated text that does not parse in its format; nothing of it is written."""


class ProfileFileError(ValueError):
    """A profile file that is missing, not JSON, or not a profile run."""
