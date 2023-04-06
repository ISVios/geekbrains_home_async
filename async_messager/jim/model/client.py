from datetime import datetime

from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base, relationship


ClientTables = declarative_base()


class ClientModel(ClientTables):
    __tablename__ = "client"

    id = Column(Integer, primary_key=True)
    name = Column(
        String(80), unique=True, nullable=False, default="", server_default=""
    )

    messages = relationship("MesagesModel", back_populates="to")

    def __init__(self, name: str) -> None:
        super().__init__()
        self.name = name

    def __repr__(self) -> str:
        return f"ClientModel[{self.id}]({self.name})"

    def __str__(self) -> str:
        return f"ClientModel[{self.id}]({self.name})"


class MesagesModel(ClientTables):
    __tablename__ = "message"

    id = Column(Integer, primary_key=True)
    to_id = Column(ForeignKey("client.id"))
    message = Column(Text)
    time = Column(DateTime, nullable=False, default=datetime.now())

    to = relationship("ClientModel", back_populates="messages")

    def __init__(self, msg: str, time: datetime = datetime.now()) -> None:
        super().__init__()
        self.message = msg
        self.time = time

    def __repr__(self) -> str:
        return f"MSG[{self.id}]({self.to.name}):\t{self.message}"

    def __str__(self) -> str:
        return f"MSG[{self.id}]({self.to.name}):\t{self.message}"
