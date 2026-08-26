# handlers/history.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from keyboards.menu import main_menu, confirm_delete_menu
from database.db import Database
from services.deposit import DepositService

router = Router()

@router.callback_query(F.data == "history")
async def history_callback(callback: CallbackQuery):
    await callback.message.delete()
    await show_history(callback.message, callback.from_user.id)
    await callback.answer()

@router.message(Command("history"))
async def history_command(message: Message):
    await show_history(message, message.from_user.id)

async def show_history(message: Message, user_id: int):
    trades = Database.get_trades(user_id, limit=50)
    
    if not trades:
        await message.answer(
            "📈 История сделок\n\n"
            "Нет сделок.",
            reply_markup=main_menu()
        )
        return
    
    await message.answer("📈 История сделок (нажмите 🗑️ для удаления):")
    
    open_count = 0
    closed_count = 0
    
    for trade in trades:
        status_emoji = "🟡" if trade.status == "open" else "🟢" if trade.result == "profit" else "🔴" if trade.result == "loss" else "⚪"
        pnl_text = f"{trade.pnl:.2f}$" if trade.pnl is not None else "—"
        
        text = (
            f"<b>#{trade.id}</b>\n"
            f"🪙 {trade.symbol} {trade.direction}\n"
            f"📅 {trade.date.strftime('%d.%m.%Y')}\n"
            f"Статус: {status_emoji}\n"
            f"PnL: {pnl_text}\n"
            f"💰 Размер: {trade.position_size}$\n"
            f"💵 Депозит: {trade.deposit}$\n"
        )
        
        if trade.setup:
            text += f"📝 Сетап: {trade.setup}\n"
        
        if trade.confidence:
            text += f"⭐ Уверенность: {trade.confidence}/10\n"
        
        if trade.mistake:
            text += f"❌ Ошибка: {trade.mistake}\n"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🗑️ Удалить сделку", callback_data=f"delete_trade_{trade.id}")]
        ])
        
        if trade.status == 'open':
            open_count += 1
        else:
            closed_count += 1
        
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    
    await message.answer(
        f"📊 Итого: {len(trades)} сделок\n"
        f"🟡 Открытых: {open_count}\n"
        f"🔒 Закрытых: {closed_count}",
        reply_markup=main_menu()
    )

@router.callback_query(F.data.startswith("delete_trade_"))
async def delete_trade_button(callback: CallbackQuery):
    trade_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    
    trade = Database.get_trade_by_id(trade_id)
    
    if not trade:
        await callback.message.delete()
        await callback.message.answer(
            f"❌ Сделка #{trade_id} не найдена",
            reply_markup=main_menu()
        )
        await callback.answer()
        return
    
    if trade.user_id != user_id:
        await callback.message.answer(
            "⛔ Вы можете удалять только свои сделки!",
            reply_markup=main_menu()
        )
        await callback.answer()
        return
    
    status_text = "🟡 Открыта" if trade.status == "open" else "🔒 Закрыта"
    
    await callback.message.delete()
    await callback.message.answer(
        f"⚠️ Вы уверены, что хотите удалить сделку #{trade_id}?\n\n"
        f"🪙 {trade.symbol} {trade.direction}\n"
        f"💰 {trade.position_size}$\n"
        f"📅 {trade.date.strftime('%d.%m.%Y')}\n"
        f"Статус: {status_text}\n"
        f"📝 Сетап: {trade.setup or '—'}\n\n"
        f"⚠️ Это действие нельзя отменить!",
        reply_markup=confirm_delete_menu(trade_id)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("confirm_delete_"))
async def confirm_delete(callback: CallbackQuery):
    trade_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    
    trade = Database.get_trade_by_id(trade_id)
    
    if not trade:
        await callback.message.delete()
        await callback.message.answer(
            f"❌ Сделка #{trade_id} не найдена",
            reply_markup=main_menu()
        )
        await callback.answer()
        return
    
    if trade.user_id != user_id:
        await callback.message.delete()
        await callback.message.answer(
            "⛔ Вы можете удалять только свои сделки!",
            reply_markup=main_menu()
        )
        await callback.answer()
        return
    
    # Сохраняем информацию до удаления
    symbol = trade.symbol
    direction = trade.direction
    position_size = trade.position_size
    trade_date = trade.date.strftime('%d.%m.%Y')
    setup = trade.setup or '—'
    
    # Удаляем сделку
    if Database.delete_trade(trade_id):
        # Пересчитываем депозит через DepositService
        new_deposit = DepositService.recalculate_deposit(user_id)
        initial_deposit = DepositService.get_initial_deposit(user_id)
        
        await callback.message.delete()
        await callback.message.answer(
            f"✅ Сделка #{trade_id} удалена!\n\n"
            f"🪙 {symbol} {direction}\n"
            f"💰 {position_size}$\n"
            f"📅 {trade_date}\n"
            f"📝 Сетап: {setup}\n\n"
            f"💰 Текущий депозит: {new_deposit:.2f}$\n"
            f"📊 Начальный депозит: {initial_deposit:.2f}$",
            reply_markup=main_menu()
        )
    else:
        await callback.message.answer(
            f"❌ Ошибка при удалении сделки #{trade_id}",
            reply_markup=main_menu()
        )
    
    await callback.answer()

@router.callback_query(F.data == "cancel_delete")
async def cancel_delete(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer(
        "✅ Удаление отменено",
        reply_markup=main_menu()
    )
    await callback.answer()