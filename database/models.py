# database/models.py
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, BIGINT
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import DATABASE_URL

Base = declarative_base()

class Trade(Base):
    __tablename__ = 'trades'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BIGINT, nullable=False)
    date = Column(DateTime, default=datetime.now)
    symbol = Column(String(20), nullable=False)
    direction = Column(String(10), nullable=False)
    position_size = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=True)
    exit_price = Column(Float, nullable=True)
    deposit = Column(Float, nullable=True)
    setup = Column(String(200))
    confidence = Column(Integer)
    screenshot = Column(String(500))
    status = Column(String(20), default='open')
    result = Column(String(20))
    pnl = Column(Float)
    close_date = Column(DateTime)
    mistake = Column(String(50))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BIGINT, unique=True, nullable=False)
    username = Column(String(100), nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    initial_deposit = Column(Float, default=0)
    current_deposit = Column(Float, default=0)
    is_active = Column(Integer, default=1)
    last_seen_at = Column(DateTime, nullable=True)
    blocked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def get_session():
    return Session()

def get_engine():
    return engine

def init_db():
    Base.metadata.create_all(engine)
    print("✅ Таблицы созданы/проверены")

def drop_db():
    Base.metadata.drop_all(engine)
    print("⚠️ Все таблицы удалены")