#!/usr/bin/env python
"""
1. Написать функцию host_ping(),
    в которой с помощью утилиты ping будет проверяться доступность сетевых узлов.
    Аргументом функции является **список**,
        в котором каждый сетевой узел должен быть представлен **именем хоста или ip-адресом**.
    В функции необходимо перебирать ip-адреса и проверять их доступность
        с выводом соответствующего сообщения («Узел доступен», «Узел недоступен»).
    При этом ip-адрес сетевого узла должен создаваться с помощью функции ip_address().
2. Написать функцию host_range_ping() для перебора ip-адресов из заданного диапазона.
    Меняться должен только последний октет каждого адреса.
    По результатам проверки должно выводиться соответствующее сообщение.
3. Написать функцию host_range_ping_tab(),
        возможности которой основаны на функции из примера 2.
    Но в данном случае результат должен быть итоговым по всем ip-адресам,
        представленным в табличном формате (использовать модуль tabulate).
        Таблица должна состоять из двух колонок и выглядеть примерно так:
            Reachable Unreachable
            10.0.0.1  10.0.0.3
            10.0.0.2  10.0.0.4
"""

import ipaddress
import logging
import os
import subprocess
from socket import gethostbyname

import tabulate

logger = logging.getLogger(__name__)
logging.root.setLevel(0)
logger.setLevel(0)
logger.addHandler(logging.StreamHandler())


def ip_address(host: str):
    try:
        ip = ipaddress.ip_address(host)
    except:
        try:
            ip = ipaddress.ip_address(gethostbyname(host))
        except:
            ip = None

    return ip


def host_ping(hosts: list[str] = []):

    ARGS = ["/usr/bin/ping", "-c4"]

    for host in hosts:
        ip = ip_address(host)
        res = subprocess.Popen(args=[*ARGS, str(ip)], stdout=subprocess.PIPE)
        res.wait()
        status = "Reachable" if res.returncode == 0 else "Unreachable"
        logger.info(f"{host} {status}")


def host_range_ping():
    pass


def host_range_ping_tab():
    pass


host_ping(["192.168.0.1"])
