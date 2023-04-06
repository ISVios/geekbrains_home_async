"""
Just logger config file
"""

import logging

LOGGER = logging.getLogger("task")
logging.root.setLevel(0)

LOGGER.setLevel(10)

LOGGER.addHandler(logging.StreamHandler())
