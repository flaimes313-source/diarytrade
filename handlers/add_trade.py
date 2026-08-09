# handlers/add_trade.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from keyboards.menu import (
    main_menu, 
    add_trade_menu, 
    direction_keyboard, 
    result_keyboard, 
    mistake_keyboard, 
    deposit_menu, 
    confirm_reset_deposit_menu,
    open_trades_menu
)
from database.db import Database
from config import SCREENSHOTS_DIR
import os
import tempfile
from datetime import datetime

router = Router()

class AddTradeStates(StatesGroup):
    waiting_symbol = State()
    waiting_direction = State()
    waiting_position_size = State()
    waiting_setup = State()
    waiting_confidence = State()
    waiting_screenshot = State()
    waiting_deposit = State()

class CloseTradeStates(StatesGroup):
    waiting_result = State()
    waiting_pnl = State()
    waiting_mistake = State()
    waiting_trade_select = State()

class DepositStates(StatesGroup):
    waiting_deposit_amount = State()
    waiting_new_deposit = State()

# ============= ПРОВЕРКА И СОЗДАНИЕ ПАПКИ ДЛЯ СКРИНШОТОВ =============
def ensure_screenshots_dir():
    """Проверяет существование папки для скриншотов и создает её при необходимости"""
    global SCREENSHOTS_DIR
    
    print(f"\n📁 ПРОВЕРКА ПАПКИ ДЛЯ СКРИНШОТОВ:")
    print(f"   Путь: {SCREENSHOTS_DIR}")
    
    try:
        # Проверяем существование
        if not os.path.exists(SCREENSHOTS_DIR):
            print(f"   ⚠️ Папка не найдена, создаю...")
            os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
            print(f"   ✅ Папка создана")
        else:
            print(f"   ✅ Папка существует")
        
        # Проверяем права на запись
        test_file = os.path.join(SCREENSHOTS_DIR, 'test_write.txt')
        try:
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            print(f"   ✅ Есть права на запись")
            return True
        except Exception as e:
            print(f"   ❌ НЕТ ПРАВ НА ЗАПИСЬ: {e}")
            print(f"   🔄 Использую временную папку...")
            temp_dir = tempfile.gettempdir()
            SCREENSHOTS_DIR = os.path.join(temp_dir, 'trading_screenshots')
            if not os.path.exists(SCREENSHOTS_DIR):
                os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
            print(f"   ✅ Использую: {SCREENSHOTS_DIR}")
            
            # Проверяем права на запись во временной папке
            test_file = os.path.join(SCREENSHOTS_DIR, 'test_write.txt')
            try:
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                print(f"   ✅ Есть права на запись во временной папке")
                return True
            except:
                print(f"   ❌ НЕТ ПРАВ НА ЗАПИСЬ ВО ВРЕМЕННОЙ ПАПКЕ!")
                return False
                
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        print(f"   🔄 Использую текущую папку...")
        SCREENSHOTS_DIR = os.path.dirname(os.path.abspath(__file__))
        print(f"   ✅ Использую: {SCREENSHOTS_DIR}")
        return True

# Вызываем при старте
ensure_screenshots_dir()

# ============= КОМАНДА /start =============
@router.message(Command("start"))
async def start(message: Message):
    user_id = message.from_user.id
    Database.get_or_create_user(user_id)
    
    # Проверяем есть ли открытые сделки
    open_trades = Database.get_open_trades(user_id)
    
    if open_trades:
        text = f"📖 У вас открыто {len(open_trades)} сделок:\n\n"
        for trade in open_trades[:5]:
            text += (
                f"#{trade.id} 🪙 {trade.symbol} 📈 {trade.direction}\n"
                f"   💰 {trade.position_size}$ | 📅 {trade.date.strftime('%d.%m.%Y')}\n"
            )
        if len(open_trades) > 5:
            text += f"\n... и еще {len(open_trades) - 5} открытых сделок"
        
        text += f"\n\nИспользуйте меню для управления:"
        await message.answer(text, reply_markup=main_menu(has_open_trade=True))
    else:
        await message.answer(
            "📖 Дневник трейдера\n\n"
            "Выберите действие:",
            reply_markup=main_menu()
        )

# ============= КОМАНДА /id =============
@router.message(Command("id"))
async def get_id(message: Message):
    await message.answer(f"🆔 Ваш Telegram ID: `{message.from_user.id}`")

# ============= КОМАНДА /deposit - УСТАНОВКА НАЧАЛЬНОГО ДЕПОЗИТА =============
@router.message(Command("deposit"))
async def set_deposit(message: Message):
    """Установить начальный депозит"""
    user_id = message.from_user.id
    
    # Парсим сумму из команды
    parts = message.text.split()
    if len(parts) < 2:
        current_deposit = Database.get_current_deposit(user_id)
        user = Database.get_or_create_user(user_id)
        await message.answer(
            f"💰 Управление депозитом\n\n"
            f"Начальный депозит: {user.initial_deposit}$\n"
            f"Текущий депозит: {current_deposit}$\n\n"
            f"Чтобы установить начальный депозит:\n"
            f"/deposit СУММА\n\n"
            f"Пример: /deposit 1000",
            reply_markup=deposit_menu()
        )
        return
    
    try:
        deposit = float(parts[1].replace(',', '.'))
        if deposit <= 0:
            await message.answer("❌ Сумма должна быть больше 0")
            return
    except ValueError:
        await message.answer("❌ Введите число (например: 1000)")
        return
    
    # Сохраняем начальный депозит
    Database.set_initial_deposit(user_id, deposit)
    
    await message.answer(
        f"✅ Начальный депозит установлен!\n\n"
        f"💰 Сумма: {deposit}$\n"
        f"📊 Текущий депозит: {Database.get_current_deposit(user_id)}$\n\n"
        f"Теперь все сделки будут автоматически обновлять депозит.",
        reply_markup=main_menu()
    )

# ============= КОМАНДА /reset_deposit - ОБНУЛИТЬ И УСТАНОВИТЬ НОВЫЙ ДЕПОЗИТ =============
@router.message(Command("reset_deposit"))
async def reset_deposit(message: Message):
    """Обнулить депозит и установить новый"""
    user_id = message.from_user.id
    current_deposit = Database.get_current_deposit(user_id)
    
    # Проверяем есть ли открытые сделки
    open_trades = Database.get_open_trades(user_id)
    if open_trades:
        await message.answer(
            f"⚠️ У вас есть открытые сделки!\n\n"
            f"Сначала закройте все открытые сделки, затем сбросьте депозит.\n"
            f"Открытых сделок: {len(open_trades)}",
            reply_markup=main_menu(has_open_trade=True)
        )
        return
    
    await message.answer(
        f"💰 Сброс депозита\n\n"
        f"Текущий депозит: {current_deposit}$\n"
        f"Все сделки будут сохранены в истории.\n\n"
        f"⚠️ Внимание! Это действие сбросит текущий депозит.\n"
        f"Вы уверены, что хотите продолжить?",
        reply_markup=confirm_reset_deposit_menu()
    )

@router.callback_query(F.data == "confirm_reset_deposit")
async def confirm_reset_deposit(callback: CallbackQuery, state: FSMContext):
    """Подтверждение сброса депозита"""
    try:
        await callback.message.delete()
    except:
        pass
    await callback.message.answer(
        "💰 Введите новый начальный депозит:\n\n"
        "Пример: 1000\n\n"
        "Или отправьте 0 чтобы обнулить депозит"
    )
    await state.set_state(DepositStates.waiting_new_deposit)
    await callback.answer()

@router.callback_query(F.data == "cancel_reset_deposit")
async def cancel_reset_deposit(callback: CallbackQuery):
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

@router.message(DepositStates.waiting_new_deposit)
async def process_new_deposit(message: Message, state: FSMContext):
    """Обработка нового депозита"""
    user_id = message.from_user.id
    
    try:
        new_deposit = float(message.text.replace(',', '.'))
        if new_deposit < 0:
            await message.answer("❌ Сумма не может быть отрицательной\n\nПопробуйте снова:")
            return
    except ValueError:
        await message.answer("❌ Введите число (например: 1000)\n\nПопробуйте снова:")
        return
    
    old_deposit = Database.get_current_deposit(user_id)
    
    # Сохраняем новый депозит
    Database.set_initial_deposit(user_id, new_deposit)
    Database.update_deposit(user_id, new_deposit)
    
    await message.answer(
        f"✅ Депозит успешно обновлен!\n\n"
        f"💰 Старый депозит: {old_deposit}$\n"
        f"💰 Новый депозит: {new_deposit}$\n"
        f"📊 Изменение: {new_deposit - old_deposit:.2f}$\n\n"
        f"Все сделки сохранены в истории.",
        reply_markup=main_menu()
    )
    await state.clear()

# ============= ОБРАБОТЧИКИ ДЛЯ ДЕПОЗИТА =============
@router.callback_query(F.data == "deposit_menu")
async def deposit_menu_callback(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except:
        pass
    current_deposit = Database.get_current_deposit(callback.from_user.id)
    user = Database.get_or_create_user(callback.from_user.id)
    await callback.message.answer(
        f"💰 Управление депозитом\n\n"
        f"Начальный депозит: {user.initial_deposit}$\n"
        f"Текущий депозит: {current_deposit}$\n"
        f"Изменение: {'+' if current_deposit - user.initial_deposit > 0 else ''}{current_deposit - user.initial_deposit}$\n\n"
        f"Выберите действие:",
        reply_markup=deposit_menu()
    )
    await callback.answer()

@router.callback_query(F.data == "show_deposit")
async def show_deposit(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except:
        pass
    user_id = callback.from_user.id
    user = Database.get_or_create_user(user_id)
    current = Database.get_current_deposit(user_id)
    
    await callback.message.answer(
        f"💰 Информация о депозите\n\n"
        f"Начальный депозит: {user.initial_deposit}$\n"
        f"Текущий депозит: {current}$\n"
        f"Изменение: {'+' if current - user.initial_deposit > 0 else ''}{current - user.initial_deposit}$\n\n"
        f"Чтобы изменить начальный депозит, используйте команду:\n"
        f"/deposit СУММА\n\n"
        f"Пример: /deposit 1000\n\n"
        f"Чтобы обнулить и установить новый депозит:\n"
        f"/reset_deposit",
        reply_markup=main_menu()
    )
    await callback.answer()

@router.callback_query(F.data == "set_deposit")
async def set_deposit_callback(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
    except:
        pass
    await callback.message.answer(
        "💰 Введите сумму начального депозита:\n\n"
        "Пример: 1000"
    )
    await state.set_state(DepositStates.waiting_deposit_amount)
    await callback.answer()

@router.message(DepositStates.waiting_deposit_amount)
async def process_deposit_amount(message: Message, state: FSMContext):
    try:
        deposit = float(message.text.replace(',', '.'))
        if deposit <= 0:
            await message.answer("❌ Сумма должна быть больше 0\n\nПопробуйте снова:")
            return
    except ValueError:
        await message.answer("❌ Введите число (например: 1000)\n\nПопробуйте снова:")
        return
    
    user_id = message.from_user.id
    Database.set_initial_deposit(user_id, deposit)
    
    await message.answer(
        f"✅ Начальный депозит установлен!\n\n"
        f"💰 Сумма: {deposit}$\n"
        f"📊 Текущий депозит: {Database.get_current_deposit(user_id)}$",
        reply_markup=main_menu()
    )
    await state.clear()

# ============= ДОБАВЛЕНИЕ НОВОЙ СДЕЛКИ =============
@router.callback_query(F.data == "new_trade")
async def new_trade(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
    except:
        pass
    
    await callback.message.answer(
        "➕ Новая сделка\n\n"
        "Введите монету (например: BTCUSDT):"
    )
    await state.set_state(AddTradeStates.waiting_symbol)
    await callback.answer()

@router.message(AddTradeStates.waiting_symbol)
async def process_symbol(message: Message, state: FSMContext):
    await state.update_data(symbol=message.text.upper())
    await message.answer(
        "📈 Выберите направление:",
        reply_markup=direction_keyboard()
    )
    await state.set_state(AddTradeStates.waiting_direction)

@router.callback_query(AddTradeStates.waiting_direction)
async def process_direction(callback: CallbackQuery, state: FSMContext):
    await state.update_data(direction=callback.data)
    try:
        await callback.message.delete()
    except:
        pass
    await callback.message.answer(
        "💰 Введите размер позиции в $ (например: 500):"
    )
    await state.set_state(AddTradeStates.waiting_position_size)
    await callback.answer()

@router.message(AddTradeStates.waiting_position_size)
async def process_position_size(message: Message, state: FSMContext):
    try:
        position_size = float(message.text.replace(',', '.'))
        if position_size <= 0:
            await message.answer("❌ Размер позиции должен быть больше 0\n\nПопробуйте снова:")
            return
        await state.update_data(position_size=position_size)
        
        await message.answer(
            "📝 Введите сетап:\n\n"
            "Например:\n"
            "Ложный пробой уровня\n"
            "Рост OI\n"
            "Funding положительный\n"
            "Дельта отрицательная\n\n"
            "Или отправьте '-' чтобы пропустить:"
        )
        await state.set_state(AddTradeStates.waiting_setup)
    except ValueError:
        await message.answer("❌ Пожалуйста, введите число\n\nПопробуйте снова:")

@router.message(AddTradeStates.waiting_setup)
async def process_setup(message: Message, state: FSMContext):
    setup = None if message.text == '-' else message.text
    await state.update_data(setup=setup)
    
    await message.answer(
        "⭐ Оцените уверенность (1-10):"
    )
    await state.set_state(AddTradeStates.waiting_confidence)

@router.message(AddTradeStates.waiting_confidence)
async def process_confidence(message: Message, state: FSMContext):
    try:
        confidence = int(message.text)
        if 1 <= confidence <= 10:
            await state.update_data(confidence=confidence)
            
            await message.answer(
                "📷 Отправьте скриншот TradingView\n\n"
                "Или нажмите 'Пропустить'",
                reply_markup=add_trade_menu()
            )
            await state.set_state(AddTradeStates.waiting_screenshot)
        else:
            await message.answer("❌ Введите число от 1 до 10\n\nПопробуйте снова:")
    except ValueError:
        await message.answer("❌ Введите число от 1 до 10\n\nПопробуйте снова:")

@router.callback_query(F.data == "skip_screenshot")
async def skip_screenshot(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.message.delete()
    except:
        pass
    await save_trade(callback.message, state, callback.from_user.id)
    await callback.answer()

# ============= ОБРАБОТКА СКРИНШОТА С ПРОВЕРКОЙ ПАПКИ =============
@router.message(AddTradeStates.waiting_screenshot)
async def process_screenshot(message: Message, state: FSMContext):
    global SCREENSHOTS_DIR
    
    if message.photo:
        try:
            print(f"\n📸 ПОЛУЧЕН СКРИНШОТ")
            print(f"   Путь к папке: {SCREENSHOTS_DIR}")
            print(f"   Папка существует: {os.path.exists(SCREENSHOTS_DIR)}")
            
            # Проверяем и создаем папку если нужно
            if not os.path.exists(SCREENSHOTS_DIR):
                print(f"   ⚠️ Папка не найдена, создаю...")
                os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
                print(f"   ✅ Папка создана")
            
            # Проверяем права на запись
            if os.access(SCREENSHOTS_DIR, os.W_OK):
                print(f"   ✅ Есть права на запись")
            else:
                print(f"   ❌ НЕТ ПРАВ НА ЗАПИСЬ!")
                temp_dir = tempfile.gettempdir()
                SCREENSHOTS_DIR = os.path.join(temp_dir, 'trading_screenshots')
                if not os.path.exists(SCREENSHOTS_DIR):
                    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
                print(f"   🔄 Использую временную папку: {SCREENSHOTS_DIR}")
            
            # Сохраняем скриншот
            photo = message.photo[-1]
            file = await message.bot.get_file(photo.file_id)
            print(f"   ID файла: {file.file_id}")
            
            # Создаем имя файла
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_name = f"{message.from_user.id}_{timestamp}.jpg"
            file_path = os.path.join(SCREENSHOTS_DIR, file_name)
            print(f"   Сохраняю в: {file_path}")
            
            # Скачиваем файл
            await message.bot.download_file(file.file_path, file_path)
            
            # Проверяем, что файл создан
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                print(f"   ✅ Файл сохранен, размер: {file_size} байт")
                if file_size > 0:
                    await state.update_data(screenshot=file_path)
                    await save_trade(message, state, message.from_user.id)
                else:
                    print(f"   ❌ Файл пустой!")
                    await message.answer(
                        "❌ Ошибка: файл пустой. Попробуйте еще раз.",
                        reply_markup=add_trade_menu()
                    )
            else:
                print(f"   ❌ Файл не создан!")
                await message.answer(
                    "❌ Ошибка при сохранении скриншота. Попробуйте еще раз.",
                    reply_markup=add_trade_menu()
                )
                
        except Exception as e:
            print(f"❌ ОШИБКА: {e}")
            import traceback
            traceback.print_exc()
            await message.answer(
                f"❌ Ошибка при сохранении скриншота\n\n"
                f"Попробуйте еще раз или нажмите 'Пропустить'",
                reply_markup=add_trade_menu()
            )
    else:
        await message.answer(
            "❌ Пожалуйста, отправьте фото или нажмите 'Пропустить'.",
            reply_markup=add_trade_menu()
        )

# ============= СОХРАНЕНИЕ СДЕЛКИ =============
async def save_trade(message: Message, state: FSMContext, user_id: int):
    data = await state.get_data()
    
    try:
        # Получаем текущий депозит
        deposit = Database.get_current_deposit(user_id)
        
        trade_id = Database.add_trade(
            user_id=user_id,
            symbol=data['symbol'],
            direction=data['direction'],
            position_size=data['position_size'],
            setup=data.get('setup'),
            confidence=data.get('confidence'),
            screenshot=data.get('screenshot'),
            deposit=deposit
        )
        
        # Формируем сообщение
        response = (
            f"✅ Сделка #{trade_id} сохранена!\n\n"
            f"🪙 {data['symbol']}\n"
            f"📈 {data['direction']}\n"
            f"💰 {data['position_size']}$\n"
            f"📅 {datetime.now().strftime('%d.%m.%Y')}\n"
            f"Статус: 🟡 Открыта\n"
            f"⭐ Уверенность: {data.get('confidence', '—')}/10\n"
            f"💵 Депозит: {deposit}$\n\n"
        )
        
        if data.get('setup'):
            response += f"📝 Сетап: {data['setup']}\n"
        
        if data.get('screenshot'):
            response += f"📷 Скриншот сохранен\n"
        else:
            response += f"📷 Без скриншота\n"
        
        response += f"\n🆔 ID сделки: {trade_id}"
        
        await message.answer(
            response,
            reply_markup=main_menu(has_open_trade=True)
        )
        
    except Exception as e:
        print(f"❌ Ошибка при сохранении сделки: {e}")
        await message.answer(
            "❌ Ошибка при сохранении сделки\n\n"
            "Попробуйте еще раз",
            reply_markup=main_menu()
        )
    
    await state.clear()

# ============= ЗАКРЫТИЕ СДЕЛКИ =============
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

# ============= КОМАНДА /mydel - УДАЛЕНИЕ СВОЕЙ СДЕЛКИ =============
@router.message(Command("mydel"))
async def delete_my_trade(message: Message):
    """Удалить свою открытую сделку по ID"""
    user_id = message.from_user.id
    
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer(
            "❌ Укажите ID сделки для удаления\n\n"
            "Пример: /mydel 5\n\n"
            "Чтобы узнать ID сделки, посмотрите в /history"
        )
        return
    
    try:
        trade_id = int(parts[1])
    except ValueError:
        await message.answer("❌ ID должен быть числом")
        return
    
    trade = Database.get_trade_by_id(trade_id)
    
    if not trade:
        await message.answer(f"❌ Сделка с ID {trade_id} не найдена")
        return
    
    if trade.user_id != user_id:
        await message.answer("⛔ Вы можете удалять только свои сделки!")
        return
    
    if trade.status == 'closed':
        await message.answer("❌ Нельзя удалить закрытую сделку")
        return
    
    if Database.delete_trade(trade_id):
        await message.answer(
            f"✅ Сделка #{trade_id} удалена!\n\n"
            f"🪙 {trade.symbol}\n"
            f"📈 {trade.direction}\n"
            f"💰 {trade.position_size}$\n"
            f"📅 {trade.date.strftime('%d.%m.%Y')}"
        )
    else:
        await message.answer(f"❌ Ошибка при удалении сделки #{trade_id}")