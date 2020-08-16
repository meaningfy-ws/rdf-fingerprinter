#!/usr/bin/python3

# __init__.py
# Date:  15/08/2020
# Author: Eugeniu Costetchi
# Email: costezki.eugen@gmail.com
import pathlib

TEMPLATE_FOLDER = pathlib.Path("./templates")

SPO_LIMIT_10 = "select * where {?s ?p ?o} limit 10"
ENDPOINT_REMOTE_CORRECT = "http://publications.europa.eu/webapi/rdf/sparql"
ENDPOINT_LOCAL_CORRECT = "http://localhost:3030/dev/query"

DEFAULT_NAMED_GRAPH = "http://publications.europa.eu/resource/authority/corporate-body"

TEST_CONFIGURATION = {
    "configuration": {
        "default_endpoint": ENDPOINT_LOCAL_CORRECT,
        "output_folder": "./output",
        "default_query": SPO_LIMIT_10,
        "default_graph": DEFAULT_NAMED_GRAPH,
        "alpha": {
            "title": "DUMMY DATASET CALLED ALPHA"
        }
    }
}

TEMPLATE_SPARQL_FETCH_TREE = '''
{% set content, error = from_endpoint(configuration.default_endpoint).with_query(configuration.default_query).fetch_tree() %} \n
content:  {{ content }}\n
error: {{ error }}\n
'''
