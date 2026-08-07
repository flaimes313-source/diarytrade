# handlers/admin.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram import Bot
from config import ADMIN_IDS, BOT_TOKEN
from database.db import Database

# Создаем отдельный экземпляр бота для админ-функций
admin_bot = Bot(token=BOT_TOKEN)

router = Router()

# Декоратор для проверки прав админа
def admin_only(func):
    async def wrapper(message: Message, *args, **kwargs):
        if message.from_user.id not in ADMIN_IDS:
            await message.answer("⛔ Только для администраторов!")
            return
        return await func(message, *args, **kwargs)
    return wrapper

@router.message(Command("admin"))
@admin_only
async def admin_panel(message: Message):
    await message.answer(
        "👑 Админ панель\n\n"
        "Доступные команды:\n"
        "/users - Список пользователей\n"
        "/broadcast - Рассылка\n"
        "/del 123 - Удалить сделку по ID (админ)\n"
        "/mydel 123 - Удалить свою сделку по ID\n"
        "/stats - Статистика\n"
        "/export_all - Экспорт всех данных"
    )

@router.message(Command("users"))
@admin_only
async def list_users(message: Message):
    users = Database.get_all_users()
    if not users:
        await message.answer("👥 Нет пользователей")
        return
    
    text = f"👥 Всего пользователей: {len(users)}\n\n"
    for user in users[:10]:
        # Получаем количество сделок пользователя
        trades = Database.get_all_trades(user.user_id)
        text += f"🆔 {user.user_id} - Сделок: {len(trades)}\n"
    
    if len(users) > 10:
        text += f"\n... и еще {len(users) - 10} пользователей"
    
    await message.answer(text)

@router.message(Command("broadcast"))
@admin_only
async def broadcast(message: Message):
    text = message.text.replace("/broadcast", "").strip()
    if not text:
        await message.answer(
            "❌ Напишите текст для рассылки после команды\n\n"
            "Пример:\n"
            "/broadcast Привет! Обновление бота!"
        )
        return
    
    users = Database.get_all_users()
    if not users:
        await message.answer("❌ Нет пользователей для рассылки")
        return
    
    # Отправляем подтверждение
    await message.answer(f"⏳ Начинаю рассылку {len(users)} пользователям...")
    
    sent = 0
    failed = 0
    failed_users = []
    
    for user in users:
        try:
            await admin_bot.send_message(user.user_id, text)
            sent += 1
        except Exception as e:
            failed += 1
            failed_users.append(user.user_id)
    
    # Отправляем результат
    result_text = (
        f"✅ Рассылка завершена!\n\n"
        f"📤 Отправлено: {sent}\n"
        f"❌ Не доставлено: {failed}\n"
        f"👥 Всего: {len(users)}"
    )
    
    if failed_users:
        result_text += f"\n\nНе доставлено пользователям:\n" + "\n".join([str(uid) for uid in failed_users[:5]])
        if len(failed_users) > 5:
            result_text += f"\n... и еще {len(failed_users) - 5}"
    
    await message.answer(result_text)

# ============= УДАЛЕНИЕ СВОЕЙ СДЕЛКИ =============
@router.message(Command("mydel"))
async def delete_my_trade(message: Message):
    """Удалить свою сделку по ID (только свои сделки)"""
    user_id = message.from_user.id
    
    # Парсим ID сделки из команды
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer(
            "❌ Укажите ID сделки для удаления\n\n"
            "Пример: /mydel 5\n\n"
            "Чтобы узнать ID сделки, посмотрите в /history"
        )
        return
    
    try:
        trade_id = int(parts[1])
    except ValueError:
        await message.answer("❌ ID должен быть числом")
        return
    
    # Получаем сделку
    trade = Database.get_trade_by_id(trade_id)
    
    if not trade:
        await message.answer(f"❌ Сделка с ID {trade_id} не найдена")
        return
    
    # Проверяем, что сделка принадлежит этому пользователю
    if trade.user_id != user_id:
        await message.answer("⛔ Вы можете удалять только свои сделки!")
        return
    
    # Проверяем, что сделка открыта
    if trade.status == 'closed':
        await message.answer("❌ Нельзя удалить закрытую сделку")
        return
    
    # Удаляем сделку
    if Database.delete_trade(trade_id):
        await message.answer(
            f"✅ Сделка #{trade_id} удалена!\n\n"
            f"🪙 {trade.symbol}\n"
            f"📈 {trade.direction}\n"
            f"💰 {trade.position_size}$\n"
            f"📅 {trade.date.strftime('%d.%m.%Y')}\n"
            f"Статус: 🟡 Открыта\n\n"
            f"💡 Вы можете создать новую сделку через меню"
        )
    else:
        await message.answer(f"❌ Ошибка при удалении сделки #{trade_id}")

# ============= УДАЛЕНИЕ ЛЮБОЙ СДЕЛКИ (ТОЛЬКО АДМИН) =============
@router.message(Command("del"))
@admin_only
async def delete_trade_admin(message: Message):
    """Удалить любую сделку по ID (только для админов)"""
    
    # Парсим ID сделки из команды
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer(
            "❌ Укажите ID сделки для удаления\n\n"
            "Пример: /del 5"
        )
        return
    
    try:
        trade_id = int(parts[1])
    except ValueError:
        await message.answer("❌ ID должен быть числом")
        return
    
    # Получаем сделку
    trade = Database.get_trade_by_id(trade_id)
    
    if not trade:
        await message.answer(f"❌ Сделка с ID {trade_id} не найдена")
        return
    
    # Сохраняем информацию о сделке для ответа
    trade_info = (
        f"🪙 {trade.symbol}\n"
        f"📈 {trade.direction}\n"
        f"💰 {trade.position_size}$\n"
        f"📅 {trade.date.strftime('%d.%m.%Y')}\n"
        f"👤 Пользователь: {trade.user_id}\n"
        f"Статус: {'🟡 Открыта' if trade.status == 'open' else '🔴 Закрыта'}"
    )
    
    if trade.status == 'closed':
        trade_info += f"\nРезультат: {trade.result}\nPnL: {trade.pnl}$"
    
    # Подтверждение удаления
    await message.answer(
        f"⚠️ Вы уверены, что хотите удалить сделку #{trade_id}?\n\n"
        f"{trade_info}\n\n"
        f"Для подтверждения отправьте:\n"
        f"/del_confirm {trade_id}"
    )

@router.message(Command("del_confirm"))
@admin_only
async def delete_trade_confirm(message: Message):
    """Подтверждение удаления сделки"""
    
    # Парсим ID сделки из команды
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("❌ Укажите ID сделки")
        return
    
    try:
        trade_id = int(parts[1])
    except ValueError:
        await message.answer("❌ ID должен быть числом")
        return
    
    # Получаем сделку
    trade = Database.get_trade_by_id(trade_id)
    
    if not trade:
        await message.answer(f"❌ Сделка с ID {trade_id} не найдена")
        return
    
    # Удаляем сделку
    if Database.delete_trade(trade_id):
        await message.answer(
            f"✅ Сделка #{trade_id} удалена админом!\n\n"
            f"🪙 {trade.symbol}\n"
            f"📈 {trade.direction}\n"
            f"👤 Пользователь: {trade.user_id}"
        )
    else:
        await message.answer(f"❌ Ошибка при удалении сделки #{trade_id}")

# ============= ЭКСПОРТ ВСЕХ ДАННЫХ (АДМИН) =============
@router.message(Command("export_all"))
@admin_only
async def export_all_data(message: Message):
    """Экспорт всех данных всех пользователей (только админ)"""
    from services.export import ExportService
    from aiogram.types import BufferedInputFile
    
    await message.answer("⏳ Генерация полного отчета...")
    
    # Получаем всех пользователей
    users = Database.get_all_users()
    if not users:
        await message.answer("❌ Нет пользователей")
        return
    
    # Экспортируем данные каждого пользователя
    # В реальности лучше сделать отдельный метод для экспорта всех данных
    
    text = "📊 Отчет по всем пользователям\n\n"
    
    total_trades = 0
    total_pnl = 0
    
    for user in users:
        trades = Database.get_all_trades(user.user_id)
        stats = Database.get_stats(user.user_id)
        deposit = Database.get_current_deposit(user.user_id)
        
        if stats['total'] > 0:
            text += (
                f"👤 Пользователь: {user.user_id}\n"
                f"   Сделок: {stats['total']}\n"
                f"   Win Rate: {stats['win_rate']:.1f}%\n"
                f"   PnL: {'+' if stats['total_pnl'] > 0 else ''}{stats['total_pnl']:.2f}$\n"
                f"   Депозит: {deposit:.2f}$\n\n"
            )
            
            total_trades += stats['total']
            total_pnl += stats['total_pnl']
    
    text += (
        f"📊 ИТОГО:\n"
        f"Всего пользователей: {len(users)}\n"
        f"Всего сделок: {total_trades}\n"
        f"Общий PnL: {'+' if total_pnl > 0 else ''}{total_pnl:.2f}$"
    )
    
    await message.answer(text, parse_mode="HTML")

# ============= СТАТИСТИКА ПОЛЬЗОВАТЕЛЯ (АДМИН) =============
@router.message(Command("user_stats"))
@admin_only
async def user_stats(message: Message):
    """Статистика конкретного пользователя (админ)"""
    
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer(
            "❌ Укажите ID пользователя\n\n"
            "Пример: /user_stats 123456789"
        )
        return
    
    try:
        user_id = int(parts[1])
    except ValueError:
        await message.answer("❌ ID должен быть числом")
        return
    
    stats = Database.get_stats(user_id)
    deposit = Database.get_current_deposit(user_id)
    user = Database.get_or_create_user(user_id)
    
    if stats['total'] == 0:
        await message.answer(f"👤 Пользователь {user_id}\n\nНет сделок")
        return
    
    text = (
        f"👤 Статистика пользователя {user_id}\n\n"
        f"📊 Статистика\n"
        f"Всего сделок: {stats['total']}\n"
        f"Побед: {stats['wins']}\n"
        f"Поражений: {stats['losses']}\n"
        f"Win Rate: {stats['win_rate']:.2f}%\n"
        f"Общий PnL: {'+' if stats['total_pnl'] > 0 else ''}{stats['total_pnl']:.2f}$\n"
        f"Начальный депозит: {user.initial_deposit:.2f}$\n"
        f"Текущий депозит: {deposit:.2f}$\n"
        f"Profit Factor: {stats['profit_factor']:.2f}"
    )
    
    await message.answer(text)