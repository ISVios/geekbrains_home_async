#!/usr/bin/env python
"""
3. Написать функцию host_range_ping_tab(),
    возможности которой основаны на функции из примера 2.
    Но в данном случае результат должен быть итоговым по всем ip-адресам,
        представленным в табличном формате (использовать модуль tabulate).
    Таблица должна состоять из двух колонок и выглядеть примерно так:
    ----------+------------
    |Reachable|Unreachable|
    |10.0.0.1 |10.0.0.3   |
    |10.0.0.2 |10.0.0.4   |
    -----------------------
"""

import tabulate

import logger
import task_2

LOGGER = logger.LOGGER


def host_range_ping_tab(hosts: list[str] = [], range_: "range" = range(0, 10)):
    print("ping...", end="\r")
    res = task_2.host_range_ping(hosts, range_=range_, print_effect=False)
    if res:
        LOGGER.info(tabulate.tabulate(res, headers="keys", tablefmt="grid"))


if __name__ == "__main__":
    TEST_ADDR = ["192.168.0.1"]
    host_range_ping_tab(TEST_ADDR, range(5))
