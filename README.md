# RDF fingerprinter

**Understand** the structure of your RDF data at a glance using automatically built **application profiles** and spot differences between dataset structures. 

An [_application profile_](https://en.wikipedia.org/wiki/Application_profile), in this context, is the set of [_data shapes_](https://www.w3.org/2014/data-shapes/wiki/Main_Page) designed for a particular purpose acting as constraints on how the data are instantiated and so can be used to validate the data.

_Fingerprinting_ is the action of generating, or rather, guessing, the application profile applied to a particular dataset. This is an inductive process of reconstructing the data shape for each class instantiated in the dataset. 

![test](https://github.com/meaningfy-ws/rdf-fingerprinter/workflows/test/badge.svg)
[![codecov](https://codecov.io/gh/meaningfy-ws/rdf-fingerprinter/branch/master/graph/badge.svg)](https://codecov.io/gh/meaningfy-ws/eds4jinja2)
[![Documentation Status](https://readthedocs.org/projects/rdf-fingerprinter/badge/?version=latest)](https://eds4jinja2.readthedocs.io/en/latest/?badge=latest)

![PyPI](https://img.shields.io/pypi/v/rdf-fingerprinter?color=teal&label=version)
![PyPI - Status](https://img.shields.io/pypi/status/rdf-fingerprinter)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/rdf-fingerprinter)
![PyPI - License](https://img.shields.io/pypi/l/rdf-fingerprinter?color=green)
![PyPI - Wheel](https://img.shields.io/pypi/wheel/rdf-fingerprinter)

Contents
--------
* [API Reference](api_ref.md)

# Installation
RDF fingerprinter may be installed with pip as follows. 
 
```
pip install rdf-fingerprinter
```
Nore that Python version 3.7 or later is required.  

# Usage

The easiest way to build a fingerprint of a SPARQL endpoint is by calling the fingeprinting CLI command and write the report in an output folder.
 
```shell script
fingerprint -e http://my.sparql.endpoint.com -o my/output/folder
``` 

To use the fingerprinter programmatically please refer to the [API Reference](api_ref.md). 

# Contributing
You are more than welcome to help expand and mature this project. We adhere to [Apache code of conduct](https://www.apache.org/foundation/policies/conduct), please follow it in all your interactions on the project.   

When contributing to this repository, please first discuss the change you wish to make via issue, email, or any other method with the maintainers of this repository before making a change.

## Licence 
This project is licensed under [GNU GPLv3](https://www.gnu.org/licenses/gpl-3.0.en.html) licence. v3](https://www.gnu.org/licenses/gpl-3.0.en.html)