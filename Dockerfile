FROM abernix/meteord:base
MAINTAINER Eugeniu Costetchi <costezki.eugen@gmail.com>
RUN apt-get update
RUN apt-get install -y git python-dev python python-pip texlive-latex-base python-pandas #dialog net-tools tar curl nano wget build-essential
RUN pip install pylatex

#downloading and installing RDF fingerprinter
RUN mkdir /rdf-fingerprinter && cd /rdf-fingerprinter
RUN git clone https://github.com/costezki/RDF-fingerprint-diff.git && cd ./RDF-fingerprint-diff && pip install .
