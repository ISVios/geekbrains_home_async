#!/usr/bin/env python
"""
1. Написать функцию host_ping(),
    в которой с помощью утилиты ping будет проверяться доступность сетевых узлов.
    Аргументом функции является **список**,
        в котором каждый сетевой узел должен быть представлен **именем хоста или ip-адресом**.
    В функции необходимо перебирать ip-адреса и проверять их доступность
        с выводом соответствующего сообщения («Узел доступен», «Узел недоступен»).
    При этом ip-адрес сетевого узла должен создаваться с помощью функции ip_address().
"""

import ipaddress
import subprocess
from socket import gethostbyname

import logger

LOGGER = logger.LOGGER


def get_ips(host: str):
    """
    return correct ip list address from: 
        (example)   '192.168.0.1'       ->  [192.168.0.1]
        (example)   'google.com'        ->  [64.233.165.113]
        (example)   '192.168.0.0/24'    ->  [192.168.0.1 ... 192.168.0.255]
        (example)   '192.168.02222.222' ->  [None]
    """
    try:
        return [ipaddress.ip_address(host)]
    except:
        try:
            return [ipaddress.ip_address(gethostbyname(host))]
        except:
            try:
                return list(ipaddress.ip_network(host).hosts())
            except:
                return None


def host_ping(hosts: list[str] = [], print_effect: bool = True) -> bool:

    ARGS = ["/usr/bin/ping", "-c4"]

    for host in hosts:
        ips = get_ips(host)

        if not ips:
            LOGGER.error(f"Invalid address '{host}'")
            # Think: exit or continue
            exit(-1)
        for ip in ips:
            res = subprocess.Popen(args=[*ARGS, str(ip)],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.DEVNULL)
            res.wait()
            ok = res.returncode == 0
            status = "Reachable" if ok else "Unreachable"
            if print_effect:
                LOGGER.info(f"{host} {status}")
            return ok
    return False


if __name__ == "__main__":
    TEST_ADDR = ["192.168.0.1", "127.0.0.1", "yandex.ru", "google.com"]
    host_ping(TEST_ADDR)
