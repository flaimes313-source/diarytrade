# config.py
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')

# Безопасная обработка ADMIN_IDS
admin_ids_str = os.getenv('ADMIN_IDS', '')
if admin_ids_str:
    try:
        ADMIN_IDS = [int(x.strip()) for x in admin_ids_str.split(',') if x.strip()]
    except ValueError:
        ADMIN_IDS = []
else:
    ADMIN_IDS = []

# Пути
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, 'database', 'journal.db')
SCREENSHOTS_DIR = os.path.join(BASE_DIR, 'data', 'screenshots')

# СОЗДАЕМ ВСЕ НЕОБХОДИМЫЕ ПАПКИ
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
            else:
                print(f"✅ Папка существует: {dir_path}")
        except Exception as e:
            print(f"⚠️ Ошибка при создании папки {dir_path}: {e}")

# Создаем папки
create_required_dirs()

# Проверяем наличие BOT_TOKEN
if not BOT_TOKEN:
    print("❌ ОШИБКА: BOT_TOKEN не найден в файле .env!")
    print("Создайте файл .env со следующим содержимым:")
    print("BOT_TOKEN=ваш_токен_бота")
    print("ADMIN_IDS=ваш_telegram_id")
    exit(1)

print(f"✅ Конфигурация загружена успешно!")
print(f"✅ Администраторы: {ADMIN_IDS}")
print(f"✅ База данных: {DATABASE_PATH}")
print(f"✅ Папка скриншотов: {SCREENSHOTS_DIR}")