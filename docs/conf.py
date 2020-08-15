# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys

sys.path.insert(0, os.path.abspath('..'))

# -- Project information -----------------------------------------------------
import re

project = 'rdf-fingerprinter'
copyright = '2020, Eugeniu Costetchi'
author = 'Eugeniu Costetchi'


# Find version. We have to do this because we can't import it in Python 3 until
# its been automatically converted in the setup process.
def find_version(filename):
    _version_re = re.compile(r'__version__ = "(.*)"')
    for line in open(filename):
        version_match = _version_re.match(line)
        if version_match:
            return version_match.group(1)


# The full version, including alpha/beta/rc tags.
release = find_version("../fingerprint/__init__.py")
# The short X.Y version.
version = re.sub("[0-9]+\\.[0-9]\\..*", "\1", release)

# The encoding of source files.
source_encoding = "utf-8"

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    # "myst_parser",
    "sphinxcontrib.apidoc",
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
]

apidoc_module_dir = "../fingerprint"
apidoc_output_dir = "srcdocs"
add_module_names = False
autodoc_default_options = {
    'members': None,
    'member-order': 'bysource',
    # 'special-members': True,
    'undoc-members': None,
    "private-members": None,
    # 'exclude-members': '__weakref__'
}

master_doc = 'index'

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', "draft"]

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'alabaster'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']
