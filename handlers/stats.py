# handlers/stats.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.filters import Command
from keyboards.menu import main_menu, stats_menu
from database.db import Database
from services.statistics import StatisticsService
from services.charts import ChartService
from services.export import ExportService
from datetime import datetime

router = Router()

@router.message(Command("stats"))
async def stats_command(message: Message):
    await show_stats(message, message.from_user.id)

@router.callback_query(F.data == "stats")
async def stats_callback(callback: CallbackQuery):
    await callback.message.delete()
    await show_stats(callback.message, callback.from_user.id)
    await callback.answer()

async def show_stats(message: Message, user_id: int):
    # 👇 ИСПРАВЛЕНО: используем Database.get_stats напрямую
    stats = Database.get_stats(user_id)
    current_deposit = Database.get_current_deposit(user_id)
    user = Database.get_or_create_user(user_id)
    
    if stats['total'] == 0:
        await message.answer(
            "📊 Статистика\n\n"
            "Нет закрытых сделок.",
            reply_markup=main_menu()
        )
        return
    
    text = (
        f"📊 Статистика\n\n"
        f"Всего сделок: {stats['total']}\n"
        f"Побед: {stats['wins']}\n"
        f"Поражений: {stats['losses']}\n"
        f"Безубыточных: {stats['breakevens']}\n"
        f"Win Rate: {stats['win_rate']:.2f}%\n"
        f"Общий PnL: {'+' if stats['total_pnl'] > 0 else ''}{stats['total_pnl']:.2f}$\n"
        f"Текущий депозит: {current_deposit:.2f}$\n"
        f"Начальный депозит: {user.initial_deposit:.2f}$\n"
        f"Средняя прибыль: +{stats['avg_profit']:.2f}$\n"
        f"Средний убыток: -{abs(stats['avg_loss']):.2f}$\n"
        f"Profit Factor: {stats['profit_factor']:.2f}\n"
        f"Макс. серия побед: {stats['max_wins']}\n"
        f"Макс. серия убытков: {stats['max_losses']}"
    )
    
    await message.answer(text, reply_markup=stats_menu())

@router.callback_query(F.data == "stats_setups")
async def stats_setups(callback: CallbackQuery):
    await callback.message.delete()
    
    setups = Database.get_stats_by_setup(callback.from_user.id)
    
    if not setups:
        await callback.message.answer(
            "📊 Статистика по сетапам\n\n"
            "Нет данных.",
            reply_markup=main_menu()
        )
        await callback.answer()
        return
    
    text = "📊 Статистика по сетапам\n\n"
    
    sorted_setups = sorted(setups.items(), key=lambda x: x[1]['win_rate'], reverse=True)
    
    for i, (setup, data) in enumerate(sorted_setups, 1):
        emoji = "🏆" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "  "
        text += (
            f"{emoji} {i}. {setup}\n"
            f"   Всего: {data['total']}\n"
            f"   Win Rate: {data['win_rate']:.1f}%\n"
            f"   PnL: {'+' if data['pnl'] > 0 else ''}{data['pnl']:.2f}$\n\n"
        )
    
    await callback.message.answer(text, reply_markup=main_menu())
    await callback.answer()

@router.callback_query(F.data == "stats_months")
async def stats_months(callback: CallbackQuery):
    await callback.message.delete()
    
    months = Database.get_stats_by_month(callback.from_user.id)
    
    if not months:
        await callback.message.answer(
            "📊 Статистика по месяцам\n\n"
            "Нет данных.",
            reply_markup=main_menu()
        )
        await callback.answer()
        return
    
    text = "📊 Статистика по месяцам\n\n"
    
    sorted_months = sorted(months.items())
    
    for month, data in sorted_months:
        month_names = {
            '01': 'Январь', '02': 'Февраль', '03': 'Март',
            '04': 'Апрель', '05': 'Май', '06': 'Июнь',
            '07': 'Июль', '08': 'Август', '09': 'Сентябрь',
            '10': 'Октябрь', '11': 'Ноябрь', '12': 'Декабрь'
        }
        month_parts = month.split('-')
        month_name = month_names.get(month_parts[1], month_parts[1])
        
        text += (
            f"📅 {month_name} {month_parts[0]}\n"
            f"{'🟢' if data['pnl'] > 0 else '🔴' if data['pnl'] < 0 else '⚪'} "
            f"{'+' if data['pnl'] > 0 else ''}{data['pnl']:.2f}$\n"
            f"WR {data['win_rate']:.1f}%\n"
            f"Сделок: {data['total']}\n"
            f"-----------------\n\n"
        )
    
    await callback.message.answer(text, reply_markup=main_menu())
    await callback.answer()

@router.callback_query(F.data == "stats_symbols")
async def stats_symbols(callback: CallbackQuery):
    await callback.message.delete()
    
    symbols = Database.get_stats_by_symbol(callback.from_user.id)
    
    if not symbols:
        await callback.message.answer(
            "📊 Статистика по монетам\n\n"
            "Нет данных.",
            reply_markup=main_menu()
        )
        await callback.answer()
        return
    
    text = "📊 Статистика по монетам\n\n"
    for symbol, pnl in symbols.items():
        emoji = "🟢" if pnl > 0 else "🔴" if pnl < 0 else "⚪"
        text += f"{emoji} {symbol}: {'+' if pnl > 0 else ''}{pnl:.2f}$\n"
    
    await callback.message.answer(text, reply_markup=main_menu())
    await callback.answer()

@router.callback_query(F.data == "stats_chart")
async def stats_chart(callback: CallbackQuery):
    await callback.message.delete()
    
    history = Database.get_deposit_history(callback.from_user.id)
    
    if len(history) < 2:
        await callback.message.answer(
            "📊 График депозита\n\n"
            "Недостаточно данных для построения графика.",
            reply_markup=main_menu()
        )
        await callback.answer()
        return
    
    chart = ChartService.create_deposit_chart(history)
    if chart:
        await callback.message.answer_photo(
            BufferedInputFile(chart.getvalue(), filename="deposit_chart.png"),
            caption=f"📊 График депозита\n"
                    f"Начальный: {history[0]:.2f}$\n"
                    f"Текущий: {history[-1]:.2f}$\n"
                    f"Изменение: {'+' if history[-1] - history[0] > 0 else ''}{history[-1] - history[0]:.2f}$",
            reply_markup=main_menu()
        )
    
    await callback.answer()

# ============= ЭКСПОРТ В EXCEL =============

@router.callback_query(F.data == "export_excel")
async def export_excel(callback: CallbackQuery):
    await callback.message.delete()
    
    trades = Database.get_all_trades(callback.from_user.id)
    
    if not trades:
        await callback.message.answer(
            "❌ Нет сделок для экспорта.",
            reply_markup=main_menu()
        )
        await callback.answer()
        return
    
    await callback.message.answer(
        "⏳ Генерация Excel файла..."
    )
    
    excel_file = ExportService.export_to_excel(callback.from_user.id)
    
    if excel_file:
        await callback.message.delete()
        
        await callback.message.answer_document(
            BufferedInputFile(
                excel_file.getvalue(), 
                filename=f"дневник_трейдера_{callback.from_user.id}_{datetime.now().strftime('%Y%m%d')}.xlsx"
            ),
            caption="📊 Ваш дневник сделок в Excel!\n\n"
                    "Файл содержит:\n"
                    "📋 Все сделки с деталями\n"
                    "📊 Статистику\n"
                    "📈 Анализ по сетапам",
            reply_markup=main_menu()
        )
    else:
        await callback.message.answer(
            "❌ Ошибка при создании Excel файла.",
            reply_markup=main_menu()
        )
    
    await callback.answer()

@router.callback_query(F.data == "export_template")
async def export_template(callback: CallbackQuery):
    await callback.message.delete()
    
    template = ExportService.export_trade_template()
    
    await callback.message.answer_document(
        BufferedInputFile(
            template.getvalue(),
            filename="шаблон_сделок.xlsx"
        ),
        caption="📋 Шаблон для импорта сделок\n\n"
                "Заполните данные и отправьте мне для импорта.",
        reply_markup=main_menu()
    )
    
    await callback.answer()