"""The RDF namespaces the representations write, in one place (profile-representations P-9)."""

RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
RDFS = "http://www.w3.org/2000/01/rdf-schema#"
XSD = "http://www.w3.org/2001/XMLSchema#"
SKOS = "http://www.w3.org/2004/02/skos/core#"
SKOSXL = "http://www.w3.org/2008/05/skos-xl#"
DCTERMS = "http://purl.org/dc/terms/"
OWL = "http://www.w3.org/2002/07/owl#"
SH = "http://www.w3.org/ns/shacl#"
FP = "https://data.meaningfy.ws/fingerprint/"  # the profile model's namespace root

RDF_LANG_STRING = RDF + "langString"
RDF_TYPE = RDF + "type"
XSD_STRING = XSD + "string"
BLANK_NODE_PREFIX = "_:"  # how the profile writes a blank node: `_:<id>`

# The predicates of a term's annotations (llm-schema-split DEC-5): labels and descriptions in priority order.
TERM_LABEL_PREDICATES = (SKOS + "prefLabel", SKOSXL + "prefLabel", RDFS + "label", DCTERMS + "title")
ALT_LABEL_PREDICATES = (SKOS + "altLabel", SKOSXL + "altLabel")
TERM_DESCRIPTION_PREDICATES = (SKOS + "definition", RDFS + "comment", DCTERMS + "description")
NOTE_PREDICATES = tuple(SKOS + name for name in ("scopeNote", "note", "example", "editorialNote", "historyNote", "changeNote"))
