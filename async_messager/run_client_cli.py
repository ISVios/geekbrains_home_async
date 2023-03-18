#!/usr/bin/env python
"""
"""

import argparse
import threading
import time
from jim.packet.packet import JIMAction, JIMPacket
from jim.client.client import RegistarationByGuest, RegistarationByName

from jim.client import JIMClient, SendTo

COMMAND = """ 
1) Registarotion by
2) Send msg to client
3) Send msg to group
4) join in group
5) leave from group
q) Quit

>> """


def read_command(client: JIMClient):
    time.sleep(2)
    try:
        while True:
            print(f"Name: {client.get_name()}\t {client.wait()}")
            print(f"Groups: {client.get_groups()}")
            command = input(COMMAND)

            if command == "1":
                name = input("Login(empty to guest): ")
                if name:
                    client.registaration(RegistarationByName(name))
                else:
                    client.registaration(RegistarationByGuest())

            elif command == "2":
                name = input("Client name: ")
                msg = input("Send msg: ")
                client.send_msg_to(SendTo.user(name), msg)

            elif command == "3":
                name = input("Group name(empty to all): ") or "___ALL___"
                msg = input("Send msg: ")

                client.send_msg_to(SendTo.group(name), msg)

            elif command == "4":
                name = input("Join group: ")
                client.join_grop(name)

            elif command == "5":
                name = input("Leave from: ")
                client.leave_group(name)

            elif command == "q":
                client.disconnect()
                raise KeyboardInterrupt
            else:
                #update
                pass

    except KeyboardInterrupt:
        raise KeyboardInterrupt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='JIM client.')
    parser.add_argument("-p",
                        "--port",
                        const=1,
                        type=int,
                        nargs="?",
                        default=7777,
                        help="TCP-port. (default: 7777)")
    parser.add_argument("-a",
                        "--addr",
                        const=1,
                        type=str,
                        nargs="?",
                        default="0.0.0.0",
                        help="IP-addres to listen. (default: 0.0.0.0)")

    args = parser.parse_args()

    client = JIMClient(args.addr, args.port)
    t = threading.Thread(target=read_command, args=(client, ))
    t.daemon = True
    t.start()

    try:
        while True:
            client.update_status()
    except KeyboardInterrupt:
        client.disconnect()
        exit(0)
    except:
        pass
