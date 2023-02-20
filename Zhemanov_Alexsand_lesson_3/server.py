#!/usr/bin/env python
"""
SERVER
1. Реализовать простое клиент-серверное взаимодействие по протоколу JIM (JSON instant messaging):
    клиент отправляет запрос серверу;
    сервер отвечает соответствующим кодом результата.
    Клиент и сервер должны быть реализованы в виде отдельных скриптов, содержащих соответствующие функции.
    Функции клиента: 
        сформировать presence-сообщение; 
        отправить сообщение серверу; 
        получить ответ сервера; 
        разобрать сообщение сервера; 
        параметры командной строки скрипта client.py <addr> [<port>]: 
            addr — ip-адрес сервера; 
            port — tcp-порт на сервере, по умолчанию 7777. 
    *** Функции сервера: принимает сообщение клиента; 
        формирует ответ клиенту; 
        отправляет ответ клиенту; 
        имеет параметры командной строки: 
            -p <port> — TCP-порт для работы (по умолчанию использует 7777);
            -a <addr> — IP-адрес для прослушивания (по умолчанию слушает все доступные адреса).
"""

import argparse
import logging
import socket

import jim

logger = logging.getLogger("server.py")
logging.basicConfig(level=logging.DEBUG, format='%(message)s')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='JIM server.')
    parser.add_argument("-p",
                        "--port",
                        const=1,
                        type=int,
                        nargs="?",
                        default=7777,
                        help="TCP-port. (default: 7777)")
    parser.add_argument("-a",
                        "--addr",
                        const=1,
                        type=str,
                        nargs="?",
                        default="0.0.0.0",
                        help="IP-addres to listen. (default: 0.0.0.0)")

    args = parser.parse_args()

    socket_ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        socket_.bind((
            args.addr,
            args.port,
        ))
        socket_.listen(1)
        logger.info(f"Server listen {args.addr}:{args.port}")
        while True:
            # get client
            client, addr = socket_.accept()
            logger.debug(f"Find user:\n\t|{addr}")
            # get client JIM_ACTION.PRESENCE
            recv_bytes = client.recv(jim.JIM_MAX_LEN_ANSWER)
            dict_ = jim.parser_jim_answ(recv_bytes)
            if type(dict_) is dict and dict_.get("action", None):
                if dict_["action"] == jim.JIM_ACTION.PRESENCE.value:
                    # Think: there test login
                    # gen client answer
                    logger.debug(
                        f"{addr} | Found {jim.JIM_ACTION.PRESENCE}. Answer.")
                    client.send(
                        jim.gen_jim_answ(response=200,
                                         msg=f"Welcome to Server."))
                    # Think: maybe here add loop(thread) while client until if not quit or responce(time)
                    # or add client to acess list
            else:
                logger.error(
                    f"{addr} | NO found {jim.JIM_ACTION.PRESENCE} action. Ignore."
                )

            client.close()
    except KeyboardInterrupt:
        print("Closing")
        socket_.shutdown(socket.SHUT_RDWR)
        socket_.close()
    except ConnectionRefusedError:
        socket_.close()
    finally:
        socket_.close()
