""" 
sample2
Created:  12/03/2019
Author: Eugeniu Costetchi
Email: costezki.eugen@gmail.com
"""
from rdflib import URIRef
from rdflib import Namespace

ns = Namespace("")

a = URIRef("http://eurovoc.europa.eu/100")
b = URIRef("adff")

print(a.n3())
