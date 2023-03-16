"""
JIMPacket
"""

import datetime
import enum
import json
from typing import Any, Callable

from jim.error import JIMPacketNoExistField, JIMPacketWrongValue


class JIMPacketConst:
    # Think: make a size header of packet
    # JIM_PACKET_BYTES_SIZE = 2
    MAX_SIZE = 640
    MAX_MSG_MESSAGE = 500
    DUMPS_KWARGS = {"indent": 4, "ensure_ascii": False, "sort_keys": True}

    @classmethod
    def reg_calback(cls, recv_pack, answer_pack, client):
        pass


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


class JIMPacketFieldName:
    TIME = "time"
    ACTION = "action"
    MESSAGE = "message"
    RESPOSE = "response"
    USER = "user"
    USER_NAME = "account_name"
    USER_PASSWORD = "password"
    FROM = "from"
    TO = "to"
    MESSAGE = "message"
    ENCODING = "encoding"


class ResponseGroup(enum.Enum):
    ALERT = "alert"
    ERROR = "error"
    UNKNOWN = ""

    def __eq__(self, str_value: str):
        return self.value == str_value


# todo add clone
class JIMPacket:
    __slots__ = ["bytes_", "str_", "dict_", "error", "calback"]

    bytes_: "bytes|None"
    str_: "str|None"
    dict_: "dict|None"
    error: "Exception|None"
    calback: "Callable|None"

    def __init__(self,
                 from_bytes: "bytes|None" = None,
                 from_str: "str|None" = None,
                 from_dict: "dict|None" = None,
                 from_packet: "JIMPacket|None" = None,
                 calback_func: "Callable|None" = None,
                 packet_encoding: str = "utf-8",
                 append_dict: dict = {}) -> None:
        self.bytes_ = from_bytes
        self.str_ = from_str
        self.dict_ = from_dict
        self.calback = calback_func

        # ToDo: Add if user isert all from
        # all(from_bytes, from_str, from_bytes) -> Exception
        # only one from

        if from_packet:
            self.bytes_ = from_packet.bytes_
            self.str_ = from_packet.str_
            self.dict_ = from_packet.dict_
            self.error = from_packet.error
            return

        try:
            if self.bytes_:
                try:
                    self.str_ = self.bytes_.decode(packet_encoding)
                except Exception as ex:
                    self.error = ex
                    return

            if self.str_:
                try:
                    self.dict_ = json.loads(self.str_.strip())
                except Exception as ex:
                    self.error = ex
                    return

            if self.dict_ and append_dict:
                self.dict_.update(append_dict)

            self.error = None
        except Exception as ex:
            self.error = ex

    def is_field(self, field_name: str, only_good: bool = False) -> bool:
        if only_good and (not self.error == None):
            return False

        if self.dict_:
            return field_name in self.dict_

        return False

    def is_field_value(self,
                       field_name: str,
                       value: Any,
                       many: bool = False,
                       only_good: bool = False) -> bool:
        if not self.is_field(field_name, only_good=only_good):
            return False

        if self.dict_:
            dict_value = self.dict_.get(field_name)
            if many:
                return value in dict_value
            else:
                return value == dict_value

        return False

    def need_field(self, field_name: str) -> "JIMPacket":

        if not self.is_field(field_name, only_good=True):
            # Think: convert to copy
            bad_packet = JIMPacket(from_packet=self)
            bad_packet.error = JIMPacketNoExistField(field_name)
            return bad_packet

        return self

    def need_field_value(self,
                         field_name: str,
                         value: Any,
                         many: bool = False) -> "JIMPacket":
        field_test = self.need_field(field_name)
        if field_test.is_bad_packet():
            return field_test

        if not field_test.is_field_value(
                field_name, value, many=many, only_good=True):
            bad_packet = JIMPacket(from_packet=self)
            bad_packet.error = JIMPacketWrongValue(field_name, value, many)
            return bad_packet

        return self

    def _answer(self, func: "Callable|None" = None, *args, **kwargs):
        """
        what do if packet have answer

        """

        if func:
            func(*args, **kwargs)
            return

        if self.calback:
            self.calback(*args, **kwargs)

    def is_bad_packet(self):
        return not self.error == None

    def empty(self):
        return self.dict_ == None

    @classmethod
    def gen_req(
        cls,
        action: JIMAction,
        # packet_encoding: str = "utf-8",
        # dumps_kwargs=JIMPacketConst.DUMPS_KWARGS,
        append_dict: dict = {}):
        dict_req: dict = {
            JIMPacketFieldName.ACTION: action.value,
            JIMPacketFieldName.TIME: int(datetime.datetime.now().timestamp())
        }

        dict_req.update(append_dict)

        return JIMPacket(from_dict=dict_req)

    @classmethod
    def gen_answer(
            cls,
            response: int,
            to_id: "int|None" = None,
            msg: "str|None" = None,
            # packet_encoding: str = "utf-8",
            # dumps_kwargs=JIMPacketConst.DUMPS_KWARGS,
            append_dict: dict = {},
            calback_func: "Callable|None" = None):
        dict_answer: dict = {
            JIMPacketFieldName.RESPOSE: response,
            JIMPacketFieldName.TIME: int(datetime.datetime.now().timestamp())
        }

        if to_id:
            dict_answer["id"] = to_id

        if msg:
            msg_group = JIMPacket.response_group(response)
            if msg_group.value:
                dict_answer[msg_group.value] = msg
            else:
                dict_answer[JIMPacketFieldName.RESPOSE] = 500

        dict_answer.update(append_dict)

        return JIMPacket(from_dict=dict_answer, calback_func=calback_func)

    @classmethod
    def response_group(cls, response: int) -> ResponseGroup:
        msg_group = response // 100
        if msg_group in [1, 2]:
            return ResponseGroup.ALERT

        if msg_group in [3, 4, 5]:
            return ResponseGroup.ERROR

        return ResponseGroup.UNKNOWN

    def __str__(self) -> str:
        if self.dict_:
            if self.dict_.get(JIMPacketFieldName.ACTION):
                return f"JIMRequest({self.dict_['action']})"
            elif self.dict_.get(JIMPacketFieldName.RESPOSE):
                return f"JIMResponse({self.dict_['response']})"
            else:
                return f"JIMPacket({self.dict_})"
        return "Empty JIMPacket"


if __name__ == "__main__":
    # ToDo
    import unittest

    class TestPacket(unittest.TestCase):

        def test__gen_req(self):
            print()
            req_pack = JIMPacket.gen_req(JIMAction.QUIT,
                                         append_dict={
                                             "a": 1,
                                             "b": "c",
                                             "user": {
                                                 "a": 1,
                                                 "b": "c"
                                             }
                                         })
            print(req_pack)

        def test__gen_answer(self):
            print()
            answer_pack = JIMPacket.gen_answer(801,
                                               to_id=123456,
                                               msg="Test test")
            print(answer_pack)

    unittest.main()
