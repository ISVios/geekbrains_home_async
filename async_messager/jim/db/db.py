"""
1. Начать реализацию класса «Хранилище» для серверной стороны. Хранение необходимо
осуществлять в базе данных. В качестве СУБД использовать sqlite. Для взаимодействия с БД
можно применять ORM.
    Опорная схема базы данных:
        ● На стороне сервера БД содержит следующие таблицы:
            ○ клиент:
                ■ логин;
                ■ информация.
            ○ история_клиента:
                ■ время входа;
                ■ ip-адрес.
            ○ список_контактов (составляется на основании выборки всех записей с id_владельца):
                ■ id_владельца;
                ■ id_клиента.
"""
DATABASE_PATH = "./db"

import socket
import unittest
from datetime import datetime
import warnings

import sqlalchemy
from sqlalchemy import (Column, DateTime, Engine, ForeignKey, Integer, String,
                        Table, Text, create_engine, select)
from sqlalchemy.orm import Session, session, sessionmaker
from sqlalchemy.sql.functions import current_time

from jim.client import JIMClient
from jim.db.orm_model import ClientHistoryModel, ClientModel, ClientORM
from jim.logger.logger_server import logger


class DataBaseORM:
    __db: Engine
    __session: Session
    __close: bool

    def __init__(self, db: str = DATABASE_PATH, debug: bool = True) -> None:
        super().__init__()
        self.__close = False
        self.__db = create_engine("sqlite:///" + db,
                                  echo=debug,
                                  pool_recycle=7200)
        # create tables
        ClientORM.metadata.create_all(self.__db)
        Session = sessionmaker(self.__db)

        session = Session()
        self.__session = session
        session.commit()

    def delete(self, db_model, force_commit: bool = False):
        self.__session.delete(db_model)
        if force_commit:
            self.__session.commit()

    def query(self, model):
        return self.__session.query(model)

    def _session(self):
        return self.__session

    def update(self):
        self.__session.commit()

    def add_client(self,
                   client: "JIMClient|ClientModel",
                   force_commit: bool = False,
                   active: bool = True):
        db_client = None
        if type(client) is JIMClient:
            name = client.get_name()
            if not name:
                logger.error("Can`t add unname client to db")
                return
            db_client = ClientModel(name=name, active=active)

        elif type(client) is ClientModel:
            db_client = client

        if db_client:
            # find dup
            dup = self.__session.query(ClientModel).filter_by(
                name=db_client.name).one_or_none()

            if not dup:
                logger.debug(f"{db_client}\t-->\tDB")
                self.__session.add(db_client)
                if force_commit:
                    self.__session.commit()
                return db_client
            else:
                logger.debug(f"DB\t--->\t{dup}")
                return dup

    def get_client(self,
                   by_name: "str|None" = None,
                   by_jim_client: "JIMClient|None" = None,
                   by_no_update_model: "ClientModel|None" = None):
        """
        return client without saved
        """

        jim = by_jim_client
        name = by_name
        no_update = by_no_update_model
        model = None

        if jim and not hasattr(jim.status, "model"):
            name = jim.get_name()
            if not name:
                raise NotImplementedError
        if name:
            model = self.query(ClientModel).filter_by(name=name).one_or_none()

        if jim and hasattr(jim.status, "model"):
            no_update = getattr(jim.status, "model")

        if no_update:
            model = self.query(ClientModel).filter_by(
                name=no_update.name).one_or_none()

        if model:
            if jim:
                setattr(jim.status, "model", model)
            return model

    def client_active_status(self,
                             client: "JIMClient|ClientModel",
                             active: bool,
                             force_commit: bool = False):
        db_client = None
        if type(client) is JIMClient:
            db_client = self.get_client(by_jim_client=client)
        else:
            db_client = self.get_client(by_no_update_model=client)

        if db_client:
            db_client.active = active
            status = "active" if active else "logout"
            logger.debug(f"Client({db_client.name}) is {status}")
            if force_commit:
                self.update()

    def add_history(self,
                    client: "JIMClient|ClientModel",
                    addr: "socket._RetAddress|str|None" = None,
                    force_commit: bool = False):

        ip = None
        db_client = self.add_client(client)
        if type(client) is ClientModel:
            if not addr:
                logger.error("can`t add history without ip")
                return
            ip = str(addr)

        else:
            ip = str(client._get_ip())

        if db_client and ip:
            current_time = datetime.now()
            db_history = ClientHistoryModel(client=db_client,
                                            ip=ip,
                                            login_time=current_time)
            self.__session.add(db_history)
            if force_commit:
                self.update()
            logger.debug(f"{db_history} ---> DB")

    def add_contact(self,
                    owner: "JIMClient|ClientModel",
                    client: "JIMClient|ClientModel",
                    add_client: bool = True,
                    force_commit: bool = False):
        db_owner = self.add_client(owner)
        if add_client:
            db_client = self.add_client(client)
        else:
            db_client = self.get_client(client)

        if db_client and db_owner:
            # test exist
            if not db_client in db_owner.contacts:
                # Think: add cross friend ?
                db_owner.contacts.append(db_client)
                logger.debug("contact({db_owner} {db_client})\t--->\tDB")
        if force_commit:
            self.update()

        return db_owner, db_client

    def get_contacts(
            self, client: "JIMClient|ClientModel") -> "list[ClientModel]|None":
        db_client = None
        if type(client) is JIMClient:
            db_client = self.get_client(by_jim_client=client)
        else:
            db_client = self.get_client(by_no_update_model=client)

        if db_client:
            return db_client.contacts

    def close(self):
        if not self.__close:
            self.__session.close()
            self.__db.dispose()
            logger.debug(f"DB: session close")
            self.__close = True

    def __del__(self):
        self.close()


if __name__ == "__main__":

    DATABASE_PATH_TEST = "./test.db"
    SHOW_DB_DEBUG = False
    DB = DataBaseORM(DATABASE_PATH_TEST, SHOW_DB_DEBUG)
    logger.propagate = False

    class DBTest(unittest.TestCase):

        # def test__over_class(self):
        #     client = ClientModel("USER0")
        #     DB._session().add(client)
        #     DB._session().commit()
        #     client_history = ClientHistoryModel(client, "0.0.0.0")
        #     DB._session().add(client_history)
        #     DB._session().commit()

        def test__add_user(self):
            print(f"{'ADD_CLIENT':-^79}")
            try:
                TEST_NAME = "USER1"
                client = ClientModel(TEST_NAME)
                logger.debug(f"Before commit {client}")
                test = DB.add_client(client, True)
                logger.debug(f"After commit {test}")

                if test:
                    self.assertIsNotNone(test.id)
                    self.assertEqual(test.name, client.name)
                else:
                    self.assertIsNone(test)

            except Exception as ex:
                self.assertFalse(True, str(ex))

            # duplicate not make error
            try:
                client = ClientModel("USER1")
                DB.add_client(client, force_commit=True)
            except Exception as ex:
                self.assertFalse(True, "Duplicate add make error")
                logger.error(str(ex))

        def test__get_client(self):
            print(f"{'GET_CLIENT':-^79}")

            # add test before create

            TEST_NAME = "USER0"
            client = ClientModel(TEST_NAME)
            DB.add_client(client, True)

            test = DB.get_client(by_name=TEST_NAME)

            if test:
                self.assertEqual(test.name, TEST_NAME)
            else:
                self.assertIsNotNone(test)

        def test__add_hiistory(self):
            print(f"{'ADD_HISTORY':-^79}")
            try:
                TEST_NAME = "USER2"
                client = ClientModel(TEST_NAME)
                DB.add_history(client, "0.0.0.3", force_commit=True)
            except Exception as ex:
                logger.error(f"DB: {str(ex)}")

            try:
                TEST_NAME = "USER1"
                client = ClientModel(TEST_NAME)
                DB.add_history(client, "0.0.0.2", force_commit=True)
            except Exception as ex:
                logger.error(f"DB: {str(ex)}")

            try:
                TEST_NAME = "USER2"
                client = ClientModel(TEST_NAME)
                DB.add_history(client, "0.0.0.1", force_commit=True)
            except Exception as ex:
                logger.error(f"DB: {str(ex)}")

        def test__add_contacts(self):
            print(f"{'ADD_CONTACTS':-^79}")
            try:
                TEST_NAME_1 = "USER2"
                TEST_NAME_2 = "USER1"
                owner = ClientModel(TEST_NAME_1)
                client = ClientModel(TEST_NAME_2)
                db_owner, db_client = DB.add_contact(owner, client, True, True)

                logger.debug(f"After commit {db_owner} {db_client}")

                test = DB.get_client(by_name=TEST_NAME_1)

                if test:
                    self.assertIsNotNone(test.contacts)
                    logger.debug(f"BD Friend from model {test.contacts}")
                    frend_list = DB.get_contacts(test)
                    logger.debug(f"DB Friend from func ---- {frend_list}")

            except Exception as ex:
                logger.error(f"DB: {str(ex)}")

        def test__status_client_logout(self):
            print(f"{'LOGOUT_CLIENT':-^79}")
            TEST_NAME_1 = "USER10"
            client = ClientModel(TEST_NAME_1, active=True)

            db_client = DB.get_client(by_no_update_model=client)
            if db_client:
                logger.warning(f"{DATABASE_PATH_TEST} exist. Del {db_client}")
                DB.delete(db_client)
                DB.update()

            DB.add_client(client, force_commit=True, active=True)

            db_client = DB.get_client(by_no_update_model=client)

            if db_client:
                self.assertTrue(
                    db_client.active,
                    f"Client before update must be True but {db_client.active}. Maybe '{DATABASE_PATH_TEST}' not deleted."
                )
                DB.client_active_status(db_client, False)
                DB.update()
                db_client = DB.get_client(by_no_update_model=client)
                if db_client:
                    logger.debug(db_client)
                    self.assertFalse(db_client.active)
                    return

            self.assertTrue(False, "Todo")

        def test__status_client_login(self):
            print(f"{'LOGIN_CLIENT':-^79}")
            TEST_NAME = "USER20"
            client = ClientModel(TEST_NAME, active=False)

            db_client = DB.get_client(by_no_update_model=client)
            if db_client:
                logger.warning(f"{DATABASE_PATH_TEST} exist. Del {db_client}")
                DB.delete(db_client, True)

            DB.add_client(client, force_commit=True)
            db_client = DB.get_client(by_no_update_model=client)
            if db_client:
                self.assertFalse(db_client.active, "No correct put in DB")
                DB.client_active_status(db_client, True)
                DB.update()
                db_client = DB.get_client(by_no_update_model=client)
                if db_client:
                    logger.debug(db_client)
                    self.assertTrue(db_client.active)
                    return

            self.assertTrue(False, "Todo")

        def tearDown(self):
            print(f"{'':-^79}")

        @classmethod
        def tearDownClass(cls):
            import os

            # remove test DB after tests
            DB.close()
            os.remove(DATABASE_PATH_TEST)
            logger.debug(f"Delete test DB {DATABASE_PATH_TEST}")
            print(f"{'END TestCase':-^79}")

    unittest.main()
