# main.py
import asyncio
import logging
import sys
import os
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot import dp, bot

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    time.sleep(1)
    await bot.delete_webhook(drop_pending_updates=True)
    print("✅ Вебхук удалён")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен")
    except Exception as e:
        print(f"❌ Ошибка: {e}")