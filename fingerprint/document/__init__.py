""" 
__init__.py
Created:  08/03/2019
Author: Eugeniu Costetchi
Email: costezki.eugen@gmail.com

# Report generator module
purpose: given a generated data context and a document template (e.g. mustache, jinja2) generate the final report.
input: (a) data context (b) document template
output: final report (HTML, PDF, package, static website, etc. )
variations of report generators:
- HTML + JINJA2 - generates the final report gtom JINJA2 templates and generated/existent data
- PyLatex - generates the final report based on hadcoded document structure
- XML/XSL-FO + JINJA2 - generates an XML document ready for XSL-FO

"""