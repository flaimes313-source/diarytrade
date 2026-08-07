# bot.py
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from config import BOT_TOKEN
import asyncio
import logging

from handlers import add_trade, close_trade, stats, history
from handlers import admin
from keyboards import menu

logging.basicConfig(level=logging.INFO)

# Создаем бота и диспетчер
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# Регистрируем роутеры
dp.include_routers(
    add_trade.router,
    close_trade.router,
    stats.router,
    history.router,
    admin.router,
    menu.router
)

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())