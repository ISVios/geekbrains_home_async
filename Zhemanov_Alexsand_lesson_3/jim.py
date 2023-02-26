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


def parser_jim_answ(jim_bytes: bytes, error_type=None, **kwargs):
    # ToDo: add param encoding
    # ToDo: add param callback
    """
    Parse JIM bytes to string

    param   jim_bytes - jim bytes
    param   kwargs - !!!no use
    """
    enc = chardet.detect(jim_bytes).get("encoding") or "ascii"
    json_str = jim_bytes.decode(enc, "replace").encode("utf-8")
    try:
        dict_: dict = json.loads(json_str)
    except ValueError:
        # ToDo: add error
        return error_type
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

    if msg:
        error_group = response // 100
        if error_group in [1, 2]:
            dict_answ["alert"] = msg
        elif error_group in [3, 4]:
            dict_answ["error"] = msg
        else:
            # response = 500
            raise ValueError("unknow response")
    return json.dumps(dict_answ, **dumps_kwargs).encode(encoding)
