"""
1. Продолжая задачу логирования, реализовать декоратор @log, фиксирующий обращение к декорируемой функции. Он сохраняет ее имя и аргументы.
2. В декораторе @log реализовать фиксацию функции, из которой была вызвана декорированная. Если имеется такой код:
@log
def func_z():
 pass

def main():
 func_z()
...в логе должна быть отражена информация:
"<дата-время> Функция func_z() вызвана из функции main"
"""
import sys
import logging
import traceback

logger = logging.getLogger()

MAIN_MODULE = sys.modules.get("__main__") or None
if MAIN_MODULE and MAIN_MODULE.__file__:
    if MAIN_MODULE.__file__.find("server") > 0:
        logger = logging.getLogger("server").getChild("__func")
    elif MAIN_MODULE.__file__.find("client") > 0:
        logger = logging.getLogger("client").getChild("__func")

# disable duplicate parent log print
logger.propagate = False

logger_func_formater = logging.Formatter("<%(asctime)s> %(message)s")
logger_func_stream = logging.StreamHandler()
logger_func_stream.setFormatter(logger_func_formater)

logger.addHandler(logger_func_stream)


def log(func):

    def decor(*args, **kwargs):

        result_func = func(*args, **kwargs)

        parent_func = traceback.extract_stack(limit=2)[-2][2]
        logger.debug(
            f"Call function '{func.__name__}' from '{parent_func}' with {args} and {kwargs}"
        )

        return result_func

    return decor


# Think: log don`t show b
@log
def test_func(a, b=2):
    pass


def parent_func():
    test_func(1)


if __name__ == "__main__":
    # simple test
    logging.root.setLevel(logging.DEBUG)
    parent_func()
