"""
JIM quick method, var

JIM ALGORIM

JIM SERVER  |   | JIM CLIENT
create sever|   |
wait_client |<--- connect
recv        |<--- send presence
test recv   |   |
send answ   ----> parse answ

_____________________________ Server client test online
send probe  ----> parse
parse       <---- send presence


_____________________________ LOOP
parse act   <---- send act
send answ   ----> parse answ
LOOP


_____________________________ Client Quit
            <---- send quit
            |   X quit
"""
import enum
import json
from datetime import datetime

import chardet

import func_decorator as decorator

JIM_MAX_LEN_ANSWER = 640


class ResponseGroup(enum.Enum):
    Alert = "alert"
    Error = "error"
    Unknown = None


class Answer:
    pass


class GoodAnswer(Answer):
    answer: dict

    # Think:  add error -> None

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
    AUTHENTICATE = "authenticate"
    JOIN = "join"
    LEAVE = "leave"
    MSG = "msg"
    PRESENCE = "presence"
    PRОBE = "probe"
    QUIT = "quit"


# Think: remake to builder pattern
@decorator.log
def gen_jim_req(action: JIMAction,
                dumps_kwargs={
                    "indent": 4,
                    "ensure_ascii": False,
                    "sort_keys": True
                },
                encoding="utf-8",
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
    return json.dumps(dict_req, **dumps_kwargs).encode(encoding)


@decorator.log
def parser_jim_answ(jim_bytes: bytes,
                    encoding="utf-8",
                    callbacks=None):  # -> Answer:
    """
    Parse JIM bytes to string

    param   jim_bytes - jim bytes
    param   callbacks - iter[functions(dic) -> dict]
    """
    enc = chardet.detect(jim_bytes).get("encoding") or "ascii"
    json_str = jim_bytes.decode(enc, "replace").encode(encoding)

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
def correct_action(dict_: dict, error_msg="Packet have wrong action"):
    return need_field_value(dict_,
                            "action",
                            JIMAction._value2member_map_,
                            many=True)


@decorator.log
def is_response(dict_: dict, response: int, error_msg=None):
    return need_field_value(dict_, "response", response)


@decorator.log
def is_action(dict_: dict, action: JIMAction, error_msg=None):
    # correct_action(dict_)
    return need_field_value(dict_, "action", action.value)


@decorator.log
def response_group(response: int):
    msg_group = response // 100
    if msg_group in [1, 2]:
        return ResponseGroup.Alert
    elif msg_group in [3, 4, 5]:
        return ResponseGroup.Error

    return ResponseGroup.Unknown


@decorator.log
def time_need(dict_: dict, error_msg="Packet no have timestamp"):
    return need_field(dict_, "time", error_msg)


@decorator.log
def response_need(dict_: dict, error_msg="Packet no have response_code"):
    return need_field(dict_, "response", error_msg)


@decorator.log
def need_field(dict_: dict, field: str, error_msg: str = "No found field {}"):
    # Think: about error_msg format -> lambda dict, feed -> str
    if not field in dict_:
        raise ValueError(error_msg)
    return dict_


@decorator.log
def need_field_value(dict_: dict,
                     field: str,
                     value,
                     many=False,
                     error_msg: str = "field no eq value"):
    need_field(dict_, field)

    if many:
        if not dict_[field] in value:
            raise ValueError(error_msg)
    else:
        if dict_[field] != value:
            raise ValueError(error_msg)

    return dict_


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
