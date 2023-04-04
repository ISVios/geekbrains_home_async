"""
JIMServer
"""
import dis
import logging
import queue
import select
import socket

import jim.logger.logger_server
from jim.client import JIMClient, RegistarationByName
from jim.db import DataBaseServerORM
from jim.error.error import JIMPacketResponseExeption
from jim.event.event import (
    JimEvent,
    JimEventAuthClient,
    JimEventLogoutClient,
    JimEventNewClient,
    JimEventServerRun,
    JimEventServerStop,
)
from jim.logger.logger_func import log
from jim.packet.packet import JIMAction, JIMPacket, JIMPacketFieldName, ResponseGroup

logger = logging.getLogger("server")

db = DataBaseServerORM()


class ServerVerifier(type):
    def __init__(self, clsname, bases, clsdict):
        logger.debug(f"run metaclass")
        methods = set()
        attr = set()
        for key, value in clsdict.items():
            if hasattr(value, "__call__"):
                func = dis.get_instructions(value)
                for dec in func:
                    if dec.opname == "LOAD_METHOD":
                        methods.add(dec.argval)
                    elif dec.opname == "LOAD_ATTR":
                        attr.add(dec.argval)

        if "connect" in methods:
            raise ValueError("Please don`t set name 'connect' function on server")

        if not ("SOCK_STREAM" in attr and "AF_INET" in attr):
            raise ValueError("Socket must be run with AF_INET and SOCK_STREAM param")

        type.__init__(self, clsname, bases, clsdict)


class PortProperty:
    def __init__(self) -> None:
        self.name = "port"
        self.default = 7777
        self.type = int
        self.range = {"min": 1024, "max": 49151}
        logger.debug("init PortProperty")

    def __set__(self, instance, value):
        if not type(value) is self.type:
            error = f"wrong port type {value} is {type(value)}"
            logger.critical(error)
            raise ValueError(error)

        if value < self.range["min"] or value > self.range["max"]:
            error = (
                f"port is unbound {self.range['min']} < {value} < {self.range['max']}"
            )
            logger.critical(error)
            raise ValueError(error)

        instance.__dict__[self.name] = value
        logger.debug("set PortProperty")

    def __get__(self, instance, cls):
        logger.debug("get PortProperty")
        if instance is None:
            return self
        return instance.__dict__.get(self.name, self.default)


class JIMServer(metaclass=ServerVerifier):
    port = PortProperty()
    # db = DataBaseProperty()
    __socket: socket.socket
    __clients: set
    __out_event: "queue.SimpleQueue|None"  # for cli or gui
    __in_event: "queue.SimpleQueue|None"  # for cli or gui

    def __init__(
        self,
        event_in: "queue.SimpleQueue|None" = None,
        event_out: "queue.SimpleQueue|None" = None,
    ) -> None:
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__clients = set()  # ToDo: use JIMClient.__all_client__
        if event_in and event_out:
            self.__out_event = event_in
            self.__in_event = event_out
        else:
            self.__out_event = None
            self.__in_event = None

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
                    logger.warning(f"{packet.dict_} is BAD {packet.error.__str__()}")
                    client._send_packet(
                        JIMPacket.gen_answer(400, msg=f"{packet.error.__str__()}")
                    )
                    logger.debug(f"OUT {404} -> {client}")
                else:
                    logger.warning(f"{packet} is Good")
                    client._push_packet(packet)
            except:
                name = client.get_name()
                if name:
                    db.client_active_status(False, by_name=name, force_commit=True)
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
                            if not in_pack.get(JIMPacketFieldName.USER) or not in_pack[
                                JIMPacketFieldName.USER
                            ].get(JIMPacketFieldName.USER_NAME):
                                client._send_packet(
                                    JIMPacket.gen_answer(400, id_, msg="bad req")
                                )
                                continue
                            self.__authenticate_action(client, packet, id_, clients)
                            # if client reg add to db
                            name = client.get_name()
                            if name != None:
                                try:
                                    ip = client._get_ip()
                                    # ToDo: add error if ip no exist
                                    db.add_client(by_name=name)
                                    db.add_history(
                                        addr=ip, by_name=name, force_commit=True
                                    )
                                except Exception as ex:
                                    logger.error(f"DB: {ex}")
                        elif action == JIMAction.JOIN:
                            client._send_packet(JIMPacket.gen_answer(400, id_))

                        elif action == JIMAction.LEAVE:
                            client._send_packet(JIMPacket.gen_answer(400, id_))
                        elif action == JIMAction.MSG:
                            packet = (
                                packet.need_field(JIMPacketFieldName.TO)
                                .need_field(JIMPacketFieldName.FROM)
                                .need_field(JIMPacketFieldName.MESSAGE)
                                .need_field(JIMPacketFieldName.ENCODING)
                            )
                            if not packet.is_bad_packet():
                                self.__msg_action(client, packet, id_, clients)
                            else:
                                client._send_packet(
                                    JIMPacket.gen_answer(400, id_, msg=packet.error)
                                )
                        elif action == JIMAction.PRESENCE:
                            # self.__presence_action(client, packet, id_, clients)
                            logger.critical(client.status.client_type)
                        elif action == JIMAction.PRОBE:
                            # only server can send this
                            logger.warning(f"{client} send PRОBE")
                            # send 404
                            client._send_packet(
                                JIMPacket.gen_answer(400, id_, "Unsupport action")
                            )
                        elif action == JIMAction.QUIT:
                            name = client.get_name()
                            if name:
                                db.client_active_status(
                                    False, by_name=name, force_commit=True
                                )
                            client._send_jim_json({})
                            logger.debug(f"{client} logout.")
                            client.disconnect()
                            clients.remove(client)
                            self.add_event(
                                JimEventLogoutClient(client=client, packet=packet)
                            )

                        elif action == JIMAction.GET_CONTACTS:
                            packet = packet.need_field(JIMPacketFieldName.USER_LOGIN)

                            if not packet.is_bad_packet():
                                self.__get_contacts_action(client, packet, id_, clients)
                            else:
                                raise JIMPacketResponseExeption(
                                    JIMPacket.gen_answer(400, id_, msg=packet.error)
                                )
                        elif action == JIMAction.ADD_CONTACT:
                            packet = packet.need_field(
                                JIMPacketFieldName.USER_ID
                            ).need_field(JIMPacketFieldName.USER_LOGIN)

                            if not packet.is_bad_packet():
                                self.__add_del_contact_action(
                                    client, packet, id_, clients, cmd="add"
                                )
                            else:
                                client._send_packet(
                                    JIMPacket.gen_answer(400, id_, msg=packet.error)
                                )

                        elif action == JIMAction.DEL_CONTACT:
                            packet = packet.need_field(
                                JIMPacketFieldName.USER_ID
                            ).need_field(JIMPacketFieldName.USER_LOGIN)

                            if not packet.is_bad_packet():
                                self.__add_del_contact_action(
                                    client, packet, id_, clients, cmd="del"
                                )
                            else:
                                client._send_packet(
                                    JIMPacket.gen_answer(400, id_, msg=packet.error)
                                )
                        else:
                            logger.error(f"UNKNOWN ACTION {action}")
                            # send 400
                            client._send_packet(
                                JIMPacket.gen_answer(400, id_, "Unsupport action")
                            )
                    elif packet.is_field(JIMPacketFieldName.RESPOSE):
                        pass
                    else:
                        # send 400
                        client._send_packet(
                            JIMPacket.gen_answer(400, id_, msg="bad req")
                        )
                        logger.error(f"UNKNOWN {packet}")
                db.update()
            # ToDo
            # except JIMPacketResponseExeption as resp:
            #     client._send_packet(resp.jim_packet)
            #     if resp.need_logout:
            #         name = client.get_name()
            #         if name:
            #             db.client_active_status(False, by_name=name, force_commit=True)
            #             clients.remove(client)
            #             client.disconnect()
            #             logger.error(f"{client} is disconnected.")
            except Exception as ex:
                name = client.get_name()
                if name:
                    db.client_active_status(False, by_name=name, force_commit=True)
                clients.remove(client)
                client.disconnect()
                logger.error(f"{client} is disconnected.")
                logger.error(f"{str(ex)}.")
                self.emit_event(JimEventLogoutClient(client=client))

    def add_event(self, event):
        if self.__in_event:
            self.__in_event.put(event)

    def emit_event(self, cmd: JimEvent):
        if self.__out_event:
            self.__out_event.put(cmd)

    @log
    def __authenticate_action(
        self, client: JIMClient, packet: JIMPacket, id_: int, clients: set
    ):
        name = ""
        if packet.dict_:
            in_pack = packet.dict_
            name = in_pack[JIMPacketFieldName.USER][JIMPacketFieldName.USER_NAME]

        client_name = client.get_name()
        if client_name == name:
            client._send_packet(JIMPacket.gen_answer(400, id_, msg="already auth"))
            logger.warning(f"{client} try rereg by '{name}'")

            # return already auth
        elif client_name != name:
            # ToDo: find duplicates
            if name in [c.get_name() for c in clients]:
                client._send_packet(
                    JIMPacket.gen_answer(
                        400, id_, msg="client with this name alredy exist"
                    )
                )
                logger.debug(f"{client} duplicate reg by {name}")
                return
            client.status.client_type = RegistarationByName(name)
            contacts = db.get_contacts(by_name=name)
            if contacts:
                contacts = list(map(lambda orm: str(orm.name), contacts))
                client._send_packet(
                    JIMPacket.gen_answer(
                        200, id_, append_dict={ResponseGroup.ALERT.value: contacts}
                    )
                )
            else:
                client._send_packet(
                    JIMPacket.gen_answer(
                        200, id_, append_dict={ResponseGroup.ALERT.value: []}
                    )
                )
            logger.debug(f"{client} reg by '{name}'")
            self.add_event(JimEventAuthClient(client=client, packet=packet))
        else:
            client._send_packet(JIMPacket.gen_answer(400, id_, msg="no support reg"))

    def __msg_action(
        self, client: JIMClient, packet: JIMPacket, id_: int, clients: set
    ):
        logging.debug(f"{packet.dict_}")

        if not client.get_name():
            client._send_packet(JIMPacket.gen_answer(403, id_, msg="need auth"))
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

    def __get_contacts_action(
        self, client: JIMClient, packet: JIMPacket, id_: int, clients: set
    ):
        name = client.get_name()
        if not name:
            # need auth
            # raise NotImplementedError("need auth")
            client._send_packet(JIMPacket.gen_answer(401, to_id=id_, msg="need auth"))
            return

        in_pack = packet.dict_
        if not in_pack:
            # Think: how delete duplicate test
            # broken pack
            # raise NotImplementedError("broken packet")
            client._send_packet(JIMPacket.gen_answer(400, to_id=id_))
            return

        login_name = in_pack.get(JIMPacketFieldName.USER_LOGIN)
        if login_name != name:
            # some try hack
            # raise NotImplementedError("some try hack")
            client._send_packet(
                JIMPacket.gen_answer(400, to_id=id_, msg="Some error. Please reauth")
            )
            return

        # format db [clients] -> [name..]
        contacts = []
        db_contacts = db.get_contacts(by_name=login_name)

        if db_contacts:
            for db_client in db_contacts:
                contacts.append(db_client.name)

        # gan answer
        answer = JIMPacket.gen_answer(
            202, id_, append_dict={ResponseGroup.ALERT.value: contacts}
        )
        client._send_packet(answer)

    def __add_del_contact_action(
        self,
        client: JIMClient,
        packet: JIMPacket,
        id_: int,
        clients: set,
        cmd: str,  # add or del
    ):
        name = client.get_name()
        if not name:
            # need auth
            # raise NotImplementedError("need auth")
            client._send_packet(JIMPacket.gen_answer(401, to_id=id_, msg="need auth"))
            return

        in_pack = packet.dict_
        if not in_pack:
            # Think: how delete duplicate test
            # broken pack
            # raise NotImplementedError("broken packet")
            client._send_packet(JIMPacket.gen_answer(400, to_id=id_, msg="broken req"))
            return

        login_name = in_pack.get(JIMPacketFieldName.USER_LOGIN)
        if login_name != name:
            # some try hack
            # raise NotImplementedError("some try hack")
            client._send_packet(
                JIMPacket.gen_answer(
                    400, to_id=id_, msg="uncorrect auth. Please re auth"
                )
            )
            return

        friend_name = in_pack.get(JIMPacketFieldName.USER_ID)
        if not friend_name:
            client._send_packet(
                JIMPacket.gen_answer(
                    400,
                    to_id=id_,
                    msg="req no found field {JIMPacketFieldName.USER_ID}",
                )
            )
            return

        if login_name == friend_name:
            client._send_packet(
                JIMPacket.gen_answer(
                    400,
                    to_id=id_,
                    msg="Can`t add youself to contact",
                )
            )
            return

        db_self_client = db.get_client(by_name=login_name)

        db_friend = db.get_client(by_name=friend_name)

        if not db_self_client:
            client._send_packet(JIMPacket.gen_answer(400, to_id=id_))
            return

        if not db_friend:
            client._send_packet(
                JIMPacket.gen_answer(
                    400, to_id=id_, msg=f"Client with `{friend_name}` name not exist"
                )
            )
            logger.error(f"{client} try add no exit user {friend_name}")
            return

        if cmd == "add":
            # test if contact is exist
            if db_friend in db_self_client.contacts:
                raise NotImplemented
            db_self_client.contacts.append(db_friend)
        elif cmd == "del":
            if not db_friend in db_self_client.contacts:
                raise NotImplemented
            db_self_client.contacts.remove(db_friend)

        client._send_packet(JIMPacket.gen_answer(200, to_id=id_))

    def run(self, args):
        try:
            logger.setLevel(args.log)
            self.port = args.port  # if del this line port will be 7777
            self.__socket.bind((args.addr, self.port))
            self.__socket.listen(args.count)
            self.__socket.settimeout(0.5)
            logger.info(f"Server listen {args.addr}:{args.port}")
            self.emit_event(JimEventServerRun())

            while True:
                try:
                    client, addr = self.__socket.accept()
                except KeyboardInterrupt:
                    raise KeyboardInterrupt
                except:
                    # if timeout
                    pass
                else:
                    jimclient = JIMClient._from_server(client, addr)
                    self.__clients.add(JIMClient._from_server(client, addr))
                    self.add_event(JimEventNewClient(client=client))
                finally:
                    read_io = []
                    write_io = []

                    try:
                        logger.debug(f"Clients online: {len(self.__clients)}")
                        # logger.debug(f"Comands: {self.__commands.qsize()}")

                        read_io, write_io, _ = select.select(
                            self.__clients, self.__clients, [], 0
                        )
                        logger.debug(f"R:{len(read_io)} | W:{len(write_io)}")
                    except KeyboardInterrupt:
                        raise KeyboardInterrupt
                    except Exception as ex:
                        logger.critical(ex.__str__())

                    try:
                        cur_command = None
                        if self.__in_event and not self.__in_event.empty():
                            cur_event = self.__in_event.get()

                        # ToDo: convet to
                        # parse comands
                        # use comands
                        # for client in clients: client.update(read_io, write_io, clients)
                        if len(read_io):
                            self._all_read(cur_command, read_io, self.__clients)

                        self._all_answer(cur_command, write_io, self.__clients)
                    except KeyboardInterrupt:
                        raise KeyboardInterrupt

        except KeyboardInterrupt:
            self.emit_event(JimEventServerStop())
            # send to all client QUIT
            logger.warning(f"stop server")
            try:
                for client in self.__clients:
                    name = client.get_name()
                    if name:
                        db.client_active_status(False, by_name=name, force_commit=True)
                    client._send_packet(JIMPacket.gen_req(JIMAction.QUIT))
                    client.disconnect()
            except KeyboardInterrupt:
                logger.warning(f"Force stop server")
                self.__socket.shutdown(socket.SHUT_RDWR)
                self.__socket.close()
                return -1
            except Exception as ex:
                self.emit_event(JimEventServerStop())

            self.__socket.shutdown(socket.SHUT_RDWR)
            self.__socket.close()
            return 0
        except OSError:
            logger.critical(f"Port {args.port} already used.")
            return -1

    def __del__(self):
        try:
            self.__socket.shutdown(socket.SHUT_RDWR)
            self.__socket.close()
        except:
            pass


if __name__ == "__main__":
    # unittest
    pass
