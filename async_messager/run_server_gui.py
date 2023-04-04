#!/usr/bin/env python
import argparse
import queue
import sys
import threading
from os import fsdecode

import PyQt5
from PyQt5 import QtGui, QtWidgets, uic
from PyQt5.QtCore import QThread

from jim.logger.logger_server import logger
from jim.server.server import JIMServer

SERVER_MAIN_UI = "jim/ui/server_main.ui"
SERVER_CONFIG_DLG_UI = "jim/ui/server_config_dlg.ui"
SERVER_RUN_DLG_UI = "jim/ui/server_run_dlg.ui"
SERVER_ABOUT_DLG_UI = "jim/ui/server_about_dlg.ui"

SERVER_CLIENT_ITEM_UI = "jim/ui/server_client_item.ui"


class ServerAboutDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(SERVER_ABOUT_DLG_UI, self)
        self.show()


class ServerConfigDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(SERVER_CONFIG_DLG_UI, self)
        self.show()

    def _select_db(self):
        QtWidgets.QFileDialog().getOpenFileName()


class ServerRunDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)


class ClientListItem(QtWidgets.QTableWidgetItem):
    def __init__(self, other):
        super().__init__()


class ServerGui(QtWidgets.QMainWindow):
    server: JIMServer
    server_config: dict
    select_client: str
    debug: bool
    event_in: queue.SimpleQueue
    event_out: queue.SimpleQueue

    def __init__(self, parent=None, debug: bool = False):
        self.event_in = queue.SimpleQueue()
        self.event_out = queue.SimpleQueue()
        self.server = JIMServer(self.event_in, self.event_out)
        self.server_config = {}
        self.debug = debug
        QtWidgets.QWidget.__init__(self, parent)
        uic.loadUi(SERVER_MAIN_UI, self)
        self.__component_init()
        if self.debug:
            self.__debug_component_init()
        else:
            self.__no_debug()

        self.loop()

    def loop(self):
        # get event from event_in
        if not self.event_in.empty():
            cmd = self.event_in.get()
            cmd_type = type(cmd)
            print(cmd)

        #     if cmd_type is EventClientNew:
        #         self.__add_anon()
        #     elif cmd_type is EventClientAuth:
        #         self.__auth_client()
        #     elif cmd_type is EventClientLogout:
        #         self.__logout_client()
        #     elif cmd_type is EventClientSendMsg:
        #         self.__msg_client()
        #
        # if not self.event_out.empty():
        #     if self.server:
        #         self.server.add_cmd(self.event_out.get())

    def __no_debug(self):
        self.debug_menu: QtWidgets.QMenu = self.menu_debug_gui
        self.debug_menu.deleteLater()

    def __debug_component_init(self):
        self.debug_menu: QtWidgets.QMenu = self.menu_debug_gui

        self.debug_menu_add_client: QtWidgets.QAction = self.action_add_anon
        self.debug_menu_logout_client: QtWidgets.QAction = self.action_logout_client
        self.debug_menu_login_client: QtWidgets.QAction = self.action_login_client
        self.debug_menu_auth_client: QtWidgets.QAction = self.action_auth_client
        self.debug_menu_kick_client: QtWidgets.QAction = self.action_kick_client
        self.debug_menu_msg_to_client: QtWidgets.QAction = self.action_send_msg_to_user
        self.debug_menu_msg_to_group: QtWidgets.QAction = self.action_send_msg_to_group

        self.debug_menu_add_client.triggered.connect(self.__add_anon_debug)
        self.debug_menu_logout_client.triggered.connect(self.__logout_client_debug)
        self.debug_menu_login_client.triggered.connect(self.__login_client_debug)
        self.debug_menu_kick_client.triggered.connect(self.__kick_client_debug)

        self.debug_menu_auth_client.triggered.connect(self.__auth_client_debug)

        self.debug_menu_msg_to_client.triggered.connect(self.__msg_client_debug)
        self.debug_menu_msg_to_group.triggered.connect(self.__msg_group_debug)

    def __component_init(self):
        # MAIN_MENU_FILE
        self.main_menu_action_run_server = self.action_run_server
        self.main_menu_action_config_server = self.action_config_server
        self.main_menu_action_stop_server = self.action_stop_server
        self.main_menu_action_exit: QtWidgets.QAction = self.action_exit

        # ABOUT
        self.about_author: QtWidgets.QAction = self.action_author

        self.client_list: QtWidgets.QListWidget = self.client_list
        self.text_log: QtWidgets.QTextBrowser = self.text_log

        # CONNECTS
        self.main_menu_action_run_server.triggered.connect(self.__run_server)
        self.main_menu_action_config_server.triggered.connect(self.__config_server)
        self.main_menu_action_exit.triggered.connect(self.__glb_quit)

        self.about_author.triggered.connect(self.__show_about)

        self.client_list.itemClicked.connect(self.__select_client)

    def __config_server(self):
        # open dialog
        dlg = ServerConfigDialog(self)
        # Todo: save config in dict

    def __select_client(self, select):
        self.debug_menu_logout_client.setEnabled(True)
        self.debug_menu_login_client.setEnabled(True)
        self.debug_menu_auth_client.setEnabled(True)
        self.debug_menu_kick_client.setEnabled(True)
        self.debug_menu_msg_to_client.setEnabled(True)
        self.debug_menu_msg_to_group.setEnabled(True)

    def __deselect_client(self):
        self.debug_menu_logout_client.setEnabled(False)
        self.debug_menu_login_client.setEnabled(False)
        self.debug_menu_auth_client.setEnabled(False)
        self.debug_menu_kick_client.setEnabled(False)
        self.debug_menu_msg_to_client.setEnabled(False)
        self.debug_menu_msg_to_group.setEnabled(False)

    def __run_server(self):
        # run server with param
        pass

    def __unlock_when_server_run(self):
        self.main_menu_action_run_server.setEnabled(False)
        self.main_menu_action_stop_server.setEnabled(True)

    def __lock_when_server_stop(self):
        self.main_menu_action_run_server.setEnabled(True)
        self.main_menu_action_stop_server.setEnabled(False)

    def __stop_server(self):
        self.__lock_when_server_stop()

    def __show_about(self):
        ServerAboutDialog(self)

    def __glb_quit(self):
        # Todo: stop thread
        self.__stop_server()
        QtWidgets.QApplication.quit()

    def __add_anon(self, client_addr):
        client_gui_item = QtWidgets.QListWidgetItem("[+] " + client_addr)
        font = client_gui_item.font()
        font.setBold(True)
        client_gui_item.setFont(font)
        self.client_list.addItem(client_gui_item)
        # add jimclient to item

    def __add_group_client(self):
        raise NotImplemented

    def __del_group_client(self):
        raise NotImplemented

    def __kick_client(self):
        pass

    def __auth_client(self, client_item, client_name):
        pass

    def __logout_client(self, client):
        pass

    def __login_client(self, client):
        pass

    def __get_select_client(self):
        pass

    def __msg_client(self):
        pass

    def __msg_group(self):
        pass

    # DEBUG FUNC
    def __add_anon_debug(self):
        # Todo: add dialog
        if not hasattr(ServerGui, "debug_ip_index"):
            setattr(ServerGui, "debug_ip_index", 0)
        else:
            ServerGui.debug_ip_index += 1

        self.__add_anon(str(ServerGui.debug_ip_index))

    def __del_client_debug(self):
        self.client_list.takeItem(self.client_list.currentRow())
        if self.client_list.currentRow() < 0:
            self.__deselect_client()

    def __logout_client_debug(self):
        current = self.client_list.currentItem()
        font = current.font()
        font.setBold(False)
        current.setFont(font)
        text = current.text().split("]")
        text = "[ ]" + text[1]
        current.setText(text)

    def __login_client_debug(self):
        current = self.client_list.currentItem()
        font = current.font()
        font.setBold(True)
        current.setFont(font)
        text = current.text().split("]")
        text = "[+]" + text[1]
        current.setText(text)

    def __auth_client_debug(self):
        select = self.client_list.currentItem()
        select.setText("[+] auth")

    def __kick_client_debug(self):
        self.__del_client_debug()

    def __msg_client_debug(self):
        self.text_log.moveCursor(QtGui.QTextCursor.End)
        self.text_log.insertPlainText("Client: --> Client\n")

    def __msg_group_debug(self):
        self.text_log.moveCursor(QtGui.QTextCursor.End)
        self.text_log.insertPlainText("Client: --> Group\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="JIM server.")
    parser.add_argument(
        "-p",
        "--port",
        const=1,
        type=int,
        nargs="?",
        default=7777,
        help="TCP-port. (default: 7777)",
    )
    parser.add_argument(
        "-a",
        "--addr",
        const=1,
        type=str,
        nargs="?",
        default="0.0.0.0",
        help="IP-addres to listen. (default: 0.0.0.0)",
    )

    parser.add_argument(
        "-c",
        "--count",
        const=1,
        type=int,
        nargs="?",
        default=10,
        help="Count of max supported client. (default: 10).",
    )

    parser.add_argument(
        "-l",
        "--log",
        const=1,
        type=int,
        nargs="?",
        default=10,
        help="Logger level. (default: 10).",
    )

    parser.add_argument(
        "-gd",
        "--gui-debug",
        default=False,
        action="store_true",
        help="Show debug menu",
    )

    args = parser.parse_args()

    app = QtWidgets.QApplication(sys.argv)
    gui = ServerGui(debug=args.gui_debug)
    gui.show()

    exit(app.exec_())
