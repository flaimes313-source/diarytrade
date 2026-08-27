# config.py
import os
from dotenv import load_dotenv
import sys

load_dotenv()

# ==================== БАЗА ДАННЫХ ====================
# Единственное место, где определяется DATABASE_URL
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///database/journal.db')

# ==================== TELEGRAM ====================
BOT_TOKEN = os.getenv('BOT_TOKEN')

# ==================== АДМИНИСТРАТОРЫ ====================
ADMIN_IDS = []
admin_ids_str = os.getenv('ADMIN_IDS', '')
if admin_ids_str:
    try:
        ADMIN_IDS = [int(x.strip()) for x in admin_ids_str.split(',') if x.strip()]
    except ValueError:
        ADMIN_IDS = []

# Если не заданы — подставить для локальной разработки
if not ADMIN_IDS:
    ADMIN_IDS = [462035571]  # Замените на свой ID

# ==================== ПУТИ ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, 'database', 'journal.db')
SCREENSHOTS_DIR = os.path.join(BASE_DIR, 'data', 'screenshots')

# ==================== ПАПКИ ====================
def create_required_dirs():
    for path in [os.path.dirname(DATABASE_PATH), SCREENSHOTS_DIR]:
        if not os.path.exists(path):
            os.makedirs(path)
            print(f"✅ Создана папка: {path}")

create_required_dirs()

# ==================== ПРОВЕРКИ ====================
if not BOT_TOKEN:
    print("❌ ОШИБКА: BOT_TOKEN не найден!")
    sys.exit(1)

# ==================== ДИАГНОСТИКА ПРОДАКШН-БД ====================
def print_db_diagnostics():
    try:
        from sqlalchemy import create_engine, text
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            # Проверяем подключение
            conn.execute(text("SELECT 1"))
            # Считаем пользователей
            users = conn.execute(text("SELECT COUNT(*) FROM users")).scalar()
            trades = conn.execute(text("SELECT COUNT(*) FROM trades")).scalar()
            print("🗄️  ПРОДАКШН-БД")
            print(f"   Тип: {'PostgreSQL' if 'postgresql' in DATABASE_URL else 'SQLite'}")
            print(f"   Пользователи: {users}")
            print(f"   Сделки: {trades}")
    except Exception as e:
        print(f"⚠️ Не удалось проверить БД: {e}")

print_db_diagnostics()

# ==================== ВЫВОД ====================
print(f"✅ Конфигурация загружена")
print(f"✅ Администраторы: {ADMIN_IDS}")
print(f"✅ DATABASE_URL: {DATABASE_URL[:60]}..." if len(DATABASE_URL) > 60 else f"✅ DATABASE_URL: {DATABASE_URL}")