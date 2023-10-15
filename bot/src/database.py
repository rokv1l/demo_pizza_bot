
from sqlalchemy import create_engine
from sqlalchemy import Column, String, BigInteger, DateTime, Integer, JSON, Text, Boolean
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.engine.url import URL
from sqlalchemy.ext.declarative import declarative_base

import config

base = declarative_base()


class User(base):
    __tablename__ = 'users'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tg_id = Column(BigInteger)
    username = Column(String(256))
    phone = Column(String(256))
    created_at = Column(DateTime)
    is_manager = Column(Boolean, default=False)


class Product(base):
    __tablename__ = 'products'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(256))
    image = Column(String(256))
    description = Column(Text)
    cost = Column(Integer)


class Order(base):
    __tablename__ = 'orders'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tg_id = Column(BigInteger)
    username = Column(String(256))
    basket = Column(JSON)
    geo = Column(JSON)
    status = Column(String(128), default="Создан")
    phone = Column(String(256))
    created_at = Column(DateTime)


engine = create_engine(URL(**config.db_connect_data, query={}))
base.metadata.create_all(engine)

session_maker = sessionmaker(bind=engine)
scoped_session_maker = scoped_session(sessionmaker(bind=engine))
global_session = session_maker()
