"""The RDF namespaces the representations write, in one place (profile-representations P-9)."""

RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
RDFS = "http://www.w3.org/2000/01/rdf-schema#"
XSD = "http://www.w3.org/2001/XMLSchema#"
OWL = "http://www.w3.org/2002/07/owl#"
SH = "http://www.w3.org/ns/shacl#"
FP = "https://data.meaningfy.ws/fingerprint/"  # the profile model's namespace root

RDF_LANG_STRING = RDF + "langString"
RDF_TYPE = RDF + "type"
BLANK_NODE_PREFIX = "_:"  # how the profile writes a blank node: `_:<id>`
