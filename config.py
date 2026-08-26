# config.py
import os
from dotenv import load_dotenv
import sys

load_dotenv()

# ============= НАСТРОЙКИ БАЗЫ ДАННЫХ =============
# Берем DATABASE_URL из переменных окружения
# Если не задана - используем локальную SQLite
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///database/journal.db')

# ============= VK НАСТРОЙКИ =============
VK_TOKEN = os.getenv('VK_TOKEN')
VK_GROUP_ID = os.getenv('VK_GROUP_ID')
ADMIN_IDS = []

admin_ids_str = os.getenv('ADMIN_IDS', '')
if admin_ids_str:
    try:
        ADMIN_IDS = [int(x.strip()) for x in admin_ids_str.split(',') if x.strip()]
    except ValueError:
        ADMIN_IDS = []

CONFIRMATION_TOKEN = os.getenv('CONFIRMATION_TOKEN')
VK_SECRET_KEY = os.getenv('VK_SECRET_KEY', '')

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
if not VK_TOKEN:
    print("❌ ОШИБКА: VK_TOKEN не найден в переменных окружения!")
    print("Добавьте VK_TOKEN в настройках хостинга или в файле .env")
    sys.exit(1)

if not VK_GROUP_ID:
    print("❌ ОШИБКА: VK_GROUP_ID не найден в переменных окружения!")
    sys.exit(1)

if not CONFIRMATION_TOKEN:
    print("❌ ОШИБКА: CONFIRMATION_TOKEN не найден в переменных окружения!")
    print("Добавьте CONFIRMATION_TOKEN в настройках хостинга или в файле .env")
    sys.exit(1)

# ============= ВЫВОД ИНФОРМАЦИИ =============
print(f"✅ Конфигурация загружена успешно!")
print(f"✅ VK Group ID: {VK_GROUP_ID}")
print(f"✅ Администраторы: {ADMIN_IDS}")
print(f"✅ База данных: {DATABASE_PATH}")
print(f"✅ DATABASE_URL: {DATABASE_URL[:50]}..." if len(DATABASE_URL) > 50 else f"✅ DATABASE_URL: {DATABASE_URL}")
print(f"✅ Confirmation Token: {CONFIRMATION_TOKEN[:10]}...")