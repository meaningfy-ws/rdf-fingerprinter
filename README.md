# RDF fingerprinter

**Understand** the structure of your RDF data at a glance using automatically built **application profiles** and spot differences between dataset structures. 

An [_application profile_](https://en.wikipedia.org/wiki/Application_profile), in this context, is the set of [_data shapes_](https://www.w3.org/2014/data-shapes/wiki/Main_Page) designed for a particular purpose acting as constraints on how the data are instantiated and so can be used to validate the data.

_Fingerprinting_ is the action of generating, or rather, guessing, the application profile applied to a particular dataset. This is an inductive process of reconstructing the data shape for each class instantiated in the dataset. 

[![ci](https://github.com/meaningfy-ws/rdf-fingerprinter/actions/workflows/ci.yml/badge.svg)](https://github.com/meaningfy-ws/rdf-fingerprinter/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/meaningfy-ws/rdf-fingerprinter/branch/master/graph/badge.svg)](https://codecov.io/gh/meaningfy-ws/rdf-fingerprinter)
[![docs](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://meaningfy-ws.github.io/rdf-fingerprinter/)

![PyPI](https://img.shields.io/pypi/v/rdf-fingerprinter?color=teal&label=version)
![PyPI - Status](https://img.shields.io/pypi/status/rdf-fingerprinter)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/rdf-fingerprinter)
![PyPI - License](https://img.shields.io/pypi/l/rdf-fingerprinter?color=green)
![PyPI - Wheel](https://img.shields.io/pypi/wheel/rdf-fingerprinter)

**Documentation:** https://meaningfy-ws.github.io/rdf-fingerprinter/

# Installation
RDF fingerprinter may be installed with pip as follows. 
 
```
pip install rdf-fingerprinter
```
Python 3.12 or later is required (tested on 3.12, 3.13 and 3.14).

**Upgrading from 0.3?** 1.0 needs Python 3.12+, runs on eds4jinja2 2 (pandas 3 / numpy 2) and no
longer configures logging when imported: configure it in your application. See the
[CHANGELOG](CHANGELOG.md).

# Usage

The easiest way to build a fingerprint of a SPARQL endpoint is by calling the fingeprinting CLI command and write the report in an output folder.
 
```shell script
fingerprint -e http://my.sparql.endpoint.com -o my/output/folder
``` 

To use the fingerprinter programmatically, see the
[API Reference](https://meaningfy-ws.github.io/rdf-fingerprinter/rdf-fingerprinter/api-reference.html). 

# Development

Requires Poetry, Docker and (for `make check-spec`) Node.js.

```shell script
make install                    # Poetry env with the test and lint groups
make check-all                  # lint, types, layers, OpenSpec, unit tests — the gate CI runs
make oxigraph-load-test-data    # in-memory Oxigraph on :7878 with the test graphs
make test-e2e                   # end-to-end tests against it (local only)
```

See [Development](https://meaningfy-ws.github.io/rdf-fingerprinter/rdf-fingerprinter/development.html).

# Contributing
You are more than welcome to help expand and mature this project. We adhere to [Apache code of conduct](https://www.apache.org/foundation/policies/conduct), please follow it in all your interactions on the project.   

When contributing to this repository, please first discuss the change you wish to make via issue, email, or any other method with the maintainers of this repository before making a change.

## Licence 
This project is licensed under [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0).