#!/usr/bin/python3

# test_eds4jinja2.py
# Date:  15/08/2020
# Author: Eugeniu Costetchi
# Email: costezki.eugen@gmail.com 

""" proof of concept usinf eds4jinja2 """

import jinja2
import pytest
from eds4jinja2.builders.jinja_builder import build_eds_environment, inject_environment_globals

from tests.poc import TEMPLATE_FOLDER, TEST_CONFIGURATION, TEMPLATE_SPARQL_FETCH_TREE


@pytest.fixture
def env():
    template_loader = jinja2.FileSystemLoader(searchpath=str(TEMPLATE_FOLDER))
    jenv = build_eds_environment(loader=template_loader)
    inject_environment_globals(jenv, TEST_CONFIGURATION)
    return jenv


def test_eds_installation(env):
    t = env.from_string(TEMPLATE_SPARQL_FETCH_TREE)
    assert t.render() is not None


def test_write_output(env):
    t = env.get_template("main.html")
    t.stream().dump("output/index.html")
