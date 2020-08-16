#!/usr/bin/python3

# test_eds4jinja2.py
# Date:  15/08/2020
# Author: Eugeniu Costetchi
# Email: costezki.eugen@gmail.com 

""" proof of concept usinf eds4jinja2 """
import re

import jinja2
import pytest
import pandas as pd
import numpy as np
from eds4jinja2.builders.jinja_builder import build_eds_environment, inject_environment_globals

from tests.poc import TEMPLATE_FOLDER, TEST_CONFIGURATION, TEMPLATE_SPARQL_FETCH_TREE


def invert_dict(my_map, reduce_values=True):
    """
        Invert the dictionary.
        If reduce_values is true then the values are single items otherwise
        the values are list of possibly multiple items.
    """
    inv_map = {}
    for k, v in my_map.items():
        inv_map[v] = inv_map.get(v, [])
        inv_map[v].append(k)
    if reduce_values:
        return {k: sorted(v, key=len)[0] for k, v in inv_map.items()}
    return inv_map


def replace_strings_in_tabular(data_frame, target_columns=[], value_mapping_dict={}, mark_touched_rows=False):
    """
        Replaces the values from the target columns in a data frame according to the value-mapping dictionary.
        If the inverted_mapping flag is true, then the inverted value_mapping_dict is considered.
        If mark_touched_rows is true, then adds a boolean column _touched_ where
    """
    # get all the string columns
    obj_columns = data_frame.select_dtypes([np.object]).columns  # [1:]
    # columns = self.target_columns if self.target_columns else self.data_frame.columns
    # limit to columns indicated in the self.target_columns
    if target_columns:
        obj_columns = [column for column in obj_columns if column in target_columns]

    # The URIs contains special regex chars, better to escape them when searching through dataframe
    escaped_value_mapping_dict = {r"" + re.escape(k): v for k, v in value_mapping_dict.items()}

    # add a column flagging touched rows
    if mark_touched_rows:
        mask = np.column_stack(
            [data_frame[col].str.contains('(' + '|'.join(escaped_value_mapping_dict.keys()) + ')', na=False)
             for col in obj_columns])
        data_frame["_touched_"] = mask
        # data_frame.sort_values(by=["_touched_"] + obj_columns, inplace=True,
        #                        ascending=[False] + [True] * len(obj_columns))

    # create a nested dictionary that pandas replace understand
    # For a DataFrame nested dictionaries, e.g., {'a': {'b': np.nan}},
    # are read as follows: look in column ‘a’ for the value ‘b’ and
    # replace it with NaN. The value parameter should be None
    # to use a nested dict in this way.
    nested_dict = {column: escaped_value_mapping_dict for column in obj_columns}
    data_frame[obj_columns] = data_frame[obj_columns].replace(to_replace=nested_dict, value=None, regex=True)
    return data_frame


@pytest.fixture
def env():
    template_loader = jinja2.FileSystemLoader(searchpath=str(TEMPLATE_FOLDER))
    jenv = build_eds_environment(loader=template_loader)
    inject_environment_globals(jenv, TEST_CONFIGURATION)
    # additional functions needed for the fingerprinter
    inject_environment_globals(jenv,
                               {"invert_dict": invert_dict,
                                "replace_strings_in_tabular": replace_strings_in_tabular})
    return jenv


def test_eds_installation(env):
    t = env.from_string(TEMPLATE_SPARQL_FETCH_TREE)
    assert t.render() is not None


def test_write_output(env):
    t = env.get_template("main.html")
    t.stream().dump("output/index.html")


def test_invert_dict():
    d = {"a": 1, "b": 2, "c": 1}
    print(invert_dict(d, reduce_values=False))
