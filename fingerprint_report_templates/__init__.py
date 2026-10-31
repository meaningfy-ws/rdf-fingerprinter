#!/usr/bin/python3

# __init__.py
# Date:  17/10/2020
# Author: Eugeniu Costetchi
# Email: costezki.eugen@gmail.com

""" """

from importlib.resources import files
from pathlib import Path


def packaged(name: str) -> Path:
    """The folder of a packaged template package; they ship as plain files, so a real path exists."""
    return Path(str(files(__name__) / name))
