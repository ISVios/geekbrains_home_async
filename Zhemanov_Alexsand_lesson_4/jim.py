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

JIM_MAX_LEN_ANSWER = 640

# class Answer
#
# class GoodAnswer(Answer):
#     package: dict
#
#
# class BadAnswer(Answer):
#     bytes_: bytes
#     error: ValueError


class JIM_ACTION(enum.Enum):
    AUTHENTICATE = "authenticate"
    JOIN = "join"
    LEAVE = "leave"
    MSG = "msg"
    PRESENCE = "presence"
    PRОBE = "probe"
    QUIT = "quit"


# Think: remake to builder pattern
def gen_jim_req(action: JIM_ACTION,
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


def parser_jim_answ(jim_bytes: bytes,
                    encoding="utf-8",
                    callbacks=None,
                    error_type=None,
                    **kwargs):  # -> Answer:
    """
    Parse JIM bytes to string

    param   jim_bytes - jim bytes
    param   kwargs - !!!no use
    """
    enc = chardet.detect(jim_bytes).get("encoding") or "ascii"
    json_str = jim_bytes.decode(enc, "replace").encode(encoding)

    try:
        dict_: dict = json.loads(json_str)
        if not callbacks is None:
            if type(callbacks) is "function":
                dict_ = callbacks(dict_)
            else:
                for fn_ in callbacks:
                    dict_ = fn_(dict_)
    except ValueError as err:
        # return BadAnswer(jim_bytes, err)
        return error_type
    # return GoodAnswer(dict_)
    return dict_


def correct_action(dict_: dict, msg="Packet have wrong action"):
    if not ("action" is dict_
            or dict_["action"] in JIM_ACTION._value2member_map_):
        raise ValueError(msg)
    return dict_


def timestamp_need(dict_: dict, error_msg="Packet no have timestamp"):
    return need_field(dict_, "time", error_msg)


def response_code_need(dict_: dict, error_msg="Packet no have response_code"):
    return need_field(dict_, "response", error_msg)


def need_field(dict_: dict, field: str, error_msg: str = ""):
    if not field in dict_:
        raise ValueError(error_msg)
    return dict_


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

    # ToDo: if response != 100-599
    #   Way: Ignore
    #   Way: Def value 500

    dict_answ = {
        "response": response,
        "time": int(datetime.now().timestamp()),
        **kwargs
    }

    error_group = response // 100
    if error_group in [1, 2]:
        if msg:
            dict_answ["alert"] = msg
    elif error_group in [3, 4, 5]:
        if msg:
            dict_answ["error"] = msg
    else:
        # response = 500
        raise ValueError("unknow response")
    return json.dumps(dict_answ, **dumps_kwargs).encode(encoding)
