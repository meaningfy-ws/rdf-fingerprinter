#!/usr/bin/python3

# main.py
# Date:  18/10/2020
# Author: Eugeniu Costetchi
# Email: costezki.eugen@gmail.com

""" """

import logging
import pathlib

import click

from fingerprint.service_layer.handlers import generate_endpoint_fingerprint_report

logger = logging.getLogger(__name__)


@click.command()
@click.option("-e", "--sparql_endpoint_url", required=True, type=str, help="SPARQL enpoint")
@click.option("-o", "--output", default="./output", required=False, type=str, help="output folder")
def fingerprint_endpoint(sparql_endpoint_url: str, output: str):
    """
        A simple program that generates a fingerprint report on a given SPARQL endpoint.
    :param sparql_endpoint_url:
    :param output:
    :return:
    """
    # the application, not the library, configures logging (DEC-9)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)5s %(name)s: %(message)s")
    logger.debug("start fingerprinting endpoint")
    output_location = pathlib.Path(output)
    output_file = generate_endpoint_fingerprint_report(
        sparql_endpoint_url=sparql_endpoint_url, output_location=output_location
    )
    logger.info("fingerprint report written to %s", output_file)


if __name__ == "__main__":
    fingerprint_endpoint()
