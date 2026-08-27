# bot.py
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from config import BOT_TOKEN
import logging
from handlers import add_trade, close_trade, stats, history, admin, deposit
from keyboards import menu
from services.broadcast import BroadcastService

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

broadcast_service = BroadcastService(bot)
admin.set_broadcast_service(broadcast_service)

dp.include_routers(
    add_trade.router,
    close_trade.router,
    stats.router,
    history.router,
    admin.router,
    deposit.router,
    menu.router
)