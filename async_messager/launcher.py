#!/usr/bin/env python
""" 
4. Продолжаем работать над проектом «Мессенджер»:
    a) Реализовать скрипт, запускающий два клиентских приложения:
        на чтение чата и на запись в него. Уместно использовать модуль subprocess).
    b) Реализовать скрипт, запускающий указанное количество клиентских приложений.
"""

import os
import subprocess
import time

PWD = os.getcwd()

CLIENT_SCRIPT_PATH = os.path.join(PWD, "run_client_cli.py")
SERVER_SCRIPT_PATH = os.path.join(PWD, "run_server_cli.py")

COUNT_OF_CLIENT_READ = 1
COUNT_OF_CLIENT_WRITE = 1

BROADCAST_ARGS = "--broadcast-time"
LISTENER_ARGS = ["--listener"]

if __name__ == "__main__":
    pwd = os.getcwd()
    pids = []
    # server
    print("Run server")
    server = subprocess.Popen([
        "konsole", f"-p tabtitle='Server'", "-e", "python", SERVER_SCRIPT_PATH
    ],
                              stderr=subprocess.PIPE)
    # Think: add wait server ready

    time.sleep(5)

    # clients
    print(f"Run writers clients ({COUNT_OF_CLIENT_WRITE})")
    for i in range(COUNT_OF_CLIENT_WRITE):
        proc = subprocess.Popen([
            "konsole", f"-p tabtitle='Writer: user{i}'", "-e", "python",
            CLIENT_SCRIPT_PATH, f"-A user{i}", "--broadcast"
        ])
        pids.append(proc)

    print(f"Run readers clients ({COUNT_OF_CLIENT_READ})")
    for i in range(COUNT_OF_CLIENT_READ):
        proc = subprocess.Popen([
            "konsole", f"-p tabtitle='Reader:{i}'", "-e", "python",
            CLIENT_SCRIPT_PATH
        ])
        pids.append(proc)

    try:
        server.wait()
    except KeyboardInterrupt:
        for pid in pids:
            pid.kill()
        server.kill()
        exit(0)
