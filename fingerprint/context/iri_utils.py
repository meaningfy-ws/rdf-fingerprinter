""" 
iri_utils
Created:  12/03/2019
Author: Eugeniu Costetchi
Email: costezki.eugen@gmail.com
"""
import re
import pandas as pd
import numpy as np
from deprecated import deprecated


def cut_last_ns_segment(s):
    return re.sub(r'[^/#]*$', "", s)


@deprecated
def generate_missing_ns(df, structural_columns=['stype', 'p', 'ootype']):
    """
    given a dataframe detect unique namespaces
    :param df:
    :return:
    """
    unique_uris = set()
    for col in structural_columns:
        unique_uris = unique_uris.union(set(df[col]))
    print(unique_uris)


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


@deprecated
def generate_and_merge_namespace_definitions(data_frame, ns_dataframe):
    known = dict(zip(ns_dataframe.uri, ns_dataframe.ns))
    bucket = set()
    for i, row in data_frame.iterrows():
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


def discover_base_uris(data_frame, target_columns=None, known_uris=None):
    """
        discover a unique set of [base_uri:prefix] pairs
    :param known_uris: if there are any known URIs they shall be in format {"base_namespace1":"prefix1",
                "base_namespace2":"prefix2"}
    :param data_frame:
    :param target_columns:
    :return:
    """
    t_columns = data_frame.select_dtypes([np.object]).columns
    if target_columns:
        t_columns = [column for column in t_columns if column in target_columns]
    bucket = set()
    print(t_columns)
    for row in data_frame[t_columns].itertuples(index=False, name='row'):
        for value in row:
            print(str(value))
            bucket.add(cut_last_ns_segment(str(value)))

    unique_list = list(bucket).sort()
    ns_map = {v: "ns" + str(unique_list.index(v)) for v in unique_list}
    print(ns_map)
    if known_uris:
        return ns_map.update(known_uris)

    # todo, continue here
    return ns_map
