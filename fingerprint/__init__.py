#!/usr/bin/python3

# __init__.py
# Date:  15/08/2019
# Author: Eugeniu Costetchi
# Email: costezki.eugen@gmail.com

import logging.config
from json import load

__docformat__ = "restructuredtext en"

__version__ = "0.2.5"
__date__ = "2020-12-11"

logging.config.dictConfig(load(open('logging_config.json')))
