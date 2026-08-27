# keyboards/menu.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram import Router, F
from database.db import Database

router = Router()

def main_menu(has_open_trade=False):
    buttons = [
        [InlineKeyboardButton(text="➕ Новая сделка", callback_data="new_trade")]
    ]
    if has_open_trade:
        buttons.append([InlineKeyboardButton(text="✅ Закрыть сделку", callback_data="close_trade")])
    buttons.extend([
        [InlineKeyboardButton(text="📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton(text="📈 История", callback_data="history")],
        [InlineKeyboardButton(text="📤 Экспорт в Excel", callback_data="export_excel")],
        [InlineKeyboardButton(text="💰 Депозит", callback_data="deposit_menu")]
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def stats_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 По сетапам", callback_data="stats_setups")],
        [InlineKeyboardButton(text="📅 По месяцам", callback_data="stats_months")],
        [InlineKeyboardButton(text="🎯 По монетам", callback_data="stats_symbols")],
        [InlineKeyboardButton(text="📉 График депозита", callback_data="stats_chart")],
        [InlineKeyboardButton(text="📤 Экспорт в Excel", callback_data="export_excel")],
        [InlineKeyboardButton(text="🗑️ Очистить статистику", callback_data="clear_stats")],
        [InlineKeyboardButton(text="🧠 Анализ ошибок", callback_data="stats_mistakes")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]
    ])

def deposit_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Текущий депозит", callback_data="show_deposit")],
        [InlineKeyboardButton(text="✏️ Изменить депозит", callback_data="change_deposit")],
        [InlineKeyboardButton(text="📊 История депозита", callback_data="deposit_history")],
        [InlineKeyboardButton(text="🔄 Сбросить депозит", callback_data="reset_deposit_menu")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]
    ])

def confirm_reset_deposit_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, сбросить", callback_data="confirm_reset_deposit"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_reset_deposit")
        ]
    ])

def direction_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 LONG", callback_data="LONG")],
        [InlineKeyboardButton(text="🔴 SHORT", callback_data="SHORT")]
    ])

def result_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 Прибыль", callback_data="profit")],
        [InlineKeyboardButton(text="🔴 Убыток", callback_data="loss")],
        [InlineKeyboardButton(text="⚪ Безубыток", callback_data="breakeven")]
    ])

def mistake_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📉 Ранний вход", callback_data="Ранний вход")],
        [InlineKeyboardButton(text="📈 Поздний вход", callback_data="Поздний вход")],
        [InlineKeyboardButton(text="🚫 Без стопа", callback_data="Без стопа")],
        [InlineKeyboardButton(text="📰 Новость", callback_data="Новость")],
        [InlineKeyboardButton(text="😤 Эмоции", callback_data="Эмоции")],
        [InlineKeyboardButton(text="📋 Нарушил стратегию", callback_data="Нарушил стратегию")],
        [InlineKeyboardButton(text="❓ Другое", callback_data="Другое")],
        [InlineKeyboardButton(text="⏭️ Пропустить", callback_data="no_mistake")]
    ])

def add_trade_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭️ Пропустить скриншот", callback_data="skip_screenshot")]
    ])

def open_trades_menu(trades):
    buttons = []
    for trade in trades:
        buttons.append([
            InlineKeyboardButton(
                text=f"#{trade.id} {trade.symbol} {trade.direction} | 💰 {trade.position_size}$",
                callback_data=f"close_trade_{trade.id}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def confirm_delete_menu(trade_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"confirm_delete_{trade_id}"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_delete")
        ]
    ])

def clear_stats_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, очистить", callback_data="confirm_clear_stats"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="back_to_menu")
        ]
    ])

def admin_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users")],
        [InlineKeyboardButton(text="📊 Общая статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]
    ])

def broadcast_photo_skip_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭️ Пропустить фото", callback_data="broadcast_skip_photo")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="broadcast_cancel")]
    ])

def broadcast_confirm_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Отправить", callback_data="broadcast_confirm")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="broadcast_cancel")]
    ])

def confirm_change_deposit_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_change_deposit"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_change_deposit")
        ]
    ])

# ============= ОБРАБОТЧИКИ =============

@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except:
        pass
    open_trades = Database.get_open_trades(callback.from_user.id)
    await callback.message.answer(
        "📖 Главное меню",
        reply_markup=main_menu(has_open_trade=bool(open_trades))
    )
    await callback.answer()

@router.callback_query(F.data == "cancel_delete")
async def cancel_delete(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except:
        pass
    await callback.message.answer("✅ Удаление отменено", reply_markup=main_menu())
    await callback.answer()

@router.callback_query(F.data == "reset_deposit_menu")
async def reset_deposit_menu(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except:
        pass
    user_id = callback.from_user.id
    current_deposit = Database.get_current_deposit(user_id)
    open_trades = Database.get_open_trades(user_id)
    if open_trades:
        await callback.message.answer(
            f"⚠️ У вас есть открытые сделки!\n\nСначала закройте все открытые сделки, затем сбросьте депозит.\nОткрытых сделок: {len(open_trades)}",
            reply_markup=main_menu(has_open_trade=True)
        )
        await callback.answer()
        return
    await callback.message.answer(
        f"💰 Сброс депозита\n\nТекущий депозит: {current_deposit}$\nВсе сделки будут сохранены в истории.\n\n⚠️ Вы уверены?",
        reply_markup=confirm_reset_deposit_menu()
    )
    await callback.answer()

@router.callback_query(F.data == "confirm_reset_deposit")
async def confirm_reset_deposit_callback(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except:
        pass
    await callback.message.answer(
        "💰 Введите новый начальный депозит:\n\nПример: 1000\n\nИли отправьте 0 чтобы обнулить"
    )
    await callback.answer()

@router.callback_query(F.data == "cancel_reset_deposit")
async def cancel_reset_deposit_callback(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except:
        pass
    await callback.message.answer("✅ Сброс депозита отменен", reply_markup=main_menu())
    await callback.answer()