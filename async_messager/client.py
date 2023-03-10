#!/usr/bin/env python
"""
CLIENT
1. Реализовать обработку нескольких клиентов на сервере,
        используя функцию select.
    Клиенты должны общаться в «общем чате»: 
        - каждое сообщение участника отправляется всем, подключенным к серверу.
** 2. Реализовать функции отправки/приема данных на стороне клиента.
    Чтобы упростить разработку на данном этапе,
        пусть клиентское приложение будет либо только принимать,
        либо только отправлять сообщения в общий чат.
    Эти функции надо реализовать в рамках отдельных скриптов.
"""
import argparse
import logging
import socket
from datetime import datetime

import jim
import log.client_log_config

logger = logging.getLogger("client")


def send_ans_wait(bytes_: bytes, socket_: socket.socket) -> jim.Answer:
    socket_.send(bytes_)
    recv = socket_.recv(jim.JIM_MAX_LEN_ANSWER)
    return jim.parser_jim_answ(recv, callbacks=[jim.time_need])


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

    logger.debug("parse input args")
    args = parser.parse_args()

    socket_ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        socket_.connect((
            args.addr,
            args.port,
        ))
        logger.info(f"client connected to {args.addr}:{args.port}")
        logger.debug("send presence to server")
        res = send_ans_wait(jim.gen_jim_req(jim.JIMAction.PRESENCE), socket_)

        if type(res) is jim.GoodAnswer:
            if res.answer["response"] == 200:
                logger.debug(f"Server answer on PRESENCE {res.answer}")
            else:
                logger.error(res.answer["error"])
                exit(-1)

            user_name = input("Input user name: ")

            if user_name:
                user_dict = {"account_name": user_name}
                res = send_ans_wait(
                    jim.gen_jim_req(jim.JIMAction.AUTHENTICATE,
                                    user=user_dict), socket_)
                if type(res) is jim.BadAnswer:
                    exit(-1)
                elif type(res) is jim.GoodAnswer and "error" in res.answer:
                    logger.error(f"{res.answer.get('error')}")
                    exit(-1)

            command = "-1"
            while True:
                command = input(
                    "\n1)send and recive\n2)loop send time\n3)loop recive\nq)quit\nInput command: "
                )

                if command == "1":
                    msg = input("input message")
                    msg_dict = {
                        "from": user_name,
                        "to": "#___ALL__",
                        "message": msg,
                        "encoding": "utf-8"
                    }
                    bytes_ = jim.gen_jim_req(jim.JIMAction.MSG, **msg_dict)
                    res = send_ans_wait(bytes_, socket_)
                    if type(res) is jim.GoodAnswer:
                        if res.answer["response"] == 200:
                            logger.debug(f"send message")
                elif command == "2":
                    try:
                        while True:
                            msg_dict = {
                                "from": user_name,
                                "to": "#___ALL__",
                                "message": str(datetime.now()),
                                "encoding": "utf-8"
                            }
                            bytes_ = jim.gen_jim_req(jim.JIMAction.MSG,
                                                     **msg_dict)
                            socket_.send(bytes_)
                    except KeyboardInterrupt:
                        pass
                elif command == "3":
                    try:
                        while True:
                            res = jim.parser_jim_answ(
                                socket_.recv(jim.JIM_MAX_LEN_ANSWER))
                            if type(res) is jim.GoodAnswer:
                                if "response" in res.answer:
                                    logger.debug(
                                        f"Server send answer with {res.answer['response']}"
                                    )
                                elif "action" in res.answer:
                                    answer = res.answer
                                    msg_from = answer["from"]
                                    # msg_to = answer["to"]
                                    msg_text = answer["message"]
                                    msg_enc = answer["encoding"]
                                    fix_tex = msg_text.encode("utf-8").decode(
                                        msg_enc)
                                    action = res.answer["action"]
                                    if action == jim.JIMAction.MSG:
                                        logger.info(f"{msg_from}:{fix_tex}")

                    except KeyboardInterrupt:
                        pass
                elif command == "q":
                    socket_.close()
                    break
    except ConnectionRefusedError:
        logger.warning("Server disconected")
        socket_.close()

    finally:
        logger.debug("close socket")
        socket_.close()
