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
        guest = set()
        users = set()
        while True:
            # get client
            anonynim, addr = socket_.accept()
            logger.debug(f"Find user | {addr}")
            # get client JIMAction.PRESENCE
            recv_bytes = anonynim.recv(jim.JIM_MAX_LEN_ANSWER)
            answer = jim.parser_jim_answ(
                recv_bytes,
                callbacks=[lambda x: jim.is_action(x, jim.JIMAction.PRESENCE)])
            if type(answer) is jim.GoodAnswer:
                logger.debug(
                    f"{addr} | get GoodAnswer {answer} with PRESENCE. Answer.")
                anonynim.send(
                    jim.gen_jim_answ(response=200, msg="Welcome to Server"))
                # add anonynim to guest
                # guest.add(client)
                # Think: maybe here add loop(thread) while client until if not quit or responce(time)
            elif type(answer) is jim.BadAnswer:
                logger.error(f"{addr} | BadAnswer with {answer.error}")
            else:
                logger.error(f"{addr} | Wrong. Ignore.")

            anonynim.close()
    except KeyboardInterrupt:
        print("Closing")
        socket_.shutdown(socket.SHUT_RDWR)
        socket_.close()
    except ConnectionRefusedError:
        socket_.close()
    finally:
        socket_.close()

# threads
# def users_logic()
# recv probe (time)
# recv quit -> del
# recv msg -> send to user (if no user found -> msg ignore)

# def guest_logic()
# send probe (time)
# recv AUTHENTICATE -> if ok move to users
# recv msg -> 401
# recv quit -> del
