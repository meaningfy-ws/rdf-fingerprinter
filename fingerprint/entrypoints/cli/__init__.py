#!/usr/bin/python3

# __init__.py
# Date:  18/10/2020
# Author: Eugeniu Costetchi
# Email: costezki.eugen@gmail.com

""" """

import logging

# Exit codes of every command (P-7, P-13); 2 is click's usage error.
EXIT_FAILURES, EXIT_UNREACHABLE, EXIT_UNEXPECTED, EXIT_PITFALLS = 1, 3, 4, 5


def configure_logging() -> None:
    """The application, not the library, configures logging."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)5s %(name)s: %(message)s")
