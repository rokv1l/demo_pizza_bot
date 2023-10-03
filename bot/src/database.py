
from sqlalchemy import create_engine
from sqlalchemy import Column, String, BigInteger, DateTime, JSON, TEXT, Boolean
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.engine.url import URL
from sqlalchemy.ext.declarative import declarative_base

import config

base = declarative_base()


class AdminAlert(base):
    __tablename__ = 'admin_alerts'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    to = Column(String(320))
    error_with = Column(TEXT)
    created_at = Column(DateTime)


class Manager(base):
    __tablename__ = 'managers'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tg_id = Column(BigInteger)
    fio = Column(String(256))
    sales_departaments = Column(JSON)
    created_at = Column(DateTime)
    edited_at = Column(DateTime)


class SalesDepatrament(base):
    __tablename__ = 'sales_departaments'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(128))
    email_list = Column(JSON, default=[])


class User(base):
    __tablename__ = 'users'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tg_id = Column(BigInteger)
    username = Column(String(256))
    created_at = Column(DateTime)


class Order(base):
    __tablename__ = 'paper_orders'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tg_id = Column(BigInteger)
    departament = Column(String(128))
    product_name = Column(String(128))
    density = Column(String(256), default="")
    format = Column(String(256), default="")
    purchase_purpose = Column(TEXT, default="")
    volume = Column(TEXT)
    client_name = Column(TEXT)
    client_phone = Column(TEXT)
    client_email = Column(TEXT)
    client_inn = Column(TEXT)
    delivery_country = Column(TEXT)
    is_notified = Column(Boolean, default=False)
    is_email_notified = Column(Boolean, default=False)
    manager_id = Column(BigInteger, default=0)
    status = Column(String(512), default="Создано")
    created_at = Column(DateTime)
    accepted_at = Column(DateTime)
    closed_at = Column(DateTime)


engine = create_engine(URL(**config.db_connect_data, query={}))
base.metadata.create_all(engine)

session_maker = sessionmaker(bind=engine)
scoped_session_maker = scoped_session(sessionmaker(bind=engine))
global_session = session_maker()
