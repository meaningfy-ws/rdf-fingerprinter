#!/usr/bin/env bash


docker build -t costezki/meteor-fingerprinter:latest .

docker login

docker push costezki/meteor-fingerprinter:latest
