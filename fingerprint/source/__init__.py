""" 
__init__.py
Created:  08/03/2019
Author: Eugeniu Costetchi
Email: costezki.eugen@gmail.com

# Data Source module
purpose: makes data available from various sources to the fingerprinter and allows writing the necessary data on disk.
input: configuration specification as python dictionary
output: (a) pandas dataframe or (b) rdflib graph
variations of data sources:
- tabular - either (a) any flavours of CSV-like file or (b) a triple source + a SPARQL query
- triples - either (a) any flavours of RDF files or (b) SPARQL endpoint

"""

