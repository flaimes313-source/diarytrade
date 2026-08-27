# handlers/deposit.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards.menu import main_menu, deposit_menu, confirm_change_deposit_menu
from services.deposit import DepositService
from database.db import Database

router = Router()

class ChangeDepositStates(StatesGroup):
    waiting_new_deposit = State()
    waiting_confirm = State()

@router.callback_query(F.data == "deposit_history")
async def deposit_history(callback: CallbackQuery):
    """Показать историю депозита"""
    user_id = callback.from_user.id
    history = Database.get_deposit_history(user_id)
    
    if len(history) < 2:
        await callback.message.answer(
            "📊 История депозита\n\nНедостаточно данных.",
            reply_markup=deposit_menu()
        )
        await callback.answer()
        return
    
    text = "📊 История депозита\n\n"
    for i, value in enumerate(history):
        if i == 0:
            text += f"💰 Начальный: {value:.2f}$\n"
        else:
            change = value - history[i-1]
            text += f"📌 {i}. {value:.2f}$ ({'+' if change > 0 else ''}{change:.2f}$)\n"
    
    await callback.message.delete()
    await callback.message.answer(text, reply_markup=deposit_menu())
    await callback.answer()

@router.callback_query(F.data == "change_deposit")
async def change_deposit_start(callback: CallbackQuery, state: FSMContext):
    """Начало изменения депозита"""
    user_id = callback.from_user.id
    
    current = DepositService.get_current(user_id)
    initial = DepositService.get_initial(user_id)
    total_pnl = DepositService.get_total_pnl(user_id)
    
    await callback.message.delete()
    await callback.message.answer(
        f"💰 **Изменение начального депозита**\n\n"
        f"📊 Текущий начальный депозит: {initial:.2f}$\n"
        f"📈 Общий PnL: {'+' if total_pnl > 0 else ''}{total_pnl:.2f}$\n"
        f"💵 Текущий депозит: {current:.2f}$\n\n"
        f"Введите новый начальный депозит:",
        parse_mode="HTML"
    )
    await state.set_state(ChangeDepositStates.waiting_new_deposit)
    await callback.answer()

@router.message(ChangeDepositStates.waiting_new_deposit)
async def change_deposit_input(message: Message, state: FSMContext):
    """Обработка ввода нового депозита"""
    try:
        new_amount = float(message.text.replace(',', '.'))
        if new_amount < 0:
            await message.answer("❌ Депозит не может быть отрицательным!")
            return
        
        user_id = message.from_user.id
        current = DepositService.get_current(user_id)
        initial = DepositService.get_initial(user_id)
        total_pnl = DepositService.get_total_pnl(user_id)
        
        await state.update_data(new_initial=new_amount)
        
        await message.answer(
            f"⚠️ **Подтверждение изменения**\n\n"
            f"📊 Старый начальный депозит: {initial:.2f}$\n"
            f"📊 Новый начальный депозит: {new_amount:.2f}$\n"
            f"📈 Исторический PnL: {'+' if total_pnl > 0 else ''}{total_pnl:.2f}$\n"
            f"💵 Новый текущий депозит: {new_amount + total_pnl:.2f}$\n\n"
            f"Подтвердить изменение?",
            reply_markup=confirm_change_deposit_menu(),
            parse_mode="HTML"
        )
        await state.set_state(ChangeDepositStates.waiting_confirm)
        
    except ValueError:
        await message.answer("❌ Введите число (например: 1000)")

@router.callback_query(F.data == "confirm_change_deposit")
async def confirm_change_deposit(callback: CallbackQuery, state: FSMContext):
    """Подтверждение изменения депозита"""
    data = await state.get_data()
    new_initial = data.get('new_initial')
    user_id = callback.from_user.id
    
    if new_initial is None:
        await callback.message.answer("❌ Ошибка: данные не найдены")
        await state.clear()
        await callback.answer()
        return
    
    # Применяем изменение
    new_current = DepositService.change_initial(user_id, new_initial)
    
    await callback.message.delete()
    await callback.message.answer(
        f"✅ **Депозит изменен!**\n\n"
        f"📊 Новый начальный депозит: {new_initial:.2f}$\n"
        f"💵 Новый текущий депозит: {new_current:.2f}$\n\n"
        f"Исторический PnL сохранен: {'+' if DepositService.get_total_pnl(user_id) > 0 else ''}{DepositService.get_total_pnl(user_id):.2f}$",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "cancel_change_deposit")
async def cancel_change_deposit(callback: CallbackQuery, state: FSMContext):
    """Отмена изменения депозита"""
    await callback.message.delete()
    await callback.message.answer("❌ Изменение отменено", reply_markup=main_menu())
    await state.clear()
    await callback.answer()