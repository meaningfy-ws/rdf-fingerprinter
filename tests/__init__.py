"""
__init__.py
Date: 10.03.19
Author: Eugeniu Costetchi
Email: costezki.eugen@gmail.com
"""

import os

# Oxigraph by default (`make start-oxigraph oxigraph-load-test-data`); point at Fuseki with
# RDF_FINGERPRINTER_TEST_ENDPOINT=http://localhost:3030/dev/query (DEC-10).
LOCAL_ENDPOINT = os.environ.get("RDF_FINGERPRINTER_TEST_ENDPOINT", "http://localhost:7878/query")
