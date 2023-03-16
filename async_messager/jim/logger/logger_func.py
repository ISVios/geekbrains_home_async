"""
"""

import sys
import logging
import traceback

# get server|client logger
logger = logging.getLogger()

MAIN_MODULE = sys.modules.get("__main__") or None
if MAIN_MODULE and MAIN_MODULE.__file__:
    if MAIN_MODULE.__file__.find("server") > 0:
        logger = logging.getLogger("server").getChild("__func__")
    elif MAIN_MODULE.__file__.find("client") > 0:
        logger = logging.getLogger("client").getChild("__func__")

# disable duplicate parent log print
logger.propagate = False

logger_func_formater = logging.Formatter("<%(asctime)s> %(message)s")
logger_func_stream = logging.StreamHandler()
logger_func_stream.setFormatter(logger_func_formater)

logger.addHandler(logger_func_stream)
# logger.setLevel(50)


def log(func):

    def wrap(*args, **kwargs):
        func_res = func(*args, **kwargs)

        parent_func = traceback.extract_stack(limit=2)[-2][2]
        logger.debug(
            f"Call function '{func.__name__}' from '{parent_func}' with {args} and {kwargs}"
        )
        return func_res

    return wrap


if __name__ == "__main__":

    @log
    def test_func(a, b=2):
        pass

    def parent_func():
        test_func(1)

    # simple test
    logging.root.setLevel(logging.DEBUG)
    parent_func()
