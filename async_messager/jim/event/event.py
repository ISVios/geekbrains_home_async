class JimEvent:
    __slots__ = ["client", "packet", "args"]

    def __init__(self, client=None, packet=None, args: "dict|None" = None) -> None:
        self.client = client
        self.packet = packet
        self.args = args


class JimEventServerStop(JimEvent):
    pass


class JimEventServerRun(JimEvent):
    pass


class JimEventNewClient(JimEvent):
    pass


class JimEventAuthClient(JimEvent):
    pass


class JimEventKickClient(JimEvent):
    pass


class JimEventLogoutClient(JimEvent):
    pass


class JimEventMsgClient(JimEvent):
    pass


class JimEventClientAddFiend(JimEvent):
    pass


class JimEventClientDelFiend(JimEvent):
    pass


class JimEventClientEnterGroup(JimEvent):
    pass


class JimEventClientLeaveGroup(JimEvent):
    pass
