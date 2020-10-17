#!/usr/bin/python3

# handlers.py
# Date:  15/10/2020
# Author: Eugeniu Costetchi
# Email: costezki.eugen@gmail.com 

""" """

import json
import logging
from pathlib import Path
from typing import Union, List

logger = logging.getLogger(__name__)


def generate_endpoint_fingerprint_report(sparql_endpoint_url: str, output_location: Union[str, Path],
                                         graph: str) -> str:
    """
        Calculate the fingerprint of a given endpoint and write the report in the output location.
        Optionally the fingerprint calculation could be restricted to a particular named graph.
    :param graph: a valid URI
    :param sparql_endpoint_url:
    :param output_location:
    :return:
    """
