FROM abernix/meteord:node-8-base
MAINTAINER Eugeniu Costetchi <costezki.eugen@gmail.com>
RUN apt-get update
RUN apt-get install -y --no-install-recommends apt-utils build-essential python python-dev python-pip libblas3 liblapack3 gcc gfortran python-dev libc6
RUN apt-get install -y --no-install-recommends lmodern texlive-fonts-recommended texlive-latex-base texlive-latex-extra
RUN apt-get install -y --no-install-recommends python-numpy python-pandas
#RUN pip install -U pip numpy pandas
#downloading and installing RDF fingerprinter
RUN mkdir /rdf-fingerprinter
RUN cd /rdf-fingerprinter && git clone https://github.com/costezki/RDF-fingerprint-diff.git && cd ./RDF-fingerprint-diff && pip install .


