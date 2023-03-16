"""
JIMServer
"""
import argparse
import logging
import queue
import select
import socket
import sys
import threading
import time
from os import name
from jim.logger.logger_func import log
from jim.error.error import JIMClientDisconnect

import jim.logger.logger_server
from jim.client import (JIMClient, RegistarationBy, RegistarationByGuest,
                        RegistarationByName)
from jim.packet.packet import JIMAction, JIMPacket, JIMPacketFieldName

logger = logging.getLogger("server")


class ReadThread(threading.Thread):

    def __init__(self):
        super().__init__()
        self.daemon = True

    def run(self) -> None:
        while True:
            print(f"Cur time {time.time()}")
            time.sleep(10)


class JIMServer:
    __socket: socket.socket
    __clients: set
    __commands: queue.SimpleQueue  # for cli or gui command

    def __init__(self) -> None:
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__clients = set()  # ToDo: use JIMClient.__all_client__
        self.__commands = queue.SimpleQueue()

    def add_command(self, ):
        # Comands
        """
        KICK user 
        JOIN user group
        MSG from to
        LEAVE user group
        """
        raise NotImplemented

    def _all_read(self, command, read_io, clients):
        for client in read_io:
            try:
                packet = client._recive_packet()
                # update probe
                client.status.probe.update_probe()
                logger.debug(f"IN {client} -> {packet}")
                if packet and packet.empty():
                    logger.critical(f"Empty packet {packet}")
                    continue
                packet = packet.need_field(JIMPacketFieldName.TIME)
                if packet.is_bad_packet():
                    logger.warning(
                        f"{packet.dict_} is BAD {packet.error.__str__()}")
                    client._send_packet(
                        JIMPacket.gen_answer(400,
                                             msg=f"{packet.error.__str__()}"))
                    logger.debug(f"OUT {404} -> {client}")
                else:
                    logger.warning(f"{packet} is Good")
                    client._push_packet(packet)
            except:
                clients.remove(client)
                client.disconnect()
                logger.error(f"{client} is disconnected.")

    def _all_answer(self, command, write_io, clients):
        for client in write_io:
            # ToDo
            # parse command
            try:
                client._send_in_stack()
                packet = client._pop_packet()
                logger.debug(f"answer to {packet}")
                if packet and not packet.empty() and packet.dict_:
                    in_pack = packet.dict_
                    id_ = in_pack.get(JIMPacketFieldName.TIME)
                    if packet.is_field(JIMPacketFieldName.ACTION):
                        action = in_pack[JIMPacketFieldName.ACTION]
                        if action == JIMAction.AUTHENTICATE:
                            # test all fields
                            if not in_pack.get(
                                    JIMPacketFieldName.USER) or \
                                 not in_pack[JIMPacketFieldName.USER].get(JIMPacketFieldName.USER_NAME):
                                client._send_packet(
                                    JIMPacket.gen_answer(400,
                                                         id_,
                                                         msg="bad req"))
                                continue
                            self.__authenticate_action(client, packet, id_,
                                                       clients)
                        elif action == JIMAction.JOIN:
                            client._send_packet(JIMPacket.gen_answer(400, id_))

                        elif action == JIMAction.LEAVE:
                            client._send_packet(JIMPacket.gen_answer(400, id_))
                        elif action == JIMAction.MSG:
                            packet = packet \
                                    .need_field(JIMPacketFieldName.TO) \
                                    .need_field(JIMPacketFieldName.FROM) \
                                    .need_field(JIMPacketFieldName.MESSAGE) \
                                    .need_field(JIMPacketFieldName.ENCODING)
                            if not packet.is_bad_packet():
                                self.__msg_action(client, packet, id_, clients)
                            else:
                                client._send_packet(
                                    JIMPacket.gen_answer(400,
                                                         id_,
                                                         msg=packet.error))
                        elif action == JIMAction.PRESENCE:

                            #self.__presence_action(client, packet, id_, clients)
                            logger.critical(client.status.client_type)
                        elif action == JIMAction.PRОBE:
                            # only server can send this
                            logger.warning(f"{client} send PRОBE")
                            # send 404
                            client._send_packet(
                                JIMPacket.gen_answer(400, id_,
                                                     "Unsupport action"))
                        elif action == JIMAction.QUIT:
                            client._send_jim_json({})
                            logger.debug(f"{client} logout.")
                            client.disconnect()
                            clients.remove(client)
                        else:
                            logger.error(f"UNKNOWN ACTION {action}")
                            # send 400
                            client._send_packet(
                                JIMPacket.gen_answer(400, id_,
                                                     "Unsupport action"))
                    elif packet.is_field(JIMPacketFieldName.RESPOSE):
                        pass
                    else:
                        # send 400
                        client._send_packet(
                            JIMPacket.gen_answer(400, id_, msg="bad req"))
                        logger.error(f"UNKNOWN {packet}")
            # except SendAnswer as send:
            # ToDo
            except:
                clients.remove(client)
                client.disconnect()
                logger.error(f"{client} is disconnected.")

    @log
    def __authenticate_action(self, client: JIMClient, packet: JIMPacket,
                              id_: int, clients: set):
        name = ""
        if packet.dict_:
            in_pack = packet.dict_
            name = in_pack[JIMPacketFieldName.USER][
                JIMPacketFieldName.USER_NAME]

        client_name = client.get_name()
        if client_name == name:
            client._send_packet(
                JIMPacket.gen_answer(400, id_, msg="already auth"))
            logger.warning(f"{client} try rereg by '{name}'")
            # return already auth
        elif client_name != name:
            # ToDo: find duplicates
            if name in [c.get_name() for c in clients]:
                client._send_packet(
                    JIMPacket.gen_answer(
                        400, id_, msg="client with this name alredy exist"))
                logger.debug(f"{client} duplicate reg by {name}")
                return

            client.status.client_type = RegistarationByName(name)
            client._send_packet(JIMPacket.gen_answer(200, id_, msg="OK"))
            logger.debug(f"{client} reg by '{name}'")
        else:
            client._send_packet(
                JIMPacket.gen_answer(400, id_, msg="no support reg"))

    def __msg_action(self, client: JIMClient, packet: JIMPacket, id_: int,
                     clients: set):

        logging.debug(f"{packet.dict_}")

        if not client.get_name():
            client._send_packet(JIMPacket.gen_answer(403, id_,
                                                     msg="need auth"))
            return

        in_pack = packet.dict_
        if in_pack:
            msg_from = in_pack["from"]
            msg_to = in_pack["to"]

            for to in clients:
                if to != client:
                    logger.debug(f"{msg_from} -> {msg_to} \n {in_pack}")
                    if msg_to[0] == "#":
                        to._push_packet_by(packet, group=msg_to[1:])
                    else:
                        to._push_packet_by(packet, name=msg_to)

            client._send_packet(JIMPacket.gen_answer(200, id_, msg="Ok"))

    def run(self, args):
        try:
            logger.setLevel(args.log)
            self.__socket.bind((args.addr, args.port))
            self.__socket.listen(args.count)
            self.__socket.settimeout(0.5)
            logger.info(f"Server listen {args.addr}:{args.port}")

            while True:
                try:
                    client, _ = self.__socket.accept()
                except KeyboardInterrupt:
                    raise KeyboardInterrupt
                except:
                    # if timeout
                    pass
                else:
                    self.__clients.add(JIMClient._from_server(client))
                finally:
                    read_io = []
                    write_io = []

                    try:
                        logger.debug(f"Clients online: {len(self.__clients)}")
                        logger.debug(f"Comands: {self.__commands.qsize()}")

                        read_io, write_io, _ = select.select(
                            self.__clients, self.__clients, [], 0)
                        logger.debug(f"R:{len(read_io)} | W:{len(write_io)}")
                    except KeyboardInterrupt:
                        raise KeyboardInterrupt
                    except Exception as ex:
                        logger.critical(ex.__str__())

                    try:
                        cur_command = None
                        if not self.__commands.empty():
                            cur_command = self.__commands.get()

                        # ToDo: convet to
                        # parse comands
                        # use comands
                        # for client in clients: client.update(read_io, write_io, clients)
                        if len(read_io):
                            self._all_read(cur_command, read_io,
                                           self.__clients)

                        self._all_answer(cur_command, write_io, self.__clients)
                    except KeyboardInterrupt:
                        raise KeyboardInterrupt
                    # except Exception as ex:
                    #     logger.critical(f"->>>>>> {ex}")
                    #     raise ex
                    #     logger.critical(ex.__str__())

        except KeyboardInterrupt:
            # send to all client QUIT
            logger.warning(f"stop server")
            for client in self.__clients:
                try:
                    client._send_packet(JIMPacket.gen_req(JIMAction.QUIT))
                    client.disconnect()
                except KeyboardInterrupt:
                    logger.warning(f"Force stop server")
                    self.__socket.shutdown(socket.SHUT_RDWR)
                    self.__socket.close()
                    exit(-1)
                except Exception as ex:
                    pass

            self.__socket.shutdown(socket.SHUT_RDWR)
            self.__socket.close()
            exit(0)
        except OSError:
            logger.critical(f"Port {args.port} already used.")
            exit(-1)


if __name__ == "__main__":
    # unittest
    pass
