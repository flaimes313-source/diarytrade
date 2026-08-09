# keyboards/menu.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram import Router, F
from database.db import Database

router = Router()

def main_menu(has_open_trade=False):
    """Главное меню"""
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
    """Меню статистики"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 По сетапам", callback_data="stats_setups")],
        [InlineKeyboardButton(text="📅 По месяцам", callback_data="stats_months")],
        [InlineKeyboardButton(text="🎯 По монетам", callback_data="stats_symbols")],
        [InlineKeyboardButton(text="📉 График депозита", callback_data="stats_chart")],
        [InlineKeyboardButton(text="📤 Экспорт в Excel", callback_data="export_excel")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]
    ])

def deposit_menu():
    """Меню управления депозитом"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Установить депозит", callback_data="set_deposit")],
        [InlineKeyboardButton(text="📊 Показать депозит", callback_data="show_deposit")],
        [InlineKeyboardButton(text="🔄 Сбросить депозит", callback_data="reset_deposit_menu")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]
    ])

def confirm_reset_deposit_menu():
    """Меню подтверждения сброса депозита"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, сбросить", callback_data="confirm_reset_deposit"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_reset_deposit")
        ]
    ])

def direction_keyboard():
    """Клавиатура выбора направления"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 LONG", callback_data="LONG")],
        [InlineKeyboardButton(text="🔴 SHORT", callback_data="SHORT")]
    ])

def result_keyboard():
    """Клавиатура выбора результата сделки"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 Прибыль", callback_data="profit")],
        [InlineKeyboardButton(text="🔴 Убыток", callback_data="loss")],
        [InlineKeyboardButton(text="⚪ Безубыток", callback_data="breakeven")]
    ])

def mistake_keyboard():
    """Клавиатура выбора причины ошибки"""
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
    """Меню добавления сделки (пропустить скриншот)"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭️ Пропустить скриншот", callback_data="skip_screenshot")]
    ])

def open_trades_menu(trades):
    """Меню выбора открытой сделки для закрытия"""
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
    """Меню подтверждения удаления сделки"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"confirm_delete_{trade_id}"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_delete")
        ]
    ])

def cancel_delete_menu():
    """Кнопка отмены удаления"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_delete")]
    ])

# ============= ОБРАБОТЧИКИ КЛАВИАТУР =============

@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    """Возврат в главное меню"""
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
    """Отмена удаления сделки"""
    try:
        await callback.message.delete()
    except:
        pass
    await callback.message.answer(
        "✅ Удаление отменено",
        reply_markup=main_menu()
    )
    await callback.answer()

@router.callback_query(F.data == "reset_deposit_menu")
async def reset_deposit_menu(callback: CallbackQuery):
    """Меню сброса депозита"""
    try:
        await callback.message.delete()
    except:
        pass
    
    user_id = callback.from_user.id
    current_deposit = Database.get_current_deposit(user_id)
    open_trades = Database.get_open_trades(user_id)
    
    if open_trades:
        await callback.message.answer(
            f"⚠️ У вас есть открытые сделки!\n\n"
            f"Сначала закройте все открытые сделки, затем сбросьте депозит.\n"
            f"Открытых сделок: {len(open_trades)}",
            reply_markup=main_menu(has_open_trade=True)
        )
        await callback.answer()
        return
    
    await callback.message.answer(
        f"💰 Сброс депозита\n\n"
        f"Текущий депозит: {current_deposit}$\n"
        f"Все сделки будут сохранены в истории.\n\n"
        f"⚠️ Внимание! Это действие сбросит текущий депозит.\n"
        f"Вы уверены, что хотите продолжить?",
        reply_markup=confirm_reset_deposit_menu()
    )
    await callback.answer()

@router.callback_query(F.data == "confirm_reset_deposit")
async def confirm_reset_deposit_callback(callback: CallbackQuery):
    """Подтверждение сброса депозита (перенаправляет на ввод суммы)"""
    try:
        await callback.message.delete()
    except:
        pass
    
    await callback.message.answer(
        "💰 Введите новый начальный депозит:\n\n"
        "Пример: 1000\n\n"
        "Или отправьте 0 чтобы обнулить депозит"
    )
    await callback.answer()

@router.callback_query(F.data == "cancel_reset_deposit")
async def cancel_reset_deposit_callback(callback: CallbackQuery):
    """Отмена сброса депозита"""
    try:
        await callback.message.delete()
    except:
        pass
    await callback.message.answer(
        "✅ Сброс депозита отменен",
        reply_markup=main_menu()
    )
    await callback.answer()

# ============= ОБРАБОТЧИКИ ДЛЯ ИСТОРИИ =============

@router.callback_query(F.data.startswith("delete_trade_"))
async def delete_trade_button(callback: CallbackQuery):
    """Удаление сделки по кнопке корзины"""
    trade_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    
    trade = Database.get_trade_by_id(trade_id)
    
    if not trade:
        try:
            await callback.message.delete()
        except:
            pass
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
    
    try:
        await callback.message.delete()
    except:
        pass
    
    await callback.message.answer(
        f"⚠️ Вы уверены, что хотите удалить сделку #{trade_id}?\n\n"
        f"🪙 {trade.symbol}\n"
        f"📈 {trade.direction}\n"
        f"💰 {trade.position_size}$\n"
        f"📅 {trade.date.strftime('%d.%m.%Y')}\n\n"
        f"💵 Депозит на момент сделки: {trade.deposit}$\n\n"
        f"Это действие нельзя отменить!",
        reply_markup=confirm_delete_menu(trade_id)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("confirm_delete_"))
async def confirm_delete(callback: CallbackQuery):
    """Подтверждение удаления сделки"""
    trade_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    
    trade = Database.get_trade_by_id(trade_id)
    
    if not trade:
        try:
            await callback.message.delete()
        except:
            pass
        await callback.message.answer(
            f"❌ Сделка #{trade_id} не найдена",
            reply_markup=main_menu()
        )
        await callback.answer()
        return
    
    if trade.user_id != user_id:
        try:
            await callback.message.delete()
        except:
            pass
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
    deposit_before = Database.get_current_deposit(user_id)
    
    # Удаляем сделку
    if Database.delete_trade(trade_id):
        deposit_after = Database.get_current_deposit(user_id)
        
        try:
            await callback.message.delete()
        except:
            pass
        
        await callback.message.answer(
            f"✅ Сделка #{trade_id} удалена!\n\n"
            f"🪙 {symbol} {direction}\n"
            f"💰 {position_size}$\n"
            f"📅 {trade_date}\n\n"
            f"💵 Депозит: {deposit_before}$ → {deposit_after}$",
            reply_markup=main_menu()
        )
    else:
        await callback.message.answer(
            f"❌ Ошибка при удалении сделки #{trade_id}",
            reply_markup=main_menu()
        )
    
    await callback.answer()

# ============= ОБРАБОТЧИКИ ДЛЯ СТАТИСТИКИ =============

@router.callback_query(F.data == "stats")
async def stats_callback(callback: CallbackQuery):
    """Обработчик кнопки статистики"""
    from handlers.stats import show_stats
    try:
        await callback.message.delete()
    except:
        pass
    await show_stats(callback.message, callback.from_user.id)
    await callback.answer()

# ============= ОБРАБОТЧИКИ ДЛЯ ЭКСПОРТА =============

@router.callback_query(F.data == "export_excel")
async def export_excel_callback(callback: CallbackQuery):
    """Обработчик кнопки экспорта"""
    from handlers.stats import export_excel
    try:
        await callback.message.delete()
    except:
        pass
    await export_excel(callback.message, callback.from_user.id)
    await callback.answer()