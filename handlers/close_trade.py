# handlers/close_trade.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from handlers.add_trade import CloseTradeStates
from keyboards.menu import main_menu, result_keyboard, mistake_keyboard, open_trades_menu
from database.db import Database

router = Router()

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
            f"📊 Закрытие сделки #{trade.id}\n\n🪙 {trade.symbol}\n📈 {trade.direction}\n💰 {trade.position_size}$\n\nВыберите результат:",
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
        f"📊 Закрытие сделки #{trade.id}\n\n🪙 {trade.symbol}\n📈 {trade.direction}\n💰 {trade.position_size}$\n\nВыберите результат:",
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
        await callback.message.answer("🟢 Прибыль\n\nВведите сумму прибыли в $\n\nНапример: 58")
        await state.set_state(CloseTradeStates.waiting_pnl)
    elif result == "loss":
        await callback.message.answer("🔴 Убыток\n\nВведите сумму убытка в $\n\nНапример: 22")
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
    
    # 👇 ОЧИЩАЕМ ТЕКСТ ОТ ЛИШНИХ СИМВОЛОВ
    text = message.text.strip().replace(',', '.')
    
    try:
        amount = float(text)
        print(f"📊 process_pnl: result={result}, amount={amount}")
        
        # 👇 ПРИНУДИТЕЛЬНО ДЕЛАЕМ PNL ОТРИЦАТЕЛЬНЫМ ДЛЯ УБЫТКА
        if result == "loss":
            pnl = -abs(amount)
        else:
            pnl = amount
        
        await state.update_data(pnl=pnl)
        print(f"📊 process_pnl: pnl={pnl}")
        
        # 👇 ВСЕГДА ПОКАЗЫВАЕМ ПРИЧИНЫ ДЛЯ УБЫТКА
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
    
    user_id = message.from_user.id
    print(f"👤 user_id: {user_id}")
    
    Database.get_or_create_user(user_id)
    Database.close_trade(trade_id, result, pnl, mistake)
    
    current_deposit = Database.get_current_deposit(user_id)
    new_deposit = current_deposit + pnl
    Database.update_deposit(user_id, new_deposit)
    
    print(f"💰 ДО: {current_deposit} + {pnl} = {new_deposit}")
    
    emoji = "🟢" if result == "profit" else "🔴" if result == "loss" else "⚪"
    result_text = "Прибыль" if result == "profit" else "Убыток" if result == "loss" else "Безубыток"
    pnl_display = f"+{pnl:.2f}$" if result == "profit" else f"-{abs(pnl):.2f}$" if result == "loss" else "0.00$"
    
    response = (f"✅ Сделка #{trade.id} закрыта!\n\n🪙 {trade.symbol}\n📈 {trade.direction}\n💰 {trade.position_size}$\n"
                f"Результат: {emoji} {result_text}\nPnL: {pnl_display}\nНовый депозит: {new_deposit:.2f}$")
    if mistake:
        response += f"\n💡 Причина: {mistake}"
    
    await message.answer(response, reply_markup=main_menu())
    await state.clear()