import re

from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

with open('requirements-dev.txt') as f:
    requirements_dev = f.read().splitlines()

extras = {
    'test': requirements_dev,
}


def find_version(filename):
    _version_re = re.compile(r'__version__ = "(.*)"')
    for line in open(filename):
        version_match = _version_re.match(line)
        if version_match:
            return version_match.group(1)


version = find_version('fingerprint/__init__.py')

packages = find_packages(exclude=('examples*', 'test*'))

setup(
    name="rdf-fingerprinter",
    version=version,
    install_requires=requirements,
    tests_require=requirements_dev,
    extras_require=extras,
    include_package_data=True,
    author="Eugeniu Costetchi",
    author_email="costezki.eugen@gmail.com",
    maintainer="Eugeniu Costetchi",
    maintainer_email="costezki.eugen@gmail.com",
    description='Find out kind of data shapes your RDF dataset instantiates.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    # long_description_content_type="text/x-rst",
    url='https://github.com/meaningfy-ws/rdf-fingerprinter',
    platforms='any',
    keywords='rdf, application profile, data shape, statistics, fingerprint, sparql, linked-data',
    packages=packages,
    # exclude=["tests", "test_*"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Environment :: Console",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Topic :: Utilities",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Software Development :: Libraries",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Natural Language :: English",
    ],
    python_requires='>=3.7',
    entry_points={
        "console_scripts": ["fingerprint=fingerprint.entrypoints.cli.main:fingerprint_endpoint"]
    }
)
