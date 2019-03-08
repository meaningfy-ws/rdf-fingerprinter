""" 
__init__.py
Created:  08/03/2019
Author: Eugeniu Costetchi
Email: costezki.eugen@gmail.com

# Data generator module
purpose: build data context from the data sources such that it is directly usable in the template files
input: data source(s) and eventually additional configuration
output: data context - a python dictionary(-like) structure ready to be used in/by the document template
variations of data sources:
- simple CSV - turns the CSV source into a data context
- simple aggregated CSV - turns the CSV source into data context following an aggregation configuration
- cascading query - turns a configuration of cascading queries into a data context (explained below)
"""

