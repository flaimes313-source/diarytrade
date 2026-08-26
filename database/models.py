# database/models.py
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, BIGINT
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import json
import os

DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database", "journal.db")}')

Base = declarative_base()

class Trade(Base):
    __tablename__ = 'trades'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BIGINT, nullable=False)  # 👈 BIGINT для Telegram ID
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
    user_id = Column(BIGINT, unique=True, nullable=False)  # 👈 BIGINT для Telegram ID
    initial_deposit = Column(Float, default=0)
    current_deposit = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.now)

engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

try:
    with engine.connect() as conn:
        print(f"✅ Подключение к базе данных успешно!")
        print(f"   URL: {DATABASE_URL[:50]}..." if len(DATABASE_URL) > 50 else f"   URL: {DATABASE_URL}")
except Exception as e:
    print(f"❌ Ошибка подключения к базе данных: {e}")

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