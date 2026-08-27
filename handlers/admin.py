# handlers/admin.py
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import ADMIN_IDS
from database.db import Database
from keyboards.menu import main_menu, admin_menu
from services.broadcast import BroadcastService
import os
import tempfile

router = Router()
broadcast_service = None

def set_broadcast_service(service):
    global broadcast_service
    broadcast_service = service

def is_admin(user_id):
    return user_id in ADMIN_IDS

class BroadcastStates(StatesGroup):
    waiting_text = State()
    waiting_photo = State()
    waiting_confirm = State()

# ============= ТЕСТОВАЯ РАССЫЛКА =============
@router.message(Command("test_broadcast"))
async def test_broadcast(message: Message):
    """Тестовая рассылка только админу"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Только для администраторов!")
        return
    
    try:
        await message.bot.send_message(
            message.from_user.id,
            "✅ **Тестовая рассылка работает!**\n\n"
            "Если вы видите это сообщение — бот может отправлять сообщения.",
            parse_mode="HTML"
        )
        await message.answer("✅ Тестовое сообщение отправлено вам!")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

# ============= АДМИН ПАНЕЛЬ =============
@router.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Только для администраторов!")
        return
    await message.answer("👑 **Админ панель**", reply_markup=admin_menu(), parse_mode="HTML")

@router.callback_query(F.data == "admin_panel")
async def admin_panel_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Только для администраторов!", show_alert=True)
        return
    await callback.message.delete()
    await callback.message.answer("👑 **Админ панель**", reply_markup=admin_menu(), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "admin_users")
async def admin_users(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Только для администраторов!", show_alert=True)
        return
    await callback.message.delete()
    users = Database.get_all_users()
    active = sum(1 for u in users if u.is_active == 1)
    blocked = sum(1 for u in users if u.is_active == 0)
    text = f"👥 **Пользователи**\nВсего: {len(users)}\n🟢 Активных: {active}\n🚫 Заблокировали: {blocked}\n\n"
    for u in users[:10]:
        text += f"🆔 {u.user_id} | {'🟢' if u.is_active else '🚫'}\n"
    if len(users) > 10:
        text += f"... и еще {len(users)-10}"
    await callback.message.answer(text, reply_markup=admin_menu(), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Только для администраторов!", show_alert=True)
        return
    await callback.message.delete()
    users = Database.get_all_users()
    total_trades = 0
    total_pnl = 0
    total_wins = 0
    total_losses = 0
    for u in users:
        stats = Database.get_stats(u.user_id)
        total_trades += stats['total']
        total_pnl += stats['total_pnl']
        total_wins += stats['wins']
        total_losses += stats['losses']
    win_rate = (total_wins / (total_wins + total_losses) * 100) if (total_wins + total_losses) > 0 else 0
    text = (
        f"📊 **Общая статистика**\n\n"
        f"👥 Пользователей: {len(users)}\n"
        f"📊 Всего сделок: {total_trades}\n"
        f"🟢 Побед: {total_wins}\n"
        f"🔴 Поражений: {total_losses}\n"
        f"📈 Win Rate: {win_rate:.1f}%\n"
        f"💰 Общий PnL: {'+' if total_pnl > 0 else ''}{total_pnl:.2f}$"
    )
    await callback.message.answer(text, reply_markup=admin_menu(), parse_mode="HTML")
    await callback.answer()

# ============= РАССЫЛКА =============
@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Только для администраторов!", show_alert=True)
        return
    await callback.message.delete()
    await callback.message.answer(
        "📢 **Создание рассылки**\n\nВведите текст (можно HTML):",
        parse_mode="HTML"
    )
    await state.set_state(BroadcastStates.waiting_text)
    await callback.answer()

@router.message(BroadcastStates.waiting_text)
async def admin_broadcast_text(message: Message, state: FSMContext):
    if message.text and message.text.lower() == "/cancel":
        await message.answer("❌ Отменено", reply_markup=admin_menu())
        await state.clear()
        return
    await state.update_data(text=message.text or " ")
    await message.answer(
        "📸 Отправьте фото или нажмите 'Пропустить'",
        reply_markup=broadcast_photo_skip_menu()
    )
    await state.set_state(BroadcastStates.waiting_photo)

@router.callback_query(F.data == "broadcast_skip_photo")
async def admin_broadcast_skip_photo(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await show_broadcast_confirm(callback.message, state, callback.from_user.id)
    await callback.answer()

@router.message(BroadcastStates.waiting_photo)
async def admin_broadcast_photo(message: Message, state: FSMContext):
    if message.photo:
        photo = message.photo[-1]
        file = await message.bot.get_file(photo.file_id)
        tmp = tempfile.gettempdir()
        path = os.path.join(tmp, f"broadcast_{message.from_user.id}.jpg")
        await message.bot.download_file(file.file_path, path)
        await state.update_data(photo_path=path, photo_id=photo.file_id)
        await show_broadcast_confirm(message, state, message.from_user.id)
    else:
        await message.answer("❌ Отправьте фото или нажмите 'Пропустить'")

async def show_broadcast_confirm(message: Message, state: FSMContext, user_id: int):
    data = await state.get_data()
    text = data.get('text', '')
    photo_id = data.get('photo_id')
    if photo_id:
        await message.answer_photo(photo_id, caption=f"📢 **Превью**\n\n{text}", parse_mode="HTML", reply_markup=broadcast_confirm_menu())
    else:
        await message.answer(f"📢 **Превью**\n\n{text}", parse_mode="HTML", reply_markup=broadcast_confirm_menu())
    await state.set_state(BroadcastStates.waiting_confirm)

@router.callback_query(F.data == "broadcast_confirm")
async def admin_broadcast_confirm(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Только для администраторов!", show_alert=True)
        return

    if broadcast_service._running:
        await callback.message.answer("⏳ Рассылка уже выполняется, подождите.")
        await callback.answer()
        return

    await callback.message.delete()
    data = await state.get_data()
    text = data.get('text', '')
    photo_path = data.get('photo_path')

    users = Database.get_all_users()
    active_users = [u for u in users if u.is_active == 1]
    if not active_users:
        await callback.message.answer("❌ Нет активных пользователей для рассылки.", reply_markup=admin_menu())
        await state.clear()
        await callback.answer()
        return

    status_msg = await callback.message.answer(f"⏳ Рассылка началась для {len(active_users)} пользователей...")

    report = await broadcast_service.broadcast(text, photo_path, only_active=True)

    result_text = (
        f"✅ **Рассылка завершена**\n\n"
        f"👥 Всего: {report['total']}\n"
        f"✅ Успешно: {report['ok']}\n"
        f"🚫 Заблокировали: {report['blocked']}\n"
        f"❌ Чат не найден: {report['chat_not_found']}\n"
        f"⚠️ Ошибок: {report['unknown_error']}\n"
    )
    await status_msg.edit_text(result_text, reply_markup=admin_menu(), parse_mode="HTML")

    errors = [d for d in report['details'] if d['status'] not in ('ok', 'blocked')]
    if errors:
        err_text = "❌ **Ошибки рассылки**\n\n"
        for e in errors[:20]:
            err_text += f"🆔 {e['user_id']} — {e['status']}\n"
        await callback.message.answer(err_text, parse_mode="HTML")

    if photo_path and os.path.exists(photo_path):
        os.remove(photo_path)

    await state.clear()
    await callback.answer()

def broadcast_photo_skip_menu():
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭️ Пропустить", callback_data="broadcast_skip_photo")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="broadcast_cancel")]
    ])

def broadcast_confirm_menu():
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Отправить", callback_data="broadcast_confirm")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="broadcast_cancel")]
    ])

@router.callback_query(F.data == "broadcast_cancel")
async def admin_broadcast_cancel(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if data.get('photo_path') and os.path.exists(data['photo_path']):
        os.remove(data['photo_path'])
    await callback.message.delete()
    await callback.message.answer("❌ Отменено", reply_markup=admin_menu())
    await state.clear()
    await callback.answer()