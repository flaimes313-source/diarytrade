# database/models.py
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import json
import os

# ============= НАСТРОЙКА ПОДКЛЮЧЕНИЯ К БД =============
# Берем DATABASE_URL из переменных окружения
# Если не задана - используем локальную SQLite
DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database", "journal.db")}')

Base = declarative_base()

# ============= МОДЕЛИ =============

class Trade(Base):
    """Модель сделки"""
    __tablename__ = 'trades'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)  # ID пользователя в Telegram
    date = Column(DateTime, default=datetime.now)  # Дата создания
    symbol = Column(String(20), nullable=False)  # Монета (BTCUSDT, ETHUSDT)
    direction = Column(String(10), nullable=False)  # LONG / SHORT
    position_size = Column(Float, nullable=False)  # Размер позиции в $
    entry_price = Column(Float, nullable=True)  # Цена входа
    exit_price = Column(Float, nullable=True)  # Цена выхода
    deposit = Column(Float, nullable=True)  # Депозит на момент сделки
    setup = Column(String(200))  # Сетап (стратегия)
    confidence = Column(Integer)  # Уверенность 1-10
    screenshot = Column(String(500))  # Путь к скриншоту
    status = Column(String(20), default='open')  # open / closed
    result = Column(String(20))  # profit / loss / breakeven
    pnl = Column(Float)  # Прибыль/убыток в $
    close_date = Column(DateTime)  # Дата закрытия
    mistake = Column(String(50))  # Причина ошибки
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class User(Base):
    """Модель пользователя"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True, nullable=False)  # ID пользователя в Telegram
    initial_deposit = Column(Float, default=0)  # Начальный депозит
    current_deposit = Column(Float, default=0)  # Текущий депозит
    created_at = Column(DateTime, default=datetime.now)

# ============= СОЗДАНИЕ ДВИЖКА И СЕССИИ =============

# Создаем движок
engine = create_engine(DATABASE_URL)

# Создаем все таблицы (если их нет)
Base.metadata.create_all(engine)

# Создаем фабрику сессий
Session = sessionmaker(bind=engine)

# ============= ПРОВЕРКА ПОДКЛЮЧЕНИЯ =============
try:
    with engine.connect() as conn:
        print(f"✅ Подключение к базе данных успешно!")
        print(f"   URL: {DATABASE_URL[:50]}..." if len(DATABASE_URL) > 50 else f"   URL: {DATABASE_URL}")
except Exception as e:
    print(f"❌ Ошибка подключения к базе данных: {e}")
    print(f"   URL: {DATABASE_URL}")

# ============= ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =============

def get_session():
    """Получить сессию для работы с БД"""
    return Session()

def get_engine():
    """Получить движок БД"""
    return engine

def init_db():
    """Инициализация БД (создание таблиц)"""
    Base.metadata.create_all(engine)
    print("✅ Таблицы созданы/проверены")

def drop_db():
    """Удаление всех таблиц (ОСТОРОЖНО!)"""
    Base.metadata.drop_all(engine)
    print("⚠️ Все таблицы удалены")