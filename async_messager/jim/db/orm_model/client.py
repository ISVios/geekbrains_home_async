from datetime import datetime

import sqlalchemy
from sqlalchemy import (DATETIME, Boolean, Column, DateTime, ForeignKey,
                        Integer, String, Table, Text, sql)
from sqlalchemy.orm import (Session, declarative_base, mapped_column,
                            relationship, sessionmaker)

Model = declarative_base()

# client_client_contact = Table("client_client_contact", Model.metadata,
#                               Column("owner_id", Integer, ForeignKey("")),
#                               Column("client_id", Integer, ForeignKey()),
#                               )

client_contact = sqlalchemy.Table(
    "client_contact",
    Model.metadata,
    Column("owner_id", Integer, ForeignKey("client.id"), primary_key=True),
    Column("client_id", Integer, ForeignKey("client.id"), primary_key=True),
)


# Think add to JIMClient in Server
class ClientModel(Model):
    __tablename__ = "client"

    id = Column(Integer, primary_key=True)
    name = Column(String(120),
                  unique=True,
                  nullable=False,
                  default="",
                  server_default="")

    active = Column(Boolean, nullable=False, default=True)

    # Think: what was there
    info = Column(Text, nullable=True, default="", server_default="")

    history = relationship("ClientHistoryModel", back_populates="client")

    contacts = relationship("ClientModel",
                            secondary=client_contact,
                            primaryjoin=id == client_contact.c.owner_id,
                            secondaryjoin=id == client_contact.c.client_id)

    def __init__(self, name: str, info: str = "", active: bool = True) -> None:
        super().__init__()
        self.name = name
        self.info = info
        self.active = active

    def __str__(self) -> str:
        active = "+" if self.active else ""
        return f"[{active}]Client[{self.id}]({self.name})"  #|{self.contacts}|" # Think: can be loop

    def __repr__(self) -> str:
        active = "+" if self.active else ""
        return f"[{active}]Client[{self.id}]({self.name})"  #|{self.contacts}|" # can be loop


class ClientHistoryModel(Model):
    __tablename__ = "client_history"
    id = Column(Integer, primary_key=True)
    client_id = Column(ForeignKey("client.id"), nullable=False)
    ip = Column(String(30), nullable=False, default="", server_default="")
    login_time = Column(DateTime, nullable=False, default=datetime.now())

    client = relationship("ClientModel", back_populates="history")

    def __init__(self,
                 client: ClientModel,
                 ip: str,
                 login_time: datetime = datetime.now()) -> None:
        super().__init__()
        self.client = client
        self.ip = ip
        self.login_time = login_time

    def __repr__(self) -> str:
        return f"ClientHistory[{self.id}]({self.ip} | {self.login_time})"

    def __str__(self) -> str:
        return f"ClientHistory[{self.id}]({self.ip} | {self.login_time})"
