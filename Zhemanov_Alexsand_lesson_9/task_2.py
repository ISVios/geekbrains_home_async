#!/usr/bin/env python
"""
2. Написать функцию host_range_ping() для перебора ip-адресов из заданного *диапазона*.
    Меняться должен только *последний октет* *каждого адреса*.
    По результатам проверки должно выводиться соответствующее сообщение.
"""

import ipaddress
from logging import Logger
from typing import Callable

import logger
from task_1 import get_ips, host_ping

LOGGER = logger.LOGGER


def host_range_ping(hosts: list[str],
                    range_: "range" = range(0, 10),
                    absolute: bool = False,
                    print_effect: bool = True) -> "dict|None":
    #Think: del duplicate in hosts
    dict_ = {}
    dict_["Reachable"] = set()
    dict_["Unreachable"] = set()
    for host in hosts:
        ips = get_ips(host)
        if ips:
            # take first address if list have > 1 elem
            ip = ips[0]
            ip_split = ip.compressed.split(".")
            init_list_octets = ip_split[:-1]
            remake_ip = ""
            for sub in range_:
                if not absolute:
                    last_int_octet = int(ip_split[-1])
                    remake_ip = ".".join(
                        [*init_list_octets,
                         str(last_int_octet + sub)])
                else:
                    remake_ip = ".".join([*init_list_octets, str(sub)])
                if host_ping(hosts=[remake_ip], print_effect=print_effect):
                    dict_["Reachable"].add(remake_ip)
                else:
                    dict_["Unreachable"].add(remake_ip)

    return dict_


if __name__ == "__main__":

    TEST_ADDR = ["192.168.0.1", "192.168.1.1", "127.0.0.1"]
    host_range_ping(hosts=TEST_ADDR)
