# handlers/close_trade.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from handlers.add_trade import CloseTradeStates
from keyboards.menu import main_menu, result_keyboard, mistake_keyboard, open_trades_menu
from database.db import Database

router = Router()

@router.callback_query(F.data == "close_trade")
async def close_trade_menu(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    open_trades = Database.get_open_trades(user_id)
    
    if not open_trades:
        await callback.message.answer(
            "❌ У вас нет открытых сделок.",
            reply_markup=main_menu()
        )
        await callback.answer()
        return
    
    if len(open_trades) == 1:
        trade = open_trades[0]
        try:
            await callback.message.delete()
        except:
            pass
        await callback.message.answer(
            f"📊 Закрытие сделки #{trade.id}\n\n"
            f"🪙 {trade.symbol}\n"
            f"📈 {trade.direction}\n"
            f"💰 {trade.position_size}$\n\n"
            f"Выберите результат:",
            reply_markup=result_keyboard()
        )
        await state.update_data(trade_id=trade.id)
        await state.set_state(CloseTradeStates.waiting_result)
    else:
        try:
            await callback.message.delete()
        except:
            pass
        text = f"📊 Выберите сделку для закрытия:\n\n"
        for trade in open_trades:
            text += f"#{trade.id} 🪙 {trade.symbol} 📈 {trade.direction} | 💰 {trade.position_size}$\n"
        
        await callback.message.answer(
            text,
            reply_markup=open_trades_menu(open_trades)
        )
    
    await callback.answer()

@router.callback_query(F.data.startswith("close_trade_"))
async def close_specific_trade(callback: CallbackQuery, state: FSMContext):
    trade_id = int(callback.data.split("_")[2])
    
    trade = Database.get_trade_by_id(trade_id)
    if not trade or trade.status != 'open':
        await callback.message.answer(
            "❌ Сделка уже закрыта или не найдена.",
            reply_markup=main_menu()
        )
        await callback.answer()
        return
    
    try:
        await callback.message.delete()
    except:
        pass
    
    await callback.message.answer(
        f"📊 Закрытие сделки #{trade.id}\n\n"
        f"🪙 {trade.symbol}\n"
        f"📈 {trade.direction}\n"
        f"💰 {trade.position_size}$\n\n"
        f"Выберите результат:",
        reply_markup=result_keyboard()
    )
    await state.update_data(trade_id=trade.id)
    await state.set_state(CloseTradeStates.waiting_result)
    await callback.answer()

@router.callback_query(CloseTradeStates.waiting_result)
async def process_result(callback: CallbackQuery, state: FSMContext):
    result = callback.data
    await state.update_data(result=result)
    
    try:
        await callback.message.delete()
    except:
        pass
    
    # 👇 Разные сообщения для разных результатов
    if result == "profit":
        await callback.message.answer(
            "🟢 Прибыль\n\n"
            "Введите сумму прибыли в $\n\n"
            "Например: 58"
        )
        await state.set_state(CloseTradeStates.waiting_pnl)
    elif result == "loss":
        await callback.message.answer(
            "🔴 Убыток\n\n"
            "Введите сумму убытка в $\n\n"
            "Например: 22"
        )
        await state.set_state(CloseTradeStates.waiting_pnl)
    else:  # breakeven
        await state.update_data(pnl=0)
        await state.update_data(mistake=None)
        await close_trade_final(callback.message, state)
    
    await callback.answer()

@router.message(CloseTradeStates.waiting_pnl)
async def process_pnl(message: Message, state: FSMContext):
    data = await state.get_data()
    result = data.get('result')
    
    try:
        amount = float(message.text.replace(',', '.'))
        
        # 👇 Если прибыль - оставляем как есть (положительное)
        # 👇 Если убыток - делаем отрицательным
        if result == "profit":
            pnl = amount
        elif result == "loss":
            pnl = -amount
        else:
            pnl = 0
        
        await state.update_data(pnl=pnl)
        
        print(f"📊 Результат: {result}, Сумма: {amount}, PnL: {pnl}")  # 👈 ОТЛАДКА
        
        # Если убыток - спрашиваем причину
        if result == "loss":
            await message.answer(
                "❓ Почему получили убыток? Выберите причину:",
                reply_markup=mistake_keyboard()
            )
            await state.set_state(CloseTradeStates.waiting_mistake)
        else:
            await state.update_data(mistake=None)
            await close_trade_final(message, state)
            
    except ValueError:
        await message.answer("❌ Введите число (например: 58 или 22)")

@router.callback_query(CloseTradeStates.waiting_mistake)
async def process_mistake(callback: CallbackQuery, state: FSMContext):
    mistake = None if callback.data == "no_mistake" else callback.data
    await state.update_data(mistake=mistake)
    
    try:
        await callback.message.delete()
    except:
        pass
    
    print(f"📊 Причина ошибки: {mistake}")  # 👈 ОТЛАДКА
    await close_trade_final(callback.message, state)
    await callback.answer()

async def close_trade_final(message: Message, state: FSMContext):
    data = await state.get_data()
    trade_id = data.get('trade_id')
    result = data.get('result')
    pnl = data.get('pnl', 0)
    mistake = data.get('mistake')
    
    print(f"📊 Закрытие: trade_id={trade_id}, result={result}, pnl={pnl}")  # 👈 ОТЛАДКА
    
    if not trade_id:
        await message.answer("❌ Ошибка: не найдена сделка для закрытия")
        await state.clear()
        return
    
    # Получаем сделку
    trade = Database.get_trade_by_id(trade_id)
    if not trade or trade.status != 'open':
        await message.answer("❌ Сделка уже закрыта или не найдена")
        await state.clear()
        return
    
    # Закрываем сделку в БД
    Database.close_trade(trade_id, result, pnl, mistake)
    print(f"📊 Сделка #{trade_id} закрыта в БД")
    
    # Обновляем депозит
    user_id = message.from_user.id
    current_deposit = Database.get_current_deposit(user_id)
    new_deposit = current_deposit + pnl
    Database.update_deposit(user_id, new_deposit)
    
    # ОТЛАДКА
    print(f"💰 Депозит ДО: {current_deposit}")
    print(f"💰 PnL: {pnl}")
    print(f"💰 Депозит ПОСЛЕ: {new_deposit}")
    
    # Определяем эмодзи для результата
    emoji = "🟢" if result == "profit" else "🔴" if result == "loss" else "⚪"
    result_text = "Прибыль" if result == "profit" else "Убыток" if result == "loss" else "Безубыток"
    
    # Форматируем PnL для отображения
    if result == "profit":
        pnl_display = f"+{pnl:.2f}$"
    elif result == "loss":
        pnl_display = f"-{abs(pnl):.2f}$"
    else:
        pnl_display = "0.00$"
    
    response = (
        f"✅ Сделка #{trade.id} закрыта!\n\n"
        f"🪙 {trade.symbol}\n"
        f"📈 {trade.direction}\n"
        f"💰 {trade.position_size}$\n"
        f"Результат: {emoji} {result_text}\n"
        f"PnL: {pnl_display}\n"
        f"Новый депозит: {new_deposit:.2f}$\n"
    )
    
    if mistake:
        response += f"\n💡 Причина: {mistake}"
    
    await message.answer(response, reply_markup=main_menu())
    await state.clear()