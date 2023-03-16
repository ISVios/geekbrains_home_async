"""
JIMError
"""

from typing import Any


class JIMError(Exception):
    pass


class JIMClientDisconnect(JIMError):
    pass


class JIMPacketNoExistField(JIMError):
    __slots__ = ["field_name"]

    def __init__(self, field_name: str, *args: object) -> None:
        super().__init__(*args)
        self.field_name = field_name

    def __str__(self) -> str:
        return f"No found  '{self.field_name}' field'"


class JIMPacketWrongValue(JIMError):
    __slots__ = ["field_name", "need_value", "many"]

    def __init__(self,
                 field_name: str,
                 need_value: Any,
                 many: bool = False,
                 *args: object) -> None:
        super().__init__(*args)
        self.field_name = field_name
        self.need_value = need_value
        self.many = many

    def __str__(self) -> str:
        many = "in" if self.many else "eq"
        return f"{self.field_name} not {many} {self.need_value}"
