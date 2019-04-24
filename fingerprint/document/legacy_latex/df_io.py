# file:     io
# created:  11/10/16
# author:   Eugeniu Costetchi

import os
import pandas as pd
import json
import re

from deprecated import deprecated


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


@deprecated
def generate_and_merge_namespace_definitions(spo_dataframe, ns_dataframe):
    known = dict(zip(ns_dataframe.uri, ns_dataframe.ns))
    bucket = set()
    for i, row in spo_dataframe.iterrows():
        if not pd.isnull(row["stype"]):
            bucket.add(cut_last_ns_segment(row["stype"]))
        if not pd.isnull(row["p"]):
            bucket.add(cut_last_ns_segment(row["p"]))
        if not pd.isnull(row["ootype"]):
            bucket.add(cut_last_ns_segment(row["ootype"]))
    l = [v for v in bucket if v not in known.keys()]
    ns_map = {v: "ns" + str(l.index(v)) for v in l}
    ns_map.update(known)
    return ns_map


@deprecated
def replace_ns(triples, ns_dataframe, generate_unknown_prefixes=True):
    """
    :param generate_unknown_prefixes: create namespace definitions for URIs
            encountered in the dataset but not covered by the NS_definition
    :param triples: a dataframe with columns (s,p,o)
    :param ns_dataframe: a dataframe with columns (ns,uri)
    :return: triples replaced with ns
    """
    d = dict(zip(ns_dataframe.uri, ns_dataframe.ns))
    if generate_unknown_prefixes:
        d = generate_and_merge_namespace_definitions(triples, ns_dataframe)
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


@deprecated
def cut_last_ns_segment(s):
    # return re.sub(r'[/#][^/#]*$', "", s)
    return re.sub(r'[^/#]*$', "", s)


if __name__ == "__main__":
    # print(cut_last_ns_segment("http://dsfdsg/saf/ewrewter/dsfdgfd"))
    # df = read_fp_spo_count("/home/lps/work/workspace-ws/fingerprinter/uploads/upload_99ab391037d7a84b077d3c37c5dbbe60")
    # nss = read_prefixes("/home/lps/work/workspace-ws/fingerprinter/resources/prefix.csv")
    # pprint.pprint(generate_and_merge_namespace_definitions(df,nss))

    # 'http://lemon-model.net/lemon#': 'lemon:',
    # 'http://lemon-model.net/lemon',
    pass
