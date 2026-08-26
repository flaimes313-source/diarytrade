# handlers/close_trade.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards.menu import main_menu, result_keyboard, mistake_keyboard, open_trades_menu
from database.db import Database
from services.deposit import DepositService

router = Router()

class CloseTradeStates(StatesGroup):
    waiting_result = State()
    waiting_pnl = State()
    waiting_mistake = State()

@router.callback_query(F.data == "close_trade")
async def close_trade_menu(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    open_trades = Database.get_open_trades(user_id)
    
    if not open_trades:
        await callback.message.answer("❌ У вас нет открытых сделок.", reply_markup=main_menu())
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
        text = "📊 Выберите сделку для закрытия:\n\n"
        for trade in open_trades:
            text += f"#{trade.id} 🪙 {trade.symbol} 📈 {trade.direction} | 💰 {trade.position_size}$\n"
        await callback.message.answer(text, reply_markup=open_trades_menu(open_trades))
    
    await callback.answer()

@router.callback_query(F.data.startswith("close_trade_"))
async def close_specific_trade(callback: CallbackQuery, state: FSMContext):
    trade_id = int(callback.data.split("_")[2])
    trade = Database.get_trade_by_id(trade_id)
    if not trade or trade.status != 'open':
        await callback.message.answer("❌ Сделка уже закрыта или не найдена.", reply_markup=main_menu())
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
    else:
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
        print(f"📊 process_pnl: result={result}, amount={amount}")
        
        if result == "loss":
            pnl = -abs(amount)
        else:
            pnl = abs(amount)
        
        await state.update_data(pnl=pnl)
        print(f"📊 process_pnl: pnl={pnl}")
        
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
    print(f"📊 process_mistake: mistake={mistake}")
    await close_trade_final(callback.message, state)
    await callback.answer()

async def close_trade_final(message: Message, state: FSMContext):
    data = await state.get_data()
    trade_id = data.get('trade_id')
    result = data.get('result')
    pnl = data.get('pnl', 0)
    mistake = data.get('mistake')
    
    print(f"📊 close_trade_final: result={result}, pnl={pnl}, mistake={mistake}")
    
    if not trade_id:
        await message.answer("❌ Ошибка: не найдена сделка")
        await state.clear()
        return
    
    trade = Database.get_trade_by_id(trade_id)
    if not trade or trade.status != 'open':
        await message.answer("❌ Сделка уже закрыта")
        await state.clear()
        return
    
    # 👇 ГЛАВНОЕ ИСПРАВЛЕНИЕ: берем user_id из сделки!
    user_id = trade.user_id
    print(f"👤 user_id из сделки: {user_id}")
    
    Database.get_or_create_user(user_id)
    Database.close_trade(trade_id, result, pnl, mistake)
    
    # Пересчитываем депозит через DepositService
    new_deposit = DepositService.recalculate_deposit(user_id)
    current_deposit = DepositService.get_current_deposit(user_id)
    
    print(f"💰 Депозит после пересчета: {current_deposit}")
    
    emoji = "🟢" if result == "profit" else "🔴" if result == "loss" else "⚪"
    result_text = "Прибыль" if result == "profit" else "Убыток" if result == "loss" else "Безубыток"
    pnl_display = f"+{pnl:.2f}$" if result == "profit" else f"-{abs(pnl):.2f}$" if result == "loss" else "0.00$"
    
    response = (
        f"✅ Сделка #{trade.id} закрыта!\n\n"
        f"🪙 {trade.symbol}\n"
        f"📈 {trade.direction}\n"
        f"💰 {trade.position_size}$\n"
        f"Результат: {emoji} {result_text}\n"
        f"PnL: {pnl_display}\n"
        f"Новый депозит: {current_deposit:.2f}$"
    )
    if mistake:
        response += f"\n💡 Причина: {mistake}"
    
    await message.answer(response, reply_markup=main_menu())
    await state.clear()