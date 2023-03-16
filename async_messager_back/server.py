#!/usr/bin/env python
"""
SERVER
** 1. Реализовать обработку нескольких клиентов на сервере,
        используя функцию select.
    Клиенты должны общаться в «общем чате»: 
        - каждое сообщение участника отправляется всем, подключенным к серверу.
2. Реализовать функции отправки/приема данных на стороне клиента.
    Чтобы упростить разработку на данном этапе,
        пусть клиентское приложение будет либо только принимать,
        либо только отправлять сообщения в общий чат.
    Эти функции надо реализовать в рамках отдельных скриптов.
"""

import argparse
import json
import logging
import queue
import select
import socket
from datetime import timedelta
from os import name

import jim
import log.server_log_config

logger = logging.getLogger("server")


def all_read(read_io, all_clients):
    """
    """
    for client in read_io:
        try:
            recv_bytes = client.recive()
            # ToDo: add correct time to callback
            res = jim.parser_jim_answ(
                recv_bytes,
                callbacks=[jim.time_need,
                           jim.need_field("action")])
            # add all
            client.push_answer(res)
        except:
            all_clients.remove(client)
            client.close()
            logger.error(f"{client} disconected")


def all_answer(write_io, all_users):
    for client in write_io:
        if client.can_read():
            try:

                # client is alive on matter what send
                client.update_probe(True)

                answer = client.pop_answer()
                answer_type = type(answer)

                # pase BadAnswer
                if answer_type is jim.BadAnswer:
                    client.send(jim.gen_jim_answ(400, "Worng request"))
                    answer = None
                    continue

                # unwarp GoodAnswer
                tested = answer.tested
                answer = answer.answer

                answer_action = answer["action"]

                logger.debug(f"{client} send {answer_action}")

                if answer_action == jim.JIMAction.AUTHENTICATE:

                    breakpoint()

                    # if client all ready auth
                    # Think: ~~recive "already auth"~~ or **drop auth**
                    if client.auth_type() == jim.ClientType.Auth:
                        # reset reg
                        client.un_reg()
                        logger.warning(f"{client} try re auth")

                    breakpoint()
                    logger.debug(f"{client} try auth")
                    if answer.get("user") and answer["user"].get(
                            "account_name"):
                        user_name = answer["user"]["account_name"]
                        # find duplicated in all_users
                        if jim.Client.can_reg(user_name):
                            client.reg(user_name)
                            logger.debug(f"{client} sucess login")
                            client.send(
                                jim.gen_jim_answ(response=200, msg="OK"))
                        else:
                            client.send(
                                jim.gen_jim_answ(
                                    response=409,
                                    msg=
                                    f"Client with name='{user_name}' already exist"
                                ))
                    breakpoint()
                elif answer_action == jim.JIMAction.PRESENCE:

                    if client.auth_type() == jim.ClientType.Unvalid:
                        client._type = jim.ClientType.Anon

                    client.send(jim.gen_jim_answ(response=200, msg="OK"))

                elif answer_action == jim.JIMAction.MSG:
                    need_fields = ["to", "from", "message", "encoding"]
                    if not all([field in answer for field in need_fields]):
                        need = []
                        for field in need_fields:
                            if not answer.get(field):
                                need.append(field)
                        client.send(
                            jim.gen_jim_answ(400,
                                             f"no all field exist: {need}"))
                        continue

                    # msg_to = answer["to"]
                    msg_from = answer["from"]

                    if tested:
                        # ToDo: add correct parce
                        bytes_ = json.dumps(answer).encode("utf-8")

                        client.send(bytes_)
                        logger.debug(f"Server -> {client} msg")
                        continue

                    if client.auth_type() == jim.ClientType.Auth:
                        if msg_from == client.name:
                            for to_send in all_users:
                                if to_send != client and to_send.auth_type(
                                ) != jim.ClientType.Unvalid:
                                    # Think: send all
                                    send_msg = jim.GoodAnswer(answer)
                                    send_msg.tested = True
                                    to_send.push_answer(send_msg)

                            client.send(
                                jim.gen_jim_answ(response=200, msg="Send"))
                            logger.debug(f"{client} -> Server")

                            continue
                        else:
                            client.send(
                                jim.gen_jim_answ(response=409,
                                                 msg="Wrong field 'to'"))
                            continue

                    client.send(
                        jim.gen_jim_answ(response=401,
                                         msg="Need Authenticate"))

                elif answer_action == jim.JIMAction.JOIN:
                    client.send(
                        jim.gen_jim_answ(response=500, msg="NotImplemented"))

                elif answer_action == jim.JIMAction.LEAVE:
                    client.send(
                        jim.gen_jim_answ(response=500, msg="NotImplemented"))

                elif answer_action == jim.JIMAction.PRОBE:
                    # only server can send this
                    client.send(
                        jim.gen_jim_answ(response=404,
                                         msg="Not supported action"))

                elif answer_action == jim.JIMAction.QUIT:
                    all_users.remove(client)
                    client.send(jim.gen_jim_answ(response=200, msg="Bye"))
                    logger.debug(f"{client} is disconnected")
                    client.close()
                else:
                    logger.debug(f"NO IMPLEMENT ACTION  {answer_action}")
                    client.send(
                        jim.gen_jim_answ(response=400, msg="Worng request"))
            except:
                logger.error(f"{client} is disconnected")
                all_users.remove(client)
                client.close()
        else:
            try:
                # probe
                if client.need_probe():
                    if not client.long_no_answer_on_probe():
                        client.send(jim.gen_jim_req(jim.JIMAction.PRОBE))
                        logger.debug(f"send probe to {client}")
                        client.update_probe()
                    else:
                        # dont duplicate except
                        raise OSError
            except:
                all_users.remove(client)
                logger.debug(f"{client} no answer. Disconnect")
                client.close()


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
        socket_.bind((
            args.addr,
            args.port,
        ))
        socket_.listen(10)
        socket_.settimeout(0.5)
        logger.info(f"Server listen {args.addr}:{args.port}")
        users = set()
        # groups = {}
        while True:
            try:
                anonynim, addr = socket_.accept()
            except KeyboardInterrupt:
                raise KeyboardInterrupt
            except OSError:
                pass
            else:
                logger.debug(f"Find user | {addr}")
                users.add(jim.Client(anonynim))
            finally:
                read_io = []
                write_io = []
                try:
                    logger.debug(f"Users Online: {len(users)}")
                    read_io, write_io, _ = select.select(users, users, [], 0)
                except KeyboardInterrupt:
                    raise KeyboardInterrupt
                except:
                    pass

                try:
                    all_read(read_io, users)
                    all_answer(write_io, users)
                except:
                    pass
    except KeyboardInterrupt:
        logger.warning("Force stop Server")
        socket_.shutdown(socket.SHUT_RDWR)
        socket_.close()
        exit(0)
    except ConnectionRefusedError:
        logger.warn(f"Can`t make connection with client.")
        socket_.close()
        exit(-2)
    except OSError:
        logger.critical(f"Port {args.port} already used.")
        exit(-1)

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
