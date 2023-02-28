#!/usr/bin/env python
"""
CLIENT
1. Реализовать простое клиент-серверное взаимодействие по протоколу JIM (JSON instant messaging):
    клиент отправляет запрос серверу;
    сервер отвечает соответствующим кодом результата.
    Клиент и сервер должны быть реализованы в виде отдельных скриптов, содержащих соответствующие функции.
    **** Функции клиента: 
        сформировать presence-сообщение; 
        отправить сообщение серверу; 
        получить ответ сервера; 
        разобрать сообщение сервера; 
        параметры командной строки скрипта client.py <addr> [<port>]: 
            addr — ip-адрес сервера; 
            port — tcp-порт на сервере, по умолчанию 7777. 
    Функции сервера: принимает сообщение клиента; 
        формирует ответ клиенту; 
        отправляет ответ клиенту; 
        имеет параметры командной строки: -p <port> — TCP-порт для работы (по умолчанию использует 7777);
        -a <addr> — IP-адрес для прослушивания (по умолчанию слушает все доступные адреса).
"""

import logging
import argparse
import socket
import jim

logger = logging.getLogger("client.py")
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
        socket_.connect((
            args.addr,
            args.port,
        ))
        logger.info(f"client connected to {args.addr}:{args.port}")
        logger.debug("send presence to server")
        socket_.send(jim.gen_jim_req(jim.JIMAction.PRESENCE))
        recv_bytes = socket_.recv(jim.JIM_MAX_LEN_ANSWER)
        answer = jim.parser_jim_answ(
            recv_bytes, callbacks=[jim.time_need, jim.response_code_need])
        if type(answer) is jim.GoodAnswer:
            logger.debug("received GoodAnswer")
            answer = answer.answer
            if jim.response_group(
                    answer["response"]) == jim.ResponseGroup.Alert:
                print("SERVER(alert): ", answer["alert"])
            elif jim.response_group(
                    answer["response"]) == jim.ResponseGroup.Error:
                print("SERVER(error): ", answer["error"])
            else:
                logger.error(f"Unknow response")
            socket_.send(jim.gen_jim_req(jim.JIMAction.QUIT))
        elif type(answer) is jim.BadAnswer:
            logger.error(f"received BadAnswer {answer.error}")
    except ConnectionRefusedError:
        socket_.close()

    finally:
        socket_.close()
