# handlers/admin.py
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, FSInputFile, BufferedInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import ADMIN_IDS, BOT_TOKEN
from database.db import Database
from keyboards.menu import main_menu, admin_menu
import os
import tempfile

router = Router()
bot = Bot(token=BOT_TOKEN)

# ============= СОСТОЯНИЯ ДЛЯ РАССЫЛКИ =============
class BroadcastStates(StatesGroup):
    waiting_text = State()
    waiting_photo = State()
    waiting_confirm = State()

# ============= ПРОВЕРКА АДМИНА =============
def is_admin(user_id):
    """Проверка, является ли пользователь администратором"""
    return user_id in ADMIN_IDS

# ============= ГЛАВНОЕ МЕНЮ АДМИНА =============
@router.message(Command("admin"))
async def admin_panel(message: Message):
    """Админ панель"""
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        await message.answer("⛔ Только для администраторов!")
        return
    
    await message.answer(
        "👑 **Админ панель**\n\n"
        "Выберите действие:",
        reply_markup=admin_menu(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "admin_panel")
async def admin_panel_callback(callback: CallbackQuery):
    """Админ панель (по кнопке)"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        await callback.answer("⛔ Только для администраторов!", show_alert=True)
        return
    
    await callback.message.delete()
    await callback.message.answer(
        "👑 **Админ панель**\n\n"
        "Выберите действие:",
        reply_markup=admin_menu(),
        parse_mode="HTML"
    )
    await callback.answer()

# ============= СПИСОК ПОЛЬЗОВАТЕЛЕЙ =============
@router.callback_query(F.data == "admin_users")
async def admin_users(callback: CallbackQuery):
    """Список всех пользователей"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        await callback.answer("⛔ Только для администраторов!", show_alert=True)
        return
    
    await callback.message.delete()
    
    users = Database.get_all_users()
    total_users = len(users)
    
    if total_users == 0:
        await callback.message.answer("👥 Нет пользователей", reply_markup=admin_menu())
        await callback.answer()
        return
    
    text = f"👥 **Всего пользователей: {total_users}**\n\n"
    
    for i, user in enumerate(users[:20], 1):
        trades = Database.get_all_trades(user.user_id)
        stats = Database.get_stats(user.user_id)
        text += (
            f"{i}. 🆔 {user.user_id}\n"
            f"   📊 Сделок: {len(trades)}\n"
            f"   📈 Win Rate: {stats['win_rate']:.1f}%\n"
            f"   💰 PnL: {'+' if stats['total_pnl'] > 0 else ''}{stats['total_pnl']:.2f}$\n\n"
        )
    
    if total_users > 20:
        text += f"... и еще {total_users - 20} пользователей"
    
    await callback.message.answer(text, reply_markup=admin_menu(), parse_mode="HTML")
    await callback.answer()

# ============= СТАТИСТИКА АДМИНА =============
@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    """Общая статистика для админа"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        await callback.answer("⛔ Только для администраторов!", show_alert=True)
        return
    
    await callback.message.delete()
    
    users = Database.get_all_users()
    total_trades = 0
    total_pnl = 0
    total_wins = 0
    total_losses = 0
    
    for user in users:
        stats = Database.get_stats(user.user_id)
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

# ============= НАЧАЛО РАССЫЛКИ =============
@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_start(callback: CallbackQuery, state: FSMContext):
    """Начало создания рассылки"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        await callback.answer("⛔ Только для администраторов!", show_alert=True)
        return
    
    await callback.message.delete()
    await callback.message.answer(
        "📢 **Создание рассылки**\n\n"
        "Введите текст для рассылки:\n"
        "(Можно использовать HTML-разметку)\n\n"
        "Пример:\n"
        "<b>Привет!</b> Это тестовое сообщение.\n"
        "<i>Текст курсивом</i>\n"
        "<a href='https://example.com'>Ссылка</a>\n\n"
        "Или отправьте /cancel для отмены",
        parse_mode="HTML"
    )
    await state.set_state(BroadcastStates.waiting_text)
    await callback.answer()

@router.message(BroadcastStates.waiting_text)
async def admin_broadcast_text(message: Message, state: FSMContext):
    """Получение текста для рассылки"""
    if message.text and message.text.lower() == "/cancel":
        await message.answer("❌ Рассылка отменена", reply_markup=admin_menu())
        await state.clear()
        return
    
    # Сохраняем текст
    await state.update_data(text=message.text or " ")
    
    await message.answer(
        "📸 Теперь отправьте фото для рассылки\n\n"
        "Или нажмите 'Пропустить' если фото не нужно",
        reply_markup=broadcast_photo_skip_menu()
    )
    await state.set_state(BroadcastStates.waiting_photo)

@router.callback_query(F.data == "broadcast_skip_photo")
async def admin_broadcast_skip_photo(callback: CallbackQuery, state: FSMContext):
    """Пропуск фото"""
    await callback.message.delete()
    await show_broadcast_confirm(callback.message, state, callback.from_user.id)
    await callback.answer()

@router.message(BroadcastStates.waiting_photo)
async def admin_broadcast_photo(message: Message, state: FSMContext):
    """Получение фото для рассылки"""
    if message.photo:
        # Сохраняем фото
        photo = message.photo[-1]
        file = await bot.get_file(photo.file_id)
        
        # Скачиваем во временную папку
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, f"broadcast_{message.from_user.id}.jpg")
        await bot.download_file(file.file_path, file_path)
        
        await state.update_data(photo_path=file_path)
        await state.update_data(photo_id=photo.file_id)
        
        await show_broadcast_confirm(message, state, message.from_user.id)
    else:
        await message.answer("❌ Пожалуйста, отправьте фото или нажмите 'Пропустить'")

async def show_broadcast_confirm(message: Message, state: FSMContext, user_id: int):
    """Показать подтверждение рассылки"""
    data = await state.get_data()
    text = data.get('text', '')
    photo_id = data.get('photo_id')
    photo_path = data.get('photo_path')
    
    # Показываем превью
    if photo_id:
        await message.answer_photo(
            photo_id,
            caption=f"📢 **Превью рассылки**\n\n{text}",
            parse_mode="HTML",
            reply_markup=broadcast_confirm_menu()
        )
    else:
        await message.answer(
            f"📢 **Превью рассылки**\n\n{text}",
            parse_mode="HTML",
            reply_markup=broadcast_confirm_menu()
        )
    
    await state.set_state(BroadcastStates.waiting_confirm)

@router.callback_query(F.data == "broadcast_confirm")
async def admin_broadcast_confirm(callback: CallbackQuery, state: FSMContext):
    """Подтверждение и отправка рассылки"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        await callback.answer("⛔ Только для администраторов!", show_alert=True)
        return
    
    await callback.message.delete()
    await callback.message.answer("⏳ Начинаю рассылку...")
    
    data = await state.get_data()
    text = data.get('text', '')
    photo_path = data.get('photo_path')
    
    # Получаем всех пользователей
    users = Database.get_all_users()
    total = len(users)
    sent = 0
    failed = 0
    
    for user in users:
        try:
            if photo_path:
                await bot.send_photo(
                    user.user_id,
                    photo_path,
                    caption=text,
                    parse_mode="HTML"
                )
            else:
                await bot.send_message(
                    user.user_id,
                    text,
                    parse_mode="HTML"
                )
            sent += 1
        except Exception as e:
            failed += 1
    
    # Чистим временный файл
    if photo_path and os.path.exists(photo_path):
        os.remove(photo_path)
    
    await callback.message.answer(
        f"✅ **Рассылка завершена!**\n\n"
        f"📤 Отправлено: {sent}\n"
        f"❌ Не доставлено: {failed}\n"
        f"👥 Всего: {total}",
        reply_markup=admin_menu(),
        parse_mode="HTML"
    )
    
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "broadcast_cancel")
async def admin_broadcast_cancel(callback: CallbackQuery, state: FSMContext):
    """Отмена рассылки"""
    user_id = callback.from_user.id
    
    if not is_admin(user_id):
        await callback.answer("⛔ Только для администраторов!", show_alert=True)
        return
    
    data = await state.get_data()
    photo_path = data.get('photo_path')
    
    if photo_path and os.path.exists(photo_path):
        os.remove(photo_path)
    
    await callback.message.delete()
    await callback.message.answer("❌ Рассылка отменена", reply_markup=admin_menu())
    await state.clear()
    await callback.answer()

# ============= ВСПОМОГАТЕЛЬНЫЕ КЛАВИАТУРЫ =============
def broadcast_photo_skip_menu():
    """Клавиатура для пропуска фото"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭️ Пропустить фото", callback_data="broadcast_skip_photo")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="broadcast_cancel")]
    ])

def broadcast_confirm_menu():
    """Клавиатура подтверждения рассылки"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Отправить", callback_data="broadcast_confirm")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="broadcast_cancel")]
    ])