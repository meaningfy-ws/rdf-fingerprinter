# file:     io
# created:  11/10/16
# author:   Eugeniu Costetchi
import os
import pandas as pd
import json


def read_prefixes(filename):
    """
    :param filename: path to a CSV file with columns "ns", "uri"
    :return:
    """
    return pd.read_csv(filename, header=0, names=["ns", "uri"])


def read_fp_spo_count(filename):
    """
    :param filename: path to a CSV file with columns ["stype","p","ootype","propType","scnt","ocnt","cnt","min_sp","max_sp","avg_sp"]
    :return:
    """
    return pd.read_csv(filename, header=0,
                       names=["stype", "p", "ootype", "propType", "scnt", "ocnt", "cnt", "min_sp", "max_sp", "avg_sp"])


def replace_ns(triples, ns_dataframe):
    """
    :param triples: a dataframe with columns (s,p,o)
    :param ns_dataframe: a dataframe with columns (ns,uri)
    :return: triples replaced with ns
    """
    d = dict(zip(ns_dataframe.uri, ns_dataframe.ns))
    return triples.replace(d, regex=True)


def read_config(configfile):
    with open(configfile, 'r') as f:
        return json.load(f)


def compile_tex_file_multipass(filename):
    """
    runs several times the latex command to simulate the multiple passes
    :param filename: the tex filename without .tex extension
    :return: None
    """
    fn = os.path.abspath(filename)
    here = os.path.abspath(os.curdir)
    os.chdir(os.path.dirname(os.path.abspath(filename)))
    os.system("pdflatex -interaction=nonstopmode " + fn + ".tex")
    os.system("pdflatex -interaction=nonstopmode " + fn + ".tex")
    os.system("pdflatex -interaction=nonstopmode " + fn + ".tex")
    os.chdir(here)


if __name__ == "__main__":
    # print(read_config("../config.json"))
    pass