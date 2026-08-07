# database/models.py
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import json
import os  # 👈 ДОБАВЛЯЕМ

# 👇 ОПРЕДЕЛЯЕМ ПУТЬ К БАЗЕ ДАННЫХ
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_PATH = os.path.join(BASE_DIR, 'database', 'journal.db')

# Создаем папку для базы данных если её нет
os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

Base = declarative_base()

class Trade(Base):
    __tablename__ = 'trades'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    date = Column(DateTime, default=datetime.now)
    symbol = Column(String(20), nullable=False)
    direction = Column(String(10), nullable=False)  # LONG/SHORT
    position_size = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=True)
    exit_price = Column(Float, nullable=True)
    deposit = Column(Float, nullable=True)  # Депозит на момент сделки
    setup = Column(String(200))  # Сетап
    confidence = Column(Integer)  # Уверенность 1-10
    screenshot = Column(String(500))  # Путь к скриншоту
    status = Column(String(20), default='open')  # open/closed
    result = Column(String(20))  # profit/loss/breakeven
    pnl = Column(Float)  # Прибыль/убыток
    close_date = Column(DateTime)
    mistake = Column(String(50))  # Причина ошибки
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True, nullable=False)
    initial_deposit = Column(Float, default=0)
    current_deposit = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.now)

# Создаем движок и сессию
engine = create_engine(f'sqlite:///{DATABASE_PATH}')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)