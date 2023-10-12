
from sqlalchemy import create_engine
from sqlalchemy import Column, String, BigInteger, DateTime, Integer, JSON, Text
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


class Product(base):
    __tablename__ = 'products'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(256))
    image = Column(DateTime)
    description = Column(DateTime)
    cost = Column(Integer)


class Order(base):
    __tablename__ = 'orders'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tg_id = Column(BigInteger)
    username = Column(String(256))
    basket = Column(JSON)
    geo = Column(Text)
    created_at = Column(DateTime)


engine = create_engine(URL(**config.db_connect_data, query={}))
base.metadata.create_all(engine)

session_maker = sessionmaker(bind=engine)
scoped_session_maker = scoped_session(sessionmaker(bind=engine))
global_session = session_maker()
