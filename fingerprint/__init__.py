#!/usr/bin/python3

# __init__.py
# Date:  15/08/2019
# Author: Eugeniu Costetchi
# Email: costezki.eugen@gmail.com

import logging

__docformat__ = "restructuredtext en"

__version__ = "0.2.4"
__date__ = "2020-11-18"

# hard coding the log level and format
logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)
