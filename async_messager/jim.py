"""
JIM quick method, var
"""
import abc
import enum
import json
import logging
import queue
import socket
import time
from datetime import datetime, timedelta
from typing import Iterable

import chardet

import func_decorator as decorator

JIM_MAX_LEN_ANSWER = 640
JIM_COMMON_PROBE_STEP = timedelta(hours=1)


class Answer:
    tested: bool

    def __init__(self) -> None:
        self.tested = False


class GoodAnswer(Answer):
    answer: dict

    @property
    def error(self):
        return None

    def __init__(self, dict_: dict) -> None:
        super().__init__()
        self.answer = dict_


class BadAnswer(Answer):
    bytes_: bytes
    error: ValueError

    def __init__(self, bytes_: bytes, error: ValueError) -> None:
        super().__init__()
        self.bytes_ = bytes_
        self.error = error


class JIMAction(enum.Enum):
    AUTHENTICATE = "authenticate"  # aut on server
    JOIN = "join"  # join chat
    LEAVE = "leave"  # leave chat
    MSG = "msg"  # send messages
    PRESENCE = "presence"  # client answer alive test
    PRОBE = "probe"  # server alive client test
    QUIT = "quit"  # disconected server

    def __eq__(self, str_value: str):
        return self.value == str_value


class ClientType(enum.Enum):
    Unvalid = -1
    Anon = 0
    Auth = 1


class Client:
    __all_clients_name_: set = set()

    _probe_send: int
    _socket: socket.socket
    _next_proble_time: datetime
    _groups: set
    _stack_msg: queue.SimpleQueue
    _name: "str|None"
    _type: ClientType

    def fileno(self) -> int:
        return self._socket.fileno()

    def close(self) -> None:
        if self.auth_type() == ClientType.Auth:
            Client.__all_clients_name_.remove(self.name)
        self._socket.close()

    def in_group(self, group_name: str) -> bool:
        """
        """
        # ToDo: convert "[#]group_name" -> "#___group_name___"
        return group_name in self._groups

    # Think: add try except
    def recive(self, size: int = JIM_MAX_LEN_ANSWER) -> bytes:
        return self._socket.recv(size)

    # Think: add try except
    def send(self, bytes_: bytes) -> None:
        self._socket.send(bytes_)

    def __init__(self, _socket, delta_probe: "timedelta|None" = None) -> None:
        self._name = None
        self._type = ClientType.Unvalid
        self._groups = set(["#___ALL___"])
        self._stack_msg = queue.SimpleQueue()
        self._socket = _socket
        self._probe_send = 0
        self._next_proble_time = datetime.now() + (
            JIM_COMMON_PROBE_STEP if delta_probe is None else delta_probe)

    @property
    def name(self):
        return self._name

    @name.setter
    def name_set(self, value: str):
        if not self._name:
            self._name = value

    def push_answer(self, msg: Answer):
        self._stack_msg.put(msg)

    def update_probe(self,
                     presence_recive=False,
                     delta: timedelta = timedelta(hours=1)) -> None:
        self._next_proble_time = datetime.now() + delta
        if presence_recive:
            self._probe_send = 0

    def auth_type(self):
        return self._type

    @decorator.log
    def reg(self, name: str, type_: ClientType = ClientType.Auth):
        self._type = type_
        self._name = name
        Client.__all_clients_name_.add(name)

    @decorator.log
    def un_reg(self):

        if self._type != ClientType.Auth:
            return

        Client.__all_clients_name_.remove(self.name)
        self._type = ClientType.Anon
        self._name = None

    def need_probe(self):
        return self._next_proble_time < datetime.now()

    def long_no_answer_on_probe(self, max_probe: int = 10) -> bool:
        self._probe_send += 1
        return self._probe_send > max_probe

    def count_probe_send(self) -> int:
        return self._probe_send

    def pop_answer(self) -> dict:
        return self._stack_msg.get()

    def can_read(self) -> bool:
        return not self._stack_msg.empty()

    # def read_package(self, wish: "None" = None) -> JIMPackage:
    #     bytes_pack = self._socket.recv(JIM_MAX_LEN_ANSWER)
    #     raise NotImplementedError()

    # Think: move send answer here
    # Think: add send_probe()

    def __str__(self) -> str:
        if self.auth_type() == ClientType.Anon:
            return f"Anon({self._socket})"
        if self.auth_type() == ClientType.Auth:
            return f"{self._name} {self._socket}"
        else:
            return super().__str__()

    @classmethod
    @decorator.log
    def can_reg(cls, name: str) -> bool:
        return not name in cls.__all_clients_name_


class ResponseGroup(enum.Enum):
    Alert = "alert"
    Error = "error"
    Unknown = None


# Think: remake to builder pattern
@decorator.log
def gen_jim_req(action: JIMAction,
                dumps_kwargs: dict = {
                    "indent": 4,
                    "ensure_ascii": False,
                    "sort_keys": True
                },
                bytes_encoding="utf-8",
                **kwargs):
    """
    Genirate JIM request

    param   action -
    param   dumps_kwargs - json kwargs
    param   encoding - result string encoding
    param   kwargs - 
    """
    dict_req = {
        "action": action.value,
        "time": int(datetime.now().timestamp()),
        **kwargs
    }
    str_ = json.dumps(dict_req, **dumps_kwargs).ljust(JIM_MAX_LEN_ANSWER)
    return str_.encode(bytes_encoding)


@decorator.log
def parser_jim_answ(jim_bytes: bytes,
                    bytes_encoding="utf-8",
                    callbacks=None):  # -> Answer:
    """
    Parse JIM bytes to string

    param   jim_bytes - jim bytes
    param   callbacks - iter[functions(dic) -> dict]
    """
    enc = chardet.detect(jim_bytes).get("encoding") or "ascii"
    json_str = jim_bytes.decode(enc, "replace").encode(bytes_encoding)

    try:
        dict_: dict = json.loads(json_str)
        if not callbacks is None:
            if callable(callbacks):
                dict_ = callbacks(dict_)
            else:
                for fn_ in callbacks:
                    dict_ = fn_(dict_)
    except ValueError as err:
        return BadAnswer(jim_bytes, err)
    return GoodAnswer(dict_)


@decorator.log
def correct_action(error_msg="Package have wrong action"):
    return need_field_value("action",
                            JIMAction._value2member_map_,
                            many=True,
                            error_msg=error_msg)


@decorator.log
def is_response(response, many=False):
    return need_field_value("response", response, many=many)


@decorator.log
def is_action(action: "JIMAction|list[JIMAction]", many=False):
    return need_field_value("action", action, many=many)


@decorator.log
def response_group(response: int):
    msg_group = response // 100
    if msg_group in [1, 2]:
        return ResponseGroup.Alert
    elif msg_group in [3, 4, 5]:
        return ResponseGroup.Error

    return ResponseGroup.Unknown


def correct_time(dict_: dict):
    need_field("time")(dict_)
    cur_time = datetime.now()
    package_time = datetime.fromtimestamp(dict_[time])

    if package_time > cur_time:
        raise ValueError("Package from future")

    return dict_


@decorator.log
def time_need(dict_: dict, error_msg="Package no have timestamp"):
    return need_field("time", error_msg)(dict_)


@decorator.log
def response_need(dict_: dict, error_msg="Package no have response_code"):
    return need_field("response", error_msg)(dict_)


@decorator.log
def need_field(field: str, error_msg: "str|None" = None):
    """
    curring function to test field

    use:
        parser_jim_answ(callbacks=[need_field('some_field')])

    param   field(str) - name of field
    param   error_msg(str) - what text raise in error(ValueError)

    return  lambda of '__need_field'
    """

    # Think: about error_msg format -> lambda dict, feed -> str
    def __need_field(dict_: dict, field: str):
        ERROR_TEMPLATE = f"No found {field} in {dict_}"
        if not field in dict_:
            if error_msg is None:
                raise ValueError(ERROR_TEMPLATE)
            else:
                raise ValueError(error_msg)
        return dict_

    return lambda dict_: __need_field(dict_, field)


@decorator.log
def need_field_value(field: str,
                     value,
                     many=False,
                     error_msg: "str|None" = None):
    """
    curring function 
    return __need_field_value
    """

    def __need_field_value(dict_: dict, field: str, value, many: bool):

        need_field(field)(dict_)

        ERROR_TEMPLATE = f"Field {dict_[field]} in {dict_} on eq {value}"
        error = False
        if many:
            if not dict_[field] in value:
                error = True
        else:
            if dict_[field] != value:
                error = True

        if error:
            if error_msg is None:
                raise ValueError(ERROR_TEMPLATE)
            else:
                raise ValueError(error_msg)

        return dict_

    return lambda dict_: __need_field_value(dict_, field, value, many)


@decorator.log
def gen_jim_answ(response: int,
                 msg=None,
                 encoding="utf-8",
                 dumps_kwargs={
                     "indent": 4,
                     "ensure_ascii": False,
                     "sort_keys": True
                 },
                 **kwargs):
    """
    Genirate JIM answer
    
    param   response - HTML presponse status code. exam: 100-599
    param   encoding -  
    param   dumps_kwargs -
    param   kwargs -
    """

    dict_answ = {
        "response": response,
        "time": int(datetime.now().timestamp()),
        **kwargs
    }

    msg_group = response_group(response)
    if msg_group == ResponseGroup.Alert:
        if msg:
            dict_answ["alert"] = msg
    elif msg_group == ResponseGroup.Error:
        if msg:
            dict_answ["error"] = msg
    else:
        # response = 500
        raise ValueError("unknow response")
    return json.dumps(dict_answ, **dumps_kwargs).encode(encoding)
