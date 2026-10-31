"""Errors the service layer reports to its callers."""


class UsageError(ValueError):
    """A setting value the user must correct (the CLI's exit 2)."""
