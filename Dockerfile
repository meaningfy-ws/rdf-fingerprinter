FROM abernix/meteord:base
MAINTAINER Eugeniu Costetchi <costezki.eugen@gmail.com>
RUN apt-get update
RUN apt-get install -y --no-install-recommends apt-utils build-essential python python-dev python-pip texlive-latex-base texlive-latex-extra 
#downloading and installing RDF fingerprinter
RUN mkdir /rdf-fingerprinter && cd /rdf-fingerprinter
RUN git clone https://github.com/costezki/RDF-fingerprint-diff.git && cd ./RDF-fingerprint-diff && pip install .
