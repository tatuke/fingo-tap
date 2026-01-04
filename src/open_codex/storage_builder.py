import datetime
from sqlalchemy import DateTime, create_engine, Column, Integer, String, Text
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from sqlalchemy.ext.declarative import declarative_base
import os

# 创建 Base 类
Base = declarative_base()

class recordcontext(Base):
    __tablename__ = 'ft_single_choice_command'
    id = Column(Integer, primary_key=True)
    choice = Column(String(10))
    command = Column(Text)
    extend_content = Column(Text)
    create_time = Column(DateTime, default=datetime.datetime.now)

def get_db_user():
    return os.getenv("DB_USER")

def get_db_password():
    return os.getenv("DB_PASSWORD")

def get_db_host():
    return os.getenv("DB_HOST", "127.0.0.1")

def get_db_port():
    return os.getenv("DB_PORT", "3308")

def get_db_name():
    return os.getenv("DB_NAME")

def get_database_url():
    return f"mysql+pymysql://{get_db_user()}:{get_db_password()}@{get_db_host()}:{get_db_port()}/{get_db_name()}"


def get_engine():
    return create_engine(get_database_url(), pool_pre_ping=True)

def get_session_local():
    return sessionmaker(bind=get_engine())

def get_db() -> Session:
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_session():
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

# # 初始化表结构
# def init_db():
#     Base.metadata.create_all(bind=get_engine())
