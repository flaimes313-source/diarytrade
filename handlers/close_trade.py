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

# ============= ОСНОВНЫЕ ОБРАБОТЧИКИ ДЛЯ РЕЗУЛЬТАТОВ =============
@router.callback_query(CloseTradeStates.waiting_result)
async def process_result(callback: CallbackQuery, state: FSMContext):
    await state.update_data(result=callback.data)
    
    try:
        await callback.message.delete()
    except:
        pass
    
    emoji = "🟢" if callback.data == "profit" else "🔴" if callback.data == "loss" else "⚪"
    result_text = "Прибыль" if callback.data == "profit" else "Убыток" if callback.data == "loss" else "Безубыток"
    
    await callback.message.answer(
        f"{emoji} {result_text}\n\n"
        f"Введите сумму в $\n\n"
        f"Например: +58 или -22"
    )
    await state.set_state(CloseTradeStates.waiting_pnl)
    await callback.answer()

@router.message(CloseTradeStates.waiting_pnl)
async def process_pnl(message: Message, state: FSMContext):
    try:
        pnl = float(message.text.replace(',', '.'))
        await state.update_data(pnl=pnl)
        
        if pnl < 0:
            await message.answer(
                "❓ Почему получили убыток? Выберите причину:",
                reply_markup=mistake_keyboard()
            )
            await state.set_state(CloseTradeStates.waiting_mistake)
        else:
            await state.update_data(mistake=None)
            await close_trade_final(message, state)
            
    except ValueError:
        await message.answer("❌ Введите число (например: +58 или -22)")

@router.callback_query(CloseTradeStates.waiting_mistake)
async def process_mistake(callback: CallbackQuery, state: FSMContext):
    mistake = None if callback.data == "no_mistake" else callback.data
    await state.update_data(mistake=mistake)
    
    try:
        await callback.message.delete()
    except:
        pass
    
    await close_trade_final(callback.message, state)
    await callback.answer()

async def close_trade_final(message: Message, state: FSMContext):
    data = await state.get_data()
    trade_id = data.get('trade_id')
    
    if not trade_id:
        await message.answer("❌ Ошибка: не найдена сделка для закрытия")
        await state.clear()
        return
    
    trade = Database.get_trade_by_id(trade_id)
    if not trade or trade.status != 'open':
        await message.answer("❌ Сделка уже закрыта или не найдена")
        await state.clear()
        return
    
    Database.close_trade(trade_id, data['result'], data['pnl'], data.get('mistake'))
    
    user_id = message.from_user.id
    current_deposit = Database.get_current_deposit(user_id)
    new_deposit = current_deposit + data['pnl']
    Database.update_deposit(user_id, new_deposit)
    
    emoji = "🟢" if data['result'] == "profit" else "🔴" if data['result'] == "loss" else "⚪"
    result_text = "Прибыль" if data['result'] == "profit" else "Убыток" if data['result'] == "loss" else "Безубыток"
    
    response = (
        f"✅ Сделка #{trade.id} закрыта!\n\n"
        f"🪙 {trade.symbol}\n"
        f"📈 {trade.direction}\n"
        f"💰 {trade.position_size}$\n"
        f"Результат: {emoji} {result_text}\n"
        f"PnL: {'+' if data['pnl'] > 0 else ''}{data['pnl']:.2f}$\n"
        f"Новый депозит: {new_deposit:.2f}$\n"
    )
    
    if data.get('mistake'):
        response += f"\n💡 Причина: {data['mistake']}"
    
    await message.answer(response, reply_markup=main_menu())
    await state.clear()