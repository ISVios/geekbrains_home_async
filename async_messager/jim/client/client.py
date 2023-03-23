"""
JIMClient

1. Реализовать метакласс ClientVerifier, выполняющий базовую проверку класса «Клиент» (для
некоторых проверок уместно использовать модуль dis):
    отсутствие вызовов accept и listen для сокетов;
    использование сокетов для работы по TCP;
    ***отсутствие создания сокетов на уровне классов, то есть отсутствие конструкций такого 

вида:

    class Client:
        __socket = socket() 

***) данную задачу решить не могу так как, JIMClient является select элементом для JIMServer. 
Для практики можно реализовать дескриптор SocketProperty()
    class SocketProperty:
        __get__ - если socket не был установлен - создать новый(для клиента), иначе вернуть существующий(клиент/сервер)

И уже его проверить на наличие(и 'приватное' расположение)

class JIMClient:
    __socket = SocketProperty()

"""
import dis
import json
import logging
import queue
import socket
import sys
from datetime import datetime, timedelta
from select import select
from typing import Any

import jim.logger.logger_client
import jim.logger.logger_func
from jim.error.error import JIMClientDisconnect
from jim.packet import JIMPacket, JIMPacketConst
from jim.packet.packet import JIMAction, JIMPacketFieldName

# ToDO: get used logger
logger = logging.getLogger("client")
MAIN_MODULE = sys.modules.get("__main__") or None
if MAIN_MODULE and hasattr(MAIN_MODULE, __file__) and MAIN_MODULE.__file__:
    if MAIN_MODULE.__file__.find("server") > 0:
        logger = logging.getLogger("server")


class ClientVerifier(type):

    def __init__(self, clsname, bases, clsdict):

        BAD_METHOD = ["accept", "listen"]

        logger.debug("run metaclass ClientVerifier")

        attr = set()
        methods = set()
        for key, value in clsdict.items():
            ##test class:
            ##    __socket = SocketProperty() -> __socket == _{clsname}{value}

            if (type(value) == SocketProperty):
                if not key.startswith(f"_{clsname}"):
                    raise ValueError(
                        f"Field of 'SocketProperty' must be __{key} (start with __)"
                    )

            if hasattr(value, "__call__"):
                decompile_code = dis.get_instructions(value)
                for cmd in decompile_code:
                    if cmd.opcode == "LOAD_METHOD":
                        methods.add(cmd.argval)
                    elif cmd.opcode == "LOAD_ATTR":
                        attr.add(cmd.argval)

        for method in methods:
            if method in BAD_METHOD:
                raise ValueError(f"Use {BAD_METHOD} in code")

        type.__init__(self, clsname, bases, clsdict)


class SocketProperty:

    def __init__(self) -> None:
        self.name = "__socket"

    def __get__(self, instance, cls):
        _socket = instance.__dict__.get(self.name)
        if not _socket:
            _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            instance.__dict__[self.name] = _socket
            return _socket
        else:
            return _socket

    def __set__(self, instance, value):
        logger.debug("set SocketProperty")

        if not type(value) is socket.socket:
            raise ValueError("socket must be socket")

        _socket = self.__dict__.get(self.name)
        if _socket:
            logger.error(f"somewhere try reset exist socket")
        else:
            instance.__dict__[self.name] = value


class SendTo:
    __slots__ = ["name", "type_"]
    name: "str|None"
    type_: "str|None"

    def __init__(self) -> None:
        self.name = None

    @classmethod
    def user(cls, user_name: str) -> "SendTo":
        to = SendTo()
        to.name = user_name
        to.type_ = "user"
        return to

    @classmethod
    def group(cls, group_name: str) -> "SendTo":
        to = SendTo()
        to.name = group_name
        to.type_ = "group_name"
        return to


class RegistarationBy:
    __slots__ = ["name"]

    def __init__(self) -> None:
        self.name = None


class RegistarationByGuest(RegistarationBy):

    def __init__(self) -> None:
        super().__init__()


class RegistarationByName(RegistarationBy):

    def __init__(self, _name: "str"):
        self.name = _name


# class RegistarationByToken(RegistarationBy):
#     __slots__ = ["token"]
#
#     def __init__(self, token: str) -> None:
#         self.token = token
#
#
# class ResetRegistration(RegistarationBy):
#     __slots__ = []
#


class JIMCllientStatus:
    __slots__ = ["client_type", "groups", "probe", "model"]
    client_type: RegistarationBy
    groups: set
    probe: "JIMClientProbe"
    model: "Any"


class JIMClientProbe:
    __slots__ = ["__next_time", "__try_count"]
    __next_time: datetime
    __try_count: int

    def __init__(self, delta: timedelta = timedelta(hours=1)) -> None:
        self.__next_time = datetime.now() + delta
        self.__try_count = 0

    def need_probe(self) -> bool:
        cur_time = datetime.now()
        return self.__next_time <= cur_time

    def update_probe(
        self,
        reset_counter: bool = False,
        delta: timedelta = timedelta(hours=1)
    ) -> None:
        self.__next_time += delta
        self.__try_count = 0 if reset_counter else self.__try_count

    def try_reconnect(self,
                      max_try: int = 10,
                      delta: timedelta = timedelta(hours=1)) -> bool:
        if self.__try_count >= max_try:
            return False

        self.update_probe(delta=delta)
        return True


class JIMClient(metaclass=ClientVerifier):
    __all_client__: "None|set" = None
    __socket = SocketProperty()
    # __socket: socket.socket
    __status: JIMCllientStatus
    __recive_packet: queue.SimpleQueue
    __to_send: queue.SimpleQueue
    __wait_packet: dict
    type_ = "client"

    def fileno(self) -> int:
        return self.__socket.fileno()

    def _model(self):
        return self.__status.model

    def __init__(self,
                 host: "str|None" = None,
                 port: "str|None" = None,
                 _socket: "socket.socket|None" = None,
                 _ip: "socket._RetAddress|None" = None) -> None:

        if _socket:
            # server mode
            self.__socket = _socket
            self.__ip = _ip
        else:
            self.__socket.connect((host, port))
            logger.debug(f"connect to {host}:{port}")

        self.__status = JIMCllientStatus()

        self.__status.client_type = RegistarationBy()
        self.__status.groups = set(["___ALL___"])
        self.__status.model = None

        self.__recive_packet = queue.SimpleQueue()
        self.__to_send = queue.SimpleQueue()
        self.__wait_packet = {}

        if _socket:
            self.__status.probe = JIMClientProbe()

    @jim.logger.logger_func.log
    def registaration(self, by: RegistarationBy):

        if type(by) is RegistarationByGuest:
            pack = JIMPacket.gen_req(JIMAction.PRESENCE)
            return

        def _a(*args, **kwargs):
            pack = kwargs.get("pack")
            answer = kwargs.get("answer")
            client = kwargs.get("client")
            name = by.name
            res = kwargs.get("res")
            if client and name:
                if answer and answer.is_field(JIMPacketFieldName.RESPOSE):
                    response = answer.dict_[JIMPacketFieldName.RESPOSE]
                    if response == 200:
                        self.status.client_type = RegistarationByName(name)
                logger.debug(f"WAITANSWER {pack} -> {answer}")

            if res:
                res.append((pack, answer))

        # gen auth pack
        pack = JIMPacket.gen_req(JIMAction.AUTHENTICATE,
                                 append_dict={
                                     JIMPacketFieldName.USER: {
                                         JIMPacketFieldName.USER_NAME: by.name
                                     }
                                 })
        pack.calback = _a
        self._reg_wait_answert(pack)
        self._push_packet_to(pack)

    @jim.logger.logger_func.log
    def send_msg_to(self, to: SendTo, message: str) -> None:

        if not self.get_name():
            logger.error("no auth user can`t send messages")
            return

        if not to.name:
            logger.error("Wrong user")
            return

        if len(message) >= JIMPacketConst.MAX_MSG_MESSAGE:
            logger.error(
                "Max message size is {JIMPacketConst.MAX_MSG_MESSAGE}")

        msg_to = to.name
        if to.type_ == "group_name":
            logger.debug("Send to group")
            if msg_to[0] != "#":
                msg_to = "#" + msg_to

        pack = JIMPacket.gen_req(JIMAction.MSG,
                                 append_dict={
                                     JIMPacketFieldName.FROM: self.get_name(),
                                     JIMPacketFieldName.TO: msg_to,
                                     JIMPacketFieldName.ENCODING: "utf-8",
                                     JIMPacketFieldName.MESSAGE: message
                                 })

        def _a(*args, **kwargs):
            pack = kwargs.get("pack")
            answer = kwargs.get("answer")
            logger.debug(f"WAITANSWER {pack} -> {answer}")

        pack.calback = _a
        self._reg_wait_answert(pack)
        self._push_packet_to(pack)

    def _reg_wait_answert(self, pack: JIMPacket):
        if pack and pack.dict_:
            id_ = pack.dict_[JIMPacketFieldName.TIME]
            self.__wait_packet[id_] = pack
            logger.debug("REG WAIT PACK {id_}")

    @jim.logger.logger_func.log
    def get_groups(self, ) -> set[str]:
        return self.__status.groups

    @jim.logger.logger_func.log
    def in_group(self, group_name: str) -> bool:
        logger.debug(f"{group_name} in {self.__status.groups}")
        return group_name in self.__status.groups

    @jim.logger.logger_func.log
    def get_name(self, ) -> "None|str":
        if self.__status and type(
                self.status.client_type) is RegistarationByName:
            return self.status.client_type.name

        return None

    @jim.logger.logger_func.log
    def join_grop(self, group_name: str):
        # gen join pack
        # put in send queue
        # add callback func when reg or no reg
        # add wait packet
        raise NotImplemented

    @jim.logger.logger_func.log
    def leave_group(self, group_name: str):
        # gen leave pack
        # put in send queue
        # add callback func when reg or no reg
        # add wait packet
        raise NotImplemented

    @jim.logger.logger_func.log
    def _logout(self, ):
        pass  #self.registaration(ResetRegistration())

    @property
    @jim.logger.logger_func.log
    def status(self):
        return self.__status

    @jim.logger.logger_func.log
    def disconnect(self, ):
        if JIMClient.__all_client__:
            JIMClient.__all_client__.remove(self)

        self.__socket.close()
        logger.debug(f"{self} is disconnect.")

    @jim.logger.logger_func.log
    def _send_bytes(self, bytes_: bytes) -> None:
        try:
            self.__socket.send(bytes_)
        except:
            logger.warning(f"{self} is disconnect")
            raise JIMClientDisconnect(self)

    @jim.logger.logger_func.log
    def _send_jim_json(self, jim_dict: dict, encoding: str = "utf-8") -> None:
        str_: str = json.dumps(jim_dict)
        bytes_ = str_.encode(encoding).ljust(JIMPacketConst.MAX_SIZE)
        self._send_bytes(bytes_)

    @jim.logger.logger_func.log
    def _send_packet(self, packet: JIMPacket, encoding: str = "utf-8"):
        "only send."
        if packet.dict_:
            self._send_jim_json(packet.dict_, encoding=encoding)
        # ToDo: add eror if pack is bad

    # @jim.logger.logger_func.log
    def _send_in_stack(self, ):
        if not self.__to_send.empty():
            self._send_packet(self.__to_send.get())
            logger.debug(f"pack -> {self}")

    @jim.logger.logger_func.log
    def _recive_bytes(self, size: int = JIMPacketConst.MAX_SIZE) -> bytes:
        # try:
        bytes_ = self.__socket.recv(size)
        if bytes == b"":
            raise JIMClientDisconnect(self)
        return bytes_
        # except:
        # logger.warning(f"{self} is disconnect")
        # raise JIMClientDisconnect(self)

    @jim.logger.logger_func.log
    def _recive_jim_json(self, encoding: str = "utf-8") -> dict:
        bytes_ = self._recive_bytes()
        str_ = bytes_.decode(encoding, "replace")
        dict_ = json.loads(str_)
        return dict_

    @jim.logger.logger_func.log
    def _get_ip(self):
        return self.__ip

    @jim.logger.logger_func.log
    def _recive_packet(self, ) -> "JIMPacket|None":
        "only recive. no stack"
        return JIMPacket(from_dict=self._recive_jim_json())

    @jim.logger.logger_func.log
    def _push_packet(self, packet: JIMPacket):
        self.__recive_packet.put(packet)

    @jim.logger.logger_func.log
    def _push_packet_to(self, packet: JIMPacket):
        logger.debug(f" {packet} to send stack")
        self.__to_send.put(packet)

    @jim.logger.logger_func.log
    def _pop_packet(self) -> "JIMPacket|None":
        if not self.__recive_packet.empty():
            return self.__recive_packet.get()
        return None

    @jim.logger.logger_func.log
    def update_wait(self, packet: JIMPacket, id_: int):
        cal: "JIMPacket|None" = self.__wait_packet.get(id_)
        if cal:
            cal._answer(pack=cal, answer=packet, client=self)
            del self.__wait_packet[id_]

    def _push_packet_by(self,
                        packet: JIMPacket,
                        name: "str|None" = None,
                        group: "str|None" = None):
        if self.__status:
            if group and self.in_group(group):
                self.__to_send.put(packet)
                logger.debug(f"OUT {packet} -> GROUP({group})")
            elif name and name == self.get_name():
                self.__to_send.put(packet)
                logger.debug(f"OUT {packet} -> USER({name})")

    def __str__(self) -> str:
        # ToDo
        return "JIMClient"

    # @jim.logger.logger_func.log
    def update_status(self):
        try:

            read, write, _ = select((self, ), (self, ), [], 0)

            if read:
                pack = self._recive_packet()
                if pack and pack.dict_ and pack.is_field("id"):
                    logger.debug(f"SERVER -> {pack.dict_}")
                    id_ = pack.dict_["id"]
                    self.update_wait(pack, id_)

                if pack and pack.dict_ and pack.is_field(
                        JIMPacketFieldName.ACTION):

                    if pack.is_field_value(JIMPacketFieldName.ACTION,
                                           JIMAction.MSG):
                        msg = pack.dict_
                        # logger.debug(f"IN {pack.dict_}")
                        logger.debug(f"{msg['from']}: {msg['message']}")

            if write:
                self._send_in_stack()

        except KeyboardInterrupt:
            exit(0)
        except JIMClientDisconnect:
            exit(0)

    def wait(self) -> int:
        return len(self.__wait_packet)

    @classmethod
    @jim.logger.logger_func.log
    def _from_server(cls, socket: socket.socket, addr) -> "JIMClient":
        if not cls.__all_client__:
            cls.__all_client__ = set()
        client = JIMClient(_socket=socket, _ip=addr)

        cls.__all_client__.add(client)
        logger.debug("some connect {client}")
        return client


if __name__ == "__main__":
    import unittest

    class TESTJIMClientMetaGood(metaclass=ClientVerifier):
        __socket = SocketProperty()

    class TESTJIMClientMetaBad(metaclass=ClientVerifier):
        socket = SocketProperty()

    class TESTJIMClient(unittest.TestCase):
        pass

    unittest.main()
