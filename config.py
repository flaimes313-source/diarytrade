# config.py
import os
from dotenv import load_dotenv
import sys

load_dotenv()

# ============= НАСТРОЙКИ БАЗЫ ДАННЫХ =============
# Берем DATABASE_URL из переменных окружения
# Если не задана - используем локальную SQLite
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///database/journal.db')

# ============= TELEGRAM НАСТРОЙКИ =============
BOT_TOKEN = os.getenv('BOT_TOKEN')

# ============= АДМИНИСТРАТОРЫ =============
# Укажите ваш Telegram ID здесь или в .env
ADMIN_IDS = []

admin_ids_str = os.getenv('ADMIN_IDS', '')
if admin_ids_str:
    try:
        ADMIN_IDS = [int(x.strip()) for x in admin_ids_str.split(',') if x.strip()]
    except ValueError:
        ADMIN_IDS = []

# Если ADMIN_IDS не задан в .env, можно указать здесь
# ADMIN_IDS = [462035571]  # раскомментируйте и укажите ваш ID

# ============= ПУТИ =============
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, 'database', 'journal.db')
SCREENSHOTS_DIR = os.path.join(BASE_DIR, 'data', 'screenshots')

# ============= СОЗДАНИЕ ПАПОК =============
def create_required_dirs():
    """Создает все необходимые папки"""
    dirs = [
        os.path.dirname(DATABASE_PATH),
        SCREENSHOTS_DIR
    ]
    for dir_path in dirs:
        try:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
                print(f"✅ Создана папка: {dir_path}")
        except Exception as e:
            print(f"⚠️ Ошибка при создании папки {dir_path}: {e}")

create_required_dirs()

# ============= ПРОВЕРКИ =============
if not BOT_TOKEN:
    print("❌ ОШИБКА: BOT_TOKEN не найден в переменных окружения!")
    print("Добавьте BOT_TOKEN в настройках хостинга или в файле .env")
    sys.exit(1)

# ============= ВЫВОД ИНФОРМАЦИИ =============
print(f"✅ Конфигурация загружена успешно!")
print(f"✅ Администраторы: {ADMIN_IDS}")
print(f"✅ База данных: {DATABASE_PATH}")
print(f"✅ DATABASE_URL: {DATABASE_URL[:50]}..." if len(DATABASE_URL) > 50 else f"✅ DATABASE_URL: {DATABASE_URL}")