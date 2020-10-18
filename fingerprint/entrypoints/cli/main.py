#!/usr/bin/python3

# main.py
# Date:  18/10/2020
# Author: Eugeniu Costetchi
# Email: costezki.eugen@gmail.com 

""" """

import pathlib
from distutils.dir_util import copy_tree
from eds4jinja2.builders.report_builder import ReportBuilder
import click
import logging

from fingerprint.service_layer.handlers import generate_endpoint_fingerprint_report

__logger = logging.getLogger(__name__)


# def copy_static_content(from_path, to_path):
#     if pathlib.Path(from_path).is_dir():
#         copy_tree(from_path, to_path)
#     else:
#         __logger.warning(from_path + " is not a directory !")


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
    output_location = pathlib.Path(output)
    output_file = generate_endpoint_fingerprint_report(sparql_endpoint_url=sparql_endpoint_url,
                                                       output_location=output_location)


if __name__ == "__main__":
    fingerprint_endpoint()
