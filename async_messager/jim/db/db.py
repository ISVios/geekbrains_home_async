"""
"""
import socket
import unittest
import warnings
from datetime import datetime

import sqlalchemy
from sqlalchemy import (
    Column,
    DateTime,
    Engine,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    create_engine,
    select,
)
from sqlalchemy.orm import Session, sessionmaker

from jim.logger.logger_server import logger
from jim.model import client, server

DATABASE_SERVER_PATH = "./server.db"
DATABASE_CLIENT_PATH = "./client.db"


class DataBaseORM:
    __db: Engine
    __session: Session
    __close: bool

    def __init__(self, orm, db_pah: str, debug: bool = True) -> None:
        super().__init__()
        self.__close = False
        self.__db = create_engine("sqlite:///" + db_pah, echo=debug, pool_recycle=7200)

        orm.metadata.create_all(self.__db)

        Session = sessionmaker(self.__db)

        self.__session = Session()
        self.__session.commit()
        self._post_init()

    def _post_init(self):
        pass

    def _session(self) -> Session:
        return self.__session

    def _query(self, orm_model):
        return self.__session.query(orm_model)

    def _add(self, orm_model, force_commit: bool = False):
        self.__session.add(orm_model)
        if force_commit:
            self.update()

    def _delete(self, orm_model, force_commit: bool = False):
        self.__session.delete(orm_model)
        if force_commit:
            self.update()

    def update(self):
        self.__session.commit()

    def close(self):
        if self.__close:
            return

        try:
            self.__close = True
            self.__session.rollback()
            self.__session.close()
            self.__db.dispose()
            logger.debug("DB: close")
        except:
            logger.debug("DB: can`t close correct")

    def __del__(self):
        self.close()


class DataBaseServerORM(DataBaseORM):
    def __init__(
        self,
        orm=server.ServerTables,
        db_pah: str = DATABASE_SERVER_PATH,
        debug: bool = True,
    ) -> None:
        super().__init__(orm, db_pah, debug)

    def _post_init(self):
        # reset all active
        broken_active = self._query(server.ClientModel).filter_by(active=True).all()
        for client in broken_active:
            self.client_active_status(client=client, active=False)
        self.update()

    def add_client(
        self,
        by_name: "str|None" = None,
        by_client: "server.ClientModel|None" = None,
        force_commit: bool = False,
        active: bool = True,
    ):
        client = by_client
        name = by_name

        if client:
            name = str(client.name)

        if not name:
            logger.error("Can`t add unname client to db")
            return

        db_client = server.ClientModel(name=name, active=active)

        if db_client:
            # find dup
            dup = (
                self._query(server.ClientModel)
                .filter_by(name=db_client.name)
                .one_or_none()
            )

            if not dup:
                logger.debug(f"{db_client}\t-->\tDB")
                self._add(db_client, force_commit)
                return db_client
            else:
                logger.debug(f"DB\t--->\t{dup}")
                return dup

    def get_client(
        self,
        by_name: "str|None" = None,
        by_client: "server.ClientModel|None" = None,
    ):
        """
        return client without saved
        """

        name = by_name
        no_update = by_client
        model = None

        if name:
            model = self._query(server.ClientModel).filter_by(name=name).one_or_none()

        if no_update:
            model = (
                self._query(server.ClientModel)
                .filter_by(name=no_update.name)
                .one_or_none()
            )

        if model:
            return model

    def client_active_status(
        self,
        active: bool,
        by_name: "str|None" = None,
        by_client: "server.ClientModel|None" = None,
        force_commit: bool = False,
    ):
        logger.debug(f"update_status")
        db_client = None
        if by_client:
            db_client = self.get_client(by_client=by_client)
        elif by_name:
            db_client = self.get_client(by_name=by_name)

        if db_client:
            db_client.active = active
            status = "active" if active else "logout"
            logger.debug(f"Client({db_client.name}) is {status}")
            if force_commit:
                self.update()

    def add_history(
        self,
        addr: "socket._RetAddress|str",
        by_name: "str|None" = None,
        by_client: "server.ClientModel|None" = None,
        force_add_client: bool = False,
        force_commit: bool = False,
    ):
        name = by_name
        if by_client:
            name = str(by_client.name)

        if not name:
            logger.error("can`t add history to client without name")
            return

        ip = str(addr)
        db_client = None

        if force_add_client:
            db_client = self.add_client(by_name=name)
        else:
            db_client = self.get_client(by_name=name)
        if db_client and ip:
            current_time = datetime.now()
            db_history = server.ClientHistoryModel(
                client=db_client, ip=ip, login_time=current_time
            )
            self._add(db_history, force_commit=force_commit)
            self.client_active_status(
                True, by_client=db_client, force_commit=force_commit
            )
            logger.debug(f"{db_history} ---> DB")
        else:
            logger.error(f"DB: can`t add history")
            if db_client == None:
                logger.error(f"DB: no found client")
            else:
                logger.error(f"DB: no found ip")

    def add_contact(
        self,
        owner: server.ClientModel,
        client: server.ClientModel,
        force_add_client: bool = True,
        force_commit: bool = False,
    ):
        db_owner = self.get_client(by_client=owner)
        if force_add_client:
            db_client = self.add_client(by_client=client)
        else:
            db_client = self.get_client(by_client=client)

        if db_client and db_owner:
            # test exist
            if not db_client in db_owner.contacts:
                # Think: add cross friend ?
                db_owner.contacts.append(db_client)
                logger.debug(f"contact({db_owner} {db_client})\t--->\tDB")
        if force_commit:
            self.update()

        return db_owner, db_client

    def get_contacts(
        self,
        by_name: "str|None" = None,
        by_client: "server.ClientModel|None" = None,
    ) -> "list[server.ClientModel]|None":
        db_client = None
        if by_name:
            db_client = self.get_client(by_name=by_name)
        elif by_client:
            db_client = self.get_client(by_client=by_client)

        if db_client:
            return db_client.contacts


class DataBaseClientORM(DataBaseORM):
    def __init__(
        self,
        orm=client.ClientTables,
        db_pah: str = DATABASE_CLIENT_PATH,
        debug: bool = True,
    ) -> None:
        super().__init__(orm, db_pah, debug)

    def add_client(
        self,
        by_name: "str|None" = None,
        by_client: "client.ClientModel|None" = None,
        force_commit: bool = False,
    ):
        name = by_name
        if by_client:
            name = str(by_client.name)

        if not name:
            logger.error("can't add user without name")
            return

        # find dup
        dup = self._query(client.ClientModel).filter_by(name=name).one_or_none()
        if dup:
            logger.debug(f"DB\t--->{dup}")
            return dup
        else:
            client_ = client.ClientModel(name)
            self._add(client_, force_commit)
            return client_

    def add_msg(
        self,
        msg: str,
        by_name: "str|None" = None,
        by_client: "client.ClientModel|None" = None,
        force_commit: bool = False,
    ):
        client_ = by_client
        name = by_name

        if name:
            client_ = self._query(client.ClientModel).filter_by(name=name).one_or_none()

        if client_:
            client_.messages.append(client.MesagesModel(msg=msg))
            if force_commit:
                self.update()
            return
        else:
            by = by_client if by_client else by_name
            logger.error(f"No found client by {by}")

    def get_contacts(self):
        return self._query(client.ClientModel).all()

    def del_client(
        self,
        by_name: "str|None" = None,
        by_client: "client.ClientModel|None" = None,
        force_commit: bool = False,
    ):
        if by_client:
            self._delete(by_client, force_commit)
            return

        if by_name:
            by_client = (
                self._query(client.ClientModel).filter_by(name=by_name).one_or_none()
            )

            if by_client:
                self._delete(by_client, force_commit)


if __name__ == "__main__":
    SHOW_DB_DEBUG = False
    logger.propagate = False

    class DBServerTest(unittest.TestCase):
        DATABASE_PATH = "./server_test.db"
        DB = DataBaseServerORM(server.ServerTables, DATABASE_PATH, SHOW_DB_DEBUG)

        def setUp(self) -> None:
            print(f"{'DataBaseServerORM':-^79}")

        def test__add_user(self):
            print(f"{'ADD_CLIENT':-^79}")
            TEST_NAME = "USER1"
            self.DB.add_client(by_name=TEST_NAME, force_commit=True)

            db_client = (
                self.DB._query(server.ClientModel)
                .filter_by(name=TEST_NAME)
                .one_or_none()
            )

            self.assertIsNotNone(db_client, "Can`t get from db")
            if db_client:
                self.assertIsNotNone(db_client.id, "No set id")

            try:
                # test duplicate
                client = server.ClientModel(name=TEST_NAME)
                self.DB.add_client(by_name=TEST_NAME, force_commit=True)
            except:
                self.assertFalse(True, "Duplicate add make error")

            TEST_NAME = "USER2"
            client = server.ClientModel(name=TEST_NAME)
            print(client)
            self.DB._add(client)
            self.DB.update()
            print(client)

        def test__get_client(self):
            print(f"{'GET_CLIENT':-^79}")
            TEST_NAME = "USER0"

            # get client before add
            test = self.DB.get_client(by_name=TEST_NAME)
            self.assertIsNone(test)

            client = server.ClientModel(TEST_NAME)
            self.DB.add_client(by_client=client, active=True)

            test = self.DB.get_client(by_name=TEST_NAME)

            if test:
                self.assertEqual(test.name, TEST_NAME)
            else:
                self.assertIsNotNone(test)

        def test__add_hiistory(self):
            print(f"{'ADD_HISTORY':-^79}")
            TEST_NAME_1 = "USER_HISTORY_1"
            TEST_NAME_2 = "USER_HISTORY_2"

            self.DB.add_client(by_name=TEST_NAME_1)
            self.DB.add_client(by_name=TEST_NAME_2)

            try:
                client = server.ClientModel(TEST_NAME_1)
                self.DB.add_history(client, "0.0.0.3", force_commit=True)
            except Exception as ex:
                logger.error(f"DB: {str(ex)}")

            try:
                client = server.ClientModel(TEST_NAME_2)
                self.DB.add_history(client, "0.0.0.2", force_commit=True)
            except Exception as ex:
                logger.error(f"DB: {str(ex)}")

            try:
                client = server.ClientModel(TEST_NAME_1)
                self.DB.add_history(client, "0.0.0.1", force_commit=True)
            except Exception as ex:
                logger.error(f"DB: {str(ex)}")

        def test__add_contacts(self):
            print(f"{'ADD_CONTACTS':-^79}")
            TEST_NAME_OWER = "USER_OWER"
            TEST_NAME_CLIENT = "USER_CLIENT"

            db_owner = self.DB.add_client(by_name=TEST_NAME_OWER, force_commit=True)
            db_client = self.DB.add_client(by_name=TEST_NAME_CLIENT, force_commit=True)

            try:
                db_owner, db_client = self.DB.add_contact(
                    db_owner, db_client, force_commit=True
                )

                test = self.DB.get_client(by_name=TEST_NAME_OWER)

                if test:
                    self.assertIsNotNone(test.contacts)
                    logger.debug(f"BD Friend from MODEL {test.contacts}")
                    frend_list = self.DB.get_contacts(test)
                    logger.debug(f"DB Friend from FUNC {frend_list}")

            except Exception as ex:
                logger.error(f"DB: {str(ex)}")

        def test__login_status_client(self):
            print(f"{'LOGOUT_CLIENT':-^79}")
            TEST_NAME_1 = "USER_STATUS"
            db_client = self.DB.get_client(by_name=TEST_NAME_1)
            if db_client:
                logger.warning(f"{self.DATABASE_PATH} exist. Del {db_client}")
                self.DB._delete(db_client)
                self.DB.update()

            db_client = self.DB.add_client(
                by_name=TEST_NAME_1, force_commit=True, active=True
            )

            if not db_client:
                self.assertTrue(False, "DB no return client")
                return
            print(db_client)
            self.assertTrue(db_client.active, "No correct init active")

            self.DB.client_active_status(db_client, False)

            print(db_client)
            self.assertFalse(db_client.active, "No change active")

            self.DB.client_active_status(db_client, True)
            print(db_client)
            self.assertTrue(db_client.active, "No correct init active")

        def tearDown(self):
            print(f"{'':-^79}")

        @classmethod
        def tearDownClass(cls):
            import os

            # remove test DB after tests
            cls.DB.close()
            os.remove(cls.DATABASE_PATH)
            logger.debug(f"Delete test DB {cls.DATABASE_PATH}")
            print(f"{'END TestCase':-^79}")

    class DBClientTest(unittest.TestCase):
        DATABASE_PATH = "./client_test.db"
        DB = DataBaseClientORM(client.ClientTables, DATABASE_PATH, SHOW_DB_DEBUG)

        def setUp(self) -> None:
            print(f"{'DataBaseClientORM':-^79}")

        def test__add_client(self):
            TEST_NAME = "Client_1"
            self.DB.add_client(by_name=TEST_NAME, force_commit=True)

            db_client = (
                self.DB._query(client.ClientModel)
                .filter_by(name=TEST_NAME)
                .one_or_none()
            )

            self.assertIsNotNone(db_client, "Can`t get from db")
            if db_client:
                self.assertIsNotNone(db_client.id, "No set id")

            try:
                # test duplicate
                client_ = client.ClientModel(name=TEST_NAME)
                self.DB.add_client(by_name=TEST_NAME, force_commit=True)
            except:
                self.assertFalse(True, "Duplicate add make error")

            TEST_NAME = "USER2"
            client_ = client.ClientModel(name=TEST_NAME)
            print(client_)
            self.DB._add(client_)
            self.DB.update()
            print(client_)

        def test__add_msg(self):
            TEST_NAME_TO_1 = "USER_TO_1"
            TEST_MESSAGE = "HI. It is Test"

            db_user_to = self.DB.add_client(by_name=TEST_NAME_TO_1)

            if not db_user_to:
                self.assertTrue(False, "DB no return user")
                return

            db_user_to.messages.append(client.MesagesModel(msg=TEST_MESSAGE))
            self.DB.update()
            print("add msg by MODEL", db_user_to.messages)
            self.assertEqual(1, len(db_user_to.messages))

            self.DB.add_msg(by_client=db_user_to, msg=TEST_MESSAGE, force_commit=True)
            print("add msg by FUNC", db_user_to.messages)
            self.assertEqual(2, len(db_user_to.messages))

            pass

        def tearDown(self):
            print(f"{'':-^79}")

        @classmethod
        def tearDownClass(cls):
            import os

            # remove test DB after tests
            cls.DB.close()
            os.remove(cls.DATABASE_PATH)
            logger.debug(f"Delete test DB {cls.DATABASE_PATH}")
            print(f"{'END TestCase':-^79}")

    unittest.main()
